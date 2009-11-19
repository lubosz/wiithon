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

#include <fcntl.h>
#include <unistd.h>
#include <getopt.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <limits.h>

#include "debug.h"
#include "version.h"
#include "types.h"
#include "lib-wdf.h"
#include "lib-std.h"

///////////////////////////////////////////////////////////////////////////////

#define NAME "wdf-dump"
#define TITLE NAME " v" VERSION " r" REVISION " " SYSTEM " - " AUTHOR " - " DATE

bool print_chunk_tab = false;
int end_delta = 0;

//
///////////////////////////////////////////////////////////////////////////////

enum // const for long options without a short brothers
{
	GETOPT_BASE	= 0x1000,
	GETOPT_IO,
};

char short_opt[] = "hVqvcl";
struct option long_opt[] =
{
	{ "help",	0, 0, 'h' },
	{ "version",	0, 0, 'V' },
	{ "quiet",	0, 0, 'q' },
	{ "verbose",	0, 0, 'v' },
	{ "chunk",	0, 0, 'c' },
	{ "long",	0, 0, 'l' },  // obsolete alternative for chunk

	{ "io",		1, 0, GETOPT_IO }, // [2do] hidden option for tests

	{0,0,0,0}
};

///////////////////////////////////////////////////////////////////////////////

static char help_text[] =
    "\n"
    TITLE "\n"
    "This tool to dumps the data structure of WDF files.\n"
    "\n"
    "Syntax: " NAME " [option]... files...\n"
    "\n"
    "Options:\n"
    "\n"
    "    -h --help     Print this help and exit.\n"
    "    -V --version  Print program name and version and exit.\n"
    "    -q --quiet    Be quiet   -> suppress output of program name.\n"
    "    -v --verbose  Be verbose -> print program name.\n"
    "    -c --chunk    Print table with chunk header.\n"
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
    printf("%s\n",TITLE);
    exit(ERR_OK);
}

///////////////////////////////////////////////////////////////////////////////

void hint_exit ( int stat )
{
    fprintf(stderr,
	    "-> Type '%s -h' or %s --help for more help.\n\n",
	    progname, progname );
    exit(stat);
}

///////////////////////////////////////////////////////////////////////////////

enumError CheckOptions ( int argc, char ** argv )
{
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
	  case 'v': verbose = verbose < 0 ? 1 : verbose+1; break;
	  case 'l':
	  case 'c': print_chunk_tab = true; break;

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
	    ERROR0(ERR_INTERNAL,"Internal error: unhandled option: '%x'\n",opt_stat);
	    ASSERT(0); // line never reached
	    err++;
	    break;
	}
    }
    return err ? ERR_SYNTAX : ERR_OK;
}

//
///////////////////////////////////////////////////////////////////////////////

static int error ( int err, int indent, ccp fname, ccp format, ... )
{
    fprintf(stdout,"%*s!!! %s: ",indent,"",progname);

    va_list arg;
    va_start(arg,format);
    vfprintf(stdout,format,arg);
    va_end(arg);
    fprintf(stdout,"\n\n");

    if (!isatty(fileno(stdout)))
    {
	fprintf(stderr,"%s: ",progname);

	va_start(arg,format);
	vfprintf(stderr,format,arg);
	va_end(arg);
	fprintf(stderr,"\n%s:  - file: %s\n",progname,fname);
    }

    return err;
}

///////////////////////////////////////////////////////////////////////////////

static u64 prev_val = 0;

static int print_range ( ccp text, u64 end, u64 len )
{
    const int err = end - prev_val != len;
    if (err)
	printf("    %-18s: %10llx .. %10llx [%10llx!=%10llx] INVALID!\n", \
		text, prev_val, end-end_delta, len, end-prev_val );
    else
	printf("    %-18s: %10llx .. %10llx [%10llx]\n", \
		text, prev_val, end-end_delta, len );

    prev_val = end;
    return err;
}

///////////////////////////////////////////////////////////////////////////////

