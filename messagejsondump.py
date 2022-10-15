import json


async def dump(messages, entity):
    with open(str(entity.channel_id) + '.' 'messages.json', 'w') as outfile:
        for message in messages:
            if 'message' in message.to_dict():
                json.dump(message.to_dict()['message'], outfile, indent=2)
                outfile.write('\n')
