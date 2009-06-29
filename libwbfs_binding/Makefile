# -*- coding: utf-8 -*-
CC = cc
CFLAGS = -O2 -Wall -DLARGE_FILES -D_FILE_OFFSET_BITS=64
LDFLAGS = -Llibwbfs -lwbfs
INCLUDE = -Ilibwbfs
OBJETIVOS = libwbfs/libwbfs.so build_wiithon_wrapper/wiithon_wrapper

all: $(OBJETIVOS)

libwbfs/libwbfs.so:
	$(MAKE) -C libwbfs

build_wiithon_wrapper/wiithon_wrapper: wiithon_wrapper.o
	$(CC) $(INCLUDE) $(LDFLAGS) -o $@ $^

%.o: %.c
	$(CC) $(INCLUDE) $(CFLAGS) -o $@ -c $<

clean:
	$(RM) *~ *.o $(OBJETIVOS)
	$(MAKE) -C libwbfs clean

