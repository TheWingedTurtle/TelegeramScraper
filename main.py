import asyncio
import sys
from configparser import ConfigParser

import aio_pika
import aiofiles
import telethon
from telethon import events
from telethon.errors import SessionPasswordNeededError
from telethon.tl.types import PeerChannel

cp = ConfigParser()
cp.read('config.ini')

mq_config = {}


async def init_rmq():
    mq_config['enabled'] = True
    mq_connection = await aio_pika.connect_robust()
    mq_connection.close_callbacks.add(mq_connection.reconnect)
    mq_config['connection']: aio_pika.abc.AbstractRobustConnection = mq_connection
    mq_config['routing_key'] = cp['RabbitMQ']['queue_route_key']
    channel = await mq_connection.channel()
    mq_config['channel']: aio_pika.abc.AbstractRobustChannel = channel
    exchange = await channel.declare_exchange('direct', auto_delete=True, robust=True)
    mq_config['exchange'] = exchange
    queue = await channel.declare_queue(cp['RabbitMQ']['queue_name'], auto_delete=True, robust=True)
    await queue.bind(exchange, cp['RabbitMQ']['queue_route_key'])
    mq_config['queue'] = queue


async def main():
    user, client = await init()
    channels = ChannelsInfo()
    channel_tasks = []
    if cp['RabbitMQ']['enabled'] == 'true':
        await init_rmq()
    for channel_id in channels.channel_ids:
        channel_tasks.append(asyncio.create_task(async_read_new_messages(channel_id, client)))
        # channel_tasks.append(asyncio.create_task(read_multiple_channels_all_messages([channel_id], client)))
    [await task for task in channel_tasks]


async def init():
    user = UserInfo()
    client = telethon.TelegramClient(user.username, int(user.api_id), user.api_hash)
    await client.start()
    if not await client.is_user_authorized():
        await client.send_code_request(user.phone)
        try:
            print("Using Phone number: " + user.phone)
            await client.sign_in(user.phone, input('Enter the code: '))
        except SessionPasswordNeededError:
            await client.sign_in(password=input('Password: '))
    return user, client


class UserInfo:
    def __init__(self):
        self.username = \
            cp['Telegram']['username'] if cp['Telegram']['username'] != 'unset' else input('Enter Telegram Username: ')
        self.api_id = \
            cp['Telegram']['api_id'] if cp['Telegram']['api_id'] != 'unset' else input('Enter api id: ')
        self.api_hash = \
            cp['Telegram']['api_hash'] if cp['Telegram']['api_hash'] != 'unset' else input('Enter api hash: ')
        self.phone = \
            cp['Telegram']['phone'] if cp['Telegram']['phone'] != 'unset' \
                else input('Enter phone number (including country code (+91 for India): ')


class ChannelsInfo:
    def __init__(self):
        self.channel_ids = []
        channels = cp['Telegram']['channel_ids']
        if channels == 'unset':
            channels = input('Enter space separated channel ids: ')
        for w in channels.split(' '):
            if w.isdigit():
                self.channel_ids.append(int(w))


async def dump(messages, prefix: str):
    if mq_config['enabled']:
        exchange: aio_pika.abc.AbstractRobustExchange = mq_config['exchange']
        for message in messages:
            if 'message' in message.to_dict():
                await exchange.publish(
                    aio_pika.Message(body=message.to_dict()['message'].encode()),
                    mq_config['routing_key']
                )
    with open(prefix + '.' 'messages.json', 'w') as outfile:
        for message in messages:
            if 'message' in message.to_dict():
                outfile.write(message.to_dict()['message'])
                outfile.write('\n')


async def dump_new_messages(message, channel_id):
    if mq_config['enabled']:
        exchange: aio_pika.abc.AbstractRobustExchange = mq_config['exchange']
        await exchange.publish(
            aio_pika.Message(body=message.to_dict()['message'].encode()),
            mq_config['routing_key'])
    else:
        async with aiofiles.open(str(channel_id) + '.' 'messages.json', 'w') as f:
            if 'message' in message.to_dict():
                await f.write(message.to_dict()['message'] + '\n')


async def async_read_new_messages(channel_id: int, client: telethon.TelegramClient):
    client.add_event_handler(lambda event: dump_new_messages(event.message, channel_id),
                             events.NewMessage(chats=channel_id))
    print('Async task to read new messages scheduled.')
    return await client.run_until_disconnected()


async def read_all_channel_messages(channel: telethon.types.InputPeerChannel, client: telethon.TelegramClient):
    last_offset = -1
    limit = 100
    while True:
        # First run
        if last_offset == -1:
            messages = await client.get_messages(entity=channel, reverse=False, limit=100)
        else:
            messages = await client.get_messages(entity=channel, reverse=False, max_id=last_offset, limit=limit)

        if messages is None or len(messages) == 0:
            break

        await dump(messages, str(channel.channel_id))
        last_offset = messages[len(messages) - 1].id


async def read_multiple_channels_all_messages(channel_ids: list, client: telethon.TelegramClient):
    channel_tasks = []
    for channel_id in channel_ids:
        entity = PeerChannel(int(channel_id))
        channel = await client.get_input_entity(entity)
        channel_tasks.append(asyncio.create_task(read_all_channel_messages(channel, client)))
        print('Async task to dump messages scheduled. Messages will be dumped at ' + str(channel_id) + '.messages.json')
    [await task for task in channel_tasks]


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Keyboard Interrupt. Exiting..")
        sys.exit(0)
    finally:
        connection: aio_pika.abc.AbstractRobustConnection = mq_config['connection']
        if not connection.is_closed:
            asyncio.run(connection.close())
