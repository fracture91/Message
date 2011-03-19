from ConfigParser import RawConfigParser

#like a RawConfigParser, but reads file upon construction, adds a section named mainSection if not present,  
#and will create the config file if it doesn't exist.
#getmain* methods are like RawConfigParser.get* methods.  Arguments are option[, section] where section defaults to mainSection.
class FriendlyConfig(RawConfigParser):
	def __init__(self, filename, defaults={}, mainSection="main"):
		#RawConfigParser is an old-style class
		RawConfigParser.__init__(self, defaults)
		self.filename = filename
		self.mainSection = mainSection
		
		configExists = False
		try:
			configFile = open(self.filename, "r")
			configExists = True
			self.readfp(configFile)
			configFile.close()
		except:
			pass
		
		if not self.has_section(self.mainSection):
			self.add_section(self.mainSection)
		
		if not configExists:
			self.write(open(self.filename, "w"))

	def getmain(self, option, section=None, type=""):
		if section is None:
			section = self.mainSection
		return getattr(RawConfigParser, "get"+type)(self, section, option)
	def getmainint(self, option, section=None):
		return self.getmain(option, section, "int")
	def getmainfloat(self, option, section=None):
		return self.getmain(option, section, "float")
	def getmainboolean(self, option, section=None):
		return self.getmain(option, section, "boolean")
