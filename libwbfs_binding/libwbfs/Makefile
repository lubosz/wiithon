# -*- coding: utf-8 -*-
CC = cc
CFLAGS = -Wall -ggdb -I. -fPIC -m32
DEFINES = -DLARGE_FILES -D_FILE_OFFSET_BITS=64
LDFLAGS = -shared -m32

libwbfs.so: libwbfs.o libwbfs_linux.o wiidisc.o rijndael.o
	$(CC) $(DEFINES) $(CFLAGS) $(LDFLAGS) -o $@ $^
	
%.o: %.c
	$(CC) $(DEFINES) $(CFLAGS) $(LDFLAGS) -c $^ -o $@

clean:
	$(RM) *~ *.o *.so

vclean: clean
	$(RM) libwfs.so

