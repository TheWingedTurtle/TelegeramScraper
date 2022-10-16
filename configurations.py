# Configurations holds the config.ini readers
from configparser import ConfigParser

cp = ConfigParser()
cp.read('config.ini')


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
