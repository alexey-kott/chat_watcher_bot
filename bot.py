#!/usr/bin/python3

import telebot
from telebot import types
import sqlite3 as sqlite
import re
import config as cfg
from peewee import *
from playhouse.sqlite_ext import *
import strings as s

from multiprocessing import Process
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.keys import Keys



# README
#
# Shortcuts:
#	sid 	= sender chat id
#	m 		= message
#	cog 	= create_or_get


bot = telebot.TeleBot(cfg.token)

db = SqliteExtDatabase('bot.db', threadlocals=True)




class BaseModel(Model):
	class Meta:
		database = db


class FTSEntry(FTSModel):
	entry_id = IntegerField()
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
	user_id = IntegerField(unique = True)
	username = TextField()
	state = TextField(null=True)

	def cog(m):
		user_id = m.from_user.id
		username = m.from_user.username

		try:
			with db.atomic():
				return User.get(user_id = user_id)
		except:
			return User.create(user_id = user_id, username = username)
			


class WordToUser(BaseModel):
	user_id = IntegerField()
	word_id = IntegerField()

	class Meta:
		primary_key = CompositeKey('user_id', 'word_id')

class ChatToUser(BaseModel):
	user_id = IntegerField()
	chat_id = IntegerField()
	chat_type = TextField(null = True)

	class Meta:
		primary_key = CompositeKey('user_id', 'chat_id')

class Chat(BaseModel):
	chat_id = IntegerField(unique = True)
	chat_name = TextField()
	joined = BooleanField(default = False)





def sid(m):
	return m.chat.id

def uid(m):
	return m.from_user.id

def cid(c):
	return c.from_user.id




@bot.message_handler(commands = ['init'])
def init(m):
	FTSEntry.create_table(fail_silently = True)
	Word.create_table(fail_silently = True)
	User.create_table(fail_silently = True)
	WordToUser.create_table(fail_silently = True)
	Chat.create_table(fail_silently = True)
	ChatToUser.create_table(fail_silently = True)


@bot.message_handler(commands = ['start'])
def start(m):
	u = User.cog(m)
	markup = types.ReplyKeyboardMarkup(resize_keyboard = True)
	add_words_btn = types.KeyboardButton(s.add_words)
	remove_words_btn = types.KeyboardButton(s.remove_words)
	add_chats_btn = types.KeyboardButton(s.add_chats)
	remove_chats_btn = types.KeyboardButton(s.remove_chats)
	markup.row(add_words_btn, remove_words_btn)
	markup.row(add_chats_btn, remove_chats_btn)
	bot.send_message(sid(m), s.manual, reply_markup = markup, parse_mode = "Markdown")

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
				.join(WordToUser, on=(Word.id == WordToUser.word_id))
				.where(WordToUser.user_id == sid(m))
				.dicts()
			)
	keyboard = types.InlineKeyboardMarkup()

	for w in words:
		callback_button = types.InlineKeyboardButton(text=w['word'], callback_data=str("remove {}".format(w['id'])))
		keyboard.add(callback_button)
	bot.send_message(sid(m), s.select_removing_words, reply_markup = keyboard)

@bot.message_handler(func=lambda x: x.text == s.add_chats)
def new_chats(m):
	u = User.cog(m)
	u.state = s.new_chats
	u.save()
	bot.send_message(sid(m), s.type_new_chats)

@bot.message_handler(func=lambda x: x.text == s.my_words)
def my_words(m):
	print(s.my_words)
	
@bot.callback_query_handler(func=lambda call: call.data.split(" ")[0] == "remove")
def remove_word(c):
	try:
		wtu = WordToUser.get(user_id = cid(c), word_id = int(c.data.split(" ")[1]))
		wtu.delete_instance()
	except Exception as e:
		print(e)
	words = (Word
				.select(Word)
				.join(WordToUser, on=(Word.id == WordToUser.word_id))
				.where(WordToUser.user_id == cid(c))
				.dicts()
			)
	keyboard = types.InlineKeyboardMarkup()

	for w in words:
		callback_button = types.InlineKeyboardButton(text=w['word'], callback_data=str("remove {}".format(w['id'])))
		keyboard.add(callback_button)
	bot.edit_message_reply_markup(chat_id = cid(c), message_id = c.message.message_id, reply_markup = keyboard)


