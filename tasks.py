import time
import logging

from google.appengine.api import xmpp

import core
import datamodel as dm

LIMIT = 100

def taskFetchPosts():
	q = dm.User.all()
	q.filter("active =", True)
	users = q.fetch(LIMIT)
	timestamp = time.time() - core.CYCLE
	for user in users:
		logging.debug("Fetching posts for: " + user.jid + " / " + user.plus_id)
		output = core.getLatest(user.plus_id, timestamp)
		if output is not None and output != '':
			#chat_message_sent = False
			status_code = xmpp.send_message(user.jid, output)
			#chat_message_sent = (status_code == xmpp.NO_ERROR)
	return