enumError wdf_dump ( ccp fname )
{
    printf("\nWDF dump of file %s\n",fname);

    File_t f;
    InitializeFile(&f);
    enumError err = OpenFile(&f,fname,IOM_IS_IMAGE);
    if (err)
	return err;

    WDF_Head_t wh;
    err = ReadAtF(&f,0,&wh,sizeof(wh));
    if (err)
    {
	CloseFile(&f,false);
	return err;
    }

    ConvertToHostWH(&wh,&wh);
    AnalyseWH(&f,&wh,false); // needed for splitting support!

    printf("\n  Header:\n\n");
    u8 * m = (u8*)wh.magic;
    printf("    %-18s: \"%c%c%c%c%c%c%c%c\"  %02x %02x %02x %02x  %02x %02x %02x %02x\n",
		"Magic",
		m[0]>=' ' && m[0]<0x7f ? m[0] : '.',
		m[1]>=' ' && m[1]<0x7f ? m[1] : '.',
		m[2]>=' ' && m[2]<0x7f ? m[2] : '.',
		m[3]>=' ' && m[3]<0x7f ? m[3] : '.',
		m[4]>=' ' && m[4]<0x7f ? m[4] : '.',
		m[5]>=' ' && m[5]<0x7f ? m[5] : '.',
		m[6]>=' ' && m[6]<0x7f ? m[6] : '.',
		m[7]>=' ' && m[7]<0x7f ? m[7] : '.',
		m[0], m[1], m[2], m[3], m[4], m[5], m[6], m[7] );

    if (memcmp(wh.magic,WDF_MAGIC,WDF_MAGIC_SIZE))
    {
	CloseFile(&f,false);
	return error(ERR_WDF_INVALID,2,fname,"Wrong magic");
    }

    #undef PRINT32
    #undef PRINT64
    #undef RANGE
    #define PRINT32(a) printf("    %-18s: %10x/hex =%11d\n",#a,wh.a,wh.a)
    #define PRINT64(a) printf("    %-18s: %10llx/hex =%11lld\n",#a,wh.a,wh.a)

    PRINT32(wdf_version);
    PRINT32(split_file_id);
    PRINT32(split_file_index);
    PRINT32(split_file_num_of);
    PRINT64(file_size);
    printf("    %18s: %10llx/hex =%11lld  %4.2f%%\n","- WDF file size ",
		f.st.st_size, f.st.st_size,  100.0 * f.st.st_size / wh.file_size );
    PRINT64(data_size);
    PRINT32(chunk_split_file);
    PRINT32(chunk_n);
    PRINT64(chunk_off);

    //--------------------------------------------------

    printf("\n  File Parts:\n\n");

    int ec = 0; // error count
    prev_val = 0;
    const int chunk_size = wh.chunk_n*sizeof(WDF_Chunk_t);

    ec += print_range( "Header",	sizeof(wh),			sizeof(wh) );
    ec += print_range( "Data",		wh.chunk_off,			wh.data_size );
    ec += print_range( "Chunk-Magic",	wh.chunk_off+WDF_MAGIC_SIZE,	WDF_MAGIC_SIZE );
    ec += print_range( "Chunk-Table",	f.st.st_size,			chunk_size );
    printf("\n");

    if (ec)
    {
	CloseFile(&f,false);
	return error(ERR_WDF_INVALID,2,fname,"Invalid data");
    }

    if ( wh.chunk_n > 10000 )
    {
	CloseFile(&f,false);
	return error(ERR_INTERNAL,2,fname,"Too much chunk enties");
    }

    //--------------------------------------------------

    char magic[WDF_MAGIC_SIZE];
    err = ReadAtF(&f,wh.chunk_off,magic,sizeof(magic));
    if (err)
    {
	CloseFile(&f,false);
	return error(ERR_READ_FAILED,2,fname,"ReadF error");
    }

    if (memcmp(magic,WDF_MAGIC,WDF_MAGIC_SIZE))
    {
	CloseFile(&f,false);
	return error(ERR_WDF_INVALID,2,fname,"Wrong chunk table magic");
    }

    WDF_Chunk_t *w, *wc = malloc(chunk_size);
    if (!wc)
	OUT_OF_MEMORY;

    err = ReadF(&f,wc,chunk_size);
    if (err)
    {
	CloseFile(&f,false);
	free(wc);
	return error(ERR_READ_FAILED,2,fname,"ReadF error");
    }

    if (print_chunk_tab)
    {
	printf("  Chunk Table:\n\n"
	       "    idx       WDF file address  data len    virtual ISO address  hole size\n"
	       "   ------------------------------------------------------------------------\n");

	int idx;
	for ( idx = 0, w = wc; idx < wh.chunk_n; idx++, w++ )
	    ConvertToHostWC(w,w);

	for ( idx = 0, w = wc; idx < wh.chunk_n; idx++, w++ )
	{
	    printf("%6d. %10llx..%10llx %9llx %10llx..%10llx  %9llx\n",
		    idx,
		    w->data_off, w->data_off + w->data_size-end_delta,
		    w->data_size,
		    w->file_pos, w->file_pos + w->data_size - end_delta,
		    idx+1 < wh.chunk_n ? w[1].file_pos - w->file_pos - w->data_size : 0llu );
	}

	printf("\n");
    }

    CloseFile(&f,false);
    return 0;
}

///////////////////////////////////////////////////////////////////////////////

int main ( int argc, char ** argv )
{
    SetupLib(argc,argv,NAME,PROG_WDF_DUMP);

    //----- process arguments

    if ( argc < 2 )
    {
	printf("\n%s\n\n",TITLE);
	hint_exit(ERR_OK);
    }

    if (CheckOptions(argc,argv))
	hint_exit(ERR_SYNTAX);

    if ( verbose >= 0 )
	printf("\n%s\n\n",TITLE);

    int i, max_err = ERR_OK;
    for ( i = optind; i < argc && !SIGINT_level; i++ )
    {
	const int last_err = wdf_dump(argv[i]);
	if ( max_err < last_err )
	    max_err = last_err;
    }

    if (SIGINT_level)
	ERROR0(ERR_INTERRUPT,"Program interrupted by user.");
    return max_err > max_error ? max_err : max_error;
}

///////////////////////////////////////////////////////////////////////////////
