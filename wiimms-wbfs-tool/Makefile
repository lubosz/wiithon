#----------------------------------------------------------------
# make manual: http://www.gnu.org/software/make/manual/make.html
#----------------------------------------------------------------

SHELL		= /bin/bash

AUTHOR		= Dirk Clemens
WWT_SHORT	= wwt
WWT_LONG	= Wiimms WBFS Tool
WIT_SHORT	= wit
WIT_LONG	= Wiimms ISO Tool
VERSION		= 0.33a

ifeq ($(TERM),cygwin)
SYSTEM		:= cygwin
else
SYSTEM		= $(shell test -x ./wwt && ./wwt version --long | awk -F= '$$1=="system" {print $$2}')
endif

DUMMY		:= $(shell $(SHELL) ./setup.sh)
include Makefile.setup

URI_REPOS		= http://opensvn.wiimm.de/wii/trunk/wiimms-wbfs-tool
URI_VIEWVC		= http://opensvn.wiimm.de/viewvc/wii/trunk/wiimms-wbfs-tool
URI_HOME		= http://wiimm.de/wwt/
URI_WDF			= http://wiimm.de/wwt/wdf/
URI_GBATEMP		= http://gbatemp.net/index.php?showtopic=182236\#entry2286365
URI_DOWNLOAD_I386	= http://wiimm.de/x/$(DISTRIB_I386)
URI_DOWNLOAD_CYGWIN	= http://wiimm.de/x/$(DISTRIB_CYGWIN)
URI_TITLES		= http://wiitdb.com/titles.txt

PRE		= 
CC		= $(PRE)gcc
CPP		= $(PRE)g++
STRIP		= $(PRE)strip

