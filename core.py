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

def delUser(jid):
	user = getUser(jid)
	if user is not None:
		user.delete()

def enableUser(jid):
	user = getUser(jid)
	if user is not None:
		user.active = True
		user.put()
		return True
	return False

def disableUser(jid):
	user = getUser(jid)
	if user is not None:
		user.active = False
		user.put()
		return True
	return False

def getFriendsIds(plus_id):
	data = memcache.get("friends_ids_"+plus_id)
	if data is None:
		data = pf.friends(plus_id)
	return data

def getFriends(plus_id):
	data = memcache.get("friends_message_"+plus_id)
	if data is not None:
		return data
	else:
		ids = pf.friends(plus_id)
		if len(ids) == 0:
			return "Can't fetch list of friends. Public access restricted?"
		else:
			return memcache.get("friends_message_"+plus_id)

def getLatest(plus_id, timestamp):
	cache_expire_timestamp = timestamp + CYCLE * 2 - 10 # next fetching time minus 10 seconds
	friend_ids = getFriendsIds(plus_id)
	output = ''
	for friend_id in friend_ids:
		posts = memcache.get("posts_data_" + friend_id)
		if posts is None and timestamp >= 0:
			posts = pf.posts(friend_id, timestamp, 10)
			memcache.set('posts_data_' + friend_id, posts, cache_expire_timestamp)
		if posts is not None and posts != '':
			output += posts
	return output
