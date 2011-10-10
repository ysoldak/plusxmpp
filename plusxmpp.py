import logging
import time

from google.appengine.api import xmpp
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.api import taskqueue
from google.appengine.ext.webapp.util import run_wsgi_app

import core
import tasks

class XMPPHandler(webapp.RequestHandler):
	def post(self, url):
		jid = self.request.get('from').split('/')[0]
		logging.debug("Message from jid: '"+jid+"'")
		logging.debug("Message at url: '"+url+"'")

		if url == 'subscription/subscribe/':
			xmpp.send_message(jid, "Welcome to PlusXMPP service.\nPlease, send me your +id in the form:\nplus 1234567890")
			return

		if url == 'subscription/unsubscribe/':
			core.delUser(jid)
			return

		if url != 'message/chat/':
			return

		body = self.request.get('body')
		if body is None:
			logging.debug("Request w/o body. Stopped.")
			return

		message = xmpp.Message(self.request.POST)

		logging.debug("Message body: '"+message.body+"'")

		if message.body[0:5].lower() == 'plus ':
			core.setUser(jid, message.body[5:])
			message.reply("Subscribed!")
			return

		user = core.getUser(jid)
		if user is None:
			message.reply("Welcome to PlusXMPP service.\nPlease, send me your +id in the form:\nplus 1234567890")
			return

		if message.body.lower() == 'f' or message.body.lower() == 'friends': # friends user follows
			message.reply(core.getFriends(user.plus_id), raw_xml=False)
			return

		if message.body.lower() == 'last' or message.body.lower() == 'latest': # latest (cached) posts
			posts = core.getLatest(user.plus_id, -1)
			if posts is None or posts == '':
				posts = "No new posts found."
			message.reply(posts, raw_xml=False)
			return

		if message.body.lower() == 'on': # make user active
			if core.enableUser(jid):
				message.reply("Delivery enabled!", raw_xml=False)
			return

		if message.body.lower() == 'off': # make user active
			if core.disableUser(jid):
				message.reply("Delivery disabled!", raw_xml=False)
			return

		if message.body.lower() == 't': # test
			message.reply(str(time.time()), raw_xml=False)
			return

		message.reply("Usage (command - description):\nfriends - short list of users in your circles\nlast - repeat last posts message\non - turn updates delivery on\noff - turn updates delivery off")

class TaskHandler(webapp.RequestHandler):

	def get(self): # touched by cron
		taskqueue.add(url='/fetch/posts', params={})

	def post(self): # touched by task queue
		tasks.taskFetchPosts()

application = webapp.WSGIApplication([(r'/_ah/xmpp/(.*)', XMPPHandler),('/fetch/posts', TaskHandler)],debug=True)

def main():
	run_wsgi_app(application)

if __name__ == "__main__":
	main()