RM_FILES	:= *.{o,d,tmp,bak,exe} */*.{tmp,bak} */*/*.{tmp,bak}
RM_FILES2	:= *.{iso,wdf,wbfs} templates.sed version.h

MODE_FILE	= ./_mode.flag
MODE		= $(shell test -s $(MODE_FILE) && cat $(MODE_FILE))
RM_FILES	+= $(MODE_FILE)

# wbfs: files / size in GiB of WBFS partiton / number of ISO files to copy
WBFS_FILE	:= a.wbfs
WBFS_FILES	:= $(WBFS_FILE) b.wbfs c.wbfs
WBFS_SIZE	:= 12
WBFS_COUNT	:= 3

#-------------------------------------------------------------------------------
# tools

TOOLS		:= wwt wit wdf2iso iso2wdf iso2wbfs wdf-cat wdf-dump
TEST_TOOLS	:= wtest
ALL_TOOLS	:= $(sort $(TOOLS) $(TEST_TOOLS))

RM_FILES	+= $(ALL_TOOLS)

#-------------------------------------------------------------------------------
# object files

# objects of tools
TOOLS_OBJ	:= $(patsubst %,%.o,$(TOOLS))
TEST_TOOLS_OBJ	:= $(patsubst %,%.o,$(TEST_TOOLS))

# other objects
WWT_O		:= debug.o lib-std.o lib-wdf.o lib-sf.o \
		   wbfs-interface.o titles.o dclib-utf8.o
LIBWBFS_O	:= libwbfs.o wiidisc.o rijndael.o
ALL_O		:= $(sort $(WWT_O) $(LIBWBFS_O))

# all object + all sources
ALL_OBJECTS	:= $(sort $(TOOLS_OBJ) $(TEST_TOOLS_OBJ) $(ALL_O))
ALL_SOURCES	:= $(patsubst %.o,%.c,$(ALL_OBJECTS))

#-------------------------------------------------------------------------------

VPATH		+= libwbfs

ifeq ($(SYSTEM),cygwin)
LIBS		= -lcrypt
else
#LIBS		= -lcrypto
LIBS		= 
endif

DEFINES1	=  -DLARGE_FILES -D_FILE_OFFSET_BITS=64
DEFINES1	+= -DWWT		# enable WWT specific modifications in libwbfs
DEFINES1	+= -DDEBUG_ASSERT	# enable ASSERTions in release version too
DEFINES1	+= -DEXTENDED_ERRORS=1	# enable extended error messages (function,line,file)
DEFINES		=  $(strip $(DEFINES1) $(MODE) $(XDEF))

CFLAGS		= -fomit-frame-pointer -fno-strict-aliasing \
		  -Wall -Wno-parentheses -Wno-unused-function -Wno-unused-result \
		  -O3 -Ilibwbfs -I.
#CFLAGS		+= -mtune=generic
#CFLAGS		+= -march=i686 
#CFLAGS		+= -march=x86-64 
CFLAGS		+= $(XFLAGS)
CFLAGS		:= $(strip $(CFLAGS))

DEPFLAGS	= -MMD

LDFLAGS		= -static-libgcc
#LDFLAGS	+= -static
#LDFLAGS	+= -Xlinker --strip-all
LDFLAGS		:= $(strip $(LDFLAGS))

INSTALL_PATH	= /usr/local
INSTALL_SCRIPTS	= install.sh load-titles.sh
RM_FILES	+= $(INSTALL_SCRIPTS)
SCRIPTS		= ./scripts
TEMPLATES	= ./templates
MODULES		= $(TEMPLATES)/module
GEN_TEMPLATE	= ./gen-template.sh

DISTRIB_RM	= ./wwt-v$(VERSION)-r
DISTRIB_BASE	= wwt-v$(VERSION)-r$(REVISION_NEXT)
DISTRIB_PATH	= ./$(DISTRIB_BASE)-$(SYSTEM)
DISTRIB_I386	= $(DISTRIB_BASE)-i386.tar.gz
DISTRIB_CYGWIN	= $(DISTRIB_BASE)-cygwin.zip
DISTRIB_FILES	= gpl-2.0.txt $(INSTALL_SCRIPTS)
DOC_FILES	= doc/*.txt
TITLE_FILES	= titles.txt $(patsubst %,titles-%.txt,$(LANGUAGES))
LANGUAGES	= de es fr it ja ko nl pt

BIN_FILES	= $(TOOLS)
LIB_FILES	= $(TITLE_FILES)

CYGWIN_DIR	= pool/cygwin
CYGWIN_BIN	= cygwin1.dll
CYGWIN_BIN_SRC	= $(patsubst %,$(CYGWIN_DIR)/%,$(CYGWIN_BIN))

DIR_LIST_BIN	= $(SCRIPTS) bin bin/debug
DIR_LIST	= $(DIR_LIST_BIN) $(TEMPLATES) $(MODULES) lib doc work pool

# local definitions
-include Makefile.local

#
###############################################################################
# default rule

default_rule: all
	@echo "HINT: try 'make help'"

# include this behind the default rule
-include Makefile.user
-include $(ALL_SOURCES:.c=.d)

#
###############################################################################
# general rules

$(ALL_TOOLS): %: %.o $(ALL_O) Makefile
	@echo "***    tool $@ $(MODE)"
	@$(CC) $(CFLAGS) $(DEFINES) $(LDFLAGS) $@.o $(ALL_O) $(LIBS) -o $@
	@if test -f $@.exe; then $(STRIP) $@.exe; else $(STRIP) $@; fi

#
#--------------------------

$(ALL_OBJECTS): %.o: %.c version.h Makefile
	@echo "***  object $@ $(MODE)"
	@$(CC) $(CFLAGS) $(DEPFLAGS) $(DEFINES) -c $< -o $@

#
###############################################################################
# specific rules in alphabetic order

.PHONY : all
all: $(ALL_TOOLS)

.PHONY : all+
all+: clean+ all distrib

.PHONY : all++
all++: clean+ all titles distrib

#
#--------------------------

.PHONY : chmod
chmod:
	@echo "***   chmod"
	@mkdir -p $(DIR_LIST)
	-@chmod -f 664 *.txt *.c *.h *.edit-list Makefile* $(SCRIPTS)/* lib*/*
	-@chmod -f 664 $(TEMPLATES)/* $(MODULES)/*
	-@chmod -f 775 $(DIR_LIST) 2>/dev/null || true
	-@chmod -f 775 *.sh $(TEMPLATES)/*.sh $(SCRIPTS)/*.sh bin/* bin/debug/*
	-@chown -f --reference=. * $(DIR_LIST)			2>/dev/null || true
	-@chown -f --reference=. * $(TEMPLATES)/* $(MODULES)/*	2>/dev/null || true
	-@chown -f --reference=. * bin/* work/*	$(SCRIPTS)/*	2>/dev/null || true
	$(shell for f in $(ALL_TOOLS); do test -f "$f" && chmod 775 "$f"; done)

#
#--------------------------

.PHONY : clean
clean:
	@echo "***      rm $(RM_FILES)"
	@rm -f $(RM_FILES)
	@rm -fr $(DISTRIB_RM)*

.PHONY : clean+
clean+: clean
	@echo "***      rm $(RM_FILES2) + template-output"
	@rm -f $(RM_FILES2)
	-@rm -fr doc

.PHONY : clean++
clean++: clean+
	@test -d .svn && svn st | sort +1 || true

#
#--------------------------

.PHONY : debug
debug:
	@echo "***  enable debug (-DDEBUG)"
	@rm -f *.o $(ALL_TOOLS)
	@echo "-DDEBUG" >>$(MODE_FILE)
	@sort $(MODE_FILE) | uniq > $(MODE_FILE).tmp
# 2 steps because a cygwin mv failure
	@cp $(MODE_FILE).tmp $(MODE_FILE)
	@rm -f $(MODE_FILE).tmp

#
#--------------------------

.PHONY : distrib
distrib: all doc $(INSTALL_SCRIPTS) gen-distrib

.PHONY : distrib+
distrib+:
	@make clean+ debug wwt
	@make clean distrib

	@mkdir -p $(DISTRIB_PATH)/bin-debug
	@cp bin/debug/wwt $(DISTRIB_PATH)/bin-debug

	@chmod -R 664 $(DISTRIB_PATH)
	@chmod a+x $(DISTRIB_PATH)/*.sh $(DISTRIB_PATH)/scripts/*.sh $(DISTRIB_PATH)/bin*/*
	@chmod -R a+X $(DISTRIB_PATH)
