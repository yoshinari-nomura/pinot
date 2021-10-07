#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import binascii
import hashlib
import re
import os
import sys

class DigestDirtree:
    """
    Calculate Digest of Files
    """

    def __init__(self):
        pass

    def isdir(self, path):
        return os.stat(path)[0] & 0x4000 != 0

    def digest(self, path, echo = True):
        hash = hashlib.sha1()

        if self.isdir(path):
            path = re.sub('/$', '', path) + '/'
            for child in os.listdir(path):
                cpath = path + child
                hash.update(self.digest(cpath))
                hash.update(cpath.encode())
        else:
            with open(path, 'rb') as file:
                while True:
                    s = file.read(512)
                    if len(s) <= 0:
                        break
                    hash.update(s)
        sha1 = hash.digest()
        if echo:
            print(str(binascii.hexlify(sha1), 'ascii'), path)
        return sha1

if __name__ == '__main__':
    if len(sys.argv) > 1:
        sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
        dir = sys.argv[1]
    else:
        dir = '/'
    DigestDirtree().digest(dir)
