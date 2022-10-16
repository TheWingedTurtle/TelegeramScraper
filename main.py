import asyncio
import sys

import telethon
from telethon.errors import SessionPasswordNeededError

import channeltasks
from configurations import UserInfo, ChannelsInfo


async def init():
    user = UserInfo()
    client = telethon.TelegramClient(user.username, user.api_id, user.api_hash)
    await client.start()
    if not await client.is_user_authorized():
        await client.send_code_request(user.phone)
        try:
            print("Using Phone number: " + user.phone)
            await client.sign_in(user.phone, input('Enter the code: '))
        except SessionPasswordNeededError:
            await client.sign_in(password=input('Password: '))
    return user, client


async def main():
    user, client = await init()
    channels = ChannelsInfo()
    channel_tasks = []
    for channel_id in channels.channel_ids:
        channel_tasks.append(asyncio.create_task(channeltasks.async_read_new_messages(channel_id, client)))
    [await task for task in channel_tasks]


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Keyboard Interrupt. Exiting..")
        sys.exit(0)
