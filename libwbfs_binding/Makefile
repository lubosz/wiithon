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
LDFLAGS = -Llibwbfs -lwbfs
INCLUDE = -Ilibwbfs
OBJETIVOS = libwbfs/libwbfs.so wiithon_wrapper

all: $(OBJETIVOS)

libwbfs/libwbfs.so:
	$(MAKE) -C libwbfs

wiithon_wrapper: wiithon_wrapper.o
	$(CC) $(DEFINES) $(INCLUDE) $(LDFLAGS) -o $@ $^

%.o: %.c
	$(CC) $(DEFINES) $(INCLUDE) $(CFLAGS) $(LDFLAGS) -o $@ -c $<

clean: clean_libwbfs
	$(RM) *~ *.o $(OBJETIVOS)
	
clean_libwbfs:
	$(MAKE) -C libwbfs clean
