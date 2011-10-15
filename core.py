import logging

from google.appengine.api import memcache

import datamodel as dm
import fetch
import plusapi

# fetcher constants, must be backed by cron.yaml (set it to fire each MIN_CYCLE secs)
MIN_CYCLE   = 60 * 60 * 1           # most active streams
MAX_CYCLE   = 60 * 60 * 24          # most idle streams and friends list
CYCLE_RATIO = MAX_CYCLE / MIN_CYCLE

POST_LIMIT = 10

def init(jid, plus_id):
	dm.set_user(jid, plus_id)
	memcache.delete("friends_" + plus_id)

# === Friends ===

def get_friends(plus_id):
	data = memcache.get("friends_" + plus_id)
	if data is None:
		data = fetch.friends(plus_id)
		memcache.set("friends_"+plus_id, data, MAX_CYCLE)
	return data


# === Stream ===

def get_stream(plus_id, timestamp):
	friends = get_friends(plus_id)
	output = ''
	for friend_id in friends['ids']:
		posts = get_posts(friend_id, timestamp)
		if posts != '':
			output += posts
	return output

def get_posts(plus_id, timestamp):
	posts = memcache.get("posts_" + plus_id)
	if posts is None: # falls here only once during the fetch cycle
		status = get_status(plus_id)
		if status['ts'] is not None and (status['ts'] + MIN_CYCLE * status['freq'] - 60) > timestamp: # "-60" in case GAE doesn't run cron sharp at time
			return ''
		oldest = timestamp - status['freq'] * MIN_CYCLE + 1 # "+1" to ensure we don't harvest any already processed post
		#posts = fetch.posts(plus_id, oldest, POST_LIMIT)
		posts = plusapi.posts(plus_id, oldest, POST_LIMIT)
		status = update_status(plus_id, posts != '', timestamp)
		memcache.set('posts_' + plus_id, posts, timestamp + MIN_CYCLE - 2) # "-2" to ensure the cache is expired before next fetch cycle
	return posts

def get_status(plus_id):
	status = memcache.get("status_" + plus_id)
	if status is None:
		status = {'ts':None, 'freq':1}
	#logging.debug("Get status for '" + plus_id + "': " + str(status))
	return status

def update_status(plus_id, has_new, timestamp):
	status = get_status(plus_id)
	
	freq = status['freq']
	old_freq = freq
	
	if has_new:
		freq = 1 # fetch plus account posts on next cycle if harvested at least one post during this cycle
	else:
		freq += 1 # otherwise postpone the fetch gradually to maximum (once a day for now); multiply by 2 is very aggresive, replaced with +1
		if freq > CYCLE_RATIO:
			freq = CYCLE_RATIO
	
	status['ts'] = timestamp
	status['freq'] = freq
	
	if old_freq != freq:
		logging.debug("Frequency '" + plus_id + "': " + str(old_freq) + "->" + str(freq))
	
	memcache.set("status_" + plus_id, status)
	
	return freq

