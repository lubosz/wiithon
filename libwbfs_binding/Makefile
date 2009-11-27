# -*- coding: utf-8 -*-
CC = gcc
CFLAGS = -O2 -Wall
#CFLAGS = -g -Wall
DEFINES = -DLARGE_FILES -D_FILE_OFFSET_BITS=64
LDFLAGS = -m32
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
