# -*- coding: utf-8 -*-
CC = cc
CFLAGS = -Wall -ggdb -I. -fPIC
LDFLAGS = -shared

libwbfs.so: libwbfs.o
	$(CC) $(CFLAGS) $(LDFLAGS) $^ -o $@

clean:
	$(RM) *~

vclean: clean
	$(RM) libwfs.so

