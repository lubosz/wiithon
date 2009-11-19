USER=~/.nautilus/python-extensions/
SYSTEM=/usr/lib/nautilus/extensions-1.0/python/
DESTINE=$(SYSTEM)

all: install

install: copy reboot_nautilus
uninstall: delete

copy:
	mkdir -p $(DESTINE)
	cp nautilus.py $(DESTINE)
	
delete:
	$(RM) $(DESTINE)nautilus.py
	
reboot_nautilus:
	-killall nautilus
	nautilus
