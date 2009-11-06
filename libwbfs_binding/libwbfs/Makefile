# -*- coding: utf-8 -*-
CC = gcc
ARCH=${shell uname -m}
ifeq ($(ARCH), x86_64)
	CFLAGS_MACH = -mtune=k8
else
	CFLAGS_MACH = -mtune=generic
endif
CFLAGS = -O2 -Wall -m32 $(CFLAGS_MACH)
DEFINES = -DLARGE_FILES -D_FILE_OFFSET_BITS=64
LDFLAGS = 
LIBRERIA = -shared -fPIC
INCLUDE = -I.
OBJETIVOS = libwbfs.so

all: $(OBJETIVOS)

libwbfs.so: libwbfs.o libwbfs_linux.o wiidisc.o rijndael.o
	$(CC) $(DEFINES) $(CFLAGS) $(INCLUDE) $(LDFLAGS) $(LIBRERIA) -o $@ $^
	
%.o: %.c
	$(CC) $(DEFINES) $(CFLAGS) $(INCLUDE) $(LDFLAGS) -c $^ -o $@

clean: clean_libwbfs
	$(RM) *~ *.o

clean_libwbfs: clean
	$(RM) libwfs.so
