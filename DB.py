import cPickle

class DB(object):
	def __init__(self, filename):
		self.filename = filename
		self.data = None
		self.dirty = False
	def load(self):
		try:
			file = open(self.filename, "r")
			self.data = cPickle.load(file)
			self.dirty = False
			file.close()
		except IOError:
			self.data = "IOError opening message file"
		except:
			self.data = "Unknown error"
	def save(self):
		try:
			if self.valid():
				file = open(self.filename, "w")
				cPickle.dump(self.data, file)
				self.dirty = False
				file.close()
				return True
			return False
		except IOError:
			self.data = "IOError writing message file"
		except:
			self.data = "Unknown error"
	def valid(self):
		return isinstance(self.data, dict)
	def close(self):
		if self.dirty:
			return self.save()
		return False
		
	