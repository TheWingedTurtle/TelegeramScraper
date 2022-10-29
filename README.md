# TelegeramScraper

## Requirement
A utility which can get listen the telegram channels 
and save the message in a machine-readable format.

## Introduction
This project uses [Telethon](https://pypi.org/project/Telethon/) to connect to telegram web APIs. Upon connection, it 
creates an Entity of type channel, and listens to new messages posted on the channel.

## Important prerequisites
Telegram provides web APIs for interacting with it. To authenticate the usage of these APIs, user needs to get following
1. API-ID
2. API-HASH
3. User id
4. Phone number

Visit [MyTelegram](https://my.telegram.org/auth) and fill out the form. In the form, basic details are fine. Upon filling
the same, API-ID, API-HASH will appear on  screen. Take a screenshot


## For the impatient
1. Download the project
2. Fill up the config.ini with details gathered in prerequisites section
3. Run the following in the root directory
```commandline
pip3 install aiofiles
pip3 install telethon
python main.py
```
4. Script asks for channel ids if not earlier put in config.ini. Fill space separated channel ids.  
5. New messages will be stored in `<channel-id>.messages.json`.

## Additional info
* Although targeted specifically for messages, telethon can be used to scrape all kinds of telegram entity. With slight 
tweak and additional configurations, it can be done. Such features will be added here in the future.
* There is also a branch which has all the code in a single script file. 
* Please feel free to file bugs and add fetures.

