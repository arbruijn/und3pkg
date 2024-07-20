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
	numfiles = struct.unpack('<i', f.read(4))[0]
	while True:
		dlenbuf = f.read(4)
		if not dlenbuf:
			break
		dirlen = struct.unpack('<i', dlenbuf)[0]
		dir = f.read(dirlen)
		dir = dir[:dir.index(b'\x00')]
		dir = dir.replace(b'\\', b'/')
		
		namelen = struct.unpack('<i', f.read(4))[0]
		name = f.read(namelen)
		name = name[:name.index(b'\x00')]
		
		(size, unknown1, unknown2) = struct.unpack('<iii', f.read(12))
		cur = f.tell()
		yield (dir + name, size, cur)
		f.seek(cur + size)

def unpkg(fn, pat, opts):
	rpat = None
	if pat:
		rpat = re.compile(fnmatch.translate(pat), re.IGNORECASE)
	dir = opts.get('d')
	list = opts.get('l')
	with open(fn, "rb") as f:
		for (bname, size, ofs) in readpkg(f):
			name = bname.decode('cp437').lower()
			if rpat and not rpat.match(name):
				continue
			if list:
				print(name)
				continue
			f.seek(ofs, 0)
			outname = os.path.join(dir, name) if dir else name
			print(outname)
			os.makedirs(os.path.dirname(outname), exist_ok = True)
			with open(outname, "wb") as fo:
				fo.write(f.read(size))

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
