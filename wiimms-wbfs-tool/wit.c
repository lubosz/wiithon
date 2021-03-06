/***************************************************************************
 *                                                                         *
 *      Copyright (c) 2009 by Dirk Clemens <develop@cle-mens.de>           *
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 *   This program is distributed in the hope that it will be useful,       *
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
 *   GNU General Public License for more details.                          *
 *                                                                         *
 *   See file gpl-2.0.txt or http://www.gnu.org/licenses/gpl-2.0.txt       *
 *                                                                         *
 ***************************************************************************/

#define _GNU_SOURCE 1

#include <sys/types.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <arpa/inet.h>

#include <fcntl.h>
#include <unistd.h>
#include <getopt.h>
#include <time.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
#include <ctype.h>
#include <errno.h>

#include "debug.h"
#include "version.h"
#include "wiidisc.h"
#include "lib-std.h"
#include "lib-wdf.h"
#include "titles.h"
#include "wbfs-interface.h"

///////////////////////////////////////////////////////////////////////////////

#define TITLE WIT_SHORT ": " WIT_LONG " v" VERSION " r" REVISION " " SYSTEM " - " AUTHOR " - " DATE

//
///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////

typedef enum enumOptions
{
	// only the command specific options are named

	OPT_PSEL,
	OPT_RAW,
	OPT_DEST,
	OPT_DEST2,
	OPT_SPLIT,
	OPT_SPLIT_SIZE,
	OPT_PRESERVE,
	OPT_UPDATE,
	OPT_SYNC,
	OPT_OVERWRITE,
	OPT_IGNORE,
	OPT_REMOVE,
	OPT_TRUNC,
	OPT_FAST,
	OPT_WDF,
	OPT_ISO,
	OPT_WBFS,
	OPT_LONG,
	OPT_ITIME,
	OPT_MTIME,
	OPT_CTIME,
	OPT_ATIME,
	OPT_TIME,
	OPT_UNIQUE,
	OPT_NO_HEADER,
	OPT_SORT,

	OPT__N_SPECIFIC,

} enumOptions;

///////////////////////////////////////////////////////////////////////////////

typedef enum enumOptionsBit
{
	// bitmask fo all command specific options

	OB_PSEL		= 1 << OPT_PSEL,
	OB_RAW		= 1 << OPT_RAW,
	OB_DEST		= 1 << OPT_DEST,
	OB_DEST2	= 1 << OPT_DEST2,
	OB_SPLIT	= 1 << OPT_SPLIT,
	OB_SPLIT_SIZE	= 1 << OPT_SPLIT_SIZE,
	OB_PRESERVE	= 1 << OPT_PRESERVE,
	OB_UPDATE	= 1 << OPT_UPDATE,
	OB_SYNC		= 1 << OPT_SYNC,
	OB_OVERWRITE	= 1 << OPT_OVERWRITE,
	OB_IGNORE	= 1 << OPT_IGNORE,
	OB_REMOVE	= 1 << OPT_REMOVE,
	OB_TRUNC	= 1 << OPT_TRUNC,
	OB_FAST		= 1 << OPT_FAST,
	OB_WDF		= 1 << OPT_WDF,
	OB_ISO		= 1 << OPT_ISO,
	OB_WBFS		= 1 << OPT_WBFS,
	OB_LONG		= 1 << OPT_LONG,
	OB_ITIME	= 1 << OPT_ITIME,
	OB_MTIME	= 1 << OPT_MTIME,
	OB_CTIME	= 1 << OPT_CTIME,
	OB_ATIME	= 1 << OPT_ATIME,
	OB_TIME		= 1 << OPT_TIME,
	OB_UNIQUE	= 1 << OPT_UNIQUE,
	OB_NO_HEADER	= 1 << OPT_NO_HEADER,
	OB_SORT		= 1 << OPT_SORT,

	OB__MASK	= ( 1 << OPT__N_SPECIFIC ) -1,
	OB__MASK_PSEL	= OB_PSEL|OB_RAW,
	OB__MASK_SPLIT	= OB_SPLIT|OB_SPLIT_SIZE,
	OB__MASK_OFT	= OB_WDF|OB_ISO|OB_WBFS,
	OB__MASK_TIME	= OB_ITIME|OB_MTIME|OB_CTIME|OB_ATIME|OB_TIME,

	// allowed options for each command

	OB_CMD_HELP	= OB__MASK,
	OB_CMD_VERSION	= OB__MASK,
	OB_CMD_TEST	= OB__MASK,
	OB_CMD_ERROR	= OB_LONG|OB_NO_HEADER,
	OB_CMD_EXCLUDE	= 0,
	OB_CMD_TITLES	= 0,
	OB_CMD_FILELIST	= OB_LONG|OB_IGNORE,
	OB_CMD_FILETYPE	= OB_LONG|OB_IGNORE,
	OB_CMD_ISOSIZE	= OB_LONG|OB_IGNORE|OB_NO_HEADER,
	OB_CMD_DUMP	= OB_LONG,
	OB_CMD_ID6	= OB_SORT|OB_UNIQUE,
	OB_CMD_LIST	= OB_SORT|OB_LONG|OB__MASK_TIME|OB_UNIQUE|OB_NO_HEADER,
	OB_CMD_DIFF	= OB__MASK_PSEL|OB_DEST|OB_DEST2|OB__MASK_OFT|OB_IGNORE|OB_LONG,
	OB_CMD_COPY	= OB__MASK_PSEL|OB__MASK_SPLIT|OB__MASK_OFT|OB_DEST|OB_DEST2
			  |OB_PRESERVE|OB_UPDATE|OB_IGNORE|OB_REMOVE|OB_OVERWRITE,
	OB_CMD_SCRUB	= OB__MASK_PSEL|OB__MASK_SPLIT|OB__MASK_OFT|OB_PRESERVE|OB_IGNORE,
	OB_CMD_MOVE	= OB_IGNORE|OB_DEST|OB_DEST2|OB_OVERWRITE|OB_IGNORE,
	OB_CMD_REMOVE	= OB_IGNORE|OB_UNIQUE,
	OB_CMD_RENAME	= OB_IGNORE|OB_ISO|OB_WBFS,
	OB_CMD_SETTITLE	= OB_CMD_RENAME,

} enumOptionsBit;

///////////////////////////////////////////////////////////////////////////////

typedef enum enumCommands
{
	CMD_HELP,
	CMD_VERSION,
	CMD_TEST,
	CMD_ERROR,
	CMD_EXCLUDE,
	CMD_TITLES,

	CMD_FILELIST,
	CMD_FILETYPE,
	CMD_ISOSIZE,

	CMD_DUMP,
	CMD_ID6,
	CMD_LIST,
	CMD_LIST_L,
	CMD_LIST_LL,
	CMD_LIST_LLL,

	CMD_DIFF,
	CMD_COPY,
	CMD_SCRUB,
	CMD_MOVE,
	CMD_REMOVE,
	CMD_RENAME,
	CMD_SETTITLE,

	CMD__N

} enumCommands;

///////////////////////////////////////////////////////////////////////////////

enumIOMode io_mode = 0;

///////////////////////////////////////////////////////////////////////////////

enum // const for long options without a short brothers
{
	GETOPT_BASE	= 0x1000,
	GETOPT_UTF8,
	GETOPT_NO_UTF8,
	GETOPT_LANG,
	GETOPT_PSEL,
	GETOPT_RAW,
	GETOPT_ITIME,
	GETOPT_MTIME,
	GETOPT_CTIME,
	GETOPT_ATIME,
	GETOPT_TIME,
	GETOPT_IO,
};

char short_opt[] = "hVqvPtE:n:N:x:X:T:s:r:d:D:zZ:puoiRCFWIBlUHS:";
struct option long_opt[] =
{
	{ "help",		0, 0, 'h' },
	{ "version",		0, 0, 'V' },
	{ "quiet",		0, 0, 'q' },
	{ "verbose",		0, 0, 'v' },
	{ "progress",		0, 0, 'P' },
	{ "test",		0, 0, 't' },
	{ "esc",		1, 0, 'E' },
	{ "include",		1, 0, 'n' },
	{ "include-path",	1, 0, 'N' },
	 { "includepath",	1, 0, 'N' },
	{ "exclude",		1, 0, 'x' },
	{ "exclude-path",	1, 0, 'X' },
	 { "excludepath",	1, 0, 'X' },
	{ "titles",		1, 0, 'T' },
	{ "utf-8",		0, 0, GETOPT_UTF8 },
	 { "utf8",		0, 0, GETOPT_UTF8 },
	{ "no-utf-8",		0, 0, GETOPT_NO_UTF8 },
	 { "no-utf8",		0, 0, GETOPT_NO_UTF8 },
	 { "noutf8",		0, 0, GETOPT_NO_UTF8 },
	{ "lang",		1, 0, GETOPT_LANG },

	{ "io",			1, 0, GETOPT_IO }, // [2do] hidden option for tests

