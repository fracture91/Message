
from DB import DB
import re

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
	if length > -1:
		difference = len(list) - length
		if difference > 0:
			del list[:difference]
			return True
	return False
	

class MessageDB(DB):
	def __init__(self, filename, validusername="", maxusers=-1, maxmessages=-1, maxcontent=-1):
		super(MessageDB, self).__init__(filename)
		self.validusername = validusername
		self.maxusers = maxusers
		self.maxmessages = maxmessages
		self.maxcontent = maxcontent
	
	def findUser(self, name=None, ip=None, add=False):
		if (not name) == (not ip): #if both arguments are given or neither are given
			raise TypeError("Must provide exactly one of name or ip")
		else:
			#find the first user with a matching name or ip
			user = next((user for user in self.data["users"] if name and user.name == name or ip and user.ip == ip), None)
			#add a new user if preferred
			if user is None and add:
				user = self.addUser(name, ip)
			return user
	
	def addUser(self, name=None, ip=None, check=False):
		if (not name) == (not ip): #if both arguments are given or neither are given
			raise TypeError("Must provide exactly one of name or ip")
		else:
			if check:
				user = self.findUser(name, ip)
				if user:
					return user

			users = self.data["users"]
			user = User(ip, name)
			users.append(user)
			enforceLength(users, self.maxusers)
			self.dirty = True
			return user
	
	def setUsername(self, user, name, indb=True):
		if re.match(self.validusername, name):
			user.name = name
			if indb:
				self.dirty = True
			return True
		return False
		
	def addMessage(self, user, date, content):
		message = Message(user, date, None)
		self.setMessageContent(message, content)
		messages = self.data["messages"]
		messages.append(message)
		enforceLength(messages, self.maxmessages)
		self.dirty = True
		return message
		
	def setMessageContent(self, message, content, indb=True):
		message.content = content[:self.maxcontent]
		if indb:
			self.dirty = True
		return len(content) - self.maxcontent
