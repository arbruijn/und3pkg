#!/usr/bin/python3
import sys
import struct
import fnmatch
import re
import getopt
import os

def readpkg(f):
	sig = f.read(4)
	if sig != b'GKPO':
		raise Exception('invalid pkg header')
	numfiles = struct.unpack('<I', f.read(4))[0]
	while True:
		dlenbuf = f.read(4)
		if not dlenbuf:
			break
		dirlen = struct.unpack('<I', dlenbuf)[0]
		dir = f.read(dirlen)
		dir = dir[:dir.index(b'\x00')]
		dir = dir.replace(b'\\', b'/')
		
		namelen = struct.unpack('<I', f.read(4))[0]
		name = f.read(namelen)
		name = name[:name.index(b'\x00')]
		
		(size, time) = struct.unpack('<IQ', f.read(12))
		time = (time / 10000000) - 11644473600 # filetime to time_t
		cur = f.tell()
		yield (dir + name, size, cur, time)
		f.seek(cur + size)

def unpkg(fn, pat, opts):
	rpat = None
	if pat:
		rpat = re.compile(fnmatch.translate(pat), re.IGNORECASE)
	dir = opts.get('d')
	list = opts.get('l')
	with open(fn, "rb") as f:
		for (bname, size, ofs, time) in readpkg(f):
			name = bname.decode('cp437').lower()
			if rpat and not rpat.match(name):
				continue
			if list:
				print(name)
				continue
			f.seek(ofs, 0)
			outname = os.path.join(dir, name) if dir else name
			print(outname)
			dir = os.path.dirname(outname)
			if dir:
				os.makedirs(dir, exist_ok = True)
			with open(outname, "wb") as fo:
				fo.write(f.read(size))
			if time:
				stat = os.stat(outname)
				os.utime(outname, (stat.st_atime, time))

if __name__ == '__main__':
	try:
		opts, args = getopt.getopt(sys.argv[1:], "ld:", ["list", "directory="])
	except getopt.GetoptError as err:
		print(err)
		sys.exit(2)
	if not args:
		print("unpkg [-l] [-doutdir] file.pkg [spec]")
		sys.exit(2)
	d = {}
	for o, a in opts:
	  d[o[1]] = a if a else True
	unpkg(args[0], args[1] if len(args) >= 2 else None, d)
