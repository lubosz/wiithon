PROGS = wiithon_wrapper
COMMON = libwbfs.o libwbfs_linux.o wiidisc.o rijndael.o
DEFINES = -DLARGE_FILES -D_FILE_OFFSET_BITS=64
LIBS = -L. 
#-lcrypto
CC = gcc
#CFLAGS = -Wall -W -Os -Ilibwbfs -I.
CFLAGS = -Wall -m32 -W  -g -ggdb -Ilibwbfs -I.
LDFLAGS = -m32 -static

VPATH+=libwbfs
OBJS = $(patsubst %,%.o,$(PROGS)) $(COMMON)

all: $(PROGS)

$(PROGS): %: %.o $(COMMON) Makefile
	$(CC) $(CFLAGS) $(LDFLAGS) $< $(COMMON) $(LIBS) -o $@

$(OBJS): %.o: %.c Makefile
	$(CC) $(CFLAGS) $(DEFINES) -c $< -o $@ 

clean:
	-rm -f $(OBJS) $(PROGS)