@bot.message_handler(content_types = ['text'])
def reply(m):
	try:
		u = User.cog(m)
	except:
		return False
	if u.state == s.new_words:
		msg = re.sub('\W+', ' ', m.text)
		words = [w.lower() for w in msg.split(' ') if len(w) > 2]
		words = list(set(words))
		for w in words:
			word = Word.cog(word = w)
			FTSEntry.create(
				entry_id = word.id,
				content = word.word
				)
			try:
				WordToUser.create(user_id = u.user_id, word_id = word.id)
			except Exception as e:
				print(e)
		u.state = ''
		u.save()

	elif u.state == s.remove:
		print("error")

	elif u.state == s.new_chats:
		print("ds")
		msg = re.sub('@\w+', ' ', m.text)
		chats = [chat.lower() for chat in msg.split(' ') if len(chat) > 2]
		chats = list(set(words))
		for w in words:
			word = Word.cog(word = w)
			FTSEntry.create(
				entry_id = word.id,
				content = word.word
				)
			try:
				WordToUser.create(user_id = u.user_id, word_id = word.id)
			except Exception as e:
				print(e)
		u.state = ''
		u.save()

	else:
		msg = re.sub('\W+', ' ', m.text)
		msg = re.sub('\s+', ' ', msg.strip())
		words = [w.lower() for w in msg.split(' ')]
		words = list(set(words))
		query = (FTSEntry
			.select(Word.word, Word.id)
			.join(
				Word,
				on=(FTSEntry.entry_id == Word.id).alias('word')
				)
			.where(FTSEntry.match(' OR '.join(words)))
			.dicts()
			)

		listeners = dict() # юзеры, которые подписались на это слово
		for q in query:
			listeners[q['id']] = set()

		followers = set()

		for l in listeners:
			users = (User
				.select(User.user_id, User.username)
				.join(
					WordToUser,
					on=(WordToUser.user_id == User.user_id)
					)
				.where(WordToUser.word_id == l)
				.dicts()
				)

			for i in users:
				followers.add(i['user_id'])
		for i in followers:
			bot.forward_message(i, m.chat.id, m.message_id)



class Watcher:
	def __call__(self):
		options = webdriver.ChromeOptions()
		options.add_argument("--start-maximized")
		driver = webdriver.Chrome("./chromedriver/chromedriver", chrome_options=options)
		url = "https://web.telegram.org"
		driver.get(url)
		sleep(1)
		phone_country = driver.find_element_by_name("phone_country")
		phone_country.send_keys(Keys.CONTROL + "a")
		phone_country.send_keys("+7")
		phone_number = driver.find_element_by_name("phone_number")
		phone_number.send_keys("9778486184")
		phone_number.send_keys(Keys.ENTER)

		driver.find_element_by_class_name("btn-md-primary").send_keys(Keys.ENTER)
		bot.send_message(328241232, "Type the code")

		# while True:
		# 	for chat in Chat.select():
		# 		print(chat.chat_name)

		# 		sleep(0.5)




# watcher = Watcher()
# p1 = Process(target = watcher)
# p1.start()



if __name__ == '__main__':
	bot.polling(none_stop=True)

# 
# 11062.bankruptcy_parser	(05.09.2017 17:08:32)	(Detached)
# 24258.parse_app_ngrok	(03.09.2017 21:10:36)	(Detached)
# 16724.zaebal_pinit_bot	(03.09.2017 17:03:22)	(Detached)
# 14792.parse_app	(03.09.2017 16:42:15)	(Attached)
# 16215.Django-Blog	(29.08.2017 10:06:18)	(Detached)
# 



# ============ эмуляция юзера
