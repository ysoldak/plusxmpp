from google.appengine.ext import db

class User(db.Model):
	jid = db.StringProperty(required=True, indexed=True)
	plus_id = db.StringProperty(required=True)
	active = db.BooleanProperty(indexed=True)

def get_user(jid):
	q = User.all()
	q.filter("jid =", jid)
	return q.get()

def set_user(jid, plus_id):
	user = get_user(jid)
	if user is not None:
		user.plus_id = plus_id
	else:
		user = User(jid=jid, plus_id=plus_id, active=True)
	user.put()
	return user

def del_user(jid):
	user = get_user(jid)
	if user is not None:
		user.delete()

def enable_user(jid):
	user = get_user(jid)
	if user is not None:
		user.active = True
		user.put()
		return True
	return False

def disable_user(jid):
	user = get_user(jid)
	if user is not None:
		user.active = False
		user.put()
		return True
	return False

def query_users(active, limit):
	q = User.all()
	q.filter("active =", active)
	return q.fetch(limit)
	