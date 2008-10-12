import re

f = open("/etc/X11/rgb.txt")

print "colors = {"
for l in f.readlines():
  if l.startswith("!"): continue
  c = re.split("[ \t]+", l.strip())
  rgb, names = map(int, c[:3]), c[3:]
  rgb = [float(c) / 255.0 for c in rgb]
  for n in names:
    print '  %-24s: (%.2f, %.2f, %.2f),' % ('"%s"' % n.lower(), rgb[0], rgb[1], rgb[2])
print "}"
