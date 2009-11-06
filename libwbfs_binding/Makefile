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
INCLUDE = -Ilibwbfs
OBJETIVOS = wiithon_wrapper
DEPENDENCIAS = libwbfs/libwbfs.o libwbfs/libwbfs_linux.o libwbfs/wiidisc.o libwbfs/rijndael.o wiithon_wrapper.o

all: $(OBJETIVOS)

wiithon_wrapper: $(DEPENDENCIAS)
	$(CC) $(DEFINES) $(INCLUDE) $(LDFLAGS) -o $@ $^

%.o: %.c
	$(CC) $(DEFINES) $(INCLUDE) $(CFLAGS) $(LDFLAGS) -o $@ -c $<

clean:
	$(RM) $(DEPENDENCIAS) $(OBJETIVOS) *~
