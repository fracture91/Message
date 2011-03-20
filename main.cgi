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
import re

#modules from the current working directory
#importing them without this sys.path stuff doesn't work for some reason
sys.path.append(os.getcwd())
from DB import DB
from FriendlyConfig import FriendlyConfig
del sys.path[0]


config = FriendlyConfig("config.ini", {
	"datafile": "data.pkl",
	"defaultusername": "Unknown User",
	"validusername": "^[\w.\-\*\(\)\&\^\%\$\#\@\!]{1,30}$",
	"maxusers": "1000",
	"maxmessages": "5000",
	"maxcontent": "5000"
	})


validationerror = None

class MessageDB(DB):
	def __init__(self, filename):
		super(MessageDB, self).__init__(filename)
	def findUser(self, name=None, ip=None, make=False):
		if (not name) == (not ip): #if both arguments are given or neither are given
			raise TypeError("Must provide exactly one of name or ip")
		else:
			#find the first user with a matching name or ip
			user = next((user for user in self.data["users"] if name and user.name == name or ip and user.ip == ip), None)
			#make a new user if preferred
			if user is None and make:
				users = self.data["users"]
				user = User(ip, name)
				users.append(user)
				enforceLength(users, config.getmainint("maxusers"))
				self.dirty = True
			return user
	
	
class User(object):
	def __init__(self, ip, name):
		self.ip = ip
		self.name = name
	
class Message(object):
	def __init__(self, user, date, content):
		self.user = user
		self.date = date
		self.content = content
	
def enforceLength(list, length):
	difference = len(list) - length
	if difference > 0:
		del list[:difference]
		return True
	return False

def handleForm(form):
	global validationerror
	if db.valid():
		if "username" in form:
			validusername = config.getmain("validusername")
			if re.match(validusername, form["username"].value):
				me.name = form["username"].value
				db.dirty = True
			else:
				validationerror = "Bad username (must match " + validusername + ")"
		if "content" in form:
			messages = db.data["messages"]
			content = form["content"].value
			maxcontent = config.getmainint("maxcontent")
			if len(content) > maxcontent:
				validationerror = "Content too long (maxcontent=" + str(maxcontent) + "), trimmed excess"
			messages.append(Message(me, datetime.utcnow(), content[:maxcontent]))
			enforceLength(messages, config.getmainint("maxmessages"))
			db.dirty = True
	
def printHeaders():
	print "Content-Type: text/html"
	print
	
def printContent():
	print "<html><head>"
	print '<link rel="stylesheet" type="text/css" media="all" href="main.css">'
	print "</head><body>"
	print '<section class="me">'
	print "<h4>" + (cgi.escape(me.name) if isinstance(me, User) and isinstance(me.name, str) else config.getmain("defaultusername")) + "</h4>"
	print "<code>" + cgi.escape(ipaddr, quote=True) + "</code>"
	print '<form method="post"><input name="username"><input type="submit" value="Set username"></form>'
	print "</section>"

	if validationerror:
		print "<div>" + validationerror + "</div>"
		
	print '<section class="post">'
	print '<h3>Post message</h3>'
	print '<form method="post">'
	print '<textarea name="content"></textarea><input type="submit" value="Post">'
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
	

ipaddr = os.environ["REMOTE_ADDR"]
form = cgi.FieldStorage()
printHeaders()

db = MessageDB(config.getmain("datafile"))
with db.wait():

	me = None
	if db.valid():
		me = db.findUser(ip=ipaddr, make=True)

	handleForm(form)

	printContent()

