#!/usr/bin/env python
# coding:utf-8
#
# locklib, convenience lock classes and synchronization functions
# Copyright (C) 2008  Mathias Stephan Panzenböck (panzi)
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
# 
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 51 Franklin St, Fifth Floor,
# Boston, MA  02110-1301, USA.
# or see <http://www.gnu.org/licenses/>.

import os
from threading import RLock, currentThread
from types     import UnboundMethodType

__all__ = 'FileLock', 'RecursiveLock', 'synchronized', \
	'Synchronizeable', 'locking', 'synchronize_all'

__version__ = '1.0-alpha1'
__author__  = 'Mathias Stephan Panzenböck (panzi)'

try:
	from msvcrt import locking, LK_LOCK, LK_NBLCK

except ImportError:
	from fcntl import flock, LOCK_EX, LOCK_NB
	from errno import EACCES, EAGAIN
	
	def _flock(fp):
		flock(fp.fileno(), LOCK_EX)

	def _tryflock(fp):
		try:
			flock(fp.fileno(), LOCK_EX | LOCK_NB)
		except IOError, e:
			if e.errno == EACCES or e.errno == EAGAIN:
				return False
			else:
				raise
		else:
			return True

else:
	def _flock(fp):
		# The string representation of a PID should never be
		# bigger than 32 characters, not even on 64bit systems.
		# However, it should work even if it is, because all
		# FileLocks want to lock the same proportion of the
		# file, even though it might not be the whole file.
		locking(fp.fileno(), LK_LOCK, 32)

	def _tryflock(fp):
		try:
			locking(fp.fileno(), LK_LOCK | LK_NBLCK, 32)
		except IOError:
			return False
		else:
			return True

class FileLock(object):
	"""
	The FileLock class provides a threading.Lock compatible interface for
	file based locks. It has implementations for POSIX compatible platforms
	and Windows (WARNING: The Windows implementations is yet to be tested).

	Example:
	
	lock = FileLock('lock')

	lock.acquire()
	try:
		do_concurrent_stuff()
	finally:
		lock.release()

	
	Using a Python version 2.5 you can achieve the same by writing:
	
	# the following line is not needed in with Python version 2.6 and newer:
	from __future__ import with_statement

	lock = FileLock('lock')
	
	with lock:
		do_concurrent_stuff()
		
	"""
	__slots__ = '__filename', '__fp', '__remove'

	def __init__(self,filename,remove=False):
		"""
		__init__(filename,remove=False)

		The filename points to the file which sould be used as lock.
		When remove is True the file gets deleted in the FileLocks
		__del__ method (default is False).
		"""
		self.__filename = filename
		self.__fp       = None
		self.__remove   = remove
		
		if not os.path.exists(filename):
			fp = open(filename, 'w')
			try:
				fp.write('-1')
			finally:
				fp.close()
	
	def __del__(self):
		try:
			if self.__fp is not None:
				self.release()
		finally:
			if self.__remove:
				try:
					os.remove(self.__filename)
				except IOError:
					pass

	def __enter__(self):
		self.acquire()
	
	def __exit__(self, exc_type, exc, tb):
		self.release()

	def acquire(self,wait=True):
		"""
		acquire([wait]) -> bool

		Lock the FileLock. Without argument, this blocks if the lock is already
		locked (even by the same thread), waiting for another thread/process to
		release the lock, and return True once the lock is acquired.
		With an argument, this will only block if the argument is True,
		and the return value reflects whether the lock is acquired.
		"""
		fp = open(self.__filename, 'r+')

		if wait:
			_flock(fp)
			self.__fp = fp
			fp.truncate()
			fp.write(str(os.getpid()))
			fp.flush()

			return True

		elif _tryflock(fp):
			self.__fp = fp
			fp.truncate()
			fp.write(str(os.getpid()))
			fp.flush()

			return True
		else:
			
			return False
	
	def getpid(self):
		"""
		getpid() -> int

		Returns the PID (process id) of the (last) owner of the lock or -1
		if noone owns it.
		
		This can be bogus information in case the last owner crashed and has
		therefore not removed it's PID from the file.
		"""
		if self.__fp is not None:
			return os.getpid()
		else:
			fp = open(self.__filename, 'r')
			try:
				s = fp.readline()
			finally:
				fp.close()

			try:
				return int(s, 10)
			except ValueError:
				return -1

	def release(self):
		"""
		release()

		Release the lock, allowing another process that is blocked waiting for
		the lock to acquire the lock. The lock must be in the locked state,
		and it needs to be locked by the same process (not thread) that unlocks it.
		"""
		assert self.__fp is not None, 'release of unacquired lock'
		fp = self.__fp
		fp.seek(0)
		fp.truncate()
		fp.write('-1')
		self.__fp = None
		fp.close()
	
	def locked(self):
		"""
		locked() -> bool
		
		Return whether the lock is in the locked state.
		
		This can be bogus information in case the last owner crashed and has
		therefore not removed it's PID from the file.
		"""
		return self.getpid() != -1

	filename = property(lambda self: self.__filename,       doc = 'The name of the file that is used as a lock.')
	isowner  = property(lambda self: self.__fp is not None, doc = 'True if this FileLock object owns the lock, False otherwise.')

