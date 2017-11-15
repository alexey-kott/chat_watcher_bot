from telebot import types
from telethon import TelegramClient
from telethon.tl.types import UpdateShortMessage, UpdateNewChannelMessage

from models import User
from config import *
import strings as s

#	sid 	= sender chat id
#	m 		= message
#	cog 	= create_or_get
sid = lambda m: m.chat.id # лямбды для определения адреса ответа
uid = lambda m: m.from_user.id
cid = lambda c: c.message.chat.id
check_owner = lambda m: uid(m) == owner

def get_full_user_name(user):
	username = ''
	last_name = ''
	if user.username is not None:
		username = "(@{})".format(user.username)
	if user.last_name is not None:
		last_name = user.last_name
	result = '{} {} {}'.format(user.first_name, username, last_name)
	return result


def get_text(update):
	if isinstance(update, UpdateShortMessage):
		return update.message
	elif isinstance(update, UpdateNewChannelMessage):
		return update.message.message

def init_clients():
	clients = dict()
	for u in User.select():
		clients[u.sname] = TelegramClient(u.sname, api_id, api_hash, update_workers=4)
		clients[u.sname].connect()
	return clients

def add_and_remove_keyboard():
	keyboard = types.ReplyKeyboardMarkup(resize_keyboard = True)
	add_words_btn = types.KeyboardButton(s.add_words)
	remove_words_btn = types.KeyboardButton(s.remove_words)
	keyboard.row(add_words_btn, remove_words_btn)
	return keyboard
