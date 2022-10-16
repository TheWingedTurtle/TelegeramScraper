import asyncio

import telethon
from telethon import events
from telethon.tl.types import PeerChannel

import messagejsondump


async def async_read_new_messages(channel_id: int, client: telethon.TelegramClient):
    client.add_event_handler(lambda event: messagejsondump.dump_new_messages(event.message, channel_id),
                             events.NewMessage(chats=channel_id))
    print('Async task to read new messages scheduled. Messages will be dumped at ' + str(channel_id) + '.messages.json')
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

        await messagejsondump.dump(messages, str(channel.channel_id))
        last_offset = messages[len(messages) - 1].id


async def read_multiple_channels_all_messages(channel_ids: list, client: telethon.TelegramClient):
    channel_tasks = []
    for channel_id in channel_ids:
        entity = PeerChannel(int(channel_id))
        channel = await client.get_input_entity(entity)
        channel_tasks.append(asyncio.create_task(read_all_channel_messages(channel, client)))
        print('Async task to dump messages scheduled. Messages will be dumped at ' + str(channel_id) + '.messages.json')
    [await task for task in channel_tasks]