def synchronized(f):
	"""
	synchronized(method) -> method

	This method decorator adds Java like synchronizing capabilities to a method.
	The object the method get's bound to needs to have a member called __lock__
	of type threading.RLock (or compatible). Using this decorator, all calls of
	the method will be synchronized. You can extend from the class Synchronizeable
	to add a __lock__ field to your class. However, you are free to not do this and
	add this field by yourself.

	Example:
	class Foo(Synchronizeable):
		@synchronized
		def bar(self):
			print "start"
			time.sleep(2)
			print "end"
	"""
	def _f(*args,**kwargs):
		lock = args[0].__lock__
		lock.acquire()
		try:
			return f(*args,**kwargs)
		finally:
			lock.release()
	return _f

def synchronized_by(lock):
	"""
	synchronized_by(lock) -> decorator

	Like synchronized but uses the lock passed to this function.

	Example:
	lock = RLock()
	@synchronized_by(lock)
	def foo():
		do_something()
	"""
	def _deco(f):
		def _f(*args,**kwargs):
			lock.acquire()
			try:
				return f(*args,**kwargs)
			finally:
				lock.release()
		return _f
	return _deco

class Synchronizeable(object):
	"""
	Cenvenience class that adds a field __lock__ of type
	threading.RLock to your derived classes objects.
	"""
	__slots__ = '__lock__',
	
	def __init__(self,lock=None):
		"""
		__init__([lock])

		The optional lock parameter will be used as the
		__lock__ field. If there is no lock passed a new
		instance of threading.RLock will be used.
		"""
		if lock is None:
			self.__lock__ = RLock()
		else:
			self.__lock__ = lock

def locking(obj):
	"""
	locking(synchronizeable) -> lock

	Returns the __lock__ field of an object. This
	is meant to be used with the with statement.

	Example:
	class Foo(Synchronizeable):
		pass

	bar = Foo()
	with locking(bar):
		do_something()
	"""
	return obj.__lock__

def synchronize_all(cls):
	"""
	synchronize_all(classobject)

	This method wrapps all unbound methods (except __new__, __init__ and __del__)
	of the given class object using synchronized().
	"""
	for name, obj in cls.__dict__.items():
		if isinstance(obj, UnboundMethodType) and name not in ('__init__', '__del__', '__new__'):
			setattr(cls, name, synchronized(obj))

class RecursiveLock(object):
	"""
	This class wrapps a lock so it can be used recursively by the same
	thread without a deadlock.
	"""
	__slots__ = '__lock', '__n', '__owner'

	def __init__(self,lock):
		"""
		__init__(lock)

		The given lock will be wrapped so it can be used recursively by
		the same thread without a deadlock. The acquire() method of the
		child lock has to return a value that evaluates to True in case
		the lock could be acquired.
		"""
		self.__lock  = lock
		self.__n     = 0
		self.__owner = None
	
	def acquire(self,*args,**kwargs):
		"""
		acquire(*args,**kwargs) -> int

		Calls the acquire() method of the child lock and passes any given
		parameters to it. This method expect that the child locks acquire()
		method returns a value that evaluetes to True in case the lock
		operation could be performed. In that case the lock-counter gets
		increased.
		
		If the lock-counter is > 0 and the current thread holds the lock,
		the childs acquire() method will not be called. Instead only the
		lock-counter gets increased.
		
		Returns the value of the lock-counter or 0 in case the lock could
		not be acquired.
		"""
		me = currentThread()

		if self.__owner == me:
			self.__n += 1
			return self.__n

		else:
			result = self.__lock.acquire(*args,**kwargs)
			if result:
				self.__n     = 1
				self.__owner = me
				return 1
			else:
				return 0
	
	def release(self):
		"""
		release()

		Calls the release() method of the child lock if the lock-counter is 1.
		If the lock-counter is > 1, only decreases the lock-counter.
		if the lock-counter is <= 0 an AssertionError gets raised.
		"""
		if self.__n > 1:
			self.__n -= 1
		else:
			assert self.__n <= 0, 'release of unacquired lock'
			self.__n     = 0
			self.__owner = None
			self.__lock.release()
	
	def __enter__(self):
		self.acquire()
	
	def __exit__(self, exc_type, exc, tb):
		self.release()
	
	def __del__(self):
		if self.__n > 0:
			self.__lock.release()
	
	def locked(self):
		"""
		locked() -> bool

		Returns the result of the locked() method of the child lock.
		"""
		return self.__lock.locked()
	
	owner = property(lambda self: self.__owner, doc = 'The thread that holds the lock.')
	count = property(lambda self: self.__n,     doc = 'The count of recursive locks by the same thread.')
