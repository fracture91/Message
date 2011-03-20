#!/usr/local/bin/python2.6

"""
Intended for testing mutex of the data file by running this once until it waits for input,
then running it again in another interpreter.  The second instance should block until the first
instance receives input.  Then it should wait for input itself.  Assuming the datafile test.pkl
was empty when the test started, you should end up with [1, 2, 1, 2].
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.pardir))

from DB import DB

del sys.path[0]

db = DB("test.pkl")

with db.wait():
	print db.data["messages"]
	db.data["messages"].append(1)
	db.dirty = True
	print db.data["messages"]
	raw_input()
	db.data["messages"].append(2)
	print db.data["messages"]
