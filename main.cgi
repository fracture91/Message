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
sys.path.insert(0, os.getcwd())
from MessageDB import MessageDB, User, Message, enforceLength
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

	

def handleForm(form):
	global validationerror
	if db.valid():
		if "username" in form:
			if not(db.setUsername(me, form["username"].value)):
				validationerror = "Bad username (must match " + db.validusername + ")"
		if "content" in form:
			content = form["content"].value
			message = db.addMessage(me, datetime.utcnow(), content)
			overflow = len(content) - db.maxcontent
			if overflow > 0:
				validationerror = "Content " + str(overflow) + " characters too long (maxcontent=" + str(db.maxcontent) + "), trimmed excess"
	
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

db = MessageDB(config.getmain("datafile"), config.getmain("validusername"), config.getmainint("maxusers"),
	config.getmainint("maxmessages"), config.getmainint("maxcontent"))
	
with db.wait():

	me = None
	if db.valid():
		me = db.addUser(ip=ipaddr, check=True)

	handleForm(form)

	printContent()

