#!/usr/bin/python3

import telebot
from telebot import types

# telethon
from telethon import TelegramClient
from telethon.tl.functions.contacts import ResolveUsernameRequest
from telethon.tl.functions.messages import GetDialogsRequest, ForwardMessagesRequest
from telethon.tl.types import UpdateShortMessage, UpdateNewChannelMessage, PeerUser, PeerChannel, InputPeerSelf

from config import *
from functions import *
from models import BaseModel, User

bot = telebot.TeleBot(bot_token)  # bot init
bot_id = int(bot_token.split(':')[0])

clients = init_clients()






@bot.message_handler(commands=['is_auth'])
def is_auth(m):
	u = User.cog(m)

	if clients[u.sname].is_user_authorized():
		bot.send_message(uid(m), "Auth")
	else:
		keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
		share_contact_btn = types.KeyboardButton(s.share_contact, request_contact=True)
		keyboard.row(share_contact_btn)
		bot.send_message(uid(m), "Not auth", reply_markup=keyboard, parse_mode="Markdown")


@bot.message_handler(content_types=['text'])
def auth_user(m):
	u = User.cog(m)
	cl = clients.get(u.sname)
	code = m.text[::-1]
	print(code)
	cl.sign_in(code=code)


@bot.message_handler(content_types=['contact'])
def contact(m):
	u = User.cog(m)
	u.phone = m.contact.phone_number
	u.save()
	if clients[u.sname].is_user_authorized():
		return
	clients[u.sname].sign_in(phone=u.phone)



if __name__ == '__main__':
	# if client.is_user_authorized():
	# 	client.add_update_handler(update_handler)
	# else:
	# 	reauth()

	bot.polling(none_stop=True)