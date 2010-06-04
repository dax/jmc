PYTHON=`which python`
DESTDIR=/
BUILDIR=$(CURDIR)/debian/jmc
PROJECT=jmc
VERSION=0.3b3

all:
	@echo "make source - Create source package"
	@echo "make install - Install on local system"
	@echo "make buildrpm - Generate a rpm package"
	@echo "make builddeb - Generate a deb package"
	@echo "make clean - Get rid of scratch and byte files"

source:
	$(PYTHON) setup.py sdist $(COMPILE)

install:
	$(PYTHON) setup.py install --root $(DESTDIR) $(COMPILE)

buildrpm:
	$(PYTHON) setup.py bdist_rpm --post-install=rpm/postinstall --pre-uninstall=rpm/preuninstall

builddeb:
	$(PYTHON) setup.py sdist $(COMPILE) --dist-dir=../
	rename -f 's/$(PROJECT)-(.*)\.tar\.gz/$(PROJECT)_$$1\.orig\.tar\.gz/' ../*
	dpkg-buildpackage -us -uc -i -I -rfakeroot

clean:
	$(PYTHON) setup.py clean
	fakeroot $(MAKE) -f $(CURDIR)/debian/rules clean
	rm -rf build/ MANIFEST
	find . -name '*.pyc' -delete
