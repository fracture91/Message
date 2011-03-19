#!/usr/local/bin/python2.6

import sys
import cPickle
try:
	file = open("data.pkl", "w")
	cPickle.dump({"messages": [], "users": []}, file)
	file.close()
except:
	print "Error: " + str(sys.exc_info()[0]) + ", " + str(sys.exc_info()[1])