#	-@chown -R --reference=. $(DISTRIB_PATH) >/dev/null

	@tar -czf $(DISTRIB_PATH).tar.gz $(DISTRIB_PATH)

.PHONY : gen-distrib
gen-distrib:

	@echo "***  create $(DISTRIB_PATH)"

ifeq ($(SYSTEM),cygwin)

	@rm -rf $(DISTRIB_PATH)/* 2>/dev/null || true
	@rm -rf $(DISTRIB_PATH) 2>/dev/null || true
	@mkdir -p $(DISTRIB_PATH)/bin $(DISTRIB_PATH)/doc
	@cp -p gpl-2.0.txt $(DISTRIB_PATH)
	@cp -p $(TOOLS) $(CYGWIN_BIN_SRC) $(DISTRIB_PATH)/bin
	@( cd lib; cp $(TITLE_FILES) ../$(DISTRIB_PATH)/bin )
	@cp -p $(DOC_FILES) $(DISTRIB_PATH)/doc
	@zip -roq $(DISTRIB_PATH).zip $(DISTRIB_PATH)

else
	@rm -rf $(DISTRIB_PATH)
	@mkdir -p $(DISTRIB_PATH)/bin $(DISTRIB_PATH)/scripts $(DISTRIB_PATH)/lib $(DISTRIB_PATH)/doc

	@cp -p $(DISTRIB_FILES) $(DISTRIB_PATH)
	@cp -p $(TOOLS) $(DISTRIB_PATH)/bin
	@cp -p lib/*.txt $(DISTRIB_PATH)/lib
	@cp -p $(DOC_FILES) $(DISTRIB_PATH)/doc
	@cp -p $(SCRIPTS)/*.{sh,txt} $(DISTRIB_PATH)/scripts

	@chmod -R 664 $(DISTRIB_PATH)
	@chmod a+x $(DISTRIB_PATH)/*.sh $(DISTRIB_PATH)/scripts/*.sh $(DISTRIB_PATH)/bin*/*
	@chmod -R a+X $(DISTRIB_PATH)
#	-@chown -R --reference=. $(DISTRIB_PATH) >/dev/null

	@tar -czf $(DISTRIB_PATH).tar.gz $(DISTRIB_PATH)
endif

#
#--------------------------

.PHONY : doc
doc: $(TOOLS) templates.sed gen-doc

.PHONY : gen-doc
gen-doc:
	@echo "***  create documentation"
	@chmod ug+x $(GEN_TEMPLATE)
	@$(GEN_TEMPLATE)
	@cp -p doc/WDF.txt .

