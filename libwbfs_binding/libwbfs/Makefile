# -*- coding: utf-8 -*-
CC = cc
CFLAGS = -Wall -ggdb -I. -fPIC -m32
LDFLAGS = -shared -m32

libwbfs.so: libwbfs.o libwbfs_linux.o wiidisc.o rijndael.o
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $^

clean:
	$(RM) *~ *.o *.so

vclean: clean
	$(RM) libwfs.so

