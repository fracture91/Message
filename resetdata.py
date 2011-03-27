#!/usr/local/bin/python2.6

"""
Resets all data in the datafile (data.pkl by default)
Can pass one argument, which is an alternate file to reset
"""

import sys
import cPickle

if len(sys.argv) > 1:
	datafile = sys.argv[1]
else :
	from FriendlyConfig import FriendlyConfig
	config = FriendlyConfig("config.ini", {"datafile": "data.pkl"}, write=False)
	datafile = config.getmain("datafile")

try:
	print "This will reset all of your data in " + datafile + "!"
	print "Enter 'y' to continue, anything else to quit."
	if raw_input() == "y":
		file = open(datafile, "w")
		cPickle.dump({"messages": [], "users": []}, file)
		file.close()
		print datafile + " has been reset."
	else:
		print datafile + " won't be reset, your data is safe."
except:
	print "Error: " + str(sys.exc_info()[0]) + ", " + str(sys.exc_info()[1])