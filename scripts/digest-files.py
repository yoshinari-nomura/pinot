#!/usr/bin/env python3

import binascii
import hashlib
import re
import os
import sys

class DigestDirtree:
    def isdir(self, path):
        return os.stat(path)[0] & 0x4000 != 0

    def digest(self, path, echo = True):
        hash = hashlib.sha1()

        if self.isdir(path):
            path = re.sub('/$', '', path) + '/'
            for child in sorted(os.listdir(path)):
                cpath = path + child
                hash.update(self.digest(cpath))
                hash.update(child.encode())
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
    dir = sys.argv[1] if len(sys.argv) > 1 else '/'
    DigestDirtree().digest(dir)
