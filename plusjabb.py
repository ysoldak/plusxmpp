import logging
import re

from django.utils import simplejson

from google.appengine.api import urlfetch
from google.appengine.api import xmpp
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

#my plus id 118056070123837000922

commas = re.compile(',,',re.M)

class XMPPHandler(webapp.RequestHandler):
	def post(self):
		message = xmpp.Message(self.request.POST)
		logging.info(message.body)
		if message.body[0:2].lower() == 'f:': # Friends user follows
			message.reply(self.doFetchFriends(message.body[2:]), raw_xml=False)
	
	def doFetchFriends(self, plus_id):
		url = 'https://plus.google.com/_/socialgraph/lookup/visible/?o=%5Bnull%2Cnull%2C%22'+plus_id+'%22%5D&_reqid=5582440&rt=j'
		logging.info(url)
		result = urlfetch.fetch(url)

		if result.status_code != 200:
			logging.error('Unexpected status code: %d' % result.status_code)
			return "Can't fetch friends list."

		received_content = result.content
		txt = received_content[5:]
		txt = commas.sub(',null,',txt)
		txt = commas.sub(',null,',txt)
		txt = txt.replace('[,','[null,')
		txt = txt.replace(',]',',null]')

		json_decoder = simplejson.decoder.JSONDecoder()
		try:
			decoded_json = json_decoder.decode(txt)
		except ValueError:
			logging.error("Can't parse data")
			return "Can't fetch friends list."
		#else:
		#	logging.info('Decoded JSON: %s' % str(decoded_json))
		
		friends = decoded_json[0][0][2]

		logging.debug('Number of friends ('+plus_id+'): ' + str(len(friends)))

		count = 0
		respond = ""

		for friend in friends:
	
			count = count + 1
			if count > 10:
				break
			
			#logging.info(str(friend[2]))

			respond += friend[2][0] + ' (https://plus.google.com/' + friend[0][2] + '/about)\n'
			#respond += '<a href="https://plus.google.com/'+friend[0][2]+'/about">'+friend[2][0]+ '</a><br/>'

		if len(friends) > 10:
			respond += '... and ' + str((len(friends) - 10)) + ' more.'
		
		return respond #'<body>' + respond + '</body>'

	# def get(self):
	#     user_address = 'ysoldak@gmail.com'
	#     #chat_message_sent = False
	#     msg = "Warmup"
	#     status_code = xmpp.send_message(user_address, msg)
	#     #chat_message_sent = (status_code == xmpp.NO_ERROR)

application = webapp.WSGIApplication([('/_ah/xmpp/message/chat/', XMPPHandler),('/ping', XMPPHandler)],debug=True)

def main():
	run_wsgi_app(application)

if __name__ == "__main__":
	main()