#
#--------------------------

.PHONY : flags
flags:
	@echo  ""
	@echo  "DEFINES: $(DEFINES)"
	@echo  ""
	@echo  "CFLAGS:  $(CFLAGS)"
	@echo  ""
	@echo  "LDFLAGS: $(LDFLAGS)"
	@echo  ""

#
#--------------------------

.PHONY : install
install: all install.sh
	@chmod a+x install.sh
	@./install.sh --make

.PHONY : install+
install+: clean+ all $(INSTALL_SCRIPTS)
	@chmod a+x install.sh
	@./install.sh --make

install.sh: templates.sed templates/install.sh
	@echo "***  create install.sh"
	@chmod ug+x $(GEN_TEMPLATE)
	@$(GEN_TEMPLATE) install.sh
	@chmod a+x install.sh

#
#--------------------------

.PHONY : predef
predef:
	@gcc -E -dM none.c | sort

#
#--------------------------

templates.sed: Makefile
	@echo "***  create templates.sed"
	@echo -e '' \
		'/^~/ d;\n' \
		's|@.@@@|$(VERSION)|g;\n' \
		's|@@@@-@@-@@|$(DATE)|g;\n' \
		's|@@:@@:@@|$(TIME)|g;\n' \
		's|@@AUTHOR@@|$(AUTHOR)|g;\n' \
		's|@@WWT-SHORT@@|$(WWT_SHORT)|g;\n' \
		's|@@WWT-LONG@@|$(WWT_LONG)|g;\n' \
		's|@@WIT-SHORT@@|$(WIT_SHORT)|g;\n' \
		's|@@WIT-LONG@@|$(WIT_LONG)|g;\n' \
		's|@@VERSION@@|$(VERSION)|g;\n' \
		's|@@REV@@|$(REVISION)|g;\n' \
		's|@@REV-NUM@@|$(REVISION_NUM)|g;\n' \
		's|@@REV-NEXT@@|$(REVISION_NEXT)|g;\n' \
		's|@@BINTIME@@|$(BINTIME)|g;\n' \
		's|@@DATE@@|$(DATE)|g;\n' \
		's|@@TIME@@|$(TIME)|g;\n' \
		's|@@INSTALL-PATH@@|$(INSTALL_PATH)|g;\n' \
		's|@@BIN-FILES@@|$(BIN_FILES)|g;\n' \
		's|@@LIB-FILES@@|$(LIB_FILES)|g;\n' \
		's|@@LANGUAGES@@|$(LANGUAGES)|g;\n' \
		's|@@DISTRIB-I386@@|$(DISTRIB_I386)|g;\n' \
		's|@@DISTRIB-CYGWIN@@|$(DISTRIB_CYGWIN)|g;\n' \
		's|@@URI-REPOS@@|$(URI_REPOS)|g;\n' \
		's|@@URI-VIEWVC@@|$(URI_VIEWVC)|g;\n' \
		's|@@URI-HOME@@|$(URI_HOME)|g;\n' \
		's|@@URI-WDF@@|$(URI_WDF)|g;\n' \
		's|@@URI-GBATEMP@@|$(URI_GBATEMP)|g;\n' \
		's|@@URI-DOWNLOAD-I386@@|$(URI_DOWNLOAD_I386)|g;\n' \
		's|@@URI-DOWNLOAD-CYGWIN@@|$(URI_DOWNLOAD_CYGWIN)|g;\n' \
		's|@@URI-TITLES@@|$(URI_TITLES)|g;\n' \
		>templates.sed

#
#--------------------------

.PHONY : test
test:
	@echo "***  enable test (-DTEST)"
	@rm -f *.o $(ALL_TOOLS)
	@echo "-DTEST" >>$(MODE_FILE)
	@sort $(MODE_FILE) | uniq > $(MODE_FILE).tmp
# 2 steps because a cygwin mv failure
	@cp $(MODE_FILE).tmp $(MODE_FILE)
	@rm -f $(MODE_FILE).tmp

#
#--------------------------

.PHONY : titles
titles: wwt load-titles.sh gen-titles

.PHONY : gen-titles
gen-titles:
	@chmod a+x load-titles.sh
	@./load-titles.sh --make

