# -*- coding: utf-8 -*-
CC = cc
CFLAGS = -Wall -ggdb -I. -fPIC
LDFLAGS = -shared

libwbfs.so: libwbfs.o libwbfs_linux.o wiidisc.o rijndael.o
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $^

clean:
	$(RM) *~ *.o

vclean: clean
	$(RM) libwfs.so