	{ "source",		1, 0, 's' },
	{ "recurse",		1, 0, 'r' },
	{ "psel",		1, 0, GETOPT_PSEL },
	{ "raw",		0, 0, GETOPT_RAW },
	{ "dest",		1, 0, 'd' },
	{ "DEST",		1, 0, 'D' },
	{ "split",		0, 0, 'z' },
	{ "split-size",		1, 0, 'Z' },
	 { "splitsize",		1, 0, 'Z' },
	{ "preserve",		0, 0, 'p' },
	{ "force",		0, 0, 'f' },
	{ "update",		0, 0, 'u' },
	{ "overwrite",		0, 0, 'o' },
	{ "ignore",		0, 0, 'i' },
	{ "remove",		0, 0, 'R' },
	{ "trunc",		0, 0, 'C' },
	{ "wdf",		0, 0, 'W' },
	{ "iso",		0, 0, 'I' },
	{ "wbfs",		0, 0, 'B' },
	{ "long",		0, 0, 'l' },
	{ "itime",		0, 0, GETOPT_ITIME },
	{ "mtime",		0, 0, GETOPT_MTIME },
	{ "ctime",		0, 0, GETOPT_CTIME },
	{ "atime",		0, 0, GETOPT_ATIME },
	{ "time",		1, 0, GETOPT_TIME },
	{ "unique",		0, 0, 'U' },
	{ "no-header",		0, 0, 'H' },
	 { "noheader",		0, 0, 'H' },
	{ "sort",		1, 0, 'S' },

	{0,0,0,0}
};

option_t used_options	= 0;
option_t env_options	= 0;
int  long_count		= 0;
int  ignore_count	= 0;
int  testmode		= 0;
ccp  opt_dest		= 0;
bool opt_mkdir		= false;
int  opt_split		= 0;
u64  opt_split_size	= 0;

///////////////////////////////////////////////////////////////////////////////

CommandTab_t CommandTab[] =
{
	{ CMD_HELP,	"HELP",		"?",		OB_CMD_HELP },
	{ CMD_VERSION,	"VERSION",	0,		OB_CMD_VERSION },
	{ CMD_TEST,	"TEST",		0,		OB_CMD_TEST },
	{ CMD_ERROR,	"ERROR",	"ERR",		OB_CMD_ERROR },
	{ CMD_EXCLUDE,	"EXCLUDE",	0,		OB_CMD_EXCLUDE },
	{ CMD_TITLES,	"TITLES",	0,		OB_CMD_TITLES },

	{ CMD_FILELIST,	"FILELIST",	"FL",		OB_CMD_FILELIST },
	{ CMD_FILETYPE,	"FILETYPE",	"FT",		OB_CMD_FILETYPE },
	{ CMD_ISOSIZE,	"ISOSIZE",	"SIZE",		OB_CMD_ISOSIZE },

	{ CMD_DUMP,	"DUMP",		"D",		OB_CMD_DUMP },
	{ CMD_ID6,	"ID6",		"ID",		OB_CMD_ID6 },
	{ CMD_LIST,	"LIST",		"LS",		OB_CMD_LIST },
	{ CMD_LIST_L,	"LIST-L",	"LL",		OB_CMD_LIST },
	{ CMD_LIST_LL,	"LIST-LL",	"LLL",		OB_CMD_LIST },
	{ CMD_LIST_LLL,	"LIST-LLL",	"LLLL",		OB_CMD_LIST },

	{ CMD_DIFF,	"DIFF",		"CMP",		OB_CMD_DIFF },
	{ CMD_COPY,	"COPY",		"CP",		OB_CMD_COPY },
	{ CMD_SCRUB,	"SCRUB",	"SB",		OB_CMD_SCRUB },
	{ CMD_MOVE,	"MOVE",		"MV",		OB_CMD_MOVE },
	{ CMD_REMOVE,	"REMOVE",	"RM",		OB_CMD_REMOVE },
	{ CMD_RENAME,	"RENAME",	"REN",		OB_CMD_RENAME },
	{ CMD_SETTITLE,	"SETTITLE",	"ST",		OB_CMD_SETTITLE },

	{ CMD__N,0,0,0 }
};

//
///////////////////////////////////////////////////////////////////////////////

static char help_text[] =
    "\n"
    TITLE "\n"
    "This is a command line tool to manage WBFS partitions and Wii ISO Images.\n"
    "\n"
    "Syntax: " WIT_SHORT " [option]... command [option|parameter|@file]...\n"
    "\n"
    "Commands:\n"
    "\n"
    "   HELP     | ?    : Print this help and exit.\n"
    "   VERSION         : Print program name and version and exit.\n"
    "   ERROR    | ERR  : Translate exit code to message.\n"
    "   EXCLUDE         : Print the internal exclude database to stdout.\n"
    "   TITLES          : Print the internal title database to stdout.\n"
    "\n"
    "   FILELIST | FL   : List all aource files decared by --source and --recurse.\n"
    "   FILETYPE | FT   : Print a status line for each source file.\n"
    "   ISOSIZE  | SIZE : Print a status line with size infos for each source file.\n"
    "\n"
    "   DUMP     | D    : Dump the content of ISO files.\n"
    "   ID6      | ID   : Print ID6 of all found ISO files.\n"
    "   LIST     | LS   : List all found ISO files.\n"
    "   LIST-L   | LL   : Same as 'LIST --long'.\n"
    "   LIST-LL  | LLL  : Same as 'LIST --long --long'.\n"
    "   LIST-LLL | LLLL : Same as 'LIST --long --long  --long'.\n"
    "\n"
    "   DIFF     | CMP  : Compare ISO images (scrubbed or raw).\n"
    "   COPY     | CP   : Copy ISO images.\n"
    "   SCRUB    | SB   : Scrub ISO images.\n"
    "   MOVE     | MV   : Move/rename ISO files.\n"
 #ifdef TEST // [2do]
    " ? REMOVE   | RM   : Remove all ISO files with the specific ID6.\n"
 #endif
    "   RENAME   | REN  : Rename the ID6 of discs. Disc title can also be set.\n"
    "   SETTITLE | ST   : Set the disc title of discs.\n"
    "\n"
    "General options (for all commands except 'ERROR'):\n"
    "\n"
    "   -h --help          Print this help and exit.\n"
    "   -V --version       Print program name and version and exit.\n"
    "   -q --quiet         Be quiet   -> print only error messages and needed output.\n"
    " * -v --verbose       Be verbose -> print more infos. Multiple usage possible.\n"
    "   -P --progress      Print progress counter independent of verbose level.\n"
    " * -t --test          Run in test mode, modify nothing.\n"
    "   -E --esc char      Define an alternative escape character, default is '%'.\n"
    " * -n --include id    Include oly discs with given ID4 or ID6 from operation.\n"
    " * -n --include @file Read include list from file.\n"
    " * -N --include-path file_or_dir\n"
    "                      ISO file or base of directory tree -> scan their ID6.\n"
    " * -x --exclude id    Exclude discs with given ID4 or ID6 from operation.\n"
    " * -x --exclude @file Read exclude list from file.\n"
    " * -X --exclude-path file_or_dir\n"
    "                      ISO file or base of directory tree -> scan their ID6.\n"
    " * -T --titles file   Read file for disc titles. -T0 disables titles lookup.\n"
 #ifdef __CYGWIN__
    "      --utf-8         Enables UTF-8 support.\n"
    "      --no-utf-8      Disables UTF-8 support (cygwin default).\n"
 #else
    "      --utf-8         Enables UTF-8 support (default).\n"
    "      --no-utf-8      Disables UTF-8 support.\n"
 #endif
    "      --lang    lang  Define the language for titles.\n"
    " * -s --source  path  ISO file or directory with ISO files.\n"
    " * -r --recurse path  ISO file or base of a directory tree with ISO files.\n"
    "\n"
    "Command specific options:\n"
    "\n"
    "      --psel  p-type  Partition selector: (no-)game|update|channel all(=def) raw.\n"
    "      --raw           Short cut for --psel=raw.\n"
    "   -d --dest  path    Define a destination file/directory.\n"
    "   -D --DEST  path    Like --dest, but create directory path automatically.\n"
    "   -s --size  size    Floating point size. Factors: bckKmMgGtT, default=G.\n"
    "   -z --split         Enable output file splitting, default split size = 4 gb.\n"
    "   -Z --split-size sz Enable output file splitting and set split size.\n"
    "   -p --preserve      Preserve file times (atime+mtime).\n"
    "   -u --update        Copy only to non existing files, ignore other.\n"
    "   -o --overwrite     Overwrite existing files\n"
    "   -i --ignore        Ignore non existing files/discs without warning.\n"
    "   -R --remove        Remove source files/discs if operation is successful.\n"
    "   -W --wdf           Write a WDF image; clears options --iso and --wbfs. (default)\n"
    "   -I --iso           Write a plain ISO image; clears options --wdf and --wbfs.\n"
    "   -B --wbfs          Write an ISO as WBFS container; clears options --wdf and --iso.\n"
    " * -l --long          Print in long format. Multiple usage possible.\n"
    "      --itime         Abbreviation of --time=i. Use 'itime' (insertion time).\n"
    "      --mtime         Abbreviation of --time=m. Use 'mtime' (last modification time).\n"
    "      --ctime         Abbreviation of --time=c. Use 'ctime' (last status change time).\n"
    "      --atime         Abbreviation of --time=a. Use 'atime' (last access time).\n"
    " *    --time  list    Set time modes (off,i,m,c,a,date,time,min,sec,...).\n"
    "   -U --unique        Eliminate multiple entries with same ID6.\n"
    "   -H --no-header     Suppress printing of header and footer.\n"
    "   -S --sort  list    Sort by: id|title|name|date|file|region|size|...|asc|desc\n"
 #ifdef TEST // [test]
    "\n"
    "      --io flags      IO mode (0=open or 1=fopen) &1=WBFS &2=IMAGE.\n"
 #endif
    "\n"
    "   Options marked with '*' can be used repeatedly to change the behavior.\n"
    "\n"
    "Usage:\n"
    "\n"
    "   HELP     | ?       [ignored]...\n"
    "   VERSION         -l [ignored]...\n"
    "   ERROR    | ERR  -l [error_code] // NO OTHER OPTIONS\n"
    "   TITLES             [additional_title_file]...\n"
    "\n"
    "   FILELIST | FL   -l   -ii                [source]...\n"
    "   FILETYPE | FT   -lll -ii        --psel= [source]...\n"
    "   ISOSIZE  | SIZE -lll -ii -H     --psel= [source]...\n"
    "   DUMP     | D    -l                      [source]...\n"
    "   ID6      | ID            -U -S=sort     [source]...\n"
    "   LIST     | LS   -lll -u  -H -S= --time  [source]...\n"
    "   LIST-*   | L*   -ll  -u  -H -S= --time  [source]...\n"
    "\n"
    "   DIFF     | CMP  -tt      -i     --psel= [source]... [-d=]dest\n"
    "   COPY     | CP   -tt  -zZ -ipRuo --psel= [source]... [-d=]dest\n"
    "   SCRUB    | SB   -tt  -zZ -ip    --psel= [source]...\n"
    "   MOVE     | MV   -tt      -i     --psel= [source]... [-d=]dest\n"
 #ifdef TEST // [2do]
    "   REMOVE   | RM   ...             id6...\n"
 #endif
    "   RENAME   | REN  -i -IB          id6=[new][,title]...\n"
    "   SETTITLE | ST   -i -IB          id6=title...\n"
    "\n";

