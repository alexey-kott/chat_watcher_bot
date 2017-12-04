#!/usr/bin/python3
from time import sleep
import sys
from multiprocessing import Process
import traceback

import telebot
from telebot import types
import sqlite3 as sqlite
import re
from peewee import *
from playhouse.sqlite_ext import *
# telethon
from telethon import TelegramClient
from telethon.tl.functions.contacts import ResolveUsernameRequest
from telethon.tl.functions.messages import GetDialogsRequest, ForwardMessagesRequest
from telethon.tl.types import UpdateShortMessage, UpdateNewChannelMessage, PeerUser, PeerChannel, InputPeerSelf

import strings as s

from config import *
from functions import *
from models import BaseModel, FTSEntry, Word, User, Routing

bot = telebot.TeleBot(bot_token)  # bot init
bot_id = int(bot_token.split(':')[0])

clients = init_clients()


# db = SqliteExtDatabase('bot.db', threadlocals=True) # DB

# owner = 5844335 # бот для единственного пользователя, так что всех остальных шлём лесом 
# owner = 328241232
# owner = 450968679
# owner = 273167770 # Денис Давыдов

# client = TelegramClient("u{}".format(owner), api_id, api_hash, update_workers = 4)
# client.connect()
# client.sign_in(phone=phone)
# code = int(input())
# me = client.sign_in(code=code)  # Put whatever code you received here.
# exit()





def update_handler(update):
	# # print(get_text(update))
	# sender = get_sender(update)
	# if sender is False:
	# 	# print(update)
	# 	return

	# if sender.id == bot_id:
	# 	return False

	# print(update)
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

	if check_msg(get_text(update)):
		# bot.send_message(owner, s.forward.format(f.get_full_user_name(sender), get_text(update)))
		try:
			client(ForwardMessagesRequest(
				from_peer=sender,  # who sent these messages?
				id=messages,  # which are the messages?
				to_peer=InputPeerSelf()  # who are we forwarding them to?
			))
			print("FORWARD")
			print(get_text(update))
		except Exception as e:
			print("EXCEPTION")
			print(get_text(update))
			print(e)


# FUNCTIONS

def auth(u, m):
	u.state = ''
	u.save()
	code = m.text  # TODO: дописать проверку на цифры
	cl = clients.get(u.sname)
	cl.sign_in(code=code)

	if cl.is_user_authorized():
		print("AUTH SUCCESS")
		bot.send_message(uid(m), s.manual, reply_markup=add_and_remove_keyboard())
	else:
		print("AUTH FAILED")
		bot.send_message(uid(m), "Ошибка.")
		# reauth()


def get_sender(update):
	sender = False
	if isinstance(update, UpdateShortMessage):
		sender = client.get_entity(PeerUser(update.user_id))
	elif isinstance(update, UpdateNewChannelMessage):
		sender = client.get_entity(PeerUser(update.message.from_id))
	else:
		# print(update)
		pass
	return sender


def check_msg(m):
	msg = re.sub('\W+|\d+', ' ', m)
	msg = re.sub('\s+', ' ', msg.strip())
	words = [w.lower() for w in msg.split(' ')]
	words = list(set(words))
	query = (FTSEntry
			 .select()
			 .join(
		Word,
		on=(FTSEntry.entry_id == Word.id).alias('word')
	)
			 .where(FTSEntry.match(' OR '.join(words)))
			 .dicts()
			 )
	result = [q for q in query]
	return len(result)


def add_words(u, m):
	msg = re.sub('\W+', ' ', m.text)
	words = [w.lower() for w in msg.split(' ') if len(w) > 2]
	words = list(set(words))
	for w in words:
		word = Word.cog(word=w)
		FTSEntry.create(
			entry_id=word.id,
			content=word.word
		)
	u.state = ''
	u.save()
	bot.send_message(uid(m), s.word_added)


# HANDLERS

@bot.message_handler(commands=['init'])
def init(m):
	FTSEntry.create_table(fail_silently=True)
	Word.create_table(fail_silently=True)
	User.create_table(fail_silently=True)
	Routing.create_table(fail_silently=True)


@bot.message_handler(commands=['is_auth'])
def is_auth(m):
	u = User.cog(m)
	if clients[u.sname].is_user_authorized():
		bot.send_message(uid(m), "Auth")
	else:
		bot.send_message(uid(m), "Not auth")


