import logging
import time

from google.appengine.api import xmpp
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.api import taskqueue
from google.appengine.ext.webapp.util import run_wsgi_app

from google.appengine.api import memcache

import core
import tasks
import datamodel as dm

OWNER_JID = "ysoldak@gmail.com"
DESCRIPTION = "PlusXMPP notifies you about new public posts from people in your Google+ circles.\nSend feedback to this jabber account: '"+OWNER_JID+"'\n"

class XMPPHandler(webapp.RequestHandler):
	def post(self, url):
		jid = self.request.get('from').split('/')[0]
		logging.debug("Message from jid: '"+jid+"'")
		logging.debug("Message at url: '"+url+"'")
		
		if url == 'subscription/unsubscribe/':
			dm.del_user(jid)
			return
		
		# Commented out to avoid multiple welcome messages, some clients send several subscribe events
		# if url == 'subscription/subscribe/':
		# 	self.welcome(jid)
		# 	return
			
		if url != 'message/chat/':
			return

		body = self.request.get('body')
		if body is None:
			logging.debug("Request w/o body. Stopped.")
			return

		message = xmpp.Message(self.request.POST)

		logging.debug("Message body: '"+message.body+"'")

		if message.body[0:5].lower() == 'plus ':
			core.init(jid, message.body[5:])
			message.reply("Subscribed!")
			return

		user = dm.get_user(jid)
		if user is None:
			self.welcome(jid)
			return

		if message.body.lower() == 'f' or message.body.lower() == 'friends': # friends user follows
			message.reply(core.get_friends(user.plus_id)['message'], raw_xml=False)
			return

		if message.body.lower() == 'last' or message.body.lower() == 'latest': # latest (cached) posts
			last = memcache.get("last_" + jid)
			if last is None:
				message.reply("No last posts message found.", raw_xml=False)
			else:
				message.reply(last, raw_xml=False)
			return

		if message.body.lower() == 'on': # make user active
			if dm.enable_user(jid):
				message.reply("Delivery enabled!", raw_xml=False)
			return

		if message.body.lower() == 'off': # make user active
			if dm.disable_user(jid):
				message.reply("Delivery disabled!", raw_xml=False)
			return

		if message.body[0:2].lower() == 's:' and jid == OWNER_JID: # system commands
			if message.body[2:].lower() == 'cache_reset':
				result = "Success!" if memcache.flush_all() else "Failed!"
				message.reply(result, raw_xml=False)
				return
			if message.body[2:].lower() == 'cache_stats':
				result = str(memcache.get_stats())
				message.reply(result, raw_xml=False)
				return
			if message.body[2:].lower() == 'test':
				message.reply(str(time.time()), raw_xml=False)
				return
				
		self.help(message)
		
	def welcome(self, jid):
		xmpp.send_message(jid, "Welcome to PlusXMPP service.\n"+DESCRIPTION+"\nTo start, please, send me your +id in the form:\nplus 1234567890")
	
	def help(self, message):
		message.reply(DESCRIPTION + "\nAvailable commands (command - description):\nfriends - short list of users in your circles\nlast - repeat last posts message\non - turn updates delivery on\noff - turn updates delivery off")
	


class TaskHandler(webapp.RequestHandler):

	def get(self): # touched by cron
		taskqueue.add(url='/fetch/posts', params={})

	def post(self): # touched by task queue
		tasks.fetch_posts()

application = webapp.WSGIApplication([(r'/_ah/xmpp/(.*)', XMPPHandler),('/fetch/posts', TaskHandler)],debug=True)

def main():
	run_wsgi_app(application)

if __name__ == "__main__":
	main()