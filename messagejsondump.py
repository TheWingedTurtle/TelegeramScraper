import aiofiles as aiofiles


async def dump(messages, prefix: str):
    with open(prefix + '.' 'messages.json', 'w') as outfile:
        for message in messages:
            if 'message' in message.to_dict():
                outfile.write(message.to_dict()['message'])
                outfile.write('\n')


async def dump_new_messages(message, channel_id):
    async with aiofiles.open(str(channel_id) + '.' 'messages.json', 'w') as f:
        if 'message' in message.to_dict():
            await f.write(message.to_dict()['message'] + '\n')
