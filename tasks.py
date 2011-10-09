import time

from google.appengine.api import xmpp

import core
import datamodel as dm

def taskFetchPosts():
	q = dm.User.all()
	q.filter("active =", True)
	users = q.fetch(5)
	timestamp = time.time() - core.CYCLE
	for user in users:
		output = core.getLatest(user.plus_id, timestamp)
		if output is not None and output != '':
			#chat_message_sent = False
			status_code = xmpp.send_message(user.jid, output)
			#chat_message_sent = (status_code == xmpp.NO_ERROR)
	return