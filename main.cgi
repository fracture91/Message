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
from Cookie import SimpleCookie
import string

#modules from the current working directory
#importing them without this sys.path stuff doesn't work for some reason
sys.path.insert(0, os.getcwd())
from MessageDB import MessageDB, User, Message, enforceLength
from FriendlyConfig import FriendlyConfig
del sys.path[0]


config = FriendlyConfig("config.ini", {
	"datafile": "data.pkl",
	"defaultusername": "Anonymous",
	"validusername": "^[\w.\-\*\(\)\&\^\%\$\#\@\!]{3,30}$",
	"maxusers": "1000",
	"maxmessages": "5000",
	"maxcontent": "5000",
	"cookienamespace": "adhmsg"
	})

	

def getCookieKey(key):
	return config.getmain("cookienamespace") + "_" + key
	
def getCookieValue(cookie, key):
	fullkey = getCookieKey(key)
	return str(cookie[fullkey].value) if isinstance(cookie, SimpleCookie) and fullkey in cookie else ""
	
def setCookieValue(cookie, key, value):
	fullkey = getCookieKey(key)
	if isinstance(cookie, SimpleCookie):
		cookie[fullkey] = value

def handleCookie(db, ipaddr, cookie, errors):
	username = getCookieValue(cookie, "username")
	username = username if db.validateUsername(username) else config.getmain("defaultusername")
	
	newcookie = SimpleCookie()
	#this will clear out the username if not valid
	setCookieValue(newcookie, "username", username)

	me = None
	if db.valid():
		#find the user based on the username in the cookie, and create if missing if username is default
		me = db.findUser(username, ipaddr, username==config.getmain("defaultusername"))
		#if username in cookie doesn't exist, set cookie to default username
		if me is None:
			setCookieValue(newcookie, "username", config.getmain("defaultusername"))
			me = db.findUser(config.getmain("defaultusername"), ipaddr, True)
		
	return me, newcookie
	
def handleForm(db, me, ipaddr, errors, cookie, form):
	if db.valid():
		if "username" in form:
			newUser = db.addUser(form["username"].value, ipaddr)
			if not(newUser):
				errors.append('Bad username (<a href="http://en.wikipedia.org/wiki/Regular_expression">must match ' + db.validusername + '</a>)')
			else:
				me = newUser
				setCookieValue(cookie, "username", form["username"].value)
		if "content" in form:
			if me is not None:
				content = form["content"].value
				message = db.addMessage(ipaddr, me, datetime.utcnow(), content)
				overflow = len(content) - db.maxcontent
				if overflow > 0:
					errors.append("Content " + str(overflow) + " characters too long (maxcontent=" + str(db.maxcontent) + "), trimmed excess")
			else:
				errors.append("Could not post message, user not found")
	return me
	
def printHeaders(newcookie):
	print "Content-Type: text/html"
	print newcookie
	print

def printErrors(errors):
	if len(errors) > 0:
		print '<ul class="errors">'
		for err in errors:
			print "<li>" + err + "</li>"
		print "</ul>"
	
def printContent(db, me, ipaddr, errors, cookie):
	print "<html><head>"
	print '<link rel="stylesheet" type="text/css" media="all" href="main.css">'
	print "</head><body>"
	print '<section id="me">'
	print "<h4>" + (cgi.escape(me.name) if isinstance(me, User) and isinstance(me.name, str) else config.getmain("defaultusername")) + "</h4>"
	print "<code>" + cgi.escape(ipaddr, quote=True) + "</code>"
	print '<form method="post"><input name="username"><input type="submit" value="Set username"></form>'
	print "</section>"

	printErrors(errors)
		
	print '<section id="post">'
	print '<h3>Post message</h3>'
	print '<form method="post">'
	print '<textarea name="content"></textarea><input type="submit" value="Post">'
	print '</form>'
	print "</section>"
	print '<section id="messages">'
	print "<h3>Messages</h3>"

	if not db.valid():
		print "Database invalid"
	elif len(db.data["messages"]) < 1 :
		print "No messages"
	else:
		for msg in reversed(db.data["messages"]):
			print "<div>"
			print cgi.escape(msg.user.name if isinstance(msg.user.name, str) else msg.user.ip, quote=True)
			print " at "
			print cgi.escape(msg.date.isoformat(), quote=True) + " UTC"
			print "</div>"
			print "<div>"
			print cgi.escape(msg.content, quote=True)
			print "</div>"
			print "<br>"

	print "</section>"
	print "</body></html>"
	

def main():
	ipaddr = os.environ["REMOTE_ADDR"]
	form = cgi.FieldStorage()
	
	cookie = None
	try:
		cookie = SimpleCookie(os.environ["HTTP_COOKIE"] if "HTTP_COOKIE" in os.environ else None)
	except:
		pass
	
	db = MessageDB(config.getmain("datafile"), config.getmain("validusername"), config.getmainint("maxusers"),
		config.getmainint("maxmessages"), config.getmainint("maxcontent"))
		
	with db.wait():

		errors = []
		me, newcookie = handleCookie(db, ipaddr, cookie, errors)
		me = handleForm(db, me, ipaddr, errors, newcookie, form)
		printHeaders(newcookie)
		printContent(db, me, ipaddr, errors, newcookie)

main()
		