load-titles.sh: templates.sed templates/load-titles.sh
	@echo "***  create load-titles.sh"
	@chmod ug+x $(GEN_TEMPLATE)
	@$(GEN_TEMPLATE) load-titles.sh
	@chmod a+x load-titles.sh

#
#--------------------------

version.h: templates.sed $(TEMPLATES)/version.h
	@echo "***  create version.h"
	@chmod 775 $(GEN_TEMPLATE)
	@$(GEN_TEMPLATE) version.h

#
#--------------------------

%.wbfs: wwt
	@echo "***  create $@, $(WBFS_SIZE)G, add smallest $(WBFS_COUNT) ISOs"
	@rm -f $@
	@./wwt format --force --size $(WBFS_SIZE)- "$@"
	@stat --format="%b|%n" pool/iso/*.iso \
		| sort -n \
		| awk '-F|' '{print $$2}' \
		| head -n$(WBFS_COUNT) \
		| ./wwt -A -p "$@" add @- -v

#
#--------------------------

.PHONY : wbfs
wbfs: wwt gen-wbfs

.PHONY : gen-wbfs
gen-wbfs:
	@echo "***  create $(WBFS_FILE), $(WBFS_SIZE)G, add smallest $(WBFS_COUNT) ISOs"
	@rm -f $(WBFS_FILE)
	@./wwt format --force --size $(WBFS_SIZE)- $(WBFS_FILE)
	@stat --format="%b|%n" pool/iso/*.iso \
		| sort -n \
		| awk '-F|' '{print $$2}' \
		| head -n$(WBFS_COUNT) \
		| ./wwt -A -p @<(ls $(WBFS_FILE)) add @- -v
	@echo
	@./wwt f -l $(WBFS_FILE)
	@./wwt ll $(WBFS_FILE) --mtime

#
#--------------------------

.PHONY : wbfs+
wbfs+: wwt gen-wbfs+

.PHONY : gen-wbfs+
gen-wbfs+:
	@echo "***  create $(WBFS_FILES), $(WBFS_SIZE)G, add smallest $(WBFS_COUNT) ISOs"
	@rm -f $(WBFS_FILES) no.wbfs
	@./wwt format --force --size $(WBFS_SIZE)- $(WBFS_FILES)
	@stat --format="%b|%n" pool/iso/*.iso \
		| sort -n \
		| awk '-F|' '{print $$2}' \
		| head -n$(WBFS_COUNT) \
		| ./wwt -A -p @<(ls $(WBFS_FILES)) add @- -v
	@echo
	@./wwt f -l $(WBFS_FILES)
	@./wwt ll $(WBFS_FILES)
	@echo "WBFS: this is not a wbfs file" >no.wbfs

#
###############################################################################
# help rule

.PHONY : help
help:
	@echo  ""
	@echo  "$(DATE) $(TIME) - $(VERSION) - svn r$(REVISION):$(REVISION_NEXT)"
	@echo  ""
	@echo  " make		compile all tools (nearly same as make all)"
	@echo  " make all	make all tools"
	@echo  " make all+	clean & make distrib"
	@echo  " make all++	clean & make really all"
	@echo  " make tool	compile only the named 'tool'"
	@echo  " make clean	remove all output files"
	@echo  " make clean+	make clean & rm test files & rm template output"
	@echo  ""
	@echo  " make debug	enable '-DDEBUG'"
	@echo  " make test	enable '-DTEST'"
	@echo  " make flags	print DEFINES, CFLAGS and LDFLAGS"
	@echo  ""
	@echo  " make chmod	change mode of files"
	@echo  " make distrib	make all & build $(DISTRIB_FILE)"
	@echo  " make doc	generate doc files from their templates"
	@echo  " make install	copy tools to $(INSTALL_PATH)"
	@echo  " make titles	get titles from $(URI_TITLES)"
	@echo  " make version	generate file 'version.h'"
	@echo  " make %.wbfs	gen %.wbfs, $(WBFS_SIZE)G, add smallest $(WBFS_COUNT) ISOs"
	@echo  " make wbfs	gen $(WBFS_FILE), $(WBFS_SIZE)G, add smallest $(WBFS_COUNT) ISOs"
	@echo  " make wbfs+	gen $(WBFS_FILES), $(WBFS_SIZE)G, add smallest $(WBFS_COUNT) ISOs"
	@echo  ""
	@echo  " make help	print this help"
	@echo  ""