///////////////////////////////////////////////////////////////////////////////

void help_exit()
{
    fputs(help_text,stdout);
    exit(ERR_OK);
}

///////////////////////////////////////////////////////////////////////////////

void version_exit()
{
    if (long_count)
	fputs(	"prog=" WIT_SHORT "\n"
		"name=\"" WIT_LONG "\"\n"
		"version=" VERSION "\n"
		"revision=" REVISION  "\n"
		"system=" SYSTEM "\n"
		"author=\"" AUTHOR "\"\n"
		"date=" DATE "\n"
		, stdout );
    else
	fputs( TITLE "\n", stdout );
    exit(ERR_OK);
}

///////////////////////////////////////////////////////////////////////////////

void print_title ( FILE * f )
{
    static bool done = false;
    if (!done)
    {
	done = true;
	if ( verbose >= 1 && f == stdout )
	    fprintf(f,"\n%s\n\n",TITLE);
	else
	    fprintf(f,"*****  %s  *****\n",TITLE);
    }
}

///////////////////////////////////////////////////////////////////////////////

void hint_exit ( enumError err )
{
    fprintf(stderr,
	    "-> Type '%s -h' (or better '%s -h|less') for more help.\n\n",
	    progname, progname );
    exit(err);
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////                     commands                    ///////////////
///////////////////////////////////////////////////////////////////////////////

// common commands of 'wwt' and 'wit'
#define IS_WIT 1
#include "wwt+wit-cmd.c"

///////////////////////////////////////////////////////////////////////////////

enumError cmd_test()
{
 #if 1 || !defined(TEST) // test options

    return cmd_test_options();

 #else

    int i, max = 5;
    for ( i=1; i <= max; i++ )
    {
	fprintf(stderr,"sleep 20 sec (%d/%d)\n",i,max);
	sleep(20);
    }
    return ERR_OK;

 #endif
}

//
///////////////////////////////////////////////////////////////////////////////

enumError exec_filelist ( SuperFile_t * sf, Iterator_t * it )
{
    ASSERT(sf);
    ASSERT(it);

    printf("%s\n", it->long_count ? it->real_path : sf->f.fname );
    return ERR_OK;
}

//-----------------------------------------------------------------------------

enumError cmd_filelist()
{
    ParamList_t * param;
    for ( param = first_param; param; param = param->next )
	AppendStringField(&source_list,param->arg,true);

    Iterator_t it;
    InitializeIterator(&it);
    it.func		= exec_filelist;
    it.act_non_exist	= ignore_count > 0 ? ACT_IGNORE : ACT_ALLOW;
    it.act_non_iso	= ignore_count > 1 ? ACT_IGNORE : ACT_ALLOW;
    it.long_count	= long_count;
    const enumError err = SourceIterator(&it,true,false);
    ResetIterator(&it);
    return err;
}

//
///////////////////////////////////////////////////////////////////////////////

enumError exec_filetype ( SuperFile_t * sf, Iterator_t * it )
{
    ASSERT(sf);
    ASSERT(it);

    const bool print_header = !(used_options&OB_NO_HEADER);
    ccp ftype = GetNameFT(sf->f.ftype,0);

    if ( it->long_count > 1 )
    {
	if ( print_header && !it->done_count++  )
	    printf("\n"
		"file     disc   size reg split\n"
		"type     ID6     MIB ion   N  %s\n"
		"%s\n",
		it->long_count > 2 ? "real path" : "filename", sep_79 );

	char split[10] = " -";
	if ( sf->f.split_used > 1 )
	    snprintf(split,sizeof(split),"%2d",sf->f.split_used);

	ccp region = "-   ";
	char size[10] = "   -";
	if (sf->f.id6[0])
	{
	    region = *GetRegionInfo(sf->f.id6[3]);
	    u32 count = CountUsedIsoBlocksSF(sf,partition_selector);
	    if (count)
		snprintf(size,sizeof(size),"%4u",
			(count+WII_SECTORS_PER_MIB/2)/WII_SECTORS_PER_MIB);
	}

	printf("%-8s %-6s %s %s %s  %s\n",
		ftype, sf->f.id6[0] ? sf->f.id6 : "-",
		size, region, split,
		it->long_count > 2 ? it->real_path : sf->f.fname );
    }
    else if (it->long_count)
    {
	if ( print_header && !it->done_count++  )
	    printf("\n"
		"file     disc  split\n"
		"type     ID6     N  filename\n"
		"%s\n", sep_79 );

	char split[10] = " -";
	if ( sf->f.split_used > 1 )
	    snprintf(split,sizeof(split),"%2d",sf->f.split_used);
	printf("%-8s %-6s %s  %s\n",
		ftype, sf->f.id6[0] ? sf->f.id6 : "-", split, sf->f.fname );
    }
    else
    {
	if ( print_header && !it->done_count++  )
	    printf("\n"
		"file\n"
		"type     filename\n"
		"%s\n", sep_79 );

	printf("%-8s %s\n", ftype, sf->f.fname );
    }

    return ERR_OK;
}

//-----------------------------------------------------------------------------

enumError cmd_filetype()
{
    ParamList_t * param;
    for ( param = first_param; param; param = param->next )
	AppendStringField(&source_list,param->arg,true);

    Iterator_t it;
    InitializeIterator(&it);
    it.func		= exec_filetype;
    it.act_non_exist	= ignore_count > 0 ? ACT_IGNORE : ACT_ALLOW;
    it.act_non_iso	= ignore_count > 1 ? ACT_IGNORE : ACT_ALLOW;
    it.long_count	= long_count;
    const enumError err = SourceIterator(&it,true,false);

    if ( !(used_options&OB_NO_HEADER) && it.done_count )
	putchar('\n');

    ResetIterator(&it);
    return err;
}

//
///////////////////////////////////////////////////////////////////////////////

enumError exec_isosize ( SuperFile_t * sf, Iterator_t * it )
{
    ASSERT(sf);
    ASSERT(it);

    const bool print_header = !(used_options&OB_NO_HEADER);

    if ( it->long_count > 1 )
    {
	if ( print_header && !it->done_count++  )
	    printf("\n"
		"   ISO  ISO .wbfs 500g\n"
		"blocks  MiB  file WBFS  %s\n"
		"%s\n",
		it->long_count > 2 ? "real path" : "filename", sep_79 );

	char size[30] = "     -    -     -    -";
	if (sf->f.id6[0])
	{
	    u32 count = CountUsedIsoBlocksSF(sf,partition_selector);
	    if (count)
	    {
		// wbfs: size=10g => block size = 2 MiB
		u32 wfile = 1 + CountUsedBlocks( wdisc_usage_tab,
						2 * WII_SECTORS_PER_MIB );
		// wbfs: size=500g => block size = 8 MiB
		u32 w500 =  CountUsedBlocks( wdisc_usage_tab,
						8 * WII_SECTORS_PER_MIB );

		snprintf(size,sizeof(size),"%6u %4u %5u %4u",
			count, (count+WII_SECTORS_PER_MIB/2)/WII_SECTORS_PER_MIB,
			2*wfile, 8*w500 );
	    }
	}
	printf("%s  %s\n", size, it->long_count > 2 ? it->real_path : sf->f.fname );
    }
    else if ( it->long_count )
    {
	if ( print_header && !it->done_count++  )
	    printf("\n"
		"   ISO  ISO\n"
		"blocks  MiB  filename\n"
		"%s\n", sep_79 );

	char size[20] = "     -    -";
	if (sf->f.id6[0])
	{
	    u32 count = CountUsedIsoBlocksSF(sf,partition_selector);
	    if (count)
		snprintf(size,sizeof(size),"%6u %4u",
			count, (count+WII_SECTORS_PER_MIB/2)/WII_SECTORS_PER_MIB);
	}
	printf("%s  %s\n", size, sf->f.fname );
    }
    else
    {
	if ( print_header && !it->done_count++  )
	    printf("\n"
		"   ISO\n"
		"blocks  filename\n"
		"%s\n", sep_79 );

	char size[20] = "     -";
	if (sf->f.id6[0])
	{
	    u32 count = CountUsedIsoBlocksSF(sf,partition_selector);
	    if (count)
		snprintf(size,sizeof(size),"%6u",count);
	}
	printf("%s  %s\n", size, sf->f.fname );
    }

    return ERR_OK;
}

//-----------------------------------------------------------------------------

enumError cmd_isosize()
{
    ParamList_t * param;
    for ( param = first_param; param; param = param->next )
	AppendStringField(&source_list,param->arg,true);

    Iterator_t it;
    InitializeIterator(&it);
    it.func		= exec_isosize;
    it.act_non_exist	= ignore_count > 0 ? ACT_IGNORE : ACT_ALLOW;
    it.act_non_iso	= ignore_count > 1 ? ACT_IGNORE : ACT_ALLOW;
    it.act_wbfs		= ACT_EXPAND;
    it.long_count	= long_count;
    const enumError err = SourceIterator(&it,true,false);

    if ( !(used_options&OB_NO_HEADER) && it.done_count )
	putchar('\n');

    ResetIterator(&it);
    return err;
}

//
///////////////////////////////////////////////////////////////////////////////

static void dump_data ( off_t base, u32 off4, off_t size, ccp text )
{
    const off_t off = (off_t)off4 << 2;
    const off_t end = off + size;
    printf("    %-5s %9llx .. %9llx -> %9llx .. %9llx, size:%10llx/hex =%11llu\n",
		text, off, end, base+off, base+end, size, size );
}

//-----------------------------------------------------------------------------

enumError exec_dump ( SuperFile_t * sf, Iterator_t * it )
{
    char buf1[100];

    ASSERT(sf);
    ASSERT(it);
    if (!sf->f.id6[0])
	return ERR_OK;
    sf->f.read_behind_eof = 2;

    WDiscInfo_t wdi;
    InitializeWDiscInfo(&wdi);

    MemMap_t mm;
    MemMapItem_t * mi;
    InitializeMemMap(&mm);

    printf("\nDump of file %s\n\n",sf->f.fname);
    if (strcmp(sf->f.fname,it->real_path))
	printf("  Real path:      %s\n",it->real_path);
    printf("  ID & type:      %s, %s\n", sf->f.id6, GetNameFT(sf->f.ftype,0) );

    printf("  ISO file size:%11llx/hex =%11llu =%5llu MiB\n",
		sf->file_size, sf->file_size,
		(sf->file_size+MiB/2)/MiB );
    if (sf->wc)
    {
	printf("  WDF file size:%11llx/hex =%11llu =%5llu MiB, %lld%%\n",
		sf->f.st.st_size, sf->f.st.st_size,
		(sf->f.st.st_size+MiB/2)/MiB,
		sf->f.st.st_size * 100 / sf->wh.file_size );
    }

    enumError err = ReadSF(sf,0,&wdi.dhead,sizeof(wdi.dhead));
    if (err)
	goto abort;
    CalcWDiscInfo(&wdi);

    err = LoadPartitionInfo(sf, &wdi, it->long_count>1 ? &mm : 0 );
    if (err)
	goto dump_mm;

    printf("  Disc name:      %s\n",wdi.dhead.game_title);
    if (wdi.title)
	printf("  DB title:       %s\n",wdi.title);
    printf("  Region:         %s [%s]\n",wdi.region,wdi.region4);
    u8 * p8 = wdi.regionset.region_byte;
    printf("  Region setting: %d / %02x %02x %02x %02x  %02x %02x %02x %02x\n",
		wdi.regionset.region,
		p8[0], p8[1], p8[2], p8[3], p8[4], p8[5], p8[6], p8[7] );

    //--------------------------------------------------

    u32 nt = wdi.n_ptab;
    u32 np = wdi.n_part;

    printf("\n  %d partition table%s with %d partition%s:\n\n"
	    "     tab.idx   n(part)       offset(part.tab) .. end(p.tab)\n"
	    "    --------------------------------------------------------\n",
		nt, nt == 1 ? "" : "s",
		np, np == 1 ? "" : "s" );

    int i;
    WDPartCount_t *pc = wdi.pcount;
    for ( i = 0; i < WII_MAX_PART_INFO; i++, pc++ )
	if (pc->n_part)
	{
	    off_t off = (off_t)pc->off4<<2;
	    printf("%9d %8d %11x*4 = %10llx .. %10llx\n",
		i, pc->n_part, pc->off4, off,
		off + pc->n_part * sizeof(WDPartTableEntry_t) );
	}

    //--------------------------------------------------

    static ccp pname[] = { "GAME", "UPDATE", "CHANNEL" };

    printf("\n  %d partition%s:\n\n"
	"     index      type      offset .. end offset   size/hex =   size/dec =  MiB\n"
	"    --------------------------------------------------------------------------\n",
	np, np == 1 ? "" : "s" );

    WDPartInfo_t *pi;
    for ( i = 0, pi = wdi.pinfo; i < np; i++, pi++ )
    {
	if ( pi->ptype < sizeof(pname)/sizeof(*pname) )
	    snprintf(buf1,sizeof(buf1),"%7s %d",pname[pi->ptype],pi->ptype);
	else
	{
	    char id4[5];
	    id4[0] = pi->ptype >> 24;
	    id4[1] = pi->ptype >> 16;
	    id4[2] = pi->ptype >>  8;
	    id4[3] = pi->ptype;
	    if ( CheckID(id4) == 4 )
		snprintf(buf1,sizeof(buf1),"   \"%s\"",id4);
	    else
		snprintf(buf1,sizeof(buf1),"%9x",pi->ptype);
	}

	if ( pi->size )
	    printf("%7d.%-2d %s %11llx ..%11llx %10llx =%11llu =%5llu\n",
		pi->ptable, pi->index, buf1, pi->off,
		pi->off + pi->size, pi->size, pi->size,
		(pi->size+MiB/2)/MiB );
	else
	    printf("%7d.%-2d %s %11llx         ** INVALID PARTITION **\n",
		pi->ptable, pi->index, buf1, pi->off );
    }

    //--------------------------------------------------

    if (it->long_count)
      for ( i = 0, pi = wdi.pinfo; i < np; i++, pi++ )
	if ( pi->size )
	{
	    printf("\n  Partition table #%d, partition #%d, type %x [%s]:\n",
		    pi->ptable, pi->index, pi->ptype,
		    pi->ptype < sizeof(pname)/sizeof(*pname) ? pname[pi->ptype] : "?" );

	    p8 = pi->part_key;
	    printf("    Partition key: %02x%02x%02x%02x %02x%02x%02x%02x"
				     " %02x%02x%02x%02x %02x%02x%02x%02x\n",
		p8[0], p8[1], p8[2], p8[3], p8[4], p8[5], p8[6], p8[7],
		p8[8], p8[9], p8[10], p8[11], p8[12], p8[13], p8[14], p8[15] );

	    dump_data( pi->off, pi->ph.tmd_off4,  pi->ph.tmd_size,		"TMD:" );
	    dump_data( pi->off, pi->ph.cert_off4, pi->ph.cert_size,		"Cert:" );
	    dump_data( pi->off, pi->ph.h3_off4,   WII_H3_SIZE,		"H3:" );
	    dump_data( pi->off, pi->ph.data_off4, (off_t)pi->ph.data_size<<2, "Data:" );
	}

    //--------------------------------------------------


 dump_mm:

    if ( it->long_count > 1 )
    {
	mi = InsertMemMap(&mm,0,0x100);
	StringCopyS(mi->info,sizeof(mi->info),"Disc header");

	printf("\n\n  ISO Memory Map:\n\n");
	PrintMemMap(&mm,stdout,3);
    }

 abort:

    putchar('\n');
    ResetWDiscInfo(&wdi);
    ResetMemMap(&mm);
    return err;
}

//-----------------------------------------------------------------------------

enumError cmd_dump()
{
    ParamList_t * param;
    for ( param = first_param; param; param = param->next )
	AppendStringField(&source_list,param->arg,true);

    Iterator_t it;
    InitializeIterator(&it);
    it.func		= exec_dump;
    it.act_wbfs		= ACT_EXPAND;
    it.long_count	= long_count;
    const enumError err = SourceIterator(&it,false,false);
    ResetIterator(&it);
    return err;
}

//
///////////////////////////////////////////////////////////////////////////////

enumError exec_collect ( SuperFile_t * sf, Iterator_t * it )
{
    ASSERT(sf);
    ASSERT(it);
    ASSERT(it->wlist);

    WDiscInfo_t wdi;
    InitializeWDiscInfo(&wdi);
    enumError err = ReadSF(sf,0,&wdi.dhead,sizeof(wdi.dhead));
    if (err)
	return err;
    CalcWDiscInfo(&wdi);

    err = CountPartitions(sf,&wdi);
    if (err)
	return err;

    WDiscList_t * wl = it->wlist;
    WDiscListItem_t * item = AppendWDiscList(wl,&wdi);
    if ( it->long_count > 2 )
	item->fname = strdup(it->real_path);
    else
    {
	item->fname = sf->f.fname;
	sf->f.fname = EmptyString;
    }
    TRACE("WLIST: %d/%d\n",wl->used,wl->size);

    item->size_mib = (sf->f.st.st_size+MiB/2)/MiB;
    wl->total_size_mib += item->size_mib;

    item->part_index = sf->f.ftype;
    item->xtime = SelectTimeOfStat(&sf->f.st,opt_print_time);

    ResetWDiscInfo(&wdi);
    return ERR_OK;
}

//-----------------------------------------------------------------------------

enumError cmd_id6()
{
    ParamList_t * param;
    for ( param = first_param; param; param = param->next )
	AppendStringField(&source_list,param->arg,true);

    WDiscList_t wlist;
    InitializeWDiscList(&wlist);

    Iterator_t it;
    InitializeIterator(&it);
    it.func		= exec_collect;
    it.act_wbfs		= ACT_EXPAND;
    it.long_count	= long_count;
    it.wlist		= &wlist;

    enumError err = SourceIterator(&it,true,false);
    ResetIterator(&it);
    if (err)
	return err;

    SortWDiscList(&wlist,sort_mode,SORT_ID, used_options&OB_UNIQUE ? 2 : 0 );

    WDiscListItem_t * ptr = wlist.first_disc;
    WDiscListItem_t * end = ptr + wlist.used;
    for ( ; ptr < end; ptr++ )
	printf("%s\n", ptr->id6 );

    ResetWDiscList(&wlist);
    return ERR_OK;
}

//
///////////////////////////////////////////////////////////////////////////////

enumError cmd_list()
{
    ParamList_t * param;
    for ( param = first_param; param; param = param->next )
	AppendStringField(&source_list,param->arg,true);

    WDiscList_t wlist;
    InitializeWDiscList(&wlist);

    Iterator_t it;
    InitializeIterator(&it);
    it.func		= exec_collect;
    it.act_wbfs		= ACT_EXPAND;
    it.long_count	= long_count;
    it.wlist		= &wlist;

    enumError err = SourceIterator(&it,true,false);
    ResetIterator(&it);
    if (err)
	return err;

    SortWDiscList(&wlist,sort_mode,SORT_TITLE, used_options&OB_UNIQUE ? 1 : 0 );

    //------------------------------

    char footer[200];
    int footer_len = 0;

    WDiscListItem_t *witem, *wend = wlist.first_disc + wlist.used;

    const bool print_header = !(used_options&OB_NO_HEADER);
    const bool line2 = long_count > 2;

    PrintTime_t pt;
    int opt_time = opt_print_time;
    if ( long_count > 1 )
	opt_time = EnablePrintTime(opt_time);
 printf("%x->%x\n",opt_print_time,opt_time);
    SetupPrintTime(&pt,opt_time);

    int max_name_wd = 0;
    if (print_header)
    {
	for ( witem = wlist.first_disc; witem < wend; witem++ )
	{
	    const int plen = strlen( witem->title
					? witem->title : witem->name64 );
	    if ( max_name_wd < plen )
		max_name_wd = plen;

	    if ( line2 && witem->fname )
	    {
		const int flen = strlen(witem->fname);
		if ( max_name_wd < flen )
		    max_name_wd = flen;
	    }
	}

	footer_len = snprintf(footer,sizeof(footer),
		"Total: %u discs, %u MiB ~ %u GiB used.",
		wlist.used,
		wlist.total_size_mib, (wlist.total_size_mib+512)/1024 );
    }

    if (long_count)
    {
	if (print_header)
	{
	    int n1, n2;
	    putchar('\n');
	    printf("ID6   %s  MiB Reg.  %n%d discs (%d GiB)%n\n",
		    pt.head, &n1, wlist.used,
		    (wlist.total_size_mib+512)/1024, &n2 );
	    max_name_wd += n1;
	    if ( max_name_wd < n2 )
		max_name_wd = n2;

	    if (line2)
	    {
		fputs(pt.fill,stdout);
		fputs("      n(p) type   path of file\n",stdout);
	    }

	    if ( max_name_wd < footer_len )
		max_name_wd = footer_len;
	    printf("%.*s\n", max_name_wd, LongSep);
	}

	for ( witem = wlist.first_disc; witem < wend; witem++ )
	{
	    printf("%s%s %4d %s  %s\n",
		    witem->id6, PrintTime(&pt,witem->xtime),
		    witem->size_mib, witem->region4,
		    witem->title ? witem->title : witem->name64 );
	    if (line2)
		printf("%s%9d %7s %s\n",
		    pt.fill, witem->n_part, GetNameFT(witem->part_index,0),
		    witem->fname ? witem->fname : "" );
	}
    }
    else
    {
	if (print_header)
	{
	    int n1, n2;
	    putchar('\n');
	    printf("ID6    %s %n%d discs (%d GiB)%n\n",
		    pt.head, &n1, wlist.used, (wlist.total_size_mib+512)/1024, &n2 );
	    max_name_wd += n1;
	    if ( max_name_wd < n2 )
		max_name_wd = n2;
	    printf("%.*s\n", max_name_wd, LongSep );
	}

	for ( witem = wlist.first_disc; witem < wend; witem++ )
	    printf("%s%s  %s\n", witem->id6, PrintTime(&pt,witem->xtime),
			witem->title ? witem->title : witem->name64 );
    }

    if (print_header)
	printf("%.*s\n%s\n\n", max_name_wd, LongSep, footer );

    ResetWDiscList(&wlist);
    return ERR_OK;
}

//-----------------------------------------------------------------------------

enumError cmd_list_l()
{
    used_options |= OB_LONG;
    long_count++;
    return cmd_list();
}

//-----------------------------------------------------------------------------

enumError cmd_list_ll()
{
    used_options |= OB_LONG;
    long_count += 2;
    return cmd_list();
}

//-----------------------------------------------------------------------------

enumError cmd_list_lll()
{
    used_options |= OB_LONG;
    long_count += 3;
    return cmd_list();
}

//
///////////////////////////////////////////////////////////////////////////////

enumError exec_diff ( SuperFile_t * f1, Iterator_t * it )
{
    if (!f1->f.id6[0])
	return ERR_OK;

    SuperFile_t f2;
    InitializeSF(&f2);
    f2.f.create_directory = opt_mkdir;

    enumOFT oft = CalcOFT(output_file_type,opt_dest,f1->f.fname,OFT__DEFAULT);
    ccp oname = oft == OFT_WBFS && f1->f.id6[0]
		    ? f1->f.id6
		    : f1->f.outname
			    ? f1->f.outname
			    : f1->f.fname;
    GenImageFileName(&f2.f,opt_dest,oname,oft);
    SubstFileNameSF(&f2,f1,0);

    //f2.f.disable_errors = it->act_non_exist != ACT_WARN;
    enumError err = OpenSF(&f2,0,it->act_non_iso||it->act_wbfs>=ACT_ALLOW,0);
    if (err)
    {
	it->diff_count++;
	return ERR_OK;
    }
    f2.f.disable_errors = false;

    f2.indent		= 5;
    f2.show_progress	= verbose > 1 || progress;
    f2.show_summary	= verbose > 0 || progress;
    f2.show_msec	= verbose > 2;

    const bool raw_mode = partition_selector == WHOLE_DISC || !f1->f.id6[0];
    if (testmode)
    {
	printf( "%s: WOULD DIFF/%s %s:%s : %s:%s\n",
		progname, raw_mode ? "RAW" : "SCRUB",
		oft_name[f1->oft], f1->f.fname, oft_name[f2.oft], f2.f.fname );
	ResetSF(&f2,0);
	return ERR_OK;
    }

    if ( verbose > 0 )
    {
	printf( "* DIFF/%s %s:%s -> %s:%s\n",
		raw_mode ? "RAW" : "SCRUB",
		oft_name[f1->oft], f1->f.fname, oft_name[f2.oft], f2.f.fname );
    }

    err =  DiffSF( f1, &f2, it->long_count, raw_mode ? WHOLE_DISC : partition_selector );
    if ( err == ERR_DIFFER )
    {
	it->diff_count++;
	err = ERR_OK;
	if ( verbose >= 0 )
	    printf( "! ISOs differ: %s:%s : %s:%s\n",
			oft_name[f1->oft], f1->f.fname, oft_name[f2.oft], f2.f.fname );
    }
    it->done_count++;

    ResetSF(&f2,0);
    return err;
}

//-----------------------------------------------------------------------------

enumError cmd_diff()
{
    if ( verbose > 0 )
	print_title(stdout);

    if (!opt_dest)
    {
	if (!first_param)
	    return ERROR0(ERR_MISSING_PARAM, "Missing destination parameter\n" );

	ParamList_t * param;
	for ( param = first_param; param->next; param = param->next )
	    ;
	ASSERT(param);
	ASSERT(!param->next);
	opt_dest = param->arg;
	param->arg = 0;
    }

    ParamList_t * param;
    for ( param = first_param; param; param = param->next )
	AppendStringField(&source_list,param->arg,true);

    Iterator_t it;
    InitializeIterator(&it);
    it.act_non_iso	= used_options & OB_IGNORE ? ACT_IGNORE : ACT_WARN;
    it.act_non_exist	= it.act_non_iso;
    it.act_wbfs		= ACT_EXPAND;
    it.long_count	= long_count;

    if ( testmode > 1 )
    {
	it.func = exec_filetype;
	enumError err = SourceIterator(&it,false,false);
	ResetIterator(&it);
	printf("DESTINATION: %s\n",opt_dest);
	return err;
    }

    it.func = exec_diff;
    enumError err = SourceIterator(&it,false,false);
    if ( err == ERR_OK && it.diff_count )
	err = ERR_DIFFER;
    ResetIterator(&it);
    return err;
}

//
///////////////////////////////////////////////////////////////////////////////

enumError exec_copy ( SuperFile_t * fi, Iterator_t * it )
{
    if (!fi->f.id6[0])
	return ERR_OK;

    const bool scrub_it = it->scrub_it
		&& ( output_file_type == OFT_UNKNOWN || output_file_type == GetOFT(fi) );

    const enumOFT oft = scrub_it
			? GetOFT(fi)
			: CalcOFT(output_file_type,opt_dest,fi->f.fname,OFT__DEFAULT);

    SuperFile_t fo;
    InitializeSF(&fo);
    fo.oft = oft;

    if (scrub_it)
	fo.f.fname = strdup(fi->f.fname);
    else
    {
	TRACE("COPY, mkdir=%d\n",opt_mkdir);
	fo.f.create_directory = opt_mkdir;
	ccp oname = oft == OFT_WBFS && fi->f.id6[0]
			? fi->f.id6
			: fi->f.outname
				? fi->f.outname
				: fi->f.fname;
	GenImageFileName(&fo.f,opt_dest,oname,oft);
	SubstFileNameSF(&fo,fi,0);

	if ( it->update && !StatFile(&fo.f.st,fo.f.fname,-1) )
	    return ERR_OK;
    }

    fo.indent		= 5;
    fo.show_progress	= verbose > 1 || progress;
    fo.show_summary	= verbose > 0 || progress;
    fo.show_msec	= verbose > 2;

    char count_buf[100];
    snprintf(count_buf,sizeof(count_buf), "%u", it->source_list.used );
    snprintf(count_buf,sizeof(count_buf), "%*u/%u",
		(int)strlen(count_buf), it->source_index+1, it->source_list.used );

    const bool raw_mode = partition_selector == WHOLE_DISC || !fi->f.id6[0];
    if (testmode)
    {
	if (scrub_it)
	    printf( "%s: WOULD %s %s %s:%s\n",
		progname, raw_mode ? "COPY " : "SCRUB",
		count_buf, oft_name[oft], fi->f.fname );
	else
	    printf( "%s: WOULD %s %s %s:%s -> %s:%s\n",
		progname, raw_mode ? "COPY " : "SCRUB",
		count_buf, oft_name[fi->oft], fi->f.fname, oft_name[oft], fo.f.fname );
	ResetSF(&fo,0);
	return ERR_OK;
    }

    if ( verbose >= 0 )
    {
	if (scrub_it)
	    printf( "* %s %s %s %s %s\n",
		progname, raw_mode ? "COPY " : "SCRUB",
		count_buf, oft_name[oft], fi->f.fname );
	else
	    printf( "* %s %s %s %s:%s -> %s:%s\n",
		progname, raw_mode ? "COPY " : "SCRUB",
		count_buf, oft_name[fi->oft], fi->f.fname, oft_name[oft], fo.f.fname );
    }

    enumError err = CreateFile( &fo.f, 0, IOM_IS_IMAGE, it->overwrite );
    if ( err == ERR_ALREADY_EXISTS )
    {
	it->exists_count++;
	err = ERR_OK;
	goto abort;
    }

    if (err)
	goto abort;

    if (opt_split)
	SetupSplitFile(&fo.f,oft,opt_split_size);

    fo.file_size = fi->file_size;
    err = SetupWriteSF(&fo,oft);
    if (err)
	goto abort;

    err =  CopySF( fi, &fo, raw_mode ? WHOLE_DISC : partition_selector );
    if (err)
	goto abort;

    if (it->remove_source)
	RemoveSF(fi);

    err = ResetSF( &fo, used_options & OB_PRESERVE ? &fi->f.st : 0 );
    if (err)
	goto abort;

    return ERR_OK;

 abort:
    RemoveSF(&fo);
    return err;
}

//-----------------------------------------------------------------------------

enumError cmd_copy()
{
    if ( verbose >= 0 )
	print_title(stdout);

    if (!opt_dest)
    {
	if (!first_param)
	    return ERROR0(ERR_MISSING_PARAM, "Missing destination parameter\n" );

	ParamList_t * param;
	for ( param = first_param; param->next; param = param->next )
	    ;
	ASSERT(param);
	ASSERT(!param->next);
	opt_dest = param->arg;
	param->arg = 0;
    }

    ParamList_t * param;
    for ( param = first_param; param; param = param->next )
	AppendStringField(&source_list,param->arg,true);

    Iterator_t it;
    InitializeIterator(&it);
    it.act_non_iso	= used_options & OB_IGNORE ? ACT_IGNORE : ACT_WARN;
    it.act_wbfs		= ACT_EXPAND;
    it.overwrite	= used_options & OB_OVERWRITE ? 1 : 0;
    it.update		= used_options & OB_UPDATE ? 1 : 0;
    it.remove_source	= used_options & OB_REMOVE ? 1 : 0;

    if ( testmode > 1 )
    {
	it.func = exec_filetype;
	enumError err = SourceIterator(&it,false,false);
	ResetIterator(&it);
	printf("DESTINATION: %s\n",opt_dest);
	return err;
    }

    enumError err = SourceIterator(&it,false,true);
    if ( err == ERR_OK )
    {
	it.func = exec_copy;
	err = SourceIteratorCollected(&it);
	if ( err == ERR_OK && it.exists_count )
	    err = ERR_ALREADY_EXISTS;
    }
    ResetIterator(&it);
    return err;
}

//
///////////////////////////////////////////////////////////////////////////////

enumError cmd_scrub()
{
    if ( verbose >= 0 )
	print_title(stdout);

    ParamList_t * param;
    for ( param = first_param; param; param = param->next )
	AppendStringField(&source_list,param->arg,true);

    Iterator_t it;
    InitializeIterator(&it);
    it.act_non_iso	= used_options & OB_IGNORE ? ACT_IGNORE : ACT_WARN;
    it.act_wbfs		= it.act_non_iso;
    it.scrub_it		= true;
    it.overwrite	= true;
    it.remove_source	= true;

    if ( testmode > 1 )
    {
	it.func = exec_filetype;
	enumError err = SourceIterator(&it,false,false);
	ResetIterator(&it);
	printf("DESTINATION: %s\n",opt_dest);
	return err;
    }

    enumError err = SourceIterator(&it,false,true);
    if ( err == ERR_OK )
    {
	it.func = exec_copy;
	SourceIteratorCollected(&it);
	if ( err == ERR_OK && it.exists_count )
	    err = ERR_ALREADY_EXISTS;
    }
    ResetIterator(&it);
    return err;
}

//
///////////////////////////////////////////////////////////////////////////////

enumError exec_move ( SuperFile_t * fi, Iterator_t * it )
{
    SuperFile_t fo;
    InitializeSF(&fo);
    fo.oft = fi->oft;
    fo.f.create_directory = opt_mkdir;

    ccp oname = fi->oft == OFT_WBFS && fi->f.id6[0]
			? fi->f.id6
			: fi->f.outname
				? fi->f.outname
				: fi->f.fname;
    GenImageFileName(&fo.f,opt_dest,oname,fi->oft);
    SubstFileNameSF(&fo,fi,0);

    if ( strcmp(fi->f.fname,fo.f.fname) )
    {
	if ( !it->overwrite && !stat(fo.f.fname,&fo.f.st) )
	{
	    ERROR0(ERR_CANT_CREATE,"File already exists: %s\n",fo.f.fname);
	}
	else if (!CheckCreated(fo.f.fname,false))
	{
	    if ( testmode || verbose >= 0 )
	    {
		snprintf(iobuf,sizeof(iobuf), "%u", it->source_list.used );
		printf(" - %sMove %*u/%u %s:%s -> %s\n",
		    testmode ? "WOULD " : "",
		    (int)strlen(iobuf), it->source_index+1, it->source_list.used,
		    oft_name[fo.oft], fi->f.fname, fo.f.fname );
	    }

	    if ( !testmode && rename(fi->f.fname,fo.f.fname) )
		return ERROR1( ERR_CANT_CREATE, "Can't create file: %s\n", fo.f.fname );
	}
    }

    ResetSF(&fo,0);
    return ERR_OK;
}

//-----------------------------------------------------------------------------

enumError cmd_move()
{
    if ( verbose >= 0 )
	print_title(stdout);

    if (!opt_dest)
    {
	if (!first_param)
	    return ERROR0(ERR_MISSING_PARAM, "Missing destination parameter\n" );

	ParamList_t * param;
	for ( param = first_param; param->next; param = param->next )
	    ;
	ASSERT(param);
	ASSERT(!param->next);
	opt_dest = param->arg;
	param->arg = 0;
    }

    ParamList_t * param;
    for ( param = first_param; param; param = param->next )
	AppendStringField(&source_list,param->arg,true);

    Iterator_t it;
    InitializeIterator(&it);
    it.act_non_iso	= used_options & OB_IGNORE ? ACT_IGNORE : ACT_WARN;
    it.act_wbfs		= ACT_ALLOW;
    it.overwrite	= used_options & OB_OVERWRITE ? 1 : 0;

    if ( testmode > 1 )
    {
	it.func = exec_filetype;
	enumError err = SourceIterator(&it,false,false);
	ResetIterator(&it);
	printf("DESTINATION: %s\n",opt_dest);
	return err;
    }

    enumError err = SourceIterator(&it,false,true);
    if ( err == ERR_OK )
    {
	it.func = exec_move;
	err = SourceIteratorCollected(&it);
    }
    ResetIterator(&it);
    return err;
}

//
///////////////////////////////////////////////////////////////////////////////

enumError exec_remove ( SuperFile_t * fi, Iterator_t * it )
{
    ParamList_t * param;
    for ( param = first_param; param; param = param->next )
	if (!strcmp(param->selector,fi->f.id6))
	    break;

    if (!param)
	return ERR_OK;

    // [2do]
    printf("NOT IMPLEMENTED: REMOVE %s\n",fi->f.fname);
    return ERR_OK;
}

//-----------------------------------------------------------------------------

enumError cmd_remove()
{
    if ( verbose >= 0 )
	print_title(stdout);

    if ( !source_list.used && !recurse_list.used )
	return ERROR0( ERR_MISSING_PARAM, "Missing source files.\n");

    CheckParamID6( ( used_options & OB_UNIQUE ) != 0, false );
    if ( !id6_param_found )
	return ERROR0(ERR_MISSING_PARAM, "Missing ID6 parameters.\n" );

    Iterator_t it;
    InitializeIterator(&it);
    it.act_non_iso	= used_options & OB_IGNORE ? ACT_IGNORE : ACT_WARN;
    it.act_wbfs		= it.act_non_iso;
    it.long_count	= long_count;

    if ( testmode > 1 )
    {
	it.func = exec_filetype;
	enumError err = SourceIterator(&it,false,false);
	ResetIterator(&it);
	printf("DESTINATION: %s\n",opt_dest);
	return err;
    }

    it.func = exec_remove;
    const enumError err = SourceIterator(&it,false,false);
    ResetIterator(&it);
    return err;
}

//
///////////////////////////////////////////////////////////////////////////////

enumError exec_rename ( SuperFile_t * fi, Iterator_t * it )
{
    ParamList_t *param, *plus_param = 0;
    for ( param = first_param; param; param = param->next )
    {
	if ( !plus_param && param->selector[0] == '+' )
	    plus_param = param;
	else if ( !strcmp(param->selector,fi->f.id6) )
	    break;
    }

    if (!param)
    {
	if (!plus_param)
	    return ERR_OK;
	param = plus_param;
    }
    param->count++;

    bool change_wbfs	= 0 != ( used_options & OB_WBFS );
    bool change_iso	= 0 != ( used_options & OB_ISO );
    if ( !change_wbfs && !change_iso )
	change_wbfs = change_iso = true;

    if ( fi->oft == OFT_WBFS )
    {
	ASSERT(fi->wbfs);
	return RenameWDisc( fi->wbfs, param->id6, param->arg,
			    change_wbfs, change_iso, verbose, testmode );
    }

    const int bufsize = WII_TITLE_OFF + WII_TITLE_SIZE;
    char buf[bufsize];

    enumError err = ReadSF(fi,0,buf,sizeof(buf));
    if (err)
	return err;

    if (RenameISOHeader( buf, fi->f.fname,
			 param->id6, param->arg, verbose, testmode ))
    {
	err = WriteSF(fi,0,buf,sizeof(buf));
	if (err)
	    return err;
	if ( fi->oft == OFT_WDF )
	    err = TermWriteWDF(fi);
    }
    return err;
}

//-----------------------------------------------------------------------------

enumError cmd_rename ( bool rename_id )
{
    if ( verbose >= 0 )
	print_title(stdout);

    if ( !source_list.used && !recurse_list.used )
	return ERROR0( ERR_MISSING_PARAM, "Missing source files.\n");

    enumError err = CheckParamRename(rename_id,!rename_id,false);
    if (err)
	return err;
    if ( !n_param )
	return ERROR0(ERR_MISSING_PARAM, "Missing renaming parameters.\n" );

    Iterator_t it;
    InitializeIterator(&it);
    it.open_modify	= true;
    it.act_non_iso	= used_options & OB_IGNORE ? ACT_IGNORE : ACT_WARN;
    it.act_wbfs		= ACT_EXPAND;
    it.long_count	= long_count;

    if ( testmode > 1 )
    {
	it.func = exec_filetype;
	enumError err = SourceIterator(&it,false,false);
	ResetIterator(&it);
	printf("DESTINATION: %s\n",opt_dest);
	return err;
    }

    it.func = exec_rename;
    err = SourceIterator(&it,false,false);
    ResetIterator(&it);
    return err;

    // [2do]: not found
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////                   check options                 ///////////////
///////////////////////////////////////////////////////////////////////////////

ccp opt_name_tab[OPT__N_SPECIFIC] = {0};

void SetOption ( int opt_idx, ccp name )
{
    TRACE("SetOption(%d,%s)\n",opt_idx,name);

    if ( opt_idx > 0 && opt_idx < OPT__N_SPECIFIC )
    {
	used_options |= 1 << opt_idx;
	opt_name_tab[opt_idx] = name;
    }
}

///////////////////////////////////////////////////////////////////////////////

enumError CheckOptions ( int argc, char ** argv, int is_env )
{
    TRACE("CheckOptions(%d,%p,%d) optind=%d\n",argc,argv,is_env,optind);

    used_options = 0;
    optind = 0;
    int err = 0;

    for(;;)
    {
	const int opt_stat = getopt_long(argc,argv,short_opt,long_opt,0);
	if ( opt_stat == -1 )
	    break;

	noTRACE("CHECK OPTION %02x\n",opt_stat);
	switch (opt_stat)
	{
	  case '?': err++; break;
	  case 'V': version_exit();
	  case 'h': help_exit();
	  case 'q': verbose = -1; break;
	  case 'v': verbose++; break;
	  case 'P': progress++; break;
	  case 't': testmode++; break;
	  case 'n': AtFileHelper(optarg,0,AddIncludeID); break;
	  case 'N': AtFileHelper(optarg,0,AddIncludePath); break;
	  case 'x': AtFileHelper(optarg,0,AddExcludeID); break;
	  case 'X': AtFileHelper(optarg,0,AddExcludePath); break;
	  case 'T': AtFileHelper(optarg,true,AddTitleFile); break;

	  case GETOPT_UTF8:	use_utf8 = true; break;
	  case GETOPT_NO_UTF8:	use_utf8 = false; break;
	  case GETOPT_LANG:	lang_info = optarg; break;

	  case 'd': SetOption(OPT_DEST,"dest"); opt_dest = optarg; break;
	  case 'D': SetOption(OPT_DEST2,"DEST"); opt_dest = optarg; opt_mkdir = true; break;
   	  case 'z': SetOption(OPT_SPLIT,"split"); opt_split++; break;
	  case 'p': SetOption(OPT_PRESERVE,"preserve"); break;
	  case 'u': SetOption(OPT_UPDATE,"update"); break;
	  case 'o': SetOption(OPT_OVERWRITE,"overwrite"); break;
	  case 'i': SetOption(OPT_IGNORE,"ignore"); ignore_count++; break;
	  case 'R': SetOption(OPT_REMOVE,"remove"); break;
	  case 'C': SetOption(OPT_TRUNC,"trunc"); break;
	  case 'F': SetOption(OPT_FAST,"fast"); break;
	  case 'W': SetOption(OPT_WDF,"wdf");   output_file_type = OFT_WDF; break;
	  case 'I': SetOption(OPT_ISO,"iso");   output_file_type = OFT_PLAIN; break;
	  case 'B': SetOption(OPT_WBFS,"wbfs"); output_file_type = OFT_WBFS; break;
	  case 'l': SetOption(OPT_LONG,"long"); long_count++; break;
	  case 'U': SetOption(OPT_UNIQUE,"unique"); break;
	  case 'H': SetOption(OPT_NO_HEADER,"no-header"); break;

	  case 's':
	    AppendStringField(&source_list,optarg,false);
	    TRACELINE;
	    break;

	  case 'r':
	    AppendStringField(&recurse_list,optarg,false);
	    TRACELINE;
	    break;

	  case 'E':
	    if ( ScanEscapeChar(optarg) < 0 )
		err++;
	    break;

	  case GETOPT_PSEL:
	    {
		SetOption(OPT_PSEL,"psel");
		const int new_psel = ScanPartitionSelector(optarg);
		if ( new_psel == -1 )
		    err++;
		else
		    partition_selector = new_psel;
	    }
	    break;

	  case GETOPT_RAW:
	    partition_selector = WHOLE_DISC;
	    break;

	  case GETOPT_ITIME:
	    SetOption(OPT_ITIME,"itime");
	    opt_print_time = SetPrintTimeMode(opt_print_time,PT_USE_ITIME|PT_ENABLED);
	    break;

	  case GETOPT_MTIME:
	    SetOption(OPT_MTIME,"mtime");
	    opt_print_time = SetPrintTimeMode(opt_print_time,PT_USE_MTIME|PT_ENABLED);
	    break;

	  case GETOPT_CTIME:
	    SetOption(OPT_CTIME,"ctime");
	    opt_print_time = SetPrintTimeMode(opt_print_time,PT_USE_CTIME|PT_ENABLED);
	    break;

	  case GETOPT_ATIME:
	    SetOption(OPT_ATIME,"atime");
	    opt_print_time = SetPrintTimeMode(opt_print_time,PT_USE_ATIME|PT_ENABLED);
	    break;

	  case GETOPT_TIME:
	    SetOption(OPT_TIME,"time");
	    if ( ScanAndSetPrintTimeMode(optarg) == PT__ERROR )
		err++;
	    break;

	  case 'Z':
	    SetOption(OPT_SPLIT_SIZE,"split-size");
	    if (ScanSizeOptU64(&opt_split_size,optarg,GiB,0,
				"split-size",MIN_SPLIT_SIZE,0,512,0,true))
		hint_exit(ERR_SYNTAX);
	    opt_split++;
	    break;

	  case 'S':
	    {
		SetOption(OPT_SORT,"sort");
		const SortMode new_mode = ScanSortMode(optarg);
		if ( new_mode == SORT__ERROR )
		    err++;
		else
		{
		    TRACE("SORT-MODE set: %d -> %d\n",sort_mode,new_mode);
		    sort_mode = new_mode;
		}
	    }
	    break;

	  case GETOPT_IO:
	    {
		const enumIOMode new_io = strtol(optarg,0,0); // [2do] error handling
		opt_iomode = new_io & IOM__IS_MASK;
		if ( verbose > 0 || opt_iomode != new_io )
		    printf("IO mode set to %#0x.\n",opt_iomode);
		opt_iomode |= IOM_FORCE_STREAM;
	    }
	    break;

	  default:
	    ERROR0(ERR_INTERNAL,"Internal error: unhandled option: '%c'\n",opt_stat);
	    ASSERT(0); // line never reached
	    break;
	}
    }
    TRACELINE;

    if (is_env)
    {
	env_options = used_options;
    }
    else if ( verbose > 3 )
    {
	print_title(stdout);
	printf("PROGRAM_NAME   = %s\n",progname);
	if (lang_info)
	    printf("LANG_INFO      = %s\n",lang_info);
	ccp * sp;
	for ( sp = search_path; *sp; sp++ )
	    printf("SEARCH_PATH[%td] = %s\n",sp-search_path,*sp);
	printf("\n");
    }

    return !err ? ERR_OK : max_error ? max_error : ERR_SYNTAX;
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////                   check command                 ///////////////
///////////////////////////////////////////////////////////////////////////////

enumError check_command ( int argc, char ** argv )
{
    TRACE("check_command(%d,) optind=%d\n",argc,optind);

    if ( optind >= argc )
    {
	ERROR0(ERR_SYNTAX,"Missing command.\n");
	hint_exit(ERR_SYNTAX);
    }

    int cmd_stat;
    CommandTab_t * cmd_ct = ScanCommand(&cmd_stat,argv[optind],CommandTab);
    if (!cmd_ct)
    {
	if ( cmd_stat > 0 )
	    ERROR0(ERR_SYNTAX,"Command abbreviation is ambiguous: %s\n",argv[optind]);
	else
	    ERROR0(ERR_SYNTAX,"Unknown command: %s\n",argv[optind]);
	hint_exit(ERR_SYNTAX);
    }

    TRACE("COMMAND FOUND: #%d = %s\n",cmd_ct->id,cmd_ct->name1);

    uint forbidden_mask = used_options & ~cmd_ct->opt;
    if ( forbidden_mask )
    {
	int i;
	for ( i=0; long_opt[i].name; i++, forbidden_mask >>= 1 )
	    if ( forbidden_mask & 1 )
		ERROR0(ERR_SYNTAX,"Command '%s' don't allow the option --%s\n",
				cmd_ct->name1, opt_name_tab[i] );
	hint_exit(ERR_SEMANTIC);
    }
    used_options |= env_options & cmd_ct->opt;

    argc -= optind+1;
    argv += optind+1;

    while ( argc-- > 0 )
	AtFileHelper(*argv++,false,AddParam);

    enumError err = 0;
    switch(cmd_ct->id)
    {
	case CMD_VERSION:	version_exit();
	case CMD_TEST:		err = cmd_test(); break;
	case CMD_ERROR:		err = cmd_error(); break;
	case CMD_EXCLUDE:	err = cmd_exclude(); break;
	case CMD_TITLES:	err = cmd_titles(); break;

	case CMD_DUMP:		err = cmd_dump(); break;
	case CMD_ID6:		err = cmd_id6(); break;
	case CMD_LIST:		err = cmd_list(); break;
	case CMD_LIST_L:	err = cmd_list_l(); break;
	case CMD_LIST_LL:	err = cmd_list_ll(); break;
	case CMD_LIST_LLL:	err = cmd_list_lll(); break;

	case CMD_FILELIST:	err = cmd_filelist(); break;
	case CMD_FILETYPE:	err = cmd_filetype(); break;
	case CMD_ISOSIZE:	err = cmd_isosize(); break;

	case CMD_DIFF:		err = cmd_diff(); break;
	case CMD_COPY:		err = cmd_copy(); break;
	case CMD_SCRUB:		err = cmd_scrub(); break;
	case CMD_MOVE:		err = cmd_move(); break;
	case CMD_REMOVE:	err = cmd_remove(); break;
	case CMD_RENAME:	err = cmd_rename(true); break;
	case CMD_SETTITLE:	err = cmd_rename(false); break;

	default:
	    help_exit();
    }

    if ( err && verbose > 0 || err == ERR_NOT_IMPLEMENTED )
	fprintf(stderr,"%s: Command '%s' returns with status #%d [%s]\n",
			progname, cmd_ct->name1, err, GetErrorName(err) );
    return err;
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////                       main()                    ///////////////
///////////////////////////////////////////////////////////////////////////////

int main ( int argc, char ** argv )
{
    SetupLib(argc,argv,WIT_SHORT,PROG_WIT);

    TRACE_SIZEOF(TDBfind_t);
    TRACE_SIZEOF(ID_DB_t);
    TRACE_SIZEOF(ID_t);

    ASSERT( OPT__N_SPECIFIC <= 32 );

    InitializeStringField(&source_list);
    InitializeStringField(&recurse_list);

    //----- process arguments

    if ( argc < 2 )
    {
	printf("\n%s\nVisit %s for more infos.\n\n",TITLE,URI_HOME);
	hint_exit(ERR_OK);
    }

    enumError err = CheckEnvOptions("WIT_OPT",CheckOptions,1);
    if (err)
	hint_exit(err);

    err = CheckOptions(argc,argv,0);
    if (err)
	hint_exit(err);

    err = check_command(argc,argv);

    if (SIGINT_level)
	err = ERROR0(ERR_INTERRUPT,"Program interrupted by user.");
    return err;
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////                     END                         ///////////////
///////////////////////////////////////////////////////////////////////////////

