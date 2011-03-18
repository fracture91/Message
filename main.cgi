#!/usr/local/bin/python2.6

import cgitb
cgitb.enable()

import cgi
#cgi.test()

import os
import sys
from datetime import datetime
#this module is broken on the CCC servers because they don't
#have the important _sqlite3.so file
#import sqlite3
import cPickle
import re

datafile = "data.pkl"
defaultusername = "Unknown User"
validusername = "^[\w.\-\*\(\)\&\^\%\$\#\@\!]{1,30}$"
maxusers = 1000
maxmessages = 5000
maxcontent = 5000
validationerror = None

class DB(object):
	def __init__(self, filename):
		self.filename = filename
		self.data = None
		self.dirty = False
	def load(self):
		try:
			file = open(self.filename, "r")
			self.data = cPickle.load(file)
		except IOError:
			self.data = "IOError opening message file"
		except:
			self.data = "Unknown error"
	def save(self):
		try:
			file = open(self.filename, "w")
			cPickle.dump(self.data, file)
		except IOError:
			self.data = "IOError writing message file"
		except:
			self.data = "Unknown error"
	def valid(self):
		return isinstance(self.data, dict)
		
	
class MessageDB(DB):
	def __init__(self, filename):
		super(MessageDB, self).__init__(filename)
	def findUser(self, name=None, ip=None, make=False):
		if (not name) == (not ip): #if both arguments are given or neither are given
			raise TypeError("Must provide exactly one of name or ip")
		else:
			for user in self.data["users"]:
				if name and user.name == name or ip and user.ip == ip:
					return user
			if make:
				users = self.data["users"]
				user = User(ip, name)
				users.append(user)
				difference = len(users) - maxusers
				if difference > 0:
					self.data["users"] = users[difference:]
					#validationerror = "Too many users, deleted some"
				self.dirty = True
				return user
			return None
	
	
class User(object):
	def __init__(self, ip, name):
		self.ip = ip
		self.name = name
	
class Message(object):
	def __init__(self, user, date, content):
		self.user = user
		self.date = date
		self.content = content
	

db = MessageDB(datafile)
db.load()

ipaddr = os.environ["REMOTE_ADDR"]
form = cgi.FieldStorage()

me = None
if db.valid():
	me = db.findUser(ip=ipaddr, make=True)
	if "username" in form:
		if re.match(validusername, form["username"].value):
			me.name = form["username"].value
			db.dirty = True
		else:
			validationerror = "Bad username (must match" + validusername + ")"
	if "content" in form:
		messages = db.data["messages"]
		content = form["content"].value
		if len(content) > maxcontent:
			validationerror = "Content too long (maxcontent=" + str(maxcontent) + "), trimmed excess"
		messages.append(Message(me, datetime.utcnow(), content[:maxcontent]))
		difference = len(messages) - maxmessages
		if difference > 0:
			db.data["messages"] = messages[difference:]
			#validationerror = "Too many messages, deleted some"
		db.dirty = True
	

#HTTP headers
print "Content-Type: text/html"
print

#HTML content
print "<html><head>"
print '<link rel="stylesheet" type="text/css" media="all" href="main.css">'
print "</head><body>"
print '<section class="me">'
print "<h4>" + (cgi.escape(me.name) if isinstance(me, User) and isinstance(me.name, str) else defaultusername) + "</h4>"
print "<code>" + cgi.escape(ipaddr, quote=True) + "</code>"
print '<form method="post"><input name="username"><input type="submit" value="Set username"></form>'
print "</section>"

if validationerror:
	print "<div>" + validationerror + "</div>"
	
print '<section class="post">'
print '<h3>Post message</h3>'
print '<form method="post">'
print '<textarea name="content"></textarea><input type="submit" value="post">'
print '</form>'
print "</section>"
print '<section class="messages">'

if not db.valid():
	print "Database invalid"
elif len(db.data["messages"]) < 1 :
	print "No messages"
else:
	for msg in reversed(db.data["messages"]):
		print "<div>"
		print cgi.escape(msg.user.name if isinstance(msg.user.name, str) else msg.user.ip, quote=True)
		print " at "
		print cgi.escape(msg.date.isoformat(), quote=True)
		print "</div>"
		print "<div>"
		print cgi.escape(msg.content, quote=True)
		print "</div>"
		print "<br>"

print "</section>"
print "</body></html>"

if db.dirty and db.valid():
	db.save()
