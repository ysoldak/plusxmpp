from google.appengine.ext import db

class User(db.Model):
	jid = db.StringProperty(required=True, indexed=True)
	plus_id = db.StringProperty(required=True)
	active = db.BooleanProperty(indexed=True)
