# JMC

## JMC installation

### Debian package

Get [JCL](http://github.com/dax/jcl/download) and [JMC](http://github.com/dax/jmc/download) Debian packages and install them:

    sudo apt-get install python-pysqlite2 python-pyxmpp python-sqlobject
    sudo dpkg -i python-jcl_0.1rc2_all.deb python-jmc_0.3rc3_all.deb

### EasyInstall

Get EasyInstall then run:

    easy_install jmc

### Manual installation

Get [JCL](http://github.com/dax/jcl) and [JMC](http://github.com/dax/jmc) sources from Git:

	python setup.py install

## Configuration

Edit `/etc/jabber/jmc.conf` `jabber` section according to your Jabber
server configuration. For help on other options, see [Configuration documentation](http://github.com/dax/jmc/wiki/Configuration-file-documentation).
Additional parameters (for Debian install) can be passed through
[command line options](http://github.com/dax/jmc/wiki/Command-line-options) defined in /etc/default/python-jmc.

## Start/Stop JMC

Debian installation:

    service python-jmc start/stop

easyinstall or manual installation (see
[command line options](http://github.com/dax/jmc/wiki/Command-line-options)):

    /usr/bin/jmc --help
