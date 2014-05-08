#!/usr/bin/env python

import sys
import os
import getpass
import struct
import string
import random
import urllib2
import operator
from StringIO import StringIO
from multiprocessing.dummy import Pool
from PIL import PngImagePlugin, Image, BmpImagePlugin

from keepass import kpdb


def random_image_name(size, ext="png"):
    s = ''.join(random.choice(string.ascii_letters) for x in range(size))
    return "{}.{}".format(s, ext)

password = getpass.getpass()


db = kpdb.Database(sys.argv[1], password)

custom_icons_entry = next((e for e in db.entries if e.notes == "KPX_CUSTOM_ICONS_4"), None)

if custom_icons_entry:
    data = custom_icons_entry.binary_data
else:
    sys.exit(1)


try:
    os.mkdir("favicons")
except OSError:
    pass

##########

num_icons, num_entries, num_groups = struct.unpack("III", data[:3*4])

print("Icons: {}\nEntries: {}\nGroups: {}".format(num_icons, num_entries, num_groups))

position = 3*4
for i in range(num_icons):
    size = struct.unpack("I", data[position:position+4])[0]
    position += 4
    image = data[position:position+size]
    position += size

    path = os.path.join("favicons", random_image_name(6))
    with open(path, 'wb') as fh:
        fh.write(image)

    print "Favicon saved to {}".format(path)