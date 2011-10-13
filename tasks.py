import time
import logging

from google.appengine.api import xmpp
from google.appengine.api import memcache

import core
import datamodel as dm

LIMIT = 100

def fetch_posts():
	users = dm.query_users(True, LIMIT)
	timestamp = time.time() # - core.CYCLE
	for user in users:
		logging.debug("Fetching posts for: " + user.jid + " / " + user.plus_id)
		output = core.get_stream(user.plus_id, timestamp)
		if output != '':
			memcache.set("last_" + user.jid, output)
			#chat_message_sent = False
			status_code = xmpp.send_message(user.jid, output)
			#chat_message_sent = (status_code == xmpp.NO_ERROR)
	return