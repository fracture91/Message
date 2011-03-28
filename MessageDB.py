
from DB import DB
import re

class User(object):
	def __init__(self, name, ip):
		self.name = name
		self.ips = [ip] if isinstance(ip, str) else []
	
class Message(object):
	def __init__(self, ip, user, date, content):
		self.ip = ip
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
	
	def findUser(self, name, ip=None, add=False):
		#find the first user with a matching name
		user = next((user for user in self.data["users"] if user.name == name), None)
		#add a new user if preferred
		if user is None and add:
			user = self.addUser(name, ip, False)
		return user
	
	def addUser(self, name, ip=None, check=True):
		if check:
			user = self.findUser(name, ip)
			if user:
				self.addUserIp(user, ip)
				return user

		if not(self.validateUsername(name)):
			return None
		
		users = self.data["users"]
		user = User(name, ip)
		users.append(user)
		enforceLength(users, self.maxusers)
		self.dirty = True
		return user
	
	def validateUsername(self, name):
		return re.match(self.validusername, name)
	
	#user's can't change usernames - this is just here for admin use
	def setUsername(self, user, name, indb=True):
		if self.validateUsername(name):
			user.name = name
			if indb:
				self.dirty = True
			return True
		return False
		
	def addUserIp(self, user, ip):
		if ip not in user.ips:
			user.ips.insert(0, ip)
			self.dirty = True
		
	def addMessage(self, ip, user, date, content):
		message = Message(ip, user, date, None)
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
