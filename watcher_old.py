from telethon import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
from telethon.errors import SessionPasswordNeededError

from getpass import getpass
from os import environ

from time import sleep
import sys
from config import *


client = TelegramClient('qqq', api_id, api_hash, update_workers = 4)
client.connect()



def main():


	if not client.is_user_authorized():
		print('INFO: Unauthorized user')
		client.send_code_request(user_phone)
		code_ok = False
		while not code_ok:
			code = input('Enter the auth code: ')
			try:
				code_ok = client.sign_in(user_phone, code)
			except SessionPasswordNeededError:
				password = getpass('Two step verification enabled. Please enter your password: ')
				code_ok = client.sign_in(password=password)
	client.add_update_handler(update_handler)
	while True:
		sleep(1)

def update_handler(update):
	print(update.message.message)

if __name__ == '__main__':
	main()