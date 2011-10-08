# -*- coding: utf-8 -*-
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
import platform

prefix = "/usr"
root = "/"
jmc_version = '0.3rc2'
for arg in sys.argv:
    if arg[0:9] == "--prefix=":
        prefix = arg[9:]
        break
for arg in sys.argv:
    if arg[0:7] == "--root=":
        root = arg[7:]
        break

if prefix == "/usr":
    prefix_config_dir = "/etc/jabber/"
else:
    prefix_config_dir = prefix + "/etc/jabber/"
config_dir = root + prefix_config_dir
full_prefix = root + prefix

setup(name='jmc',
      version=jmc_version,
      description='Jabber Mail Component',
      long_description="""\
JMC is a jabber service to check email from POP3 and IMAP4 server and retrieve
them or just a notification of new emails. Jabber users can register multiple
email accounts.""",
      author='David Rousselie',
      author_email='dax@happycoders.org',
      license="GPL",
      keywords="jabber component email IMAP POP3 SMTP",
      url='http://people.happycoders.org/dax/projects/jmc',
      classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Programming Language :: Python",
        "Topic :: Communications",
        "Topic :: Communications :: Chat",
        "Topic :: Communications :: Email",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      package_dir={'': 'src'},
      packages=find_packages('src', exclude=["*.tests",
                                             "*.tests.*",
                                             "tests.*",
                                             "tests"]),
      entry_points={'console_scripts': ['jmc=jmc.runner:main']},
      test_suite='jmc.tests.suite',
      install_requires=["jcl==0.1b3"])

if len(sys.argv) >= 2 and sys.argv[1] == "install" \
        and not "--single-version-externally-managed" in sys.argv:
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    shutil.copy("conf/jmc.conf", config_dir)
    python_version = ".".join(platform.python_version_tuple()[:2])
    runner_file_name = full_prefix + "/lib/python" + python_version + "/site-packages/jmc-" + jmc_version + "-py" + python_version + ".egg/jmc/runner.py"
    runner_file = open(runner_file_name)
    dest_runner_file_name = runner_file_name + ".tmp"
    dest_runner_file = open(dest_runner_file_name, "w")
    config_file_re = re.compile("(.*self\.config_file = \")(jmc.conf\")")
    for line in runner_file:
        match = config_file_re.match(line)
        if match is not None:
            dest_runner_file.write(match.group(1) + prefix_config_dir
                                   + match.group(2) + "\n")
        else:
            dest_runner_file.write(line)
    dest_runner_file.close()
    runner_file.close()
    shutil.move(dest_runner_file_name, runner_file_name)
