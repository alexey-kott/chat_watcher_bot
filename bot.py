#!/usr/bin/python3
# bot
import telebot
from telebot import types
import sqlite3 as sqlite
import re
from peewee import *
from playhouse.sqlite_ext import *

# telethon
from telethon import TelegramClient
from telethon.tl.functions.contacts import ResolveUsernameRequest
from telethon.tl.types import UpdateShortMessage, UpdateNewChannelMessage, PeerUser, PeerChannel


import strings as s
from time import sleep
import sys
from config import *
from multiprocessing import Process
import functions as f
import traceback




# README
#
# Shortcuts:
#	sid 	= sender chat id
#	m 		= message
#	cog 	= create_or_get


bot = telebot.TeleBot(bot_token) # bot init
bot_id = int(bot_token.split(':')[0])

db = SqliteExtDatabase('bot.db', threadlocals=True) # DB

sid = lambda m: m.chat.id # лямбды для определения адреса ответа
uid = lambda m: m.from_user.id
cid = lambda c: c.message.chat.id
check_owner = lambda m: uid(m) == owner

owner = 5844335 # бот для единственного пользователя, так что всех остальных шлём лесом 
# owner = 328241232
# owner = 450968679
# owner = 273167770 # Денис Давыдов

client = TelegramClient("u{}".format(owner), api_id, api_hash, update_workers = 4)
client.connect()
# client.sign_in(phone=phone)
# code = int(input())
# me = client.sign_in(code=code)  # Put whatever code you received here.
# exit()

class BaseModel(Model):
	class Meta:
		database = db


class FTSEntry(FTSModel):
	entry_id = IntegerField(unique = True)
	content = TextField()

	class Meta:
		database = db

class Word(BaseModel):
	word = TextField(unique = True)

	def cog(word):
		try:
			with db.atomic():
				return Word.create(word = word)
		except:
			return Word.get(word = word)

class User(BaseModel):
	user_id 	= IntegerField(unique = True)
	username 	= TextField()
	first_name 	= TextField()
	last_name 	= TextField(null = True)
	phone		= IntegerField(null = True)
	state 		= TextField(null = True)

	def cog(m):
		user_id 	= uid(m)
		username 	= m.from_user.username
		first_name 	= m.from_user.first_name
		last_name 	= m.from_user.last_name

		try:
			with db.atomic():
				return User.create(user_id = user_id, username = username, first_name = first_name, last_name = last_name)
		except:
			return User.get(user_id = user_id)
			
class Routing(BaseModel):
	state 		= TextField()
	decision 	= TextField() # соответствует либо атрибуту data в инлайн кнопках, 
							  # либо специальному значению text, которое соответствует любому текстовому сообщению
	action		= TextField()

	class Meta:
		primary_key = CompositeKey('state', 'decision')


def update_handler(update):
	# print(get_text(update))
	sender = get_sender(update)
	if sender is False:
		# print(update)
		return

	if sender.id == bot_id:
		return False

	if check_msg(get_text(update)):
		bot.send_message(owner, s.forward.format(f.get_full_user_name(sender), get_text(update)))


# FUNCTIONS

def auth(u, m):
	u.state = ''
	u.save()
	code = m.text
	client.sign_in(code=code)
	if client.is_user_authorized():
		client.add_update_handler(update_handler)
	else:
		bot.send_message(u.user_id, "Ошибка.")
		reauth()


def get_text(update):
	if isinstance(update, UpdateShortMessage):
		return update.message
	elif isinstance(update, UpdateNewChannelMessage):
		return update.message.message

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
	# print(m)
	msg = re.sub('\W+', ' ', m)
	# print(msg)
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
	listeners = dict() # юзеры, которые подписались на это слово
	result = [q for q in query]
	return len(result)


def add_words(u, m):
	msg = re.sub('\W+', ' ', m.text)
	words = [w.lower() for w in msg.split(' ') if len(w) > 2]
	words = list(set(words))
	for w in words:
		word = Word.cog(word = w)
		FTSEntry.create(
			entry_id = word.id,
			content = word.word
			)
	u.state = ''
	u.save()
	bot.send_message(uid(m), s.word_added)



# HANDLERS

@bot.message_handler(commands = ['init'])
def init(m):
	FTSEntry.create_table(fail_silently = True)
	Word.create_table(fail_silently = True)
	User.create_table(fail_silently = True)
	Routing.create_table(fail_silently = True)


@bot.message_handler(commands = ['is_auth'])
def is_auth(m):
	if client.is_user_authorized():
		bot.send_message(uid(m), "Auth")
	else:
		bot.send_message(uid(m), "Not auth")





@bot.message_handler(commands = ['start'])
def start(m):
	if not check_owner(m):
		return False
	u = User.cog(m)
	keyboard = types.ReplyKeyboardMarkup(resize_keyboard = True)
	if client.is_user_authorized():
		add_words_btn = types.KeyboardButton(s.add_words)
		remove_words_btn = types.KeyboardButton(s.remove_words)
		keyboard.row(add_words_btn, remove_words_btn)
		bot.send_message(uid(m), s.manual, reply_markup = keyboard, parse_mode = "Markdown")
	else:
		share_contact_btn = types.KeyboardButton(s.share_contact, request_contact = True)
		keyboard.row(share_contact_btn)
		bot.send_message(uid(m), s.need_auth, reply_markup = keyboard, parse_mode = "Markdown")
		bot.send_message(uid(m), s.manual, reply_markup = keyboard, parse_mode = "Markdown")

def reauth():
	try:
		u = User.select().where(User.user_id == owner).get()
	except:
		return
	keyboard = types.ReplyKeyboardMarkup(resize_keyboard = True)
	share_contact_btn = types.KeyboardButton(s.share_contact, request_contact = True)
	keyboard.row(share_contact_btn)
	bot.send_message(u.user_id, s.reauth, reply_markup = keyboard, parse_mode = "Markdown")

	

@bot.message_handler(func=lambda x: x.text == s.add_words)
def new_words(m):
	u = User.cog(m)
	u.state = s.new_words
	u.save()
	bot.send_message(sid(m), s.type_new_words)

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
	bot.send_message(sid(m), s.select_removing_words, reply_markup = keyboard)


	
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
	bot.edit_message_reply_markup(chat_id = cid(c), message_id = c.message.message_id, reply_markup = keyboard)


@bot.message_handler(content_types = ['contact'])
def contact(m):
	u = User.cog(m)
	u.state = s.send_contact
	u.phone = m.contact.phone_number
	u.save()
	# client.connect()
	client.sign_in(phone=u.phone)
	keyboard = types.ReplyKeyboardMarkup(resize_keyboard = True)
	add_words_btn = types.KeyboardButton(s.add_words)
	remove_words_btn = types.KeyboardButton(s.remove_words)
	keyboard.row(add_words_btn, remove_words_btn)
	bot.send_message(uid(m), s.type_code, reply_markup = keyboard, parse_mode = "Markdown")




@bot.message_handler(content_types = ['text'])
def action(m):
	if not check_owner(m):
		return False
	u = User.cog(m)
	try:
		r = Routing.get(state = u.state, decision = 'text')
		try: # на случай если action не определён в таблице роутинга
			eval(r.action)(u = u, m = m)
		except Exception as e:
			print(e)
			print(m)
	except Exception as e:
		print(e)








if __name__ == '__main__':
	if client.is_user_authorized():
		client.add_update_handler(update_handler)
	else:
		reauth()

	bot.polling(none_stop=True)
