#!/usr/bin/python3

import telebot
import sqlite3 as sqlite
import re
import config as cfg
from peewee import *


bot = telebot.TeleBot(cfg.token)

db = SqliteDatabase('bot.db')




class BaseModel(Model):

	class Meta:
		database = db

class Word(BaseModel):
	word = TextField()


class User(BaseModel):
	alias = TextField()


class WordToUser(BaseModel):
	user_id = IntegerField()
	word_id = IntegerField()



@bot.message_handler(commands = ['init'])
def init(message):
	Word.create(fail_silently = True)
	User.create(fail_silently = True)
	WordToUser.create(fail_silently = True)

@bot.message_handler(commands = ['start'])
def start(message):
	print(message)

@bot.message_handler(content_types = ['text'])
def reply(message):
	print(message)




if __name__ == '__main__':
	bot.polling(none_stop=True)
