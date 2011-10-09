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
	def post(self):
		message = xmpp.Message(self.request.POST)

		logging.debug("jid:"+message.sender)
		logging.debug("body:"+message.body)

		if message.body[0:5].lower() == 'plus ':
			core.setUser(message.sender, message.body[5:])
			message.reply("Subscribed!")
			return

		user = core.getUser(message.sender)
		if user is None:
			message.reply("Welcome to PlusXMPP service.\nPlease, send me your +id in the form:\nplus 1234567890")
			return

		if message.body.lower() == 'f': # friends user follows
			message.reply(core.getFriends(user.plus_id), raw_xml=False)
			return

		if message.body.lower() == 'l': # latest (cached) posts
			posts = core.getLatest(user.plus_id, -1)
			if posts is None or posts == '':
				posts = "No new posts found."
			message.reply(posts, raw_xml=False)
			return

		if message.body.lower() == 't': # test
			message.reply(str(time.time()), raw_xml=False)
			return

class TaskHandler(webapp.RequestHandler):

	def get(self): # touched by cron
		taskqueue.add(url='/fetch/posts', params={})

	def post(self): # touched by task queue
		tasks.taskFetchPosts()

application = webapp.WSGIApplication([('/_ah/xmpp/message/chat/', XMPPHandler),('/fetch/posts', TaskHandler)],debug=True)

def main():
	run_wsgi_app(application)

if __name__ == "__main__":
	main()