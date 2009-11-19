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

#define NAME "wtest"
#undef TITLE
#define TITLE NAME " v" VERSION " r" REVISION " " SYSTEM " - " AUTHOR " - " DATE

u32 used_options;

//
///////////////////////////////////////////////////////////////////////////////

enumError WriteBlock ( SuperFile_t * sf, char ch, off_t off, u32 count )
{
    ASSERT(sf);
    if ( count > sizeof(iobuf) )
	count = sizeof(iobuf);

    memset(iobuf,ch,count);
    return WriteWDF(sf,off,iobuf,count);
}

//
///////////////////////////////////////////////////////////////////////////////

enumError gen_wdf ( ccp fname )
{
    SuperFile_t sf;
    InitializeSF(&sf);

    enumError stat = CreateFile(&sf.f,fname,IOM_IS_IMAGE,1);
    if (stat)
	return stat;

    stat = SetupWriteWDF(&sf);
    if (stat)
	goto abort;

    WriteBlock(&sf,'a',0x40,0x30);
    WriteBlock(&sf,'b',0x08,0x04);
    WriteBlock(&sf,'c',0x60,0x20);
    WriteBlock(&sf,'d',0x80,0x10);
    WriteBlock(&sf,'d',0x30,0x20);

    stat = TermWriteWDF(&sf);
    if (stat)
	goto abort;

    return CloseSF(&sf,0);

 abort:
    CloseSF(&sf,0);
    unlink(fname);
    return stat;
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////

void read_behind_file ( ccp fname )
{
    File_t f;
    InitializeFile(&f);

    OpenFile(&f,fname,IOM_IS_IMAGE);
    ReadAtF(&f,0,iobuf,sizeof(iobuf));
    ReadAtF(&f,0x10000,iobuf,sizeof(iobuf));
    ClearFile(&f,false);

    OpenFile(&f,fname,IOM_IS_IMAGE);
    f.read_behind_eof = 1;
    ReadAtF(&f,0,iobuf,sizeof(iobuf));
    ReadAtF(&f,0x10000,iobuf,sizeof(iobuf));
    ClearFile(&f,false);
}

///////////////////////////////////////////////////////////////////////////////

void read_behind_wdf ( ccp fname )
{
    SuperFile_t sf;
    InitializeSF(&sf);

    OpenFile(&sf.f,fname,IOM_IS_IMAGE);
    SetupReadWDF(&sf);
    ReadWDF(&sf,0,iobuf,sizeof(iobuf));
    ReadWDF(&sf,0x10000,iobuf,sizeof(iobuf));
    CloseSF(&sf,0);

    OpenFile(&sf.f,fname,IOM_IS_IMAGE);
    SetupReadWDF(&sf);
    sf.f.read_behind_eof = 1;
    ReadWDF(&sf,0,iobuf,sizeof(iobuf));
    ReadWDF(&sf,0x10000,iobuf,sizeof(iobuf));
    CloseSF(&sf,0);
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////

void test_string_field()
{
    StringField_t sf;
    InitializeStringField(&sf);

    InsertStringField(&sf,"b",false);
    InsertStringField(&sf,"a",false);
    InsertStringField(&sf,"c",false);
    InsertStringField(&sf,"b",false);

    int i;
    for ( i = 0; i < sf.used; i++ )
	printf("%4d.: |%s|\n",i,sf.field[i]);

    ResetStringField(&sf);
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////

void test_create_file()
{
    File_t f;
    InitializeFile(&f);

    CreateFile(&f,"pool/hallo.tmp",IOM_NO_STREAM,1);
    SetupSplitFile(&f,OFT_PLAIN,0x80);
    WriteAtF(&f,0x150,"Hallo\n",6);
    printf("*** created -> press ENTER: "); fflush(stdout); getchar();

    CloseFile(&f,1);
    printf("*** closed -> press ENTER: "); fflush(stdout); getchar();
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////

void test_splitted_file()
{
    File_t of;
    InitializeFile(&of);

    GenDestFileName(&of,"pool/","split-file",".xxx",0);
    CreateFile( &of, 0, IOM_NO_STREAM,true);

    printf("*** created -> press ENTER: "); fflush(stdout); getchar();
    
    SetupSplitFile(&of,OFT_PLAIN,0x80);

    static char abc[] = "abcdefghijklmnopqrstuvwxyz\n";
    static char ABC[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZ\n";

    int i;
    for ( i = 0; i < 10; i++ )
	WriteF(&of,abc,strlen(abc));

    printf("*** written -> press ENTER: "); fflush(stdout); getchar();

    TRACELINE;
    CloseFile(&of,0);

    printf("*** closed -> press ENTER: "); fflush(stdout); getchar();

    File_t f;
    InitializeFile(&f);
    OpenFileModify(&f,"pool/split-file.xxx",IOM_NO_STREAM);
    SetupSplitFile(&f,OFT_PLAIN,0x100);
    
    SeekF(&f,0xc0);
    
    for ( i = 0; i < 20; i++ )
	WriteF(&f,ABC,strlen(ABC));

    char buf[200];
    ReadAtF(&f,0,buf,sizeof(buf));
    printf("%.*s|\n",sizeof(buf),buf);

    CloseFile(&f,false);
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////

int main ( int argc, char ** argv )
{
    SetupLib(argc,argv,NAME,PROG_UNKNOWN);

 #if 0
    unlink("_temp.wdf");
    gen_wdf("_temp.wdf");
    read_behind_file("_temp.wdf");
    read_behind_wdf("_temp.wdf");
 #endif

    //test_string_field();

    test_create_file();
    //test_splitted_file();

    if (SIGINT_level)
	ERROR0(ERR_INTERRUPT,"Program interrupted by user.");
    return max_error;
}

///////////////////////////////////////////////////////////////////////////////