@bot.message_handler(commands=['start'])
def start(m):
	u = User.cog(m)
	clients[u.sname] = TelegramClient(u.sname, api_id, api_hash, update_workers=4)
	clients[u.sname].connect()

	if clients[u.sname].is_user_authorized():
		bot.send_message(uid(m), s.manual, reply_markup=add_and_remove_keyboard(), parse_mode="Markdown")
	else:
		keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
		share_contact_btn = types.KeyboardButton(s.share_contact, request_contact=True)
		keyboard.row(share_contact_btn)
		bot.send_message(uid(m), s.need_auth, reply_markup=keyboard, parse_mode="Markdown")
		# bot.send_message(uid(m), s.manual, reply_markup = keyboard, parse_mode = "Markdown")


def reauth():
	try:
		u = User.select().where(User.user_id == owner).get()
	except:
		return
	keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
	share_contact_btn = types.KeyboardButton(s.share_contact, request_contact=True)
	keyboard.row(share_contact_btn)
	bot.send_message(u.user_id, s.reauth, reply_markup=keyboard, parse_mode="Markdown")


@bot.message_handler(func=lambda x: x.text == s.add_words)
def new_words(m):
	u = User.cog(m)
	u.state = s.new_words
	u.save()
	keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
	if client.is_user_authorized():
		add_words_btn = types.KeyboardButton(s.add_words)
		remove_words_btn = types.KeyboardButton(s.remove_words)
		keyboard.row(add_words_btn, remove_words_btn)
	bot.send_message(sid(m), s.type_new_words, reply_markup=keyboard)


@bot.message_handler(func=lambda x: x.text == s.remove_words)
def remove_words(m):
	u = User.cog(m)
	u.state = ''
	u.save()
	words = (Word
			 .select(Word)
			 .dicts()
			 )
	keyboard = types.InlineKeyboardMarkup()

	for w in words:
		callback_button = types.InlineKeyboardButton(text=w['word'], callback_data=str("remove {}".format(w['id'])))
		keyboard.add(callback_button)
	bot.send_message(sid(m), s.select_removing_words, reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data.split(" ")[0] == "remove")
def remove_word(c):
	word_id = c.data.split(" ")[1]
	word = Word.get(Word.id == word_id)
	word.delete_instance()
	words = Word.select(Word)
	keyboard = types.InlineKeyboardMarkup()
	if len(words) == 0:
		bot.send_message(cid(c), s.empty_words)
	for w in words:
		callback_button = types.InlineKeyboardButton(text=w.word, callback_data=str("remove {}".format(w.id)))
		keyboard.add(callback_button)
	bot.edit_message_reply_markup(chat_id=cid(c), message_id=c.message.message_id, reply_markup=keyboard)


@bot.message_handler(content_types=['contact'])
def contact(m):
	u = User.cog(m)
	u.state = s.send_contact
	u.phone = m.contact.phone_number
	u.save()
	if clients[u.sname].is_user_authorized():
		return
	clients[u.sname].sign_in(phone=u.phone)
	keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
	add_words_btn = types.KeyboardButton(s.add_words)
	remove_words_btn = types.KeyboardButton(s.remove_words)
	keyboard.row(add_words_btn, remove_words_btn)
	bot.send_message(uid(m), s.type_code, reply_markup=keyboard, parse_mode="Markdown")


@bot.message_handler(content_types=['text'])
def action(m):
	u = User.cog(m)
	try:
		r = Routing.get(state=u.state, decision='text')
		try:  # на случай если action не определён в таблице роутинга
			eval(r.action)(u=u, m=m)
		except Exception as e:
			# print(e)
			# print(m)
			keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
			if clients[u.sname].is_user_authorized():
				print("CLIENT AUTH")
				add_words_btn = types.KeyboardButton(s.add_words)
				remove_words_btn = types.KeyboardButton(s.remove_words)
				keyboard.row(add_words_btn, remove_words_btn)
			bot.send_message(uid(m), s.select_action, reply_markup=keyboard)
	except Exception as e:
		pass
		print(e)


if __name__ == '__main__':
	# if client.is_user_authorized():
	# 	client.add_update_handler(update_handler)
	# else:
	# 	reauth()

	bot.polling(none_stop=True)
