##
## setup.py
## Login : David Rousselie <dax@happycoders.org>
## Started on  Tue Apr 17 21:12:33 2007 David Rousselie
## $Id$
## 
## Copyright (C) 2007 David Rousselie
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
## 
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
## 
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
##

from setuptools import setup, find_packages
import sys
import re
import shutil
import os

prefix = "/usr"
for arg in sys.argv:
    if arg[0:9] == "--prefix=":
        prefix = arg[9:]
        break

if prefix == "/usr":
    config_dir = "/etc/jabber/"
else:
    config_dir = prefix + "/etc/jabber/"

setup(name='jmc',
      version='0.3',
      description='Jabber Mail Component',
      author='David Rousselie',
      author_email='dax@happycoders.org',
      license="GPL",
      keywords="jabber component email IMAP POP3 SMTP",
      url='http://people.happycoders.org/dax/projects/jmc',
      package_dir={'': 'src'},
      packages=find_packages('src', exclude=["*.tests",
                                             "*.tests.*",
                                             "tests.*",
                                             "tests"]),
      entry_points={'console_scripts': ['jmc=jmc.runner:main']},
      test_suite='jmc.tests.suite')

if len(sys.argv) >= 2 and sys.argv[1] == "install":
    os.makedirs(config_dir)
    shutil.copy("conf/jmc.conf", config_dir)
    runner_file = open("src/jmc/runner.py")
    dest_runner_file = open("build/lib/jmc/runner.py", "w")
    config_file_re = re.compile("(.*self\.config_file = \")(jmc.conf\")")
    for line in runner_file:
        match = config_file_re.match(line)
        if match is not None:
            dest_runner_file.write(match.group(1) + config_dir
                                   + match.group(2) + "\n")
        else:
            dest_runner_file.write(line)
