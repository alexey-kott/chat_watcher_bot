import argparse

from time import sleep
# telethon
from telethon import TelegramClient
from telethon.tl.functions.contacts import ResolveUsernameRequest
from telethon.tl.functions.messages import GetDialogsRequest, ForwardMessagesRequest
from telethon.tl.types import UpdateShortMessage, UpdateNewChannelMessage, PeerUser, PeerChannel, InputPeerSelf

from config import *
from functions import *
from models import BaseModel, FTSEntry, Word, User, Routing


def update_handler(update):
	try:
		message = update.message
		messages = []
		if isinstance(update, UpdateShortMessage):
			sender = client.get_entity(PeerUser(update.user_id))
			messages.append(update.id)
		elif isinstance(update, UpdateNewChannelMessage):
			sender = client.get_entity(PeerChannel(update.message.to_id.channel_id))
			# print(update.message.id)
			messages.append(update.message.id)
		elif isinstance(update, UpdateEditChannelMessage):
			pass
		else:
			# print(type(update))
			# print(update)
			return False
	except Exception as e:
		# print(e)
		return

	try:
		client(ForwardMessagesRequest(
		    from_peer=sender,  # who sent these messages?
		    id=messages,  # which are the messages?
		    to_peer=InputPeerSelf() # who are we forwarding them to?
		))
		print("FORWARD")
		# print(get_text(update))
	except Exception as e:
		print("EXCEPTION")
		print(get_text(update))
		print(e)



if __name__ == "__main__":
	arg_parser = argparse.ArgumentParser(description="Watcher forwards all messages which contain monitored words")
	arg_parser.add_argument('--user', '-u', type=int, help="Watched user id", required=True)
	# arg_parser.add_argument('--phone', '-ph', type=str, help="User phone", required=True)

	args = arg_parser.parse_args()


	client = TelegramClient("u{}".format(args.user), api_id, api_hash, update_workers = 4)
	client.connect()

	client.add_update_handler(update_handler)

	while True:
		sleep(1)