import sys, zipfile, hashlib, json, os
z = zipfile.ZipFile(sys.argv[1])
names = z.namelist()
bad = [n for n in names if n.startswith('/') or '..' in n.split('/') or '\\' in n]
syml = [i.filename for i in z.infolist() if (i.external_attr >> 16) & 0o170000 == 0o120000]
print("entries", len(names), "dirs", sum(n.endswith('/') for n in names), "bad", bad[:5], "symlinks", syml[:5])
print("dupes", len(names) - len(set(names)))
print("testzip", z.testzip())
tops = sorted({n.split('/')[0] for n in names})
print("top-level", tops[:60])
total = sum(i.file_size for i in z.infolist())
print("uncompressed MB", total/1e6)
