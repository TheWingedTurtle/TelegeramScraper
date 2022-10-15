import asyncio

import telethon
from telethon.errors import SessionPasswordNeededError
from telethon.tl.types import PeerChannel

import messagejsondump
from userinfo import UserInfo


async def main():
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

    channel_id = input('enter channel id:')
    if channel_id.isdigit():
        entity = PeerChannel(int(channel_id))
    else:
        print("Enter proper channel id")
        channel_id = input("Channel id: ")
        if channel_id.isdigit():
            entity = PeerChannel(int(channel_id))
        else:
            raise Exception("Incorrect channel id format. Expected integer channel id")

    channel = await client.get_input_entity(entity)
    last_offset = -1
    limit = 100
    allTasks = []
    while True:
        # First run
        if last_offset == -1:
            messages = await client.get_messages(entity=channel, reverse=False, limit=100)
        else:
            messages = await client.get_messages(entity=channel, reverse=False, max_id=last_offset, limit=limit)
        if messages is None or len(messages) == 0:
            break

        allTasks.append(asyncio.create_task(messagejsondump.dump(messages, channel)))
        last_offset = messages[len(messages) - 1].id

    [await task for task in allTasks]

if __name__ == '__main__':
    asyncio.run(main())
