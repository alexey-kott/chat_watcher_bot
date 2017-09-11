#!/usr/bin/python3

import telebot
from telebot import types
import sqlite3 as sqlite
import re
import config as cfg
from peewee import *
from playhouse.sqlite_ext import *
import strings as s

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


@bot.message_handler(commands = ['start'])
def start(m):
	u = User.cog(m)
	markup = types.ReplyKeyboardMarkup()
	add_words_btn = types.KeyboardButton(s.add_words)
	remove_words_btn = types.KeyboardButton(s.remove_words)
	# my_words_btn = types.KeyboardButton(s.my_words)
	markup.row(add_words_btn)
	markup.row(remove_words_btn)
	markup.row(my_words_btn)
	bot.send_message(sid(m), s.manual, reply_markup = markup, parse_mode = "Markdown")

@bot.message_handler(func=lambda x: x.text == s.add_words)
def new_words(m):
	u = User.cog(m)
	u.state = s.new
	u.save()
	bot.send_message(sid(m), s.type_new_words)

@bot.message_handler(func=lambda x: x.text == s.remove_words)
def new_words(m):
	u = User.cog(m)
	u.state = s.remove
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
	
@bot.callback_query_handler(func=lambda call: call.data.split(" ")[0] == "remove")
def remove_word(c):
	wtu = WordToUser.get(user_id = cid(c), word_id = int(c.data.split(" ")[1]))
	wtu.delete_instance()
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
	if u.state == s.new:
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
		words = (Word
			.select(Word)
			.join(
				Word,
				on=(Word.id == WordToUser.user_id)
				)
			.where(WordToUser.user_id == sid(m))
			)
		for w in words:
			print(w)
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







if __name__ == '__main__':
	bot.polling(none_stop=True)
