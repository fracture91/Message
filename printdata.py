#!/usr/local/bin/python2.6

"""
Prints data in either the configured datafile or the datafile that's passed in
"""

import sys
import cPickle

#make sure to import anything necessary for unpickling
from MessageDB import User, Message


def handlePrint(key, value, tabs="", indent=0):
	if isinstance(value, list):
		printList(key, value, indent+1)
	elif isinstance(value, dict):
		printObj(key, value, indent+1, True)
	elif hasattr(value, "__dict__"):
		printObj(key, value, indent+1)
	else:
		print tabs + "\t" + str(key) + ": " + str(value),
	print ","

def printList(name, lis, indent=0):
	tabs = "\t" * indent
	print tabs + str(name) + ": ["
	index = 0
	for val in lis:
		handlePrint(index, val, tabs, indent)
		index = index + 1
	print tabs + "]",
	
def printObj(name, obj, indent=0, isDict=False):
	tabs = "\t" * indent
	members = obj.__dict__ if not(isDict) else obj
	print tabs + str(name) + ": {"
	for prop, val in members.iteritems():
		handlePrint(prop, val, tabs, indent)
	print tabs + "}",
	
	
if len(sys.argv) > 1:
	datafile = sys.argv[1]
else :
	from FriendlyConfig import FriendlyConfig
	config = FriendlyConfig("config.ini", {"datafile": "data.pkl"}, write=False)
	datafile = config.getmain("datafile")
	
try:
	file = open(datafile, "rb")
	data = cPickle.load(file)
	handlePrint("data", data, indent=-1)
	file.close()
except:
	print "Error: " + str(sys.exc_info()[0]) + ", " + str(sys.exc_info()[1])
