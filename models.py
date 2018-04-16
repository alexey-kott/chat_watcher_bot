from peewee import *
from playhouse.sqlite_ext import *

from functions import *

db = SqliteExtDatabase('bot.db') # DB

sid = lambda m: m.chat.id # лямбды для определения адреса ответа
uid = lambda m: m.from_user.id
cid = lambda c: c.message.chat.id

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
	sname		= TextField(null = True) # session name

	def cog(m):
		user_id 	= uid(m)
		username 	= m.from_user.username
		first_name 	= m.from_user.first_name
		last_name 	= m.from_user.last_name
		sname 		= 'u{}'.format(uid(m))

		try:
			with db.atomic():
				return User.create(user_id = user_id, 
									username = username, 
									first_name = first_name, 
									last_name = last_name,
									sname = sname)
		except:
			return User.get(user_id = user_id)
			
class Routing(BaseModel):
	state 		= TextField()
	decision 	= TextField() # соответствует либо атрибуту data в инлайн кнопках, 
							  # либо специальному значению text, которое соответствует любому текстовому сообщению
	action		= TextField()

	class Meta:
		primary_key = CompositeKey('state', 'decision')