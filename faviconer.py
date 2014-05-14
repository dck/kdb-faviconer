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


def get_favicon(url):
    url += "/favicon.ico"
    try:
        data = urllib2.urlopen(url).read()
    except urllib2.URLError as e:
        print "Cant retrieve favicon for {}".format(url)
        raise
    return data

def load_icon(file, index=None):
    try:
        header = struct.unpack('<3H', file.read(6))
    except:
        raise IOError('Not an ICO file')

    # Check magic
    if header[:2] != (0, 1):
        raise IOError('Not an ICO file')

    # Collect icon directories
    directories = []
    for i in xrange(header[2]):
        directory = list(struct.unpack('<4B2H2I', file.read(16)))
        for j in xrange(3):
            if not directory[j]:
                directory[j] = 256

        directories.append(directory)

    if index is None:
        # Select best icon
        directory = max(directories, key=operator.itemgetter(slice(0, 3)))
    else:
        directory = directories[index]

    # Seek to the bitmap data
    file.seek(directory[7])

    prefix = file.read(16)
    file.seek(-16, 1)

    if PngImagePlugin._accept(prefix):
        # Windows Vista icon with PNG inside
        image = PngImagePlugin.PngImageFile(file)
    else:
        # Load XOR bitmap
        image = BmpImagePlugin.DibImageFile(file)
        if image.mode == 'RGBA':
            # Windows XP 32-bit color depth icon without AND bitmap
            pass
        else:
            # Patch up the bitmap height
            image.size = image.size[0], image.size[1] >> 1
            d, e, o, a = image.tile[0]
            image.tile[0] = d, (0, 0) + image.size, o, a

            # Calculate AND bitmap dimensions. See
            # http://en.wikipedia.org/w/index.php?oldid=264236948#Pixel_storage
            # for description
            offset = o + a[1] * image.size[1]
            stride = ((image.size[0] + 31) >> 5) << 2
            size = stride * image.size[1]

            # Load AND bitmap
            file.seek(offset)
            string = file.read(size)
            mask = Image.fromstring('1', image.size, string, 'raw',
                                    ('1;I', stride, -1))

            image = image.convert('RGBA')
            image.putalpha(mask)

    return image

def ico_to_png_data(data):
    s = StringIO(data)
    image = load_icon(s)
    return image

def save_png(image, name):
    image.save("favicons/" + name + ".png")

def save_raw(data, name):
    with open("favicons/" + name + ".ico", "wb") as fh:
        fh.write(data)

def chain(input_value):
    #chain = (get_favicon, ico_to_png_data, lambda data: save_png(data, input_value[7:]))
    chain = (get_favicon, lambda data: save_raw(data, input_value[7:]))
    try:
        reduce((lambda x, y: y(x)), chain, input_value)
    except Exception as e:
        return

try:
    path = sys.argv[1]
except IndexError:
    print "Specify a path to kdb file"
    sys.exit(1)

password = getpass.getpass()
db = kpdb.Database(path, password)

try:
    os.mkdir("favicons")
except OSError:
    pass


urls = [e.url for e in db.entries if e.url.startswith("http")]

pool = Pool()

pool.map(chain, urls)