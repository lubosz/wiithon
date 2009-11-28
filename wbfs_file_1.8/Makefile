# -*- coding: utf-8 -*-
CC = gcc
CFLAGS = -O2 -Wall -Wno-unused-variable -Wno-unused-result
DEFINES = -DLARGE_FILES -D_FILE_OFFSET_BITS=64
LDFLAGS = -m32
INCLUDE = -Ilibwbfs
OBJETIVOS = wiithon_wbfs_file
DEPENDENCIAS = libwbfs/libwbfs.o libwbfs/libwbfs_linux.o libwbfs/wiidisc.o libwbfs/rijndael.o splits.o wiithon_wbfs_file.o

all: $(OBJETIVOS)

wiithon_wbfs_file: $(DEPENDENCIAS)
	$(CC) $(DEFINES) $(INCLUDE) $(LDFLAGS) -o $@ $^

%.o: %.c
	$(CC) $(DEFINES) $(INCLUDE) $(CFLAGS) $(LDFLAGS) -o $@ -c $<

clean:
	$(RM) $(DEPENDENCIAS) $(OBJETIVOS) *~
