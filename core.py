from google.appengine.api import memcache

import datamodel as dm
import fetcher as pf

CYCLE = 60*60

def getUser(jid):
	q = dm.User.all()
	q.filter("jid =", jid)
	return q.get()

def setUser(jid, plus_id):
	user = getUser(jid)
	if user is not None:
		user.plus_id = plus_id
	else:
		user = dm.User(jid=jid, plus_id=plus_id, active=True)
	user.put()
	memcache.delete("friends_ids_"+plus_id)
	memcache.delete("friends_message_"+plus_id)
	return user

def getFriendsIds(plus_id):
	data = memcache.get("friends_ids_"+plus_id)
	if data is None:
		data = pf.friends(plus_id)
	return data

def getFriends(plus_id):
	data = memcache.get("friends_message_"+plus_id)
	if data is None:
		pf.friends(plus_id)
	data = memcache.get("friends_message_"+plus_id)
	return data

def getLatest(plus_id, timestamp):
	friend_ids = getFriendsIds(plus_id)
	output = ''
	for friend_id in friend_ids:
		posts = memcache.get("posts_data_" + friend_id)
		if posts is None and timestamp >= 0:
			posts = pf.posts(friend_id, timestamp, 10)
			memcache.set('posts_data_' + friend_id, posts, CYCLE)
		if posts is not None and posts != '':
			output += posts
	return output
