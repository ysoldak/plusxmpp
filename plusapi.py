import logging
import time

from datetime import datetime
from cgi import escape

from django.utils import simplejson

from google.appengine.api import urlfetch


api_key_file = open('API_KEY', 'r')
API_KEY = api_key_file.read()
api_key_file.close()

def posts(plus_id, timestamp, max_count):
	
	just_now = time.time()
	
	url = "https://www.googleapis.com/plus/v1/people/"+plus_id+"/activities/public?alt=json&maxResults="+str(max_count)+"&fields=items(actor%2FdisplayName%2Ctitle%2Cupdated%2Curl%2Cverb)%2Ctitle%2Cupdated&pp=1&key="+API_KEY
	# logging.debug(url)
	# return ''
	
	result = ''
	try:
		result = urlfetch.fetch(url, deadline=10)
	except urlfetch.Error:
		return ''
	if result.status_code != 200:
		return ''
		
	#logging.debug(result.content)
	
	obj = simplejson.loads(result.content)
	if not 'items' in obj:
		return ''
		
	updated = datetime.strptime(obj['updated'], "%Y-%m-%dT%H:%M:%S.%fZ")
	updated_ts = time.mktime(updated.timetuple())
	if timestamp is not None and timestamp != 0 and updated_ts < timestamp:
		return ''
	
	posts = obj['items']
	if not posts:
		return ''
		
	author = posts[0]['actor']['displayName']
	
	output = ''
	count = 0
	for post in posts:
		
		post_updated = datetime.strptime(post['updated'], "%Y-%m-%dT%H:%M:%S.%fZ")
		post_updated_ts = time.mktime(post_updated.timetuple())
		if timestamp is not None and timestamp != 0 and post_updated_ts < timestamp:
			break
		
		count = count + 1
		if max_count is not None and max_count != 0 and count > max_count:
			break
		
		title = post['title'].replace('\n','')
		
		output += author + ' @ ' + str(int((just_now - post_updated_ts)/60)) + ' mins ago\n'
		if title != "":
			output += escape(title) + '\n'
		output += post['url'] + '\n\n'
		
	logging.debug("Fetched posts " + plus_id + ": " + str(count))
		
	return output
