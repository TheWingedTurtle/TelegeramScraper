import asyncio
import logging
from configparser import ConfigParser

import aio_pika
import aiofiles
import telethon
from telethon import events
from telethon.errors import SessionPasswordNeededError

cp = ConfigParser()
cp.read('config.ini')

mq_config = {}

logging.basicConfig(filename='tgbot.log', filemode='a', format='%(asctime)s - %(message)s', level=logging.INFO)


class UserInfo:
    def __init__(self):
        self.username = \
            cp['Telegram']['username'] if cp['Telegram']['username'] != 'unset' else None
        self.api_id = \
            cp['Telegram']['api_id'] if cp['Telegram']['api_id'] != 'unset' else None
        self.api_hash = \
            cp['Telegram']['api_hash'] if cp['Telegram']['api_hash'] != 'unset' else None
        self.phone = \
            cp['Telegram']['phone'] if cp['Telegram']['phone'] != 'unset' else None


async def init():
    user = UserInfo()
    if user.username is None or user.phone is None or user.api_id is None or user.api_hash is None:
        raise Exception("Please fill the config.ini")
    client = telethon.TelegramClient(user.username, int(user.api_id), user.api_hash)
    await client.start()
    if not await client.is_user_authorized():
        await client.send_code_request(user.phone)
        try:
            logging.info("Using Phone number: " + user.phone)
            await client.sign_in(user.phone, input('Enter the code: '))
        except SessionPasswordNeededError:
            await client.sign_in(password=input('Password: '))
    return user, client


class ChannelsInfo:
    def __init__(self):
        self.channel_ids = []
        channels = cp['Telegram']['channel_ids']
        if channels == 'unset':
            raise Exception("Please fill the details in config.ini")
        for w in channels.split(' '):
            self.channel_ids.append(w)


async def init_rmq(ext_loop, channel_id):
    mq_config['enabled'] = True
    mq_connection = await aio_pika.connect_robust(
        "amqp://guest:guest@127.0.0.1/", loop=ext_loop, timeout=60
    )
    mq_config['connection']: aio_pika.abc.AbstractRobustConnection = mq_connection
    channel = await mq_connection.channel()
    mq_config['channel']: aio_pika.abc.AbstractRobustChannel = channel
    exchange = await channel.declare_exchange('direct', auto_delete=True, robust=True)
    mq_config['exchange'] = exchange
    queue = await channel.declare_queue(cp['RabbitMQ']['queue_name'] + "_" + str(channel_id),
                                        auto_delete=True, robust=True)
    await queue.bind(exchange, str(channel_id))
    mq_config['queue'] = queue


async def dump_new_messages(message, channel_id):
    try:
        if cp['RabbitMQ']['enabled']:
            await init_rmq(asyncio.get_running_loop(), channel_id)
            exchange: aio_pika.abc.AbstractRobustExchange = mq_config['exchange']
            if 'message' in message.to_dict():
                message_body = message.to_dict()['message']
                logging.info("Sending message: " + str(message_body))
                await exchange.publish(
                    aio_pika.Message(body=message_body.encode()), str(channel_id))
        else:
            async with aiofiles.open(str(channel_id) + '.' 'messages.json', 'w') as f:
                if 'message' in message.to_dict():
                    await f.write(message.to_dict()['message'] + '\n')
    except Exception as e:
        logging.info("Exception occurred:" + str(e))
    finally:
        await mq_config['connection'].close()


async def async_read_new_messages(channel_id: str, client: telethon.TelegramClient):
    chat_id = channel_id
    if not channel_id.isnumeric():
        entity = await client.get_entity(channel_id)
        chat_id = int(entity.id)
    client.add_event_handler(lambda event: dump_new_messages(event.message, channel_id),
                             events.NewMessage(chats=chat_id))
    logging.info('Async task to read new messages scheduled.')
    return await client.run_until_disconnected()


async def read_all_channel_messages(channel: str, client: telethon.TelegramClient):
    last_offset = -1
    limit = 100
    try:
        if channel.isnumeric():
            entity = None
            async for d in client.iter_dialogs(offset_id=int(channel)):
                if int(d.entity.id) == int(channel):
                    entity = d.entity
                    break
            if entity is None:
                raise ValueError
        else:
            entity = await client.get_entity(channel)
    except ValueError:
        logging.info("No entity found for " + channel)
        return

    while True:
        # First run
        if last_offset == -1:
            messages = await client.get_messages(entity=entity, reverse=False, limit=100)
        else:
            messages = await client.get_messages(entity=entity, reverse=False, max_id=last_offset, limit=limit)

        if messages is None or len(messages) == 0:
            break

        print(messages)
        last_offset = messages[len(messages) - 1].id


async def main():
    user, client = await init()
    channels = ChannelsInfo()
    channel_tasks = []
    for channel_id in channels.channel_ids:
        channel_tasks.append(asyncio.create_task(async_read_new_messages(channel_id, client)))
    [await task for task in channel_tasks]


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logging.info("Keyboard Interrupt. Exiting..")
        if loop.is_running():
            loop.stop()
