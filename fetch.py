import logging
import re
import time
from datetime import datetime
from htmlentitydefs import name2codepoint
from cgi import escape

from django.utils import simplejson

from google.appengine.api import urlfetch

remtags = re.compile(r'<.*?>')
remspaces = re.compile(r'\s+')
commas = re.compile(',,',re.M)
se_break = re.compile('[.!?:]\s+', re.VERBOSE)
charrefpat = re.compile(r'&(#(\d+|x[\da-fA-F]+)|[\w.:-]+);?')

def friends(plus_id):
	logging.debug("plusfetcher.friends: " + plus_id)
	url = 'https://plus.google.com/_/socialgraph/lookup/visible/?o=%5Bnull%2Cnull%2C%22'+plus_id+'%22%5D&_reqid=5582440&rt=j'
	logging.debug("url: "+url)
	result = urlfetch.fetch(url)
	
	if result.status_code != 200:
		logging.error('Unexpected status code: %d' % result.status_code)
		return {'ids':[], 'message':'Can\'t fetch friends list. Internal error.'}
	
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
		return {'ids':[], 'message':'Can\'t fetch friends list. Internal error.'}
	
	friends = decoded_json[0][0][2]
	friends_count = len(friends)

	logging.debug('count: ' + str(friends_count))

	if friends_count == 0:
		return {'ids':[], 'message':'Can\'t fetch friends list. Public access restricted?'}

	count = 0
	respond = ""
	ids = []

	for friend in friends:
		ids.append(friend[0][2])

		count = count + 1
		if count > 10:
			continue

		respond += friend[2][0] + ' (https://plus.google.com/' + friend[0][2] + '/about)\n'
		#respond += '<a href="https://plus.google.com/'+friend[0][2]+'/about">'+friend[2][0]+ '</a><br/>'

	if friends_count > 10:
		respond += '... and ' + str((friends_count - 10)) + ' more.'

	return {'ids':ids, 'message':respond}

# code in this method is based on plusfeed project
def posts(plus_id, timestamp, max_count):
	logging.debug("plusfetcher.posts: " + plus_id + ", " + str(timestamp) + ", " + str(max_count))
	
	just_now = time.time()
	
	url = 'https://plus.google.com/_/stream/getactivities/' + plus_id + '/?sp=[1,2,"' + plus_id + '",null,null,null,null,"social.google.com",[]]'
	result = ''
	
	try:
		result = urlfetch.fetch(url, deadline=10)
	except urlfetch.Error:
		return ''
		
	if result.status_code != 200:
		return ''
		
	txt = result.content
	txt = txt[5:]
	txt = commas.sub(',null,',txt)
	txt = commas.sub(',null,',txt)
	txt = txt.replace('[,','[null,')
	txt = txt.replace(',]',',null]')
	obj = simplejson.loads(txt)
	
	posts = obj[1][0]
	
	output = ''
	
	if posts:
		
		author = posts[0][3]
		updated_ts = float(posts[0][5])/1000
		#logging.debug("up_ts = "+str(updated_ts))
		updated = datetime.fromtimestamp(updated_ts)
		
		if timestamp is not None and timestamp != 0 and updated_ts < timestamp:
			return ''
			
		count = 0
		
		for post in posts:
			
			count = count + 1
			if max_count is not None and max_count != 0 and count > max_count:
				break
				
			dt_ts = float(post[5])/1000
			#logging.debug("dt_ts = "+str(dt_ts))
			dt = datetime.fromtimestamp(dt_ts)
			if timestamp is not None and timestamp != 0 and dt_ts < timestamp:
				break
				
			id = post[21]
			permalink = "https://plus.google.com/" + post[21]
			
			desc = ''
			
			if post[47]:
				desc = post[47]
			elif post[4]:
				desc = post[4]
				
			if desc == '':
				desc = permalink
				
			ptitle = htmldecode(desc)
			ptitle = remtags.sub(' ', ptitle)
			ptitle = remspaces.sub(' ', ptitle)
			
			sentend = 75
			
			m = se_break.split(ptitle)
			if m:
				sentend = len(m[0]) + 1
				
			if sentend < 5 or sentend > 75:
				sentend = 75
				
			#output += author + ' @ ' + dt.strftime('%Y-%m-%d %H:%M:%S (UTC)') + '\n'
			output += author + ' @ ' + str(int((just_now - dt_ts)/60)) + ' mins ago\n'
			output += escape(ptitle[:sentend]) + '\n'
			output += permalink + '\n\n'
			
	return output

def htmldecode(text):
	
	if type(text) is unicode:
		uchr = unichr
	else:
		uchr = lambda value: value > 255 and unichr(value) or chr(value)
		
	def entitydecode(match, uchr=uchr):
		entity = match.group(1)
		if entity.startswith('#x'):
			return uchr(int(entity[2:], 16))
		elif entity.startswith('#'):
			return uchr(int(entity[1:]))
		elif entity in name2codepoint:
			return uchr(name2codepoint[entity])
		else:
			return match.group(0)
	
	return charrefpat.sub(entitydecode, text) 
