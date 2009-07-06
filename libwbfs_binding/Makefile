# -*- coding: utf-8 -*-
CC = cc
CFLAGS = -O2 -Wall -DLARGE_FILES -D_FILE_OFFSET_BITS=64
LDFLAGS = -Llibwbfs -lwbfs -m32
INCLUDE = -Ilibwbfs
OBJETIVOS = libwbfs/libwbfs.so wiithon_wrapper

all: $(OBJETIVOS)

libwbfs/libwbfs.so:
	$(MAKE) -C libwbfs

wiithon_wrapper: wiithon_wrapper.o
	$(CC) $(INCLUDE) $(LDFLAGS) -o $@ $^

%.o: %.c
	$(CC) $(INCLUDE) $(LDFLAGS) $(CFLAGS) -o $@ -c $<

clean:
	$(RM) *~ *.o $(OBJETIVOS)
	$(MAKE) -C libwbfs clean

