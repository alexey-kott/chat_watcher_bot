from telethon import TelegramClient
from config import *

owner = 328241232


client = TelegramClient("u{}".format(owner), api_id, api_hash, update_workers = 4)
client.connect()
if client.is_user_authorized():
	print("User already authorized")
	exit()
client.sign_in(phone=phone)
code = int(input())
me = client.sign_in(code=code)  # Put whatever code you received here.
exit()