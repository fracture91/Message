import cPickle
from contextlib import contextmanager
from locklib import FileLock

class DB(object):
	def __init__(self, filename):
		self.filename = filename
		self.data = None
		self.dirty = False
		self.lock = FileLock(filename+".lock")
	@contextmanager
	def wait(self):
		#wait for the data lock file
		with self.lock:
			self.load()
			try:
				#yield control to whatever's acquiring the data
				yield self.data
			finally:
				#always close the data file when done (save if dirty)
				self.close()
	def load(self):
		try:
			#open the data file and read data into self.data 
			file = open(self.filename, "rb")
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
				file = open(self.filename, "wb")
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
		
	