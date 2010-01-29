
#define _GNU_SOURCE 1

//#include <sys/types.h>
//#include <sys/stat.h>
//#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <arpa/inet.h>
#include <dirent.h>

#include "debug.h"
#include "libwbfs.h"
#include "lib-wdf.h"
#include "wbfs-interface.h"
#include "titles.h"

//
///////////////////////////////////////////////////////////////////////////////
///////////////                 SuperFile_t: setup              ///////////////
///////////////////////////////////////////////////////////////////////////////

void InitializeSF ( SuperFile_t * sf )
{
    ASSERT(sf);
    memset(sf,0,sizeof(*sf));
    InitializeWH(&sf->wh);
    InitializeFile(&sf->f);
    ResetSF(sf,0);
}

///////////////////////////////////////////////////////////////////////////////
// close file & remove all dynamic data

void FreeSF ( SuperFile_t * sf )
{
    ASSERT(sf);
    if (sf->wc)
	free(sf->wc);
    sf->wc = 0;
    sf->wc_size = 0;
    sf->wc_used = 0;

    if (sf->wbfs)
    {
	TRACE("#S# close WBFS %s id=%s\n",sf->f.fname,sf->f.id6);
	ResetWBFS(sf->wbfs);
	free(sf->wbfs);
	sf->wbfs = 0;
    }
}

///////////////////////////////////////////////////////////////////////////////

enumError CloseSF ( SuperFile_t * sf, struct stat * set_time )
{
    ASSERT(sf);
    enumError err = ERR_OK;
    if ( sf->f.is_writing && !sf->f.is_reading )
    {
	if (sf->wc)
	    err = TermWriteWDF(sf);

	if (sf->wbfs)
	{
	    CloseWDisc(sf->wbfs);
	    err = TruncateWBFS(sf->wbfs);
	}
    }

    if ( err != ERR_OK )
	CloseFile(&sf->f,true);
    else
    {
	err = CloseFile(&sf->f,false);
	if (set_time)
	    SetFileTime(&sf->f,set_time);
    }

    FreeSF(sf);
    return err;
}

///////////////////////////////////////////////////////////////////////////////

enumError ResetSF ( SuperFile_t * sf, struct stat * set_time )
{
    ASSERT(sf);

    // free dynamic memory
    enumError err = CloseSF(sf,set_time);
    ResetFile(&sf->f,false);

    // normalize indent
    if ( sf->indent < 0 )
	sf->indent = 0;
    else if ( sf->indent > 50 )
	sf->indent = 50;

    // reset data
    InitializeWH(&sf->wh);
    sf->max_virt_off = 0;

    // reset timer
    sf->progress_start_time = sf->progress_last_calc_time = GetTimerMSec();
    sf->progress_last_view_sec = 0;
    sf->progress_sum_time = 0;
    sf->progress_time_divisor = 0;
    sf->progress_max_wd = 0;
 #if defined(DEBUG) || defined(TEST)
    sf->show_msec = true;
 #else
    sf->show_msec = false;
 #endif

    return err;
}

///////////////////////////////////////////////////////////////////////////////

enumError RemoveSF ( SuperFile_t * sf )
{
    ASSERT(sf);
    TRACE("RemoveSF(%p)\n",sf);

    if (sf->wbfs)
    {
	if ( sf->wbfs->used_discs > 1 )
	{
	    TRACE(" - remove wdisc %s\n",sf->f.id6);
	    RemoveWDisc(sf->wbfs,sf->f.id6,0);
	    return ResetSF(sf,0);
	}
    }

    TRACE(" - remove file %s\n",sf->f.fname);
    enumError err = CloseSF(sf,0);
    CloseFile(&sf->f,true);
    ResetSF(sf,0);
    return err;
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////	                       Setup SF                ////////////////
///////////////////////////////////////////////////////////////////////////////

enumError SetupReadSF ( SuperFile_t * sf )
{
    ASSERT(sf);
    TRACE("SetupReadSF(%p) fd=%d is-r=%d is-w=%d\n",
	sf, sf->f.fd, sf->f.is_reading, sf->f.is_writing );

    if ( !sf || !sf->f.is_reading )
	return ERROR0(ERR_INTERNAL,0);

    sf->oft = OFT_PLAIN;
    if ( sf->f.ftype == FT_UNKNOWN )
	AnalyseFT(&sf->f);

    if ( !IsFileOpen(&sf->f) )
    {
	if (!sf->f.disable_errors)
	    ERROR0( ERR_CANT_OPEN, "Can't open file: %s\n", sf->f.fname );
	return ERR_CANT_OPEN;
    }

    if ( sf->f.ftype & FT_A_WDF )
	return SetupReadWDF(sf);

    if ( sf->f.ftype & FT_ID_WBFS && sf->f.id6[0] )
	return SetupReadWBFS(sf);

    sf->file_size = sf->f.st.st_size;
    return ERR_OK;
}

///////////////////////////////////////////////////////////////////////////////

enumError SetupReadISO ( SuperFile_t * sf )
{
    ASSERT(sf);
    TRACE("SetupReadISO(%p)\n",sf);

    enumError err = SetupReadSF(sf);
    if ( err || sf->f.ftype & FT_A_ISO )
	return err;

    if (!sf->f.disable_errors)
	PrintErrorFT(&sf->f,FT_A_ISO);
    return ERR_WRONG_FILE_TYPE;
}

///////////////////////////////////////////////////////////////////////////////

enumError SetupReadWBFS ( SuperFile_t * sf )
{
    ASSERT(sf);
    TRACE("SetupReadWBFS(%p)\n",sf);

    if ( !sf || !sf->f.is_reading || sf->wbfs )
	return ERROR0(ERR_INTERNAL,0);

    WBFS_t * wbfs =  malloc(sizeof(*wbfs));
    if (!wbfs)
	OUT_OF_MEMORY;
    InitializeWBFS(wbfs);
    enumError err = SetupWBFS(wbfs,sf,true,0);
    if (err)
	goto abort;

    err = OpenWDiscID6(wbfs,sf->f.id6);
    if (err)
	goto abort;

    //----- calc file size

    ASSERT(wbfs->disc);
    ASSERT(wbfs->disc->header);
    u16 * wlba_tab = wbfs->disc->header->wlba_table;
    ASSERT(wlba_tab);

    wbfs_t *w = wbfs->wbfs;
    ASSERT(w);

    int bl;
    for ( bl = w->n_wbfs_sec_per_disc-1; bl > 0; bl-- )
	if (ntohs(wlba_tab[bl]))
	{
	    bl++;
	    break;
	}
    sf->file_size = (off_t)bl * w->wbfs_sec_sz;
    const off_t single_size = WII_SECTORS_SINGLE_LAYER * (off_t)WII_SECTOR_SIZE;
    if ( sf->file_size < single_size )
	sf->file_size = single_size;

    //---- store data

    TRACE("WBFS %s/%s opened.\n",sf->f.fname,sf->f.id6);
    sf->wbfs = wbfs;

    WDiscHeader_t * dh = (WDiscHeader_t*)wbfs->disc->header;
    snprintf(iobuf,sizeof(iobuf),"%s [%s]",
		GetTitle(sf->f.id6,(ccp)dh->game_title), sf->f.id6 );
    FreeString(sf->f.outname);
    sf->f.outname = strdup(iobuf);
    sf->oft = OFT_WBFS;
    return ERR_OK;

 abort:
    ResetWBFS(wbfs);
    free(wbfs);
    return err;
}

///////////////////////////////////////////////////////////////////////////////

enumError OpenSF
	( SuperFile_t * sf, ccp fname, bool allow_non_iso, bool open_modify )
{
    ASSERT(sf);
    CloseSF(sf,0);
    TRACE("#S# OpenSF(%p,%s,%d,%d)\n",sf,fname,allow_non_iso,open_modify);

    const bool disable_errors = sf->f.disable_errors;
    sf->f.disable_errors = true;
    if (open_modify)
	OpenFileModify(&sf->f,fname,IOM_IS_IMAGE);
    else
	OpenFile(&sf->f,fname,IOM_IS_IMAGE);
    sf->f.disable_errors = disable_errors;

    DefineCachedAreaISO(&sf->f,true);

    return allow_non_iso
		? SetupReadSF(sf)
		: SetupReadISO(sf);
}

///////////////////////////////////////////////////////////////////////////////

enumError SetupWriteSF ( SuperFile_t * sf, enumOFT oft )
{
    ASSERT(sf);
    TRACE("SetupWriteSF(%p)\n",sf);

    if ( !sf || sf->f.is_reading || !sf->f.is_writing )
	return ERROR0(ERR_INTERNAL,0);

    sf->oft = CalcOFT(oft,sf->f.fname,0,OFT__DEFAULT);
    switch(sf->oft)
    {
	case OFT_PLAIN:
	    return ERR_OK;

	case OFT_WDF:
	    return SetupWriteWDF(sf);

	case OFT_WBFS:
	    return SetupWriteWBFS(sf);

	default:
	    return ERROR0(ERR_INTERNAL,"Unknown output file format: %s\n",sf->oft);
    }
}

///////////////////////////////////////////////////////////////////////////////

enumError SetupWriteWBFS ( SuperFile_t * sf )
{
    ASSERT(sf);
    TRACE("SetupWriteWBFS(%p)\n",sf);

    if ( !sf || sf->f.is_reading || !sf->f.is_writing || sf->wbfs )
	return ERROR0(ERR_INTERNAL,0);

    WBFS_t * wbfs =  malloc(sizeof(*wbfs));
    if (!wbfs)
	OUT_OF_MEMORY;
    InitializeWBFS(wbfs);
    enumError err = CreateGrowingWBFS(wbfs,sf,(off_t)10*GiB,sf->f.sector_size);
    sf->wbfs = wbfs;
    sf->oft = OFT_WBFS;
    return err;
}

///////////////////////////////////////////////////////////////////////////////

void SubstFileNameSF
	( SuperFile_t * fo, SuperFile_t * fi, ccp f_name )
{
    ASSERT(fo);
    ASSERT(fi);

    char buf[HD_SECTOR_SIZE];
    memset(&buf,0,sizeof(buf));
    if (fi->f.id6[0])
    {
	const bool disable_errors = fi->f.disable_errors;
	fi->f.disable_errors = true;
	ReadSF(fi,0,&buf,sizeof(buf));
	fi->f.disable_errors = disable_errors;
    }

    if (!f_name)
    {
	f_name = fi->f.fname;
	ccp temp = strrchr(f_name,'/');
	if (temp)
	    f_name = temp+1;
    }

    char src_path[PATH_MAX];
    StringCopyS(src_path,sizeof(src_path),fi->f.fname);
    char * temp = strrchr(src_path,'/');
    if (temp)
	*temp = 0;
    else
	*src_path = 0;

    ccp name = (ccp)((WDiscHeader_t*)buf)->game_title;
    if (!name)
	name = fi->f.id6;

    ccp title = GetTitle(fi->f.id6,name);

    char x_buf[1000];
    snprintf(x_buf,sizeof(x_buf),"%s [%s]%s",
		title, fi->f.id6, oft_ext[fo->oft] );

    char plus_buf[20];
    ccp plus_name;
    if ( fo->oft == OFT_WBFS )
    {
	snprintf(plus_buf,sizeof(plus_buf),"%s%s",
	    fi->f.id6, oft_ext[fo->oft] );
	plus_name = plus_buf;
    }
    else
	plus_name = x_buf;

    SubstString_t subst_tab[] =
    {
	{ 'i', 'I', 0, fi->f.id6 },
	{ 'n', 'N', 0, name },
	{ 't', 'T', 0, title },
	{ 'e', 'E', 0, oft_ext[fo->oft]+1 },
	{ 'p', 'P', 1, src_path },
	{ 'f', 'F', 1, f_name },
	{ 'x', 'X', 0, x_buf },
	{ '+', '+', 0, plus_name },
	{0,0,0,0}
    };

    char fname[PATH_MAX*2];
    int conv_count;
    SubstString(fname,sizeof(fname),subst_tab,fo->f.fname,&conv_count);
    if ( conv_count > 0)
	fo->f.create_directory = true;
    SetFileName(&fo->f,fname,true);
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////            ReadSF(), WriteSF, SetSizeSF()       ///////////////
///////////////////////////////////////////////////////////////////////////////

enumError ReadSF ( SuperFile_t * sf, off_t off, void * buf, size_t count )
{
    ASSERT(sf);
    if (!sf->wbfs)
	return sf->wc
		? ReadWDF(sf,off,buf,count)
		: ReadAtF(&sf->f,off,buf,count);

    //---------- read wbfs/disc

    TRACE(TRACE_RDWR_FORMAT, "#B# ReadSF()",
		GetFD(&sf->f), GetFP(&sf->f), off, off+count, count, "" );

    ASSERT(sf->wbfs->disc);
    ASSERT(sf->wbfs->disc->header);
    u16 * wlba_tab = sf->wbfs->disc->header->wlba_table;
    ASSERT(wlba_tab);

    wbfs_t * w = sf->wbfs->wbfs;
    ASSERT(w);

    u32 bl = (u32)( off / w->wbfs_sec_sz );
    u32 bl_off = (u32)( off - (u64)bl * w->wbfs_sec_sz );

    while ( count > 0 )
    {
	u32 max_count = w->wbfs_sec_sz - bl_off;
	ASSERT( max_count > 0 );
	if ( max_count > count )
	    max_count = count;

	const u32 wlba = bl < w->n_wbfs_sec_per_disc ? ntohs(wlba_tab[bl]) : 0;

	TRACE(">> BL=%d[%d], BL-OFF=%x, count=%x/%x\n",
		bl, wlba, bl_off, max_count, count );

	if (wlba)
	{
	    enumError err = ReadAtF( &sf->f,
				     (off_t)w->wbfs_sec_sz * wlba + bl_off,
				     buf, max_count);
	    if (err)
		return err;
	}
	else
	    memset(buf,0,max_count);

	bl++;
	bl_off = 0;
	count -= max_count;
	buf = (char*)buf + max_count;
    }

    return ERR_OK;
}

///////////////////////////////////////////////////////////////////////////////

enumError WriteSF ( SuperFile_t * sf, off_t off, const void * buf, size_t count )
{
    ASSERT(sf);

    switch(sf->oft)
    {
	case OFT_PLAIN:
	    return WriteAtF(&sf->f,off,buf,count);

	case OFT_WDF:
	    ASSERT(sf->wc);
	    return WriteWDF(sf,off,buf,count);

	case OFT_WBFS:
	    ASSERT(sf->wbfs);
	    return ERROR0(ERR_INTERNAL,"WBFS direct writing not supported.");

	default:
	    return ERROR0(ERR_INTERNAL,0);
    }
}

///////////////////////////////////////////////////////////////////////////////

enumError WriteSparseSF ( SuperFile_t * sf, off_t off, const void * buf, size_t count )
{
    ASSERT(sf);

    switch(sf->oft)
    {
	case OFT_PLAIN:
	    return WriteSparseAtF(&sf->f,off,buf,count);

	case OFT_WDF:
	    ASSERT(sf->wc);
	    return WriteSparseWDF(sf,off,buf,count);

	case OFT_WBFS:
	    ASSERT(sf->wbfs);
	    return ERROR0(ERR_INTERNAL,"WBFS direct writing not supported.");

	default:
	    return ERROR0(ERR_INTERNAL,0);
    }
}

///////////////////////////////////////////////////////////////////////////////

enumError SetSizeSF ( SuperFile_t * sf, off_t off )
{
    ASSERT(sf);
    TRACE("SetSizeSF(%p,%llx) wbfs=%p wc=%p\n",sf,off,sf->wbfs,sf->wc);

    if ( sf->wbfs )
    {
	// [2do]
	return ERR_OK;
    }

    if ( sf->wc )
    {
	sf->file_size = off;
	return ERR_OK;
    }

    return SetSizeF(&sf->f,off);
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////         SuperFile_t: read + write wrapper       ///////////////
///////////////////////////////////////////////////////////////////////////////

int WrapperReadISO ( void * sf, u32 offset, u32 count, void * iobuf )
{
    if (SIGINT_level>1)
	return ERR_INTERRUPT;

 #if defined(DEBUG)
    {
	TRACE("\n");
	SuperFile_t * W = (SuperFile_t *)sf;
	const off_t off = (off_t)offset << 2;
	TRACE(TRACE_RDWR_FORMAT, "WrapperReadISO()",
		W->f.fd, W->f.fp, off, off+count, count, "" );
    }
 #endif
    return ReadSF(
		(SuperFile_t*)sf,
		(off_t)offset << 2,
		iobuf,
		count );
}

///////////////////////////////////////////////////////////////////////////////

int WrapperReadSF ( void * sf, u32 offset, u32 count, void * iobuf )
{
    if (SIGINT_level>1)
	return ERR_INTERRUPT;

    return ReadSF(
		(SuperFile_t *)sf,
		(off_t)offset << 2,
		iobuf,
		count );
}

///////////////////////////////////////////////////////////////////////////////

int WrapperWriteDirectISO ( void * p_sf, u32 lba, u32 count, void * iobuf )
{
    if (SIGINT_level>1)
	return ERR_INTERRUPT;

    SuperFile_t *sf = (SuperFile_t *)p_sf;

    count *= WII_SECTOR_SIZE;
    const off_t off = (off_t)lba * WII_SECTOR_SIZE;
    const off_t end = off + count;
    if ( sf->file_size < end )
	sf->file_size = end;

    return WriteAtF( &sf->f, off, iobuf, count );
}

///////////////////////////////////////////////////////////////////////////////

int WrapperWriteSparseISO ( void * p_sf, u32 lba, u32 count, void * iobuf )
{
    if (SIGINT_level>1)
	return ERR_INTERRUPT;

    SuperFile_t *sf = (SuperFile_t *)p_sf;

    count *= WII_SECTOR_SIZE;
    const off_t off = (off_t)lba * WII_SECTOR_SIZE;
    const off_t end = off + count;
    if ( sf->file_size < end )
	sf->file_size = end;

    return WriteSparseAtF( &sf->f, off, iobuf, count );
}

///////////////////////////////////////////////////////////////////////////////

int WrapperWriteDirectSF ( void * p_sf, u32 lba, u32 count, void * iobuf )
{
    if (SIGINT_level>1)
	return ERR_INTERRUPT;

    return WriteSF(
		(SuperFile_t *)p_sf,
		(off_t)lba * WII_SECTOR_SIZE,
		iobuf,
		count * WII_SECTOR_SIZE );
}

///////////////////////////////////////////////////////////////////////////////

int WrapperWriteSparseSF ( void * p_sf, u32 lba, u32 count, void * iobuf )
{
    if (SIGINT_level>1)
	return ERR_INTERRUPT;

    return WriteSparseSF(
		(SuperFile_t *)p_sf,
		(off_t)lba * WII_SECTOR_SIZE,
		iobuf,
		count * WII_SECTOR_SIZE );
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////                SuperFile_t: progress            ///////////////
///////////////////////////////////////////////////////////////////////////////
// progress and statistics

void CopyProgressSF ( SuperFile_t * dest, SuperFile_t * src )
{
    ASSERT(dest);
    ASSERT(src);

    dest->indent			= src->indent;
    dest->show_progress			= src->show_progress;
    dest->show_summary			= src->show_summary;
    dest->show_msec			= src->show_msec;
    dest->progress_start_time		= src->progress_start_time;
    dest->progress_last_view_sec	= src->progress_last_view_sec;
    dest->progress_last_calc_time	= src->progress_last_calc_time;
    dest->progress_sum_time		= src->progress_sum_time;
    dest->progress_time_divisor		= src->progress_time_divisor;
    dest->progress_max_wd		= src->progress_max_wd;
    dest->progress_verb			= src->progress_verb;
}

///////////////////////////////////////////////////////////////////////////////


void PrintProgressSF ( u64 p_done, u64 p_total, void * param )
{
    SuperFile_t * sf = (SuperFile_t*) param;
    TRACE("PrintProgressSF(%llu,%llu), sf=%p, fd=%d, sh-prog=%d\n",
		p_done, p_total, sf,
		sf ? GetFD(&sf->f) : -2,
		sf ? sf->show_progress : -1 );

    if ( !sf || !sf->show_progress || !p_done || !p_total )
	return;

    if ( p_total > TiB )
    {
	// avoid integer overflow
	p_done  >>= 15;
	p_total >>= 15;
    }

    const u32 now		= GetTimerMSec();
    const u32 elapsed		= now - sf->progress_start_time;
    const u32 view_sec		= elapsed / 1000;
    const u32 rate		= 10000 * p_done / p_total;
    const u32 percent		= rate / 100;
    const u64 total		= sf->f.bytes_read + sf->f.bytes_written;

    TRACE(" - sec=%d->%d, rate=%d, total=%llu=%llu+%llu\n",
		sf->progress_last_view_sec, view_sec, rate,
		total, sf->f.bytes_read, sf->f.bytes_written );

    if ( sf->progress_last_view_sec != view_sec && rate > 0 && total > 0 )
    {
	sf->progress_last_view_sec	= view_sec;
	sf->progress_sum_time		+= ( now - sf->progress_last_calc_time ) * view_sec;
	sf->progress_time_divisor	+= view_sec;
	sf->progress_last_calc_time	= now;

	const u32 elapsed	= now - sf->progress_start_time;
	const u32 eta		= ( view_sec * sf->progress_sum_time * (10000-rate) )
				/ ( sf->progress_time_divisor * rate );

	char buf1[50], buf2[50];
	ccp time1 = PrintMSec(buf1,sizeof(buf1),elapsed,sf->show_msec);
	ccp time2 = PrintMSec(buf2,sizeof(buf2),eta,false);

	TRACE("PROGRESS: now=%7u quot=%8llu/%-5llu perc=%3u ela=%6u eta=%6u [%s,%s]\n",
		now, sf->progress_sum_time, sf->progress_time_divisor,
		percent, elapsed, eta, time1, time2 );

	if ( !sf->progress_verb || !*sf->progress_verb )
	    sf->progress_verb = "copied";

	int wd;
	if ( percent < 10 && view_sec < 10 )
	    printf("%*s%3d%% %s in %s (%3.1f MiB/sec)  %n\r",
		sf->indent,"", percent, sf->progress_verb, time1,
		(double)total * 1000 / MiB / elapsed, &wd );
	else
	    printf("%*s%3d%% %s in %s (%3.1f MiB/sec) -> ETA %s   %n\r",
		sf->indent,"", percent, sf->progress_verb, time1,
		(double)total * 1000 / MiB / elapsed, time2, &wd );

	if ( sf->progress_max_wd < wd )
	    sf->progress_max_wd = wd;
	fflush(stdout);
    }
}

///////////////////////////////////////////////////////////////////////////////
// missing void* support

void PrintSummarySF ( SuperFile_t * sf )
{
    if ( !sf || !sf->show_progress && !sf->show_summary )
	return;

    char buf[200];
    buf[0] = 0;

    if (sf->show_summary)
    {
	const u32 elapsed = GetTimerMSec() - sf->progress_start_time;
	char timbuf[50];
	ccp tim = PrintMSec(timbuf,sizeof(timbuf),elapsed,sf->show_msec);

	u64 total = sf->f.bytes_read + sf->f.bytes_written;
	if (total)
	{
	    if ( !sf->progress_verb || !*sf->progress_verb )
		sf->progress_verb = "copied";

	    snprintf(buf,sizeof(buf),"%*s%4llu MiB %s in %s, %4.1f MiB/sec",
		sf->indent,"", (total+MiB/2)/MiB, sf->progress_verb,
		tim, (double)total * 1000 / MiB / elapsed );
	}
	else
	    snprintf(buf,sizeof(buf),"%*sFinished in %s",
		sf->indent,"", tim );
    }

    if (sf->show_progress)
	printf("%-*s\n",sf->progress_max_wd,buf);
    else
	printf("%s\n",buf);
    fflush(stdout);
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////                     AnalyseFT()                 ///////////////
///////////////////////////////////////////////////////////////////////////////

enumFileType AnalyseFT ( File_t * f )
{
    ASSERT(f);

    TRACE("AnalyseFT(%p) fd=%d, split=%d\n",f,GetFD(f),IsFileSplitted(f));

    if (!IsFileOpen(f))
    {
	TRACELINE;
	f->ftype = FT_UNKNOWN;

	if ( !f->is_reading )
	    return f->ftype;

	ccp name = strrchr(f->fname,'/');
	if (!name)
	    return f->ftype;

	enum { IS_NONE, IS_ID6, IS_INDEX, IS_SLOT } mode = IS_NONE;
	char id6[7];

	ulong idx = 0;
	name++;
	if ( strlen(name) == 6 )
	{
	    TRACELINE;
	    // maybe an id6
	    int i;
	    for ( i = 0; i < 6; i++ )
		id6[i] = toupper(name[i]);
	    id6[6] = 0;
	    if (CheckID6(id6))
		mode = IS_ID6;
	}

	if ( mode == IS_NONE )
	{
	    TRACELINE;
	    const bool is_slot = *name == '#';
	    ccp start = name + is_slot;
	    char * end;
	    idx = strtoul(start,&end,10);
	    if ( end > start && !*end )
		mode = is_slot ? IS_SLOT : IS_INDEX;
	    else
		return f->ftype;
	}

	TRACELINE;
	ASSERT( mode != IS_NONE );

	// try open ..
	char fname[PATH_MAX];
	int max = name - f->fname;
	if ( max > sizeof(fname) )
	    max = sizeof(fname);
	memcpy(fname,f->fname,max);
	fname[max-1] = 0;

	SuperFile_t sf;
	InitializeSF(&sf);
	sf.f.disable_errors = true;
	if (OpenFileModify(&sf.f,fname,IOM_IS_WBFS))
	    return f->ftype;

	AnalyseFT(&sf.f);
	bool ok = false;
	if ( sf.f.ftype & FT_ID_WBFS )
	{
	    TRACE(" - f2=WBFS\n");
	    WBFS_t wbfs;
	    InitializeWBFS(&wbfs);
	    if (!SetupWBFS(&wbfs,&sf,false,0))
	    {
		WDiscInfo_t wdisk;
		InitializeWDiscInfo(&wdisk);

		switch(mode)
		{
		    case IS_ID6:
			ok = !FindWDiscInfo(&wbfs,&wdisk,id6);
			break;

		    case IS_INDEX:
			if (!GetWDiscInfo(&wbfs,&wdisk,idx))
			{
			    memcpy(id6,wdisk.id6,6);
			    ok = true;
			}
			break;

		    case IS_SLOT:
			if (!GetWDiscInfoBySlot(&wbfs,&wdisk,idx))
			{
			    memcpy(id6,wdisk.id6,6);
			    ok = true;
			}
			break;

		    default: // suppress warning "IS_NONE not handled in switch"
			break;
		}
	    }
	    TRACELINE;
	    ResetWBFS(&wbfs);
	}

	if (ok)
	{
	    TRACE(" - WBFS/%s found\n",id6);
	    sf.f.disable_errors = f->disable_errors;
	    ASSERT(!sf.f.path);
	    sf.f.path = sf.f.fname;
	    sf.f.fname = f->fname;
	    f->fname = 0;
	    ResetFile(f,false);
	    memcpy(f,&sf.f,sizeof(*f));
	    memcpy(f->id6,id6,6);
	    memset(&sf.f,0,sizeof(sf.f));
	    TRACE(" - WBFS/fname = %s\n",f->fname);
	    TRACE(" - WBFS/path  = %s\n",f->path);
	    TRACE(" - WBFS/id6   = %s\n",f->id6);
	    f->ftype |= FT_A_ISO|FT_A_WDISC;
	}
	else
	    ResetSF(&sf,0);
	return f->ftype;
    }

    enumFileType ft = 0;

    if (S_ISREG(f->st.st_mode))
	ft |= FT_A_REGFILE;

    if (S_ISBLK(f->st.st_mode))
	ft |= FT_A_BLOCKDEV;

    if (f->seek_allowed)
	ft |= FT_A_SEEKABLE;

    if (S_ISDIR(f->st.st_mode))
	return f->ftype = ft | FT_ID_DIR;

    if (f->is_writing)
	ft |= FT_A_WRITING;

    if (!f->is_reading)
	return f->ftype;

    //----- now we must analyse the file contents

    // disable warnings
    const bool disable_errors = f->disable_errors;
    f->disable_errors = true;

    // read file header
    const int iso_magic_off = 0x18;
    const int iso_magic_len = 0x04;
    char buf1[HD_SECTOR_SIZE];
    char buf2[HD_SECTOR_SIZE];
    enumError err = ReadAtF(f,0,&buf1,sizeof(buf1));
    if (err)
	ft |= FT_ID_OTHER;
    else
    {
     #ifdef DEBUG
	{
	  ccp ptr = buf1;
	  int i;
	  for ( i = 0; i < 4; i++, ptr+=8 )
	  {
	    TRACE("ANALYSE/HEAD: \"%c%c%c%c%c%c%c%c\"  "
			"%02x %02x %02x %02x  %02x %02x %02x %02x\n",
		ptr[0]>=' ' && ptr[0]<0x7f ? ptr[0] : '.',
		ptr[1]>=' ' && ptr[1]<0x7f ? ptr[1] : '.',
		ptr[2]>=' ' && ptr[2]<0x7f ? ptr[2] : '.',
		ptr[3]>=' ' && ptr[3]<0x7f ? ptr[3] : '.',
		ptr[4]>=' ' && ptr[4]<0x7f ? ptr[4] : '.',
		ptr[5]>=' ' && ptr[5]<0x7f ? ptr[5] : '.',
		ptr[6]>=' ' && ptr[6]<0x7f ? ptr[6] : '.',
		ptr[7]>=' ' && ptr[7]<0x7f ? ptr[7] : '.',
		(u8)ptr[0], (u8)ptr[1], (u8)ptr[2], (u8)ptr[3],
		(u8)ptr[4], (u8)ptr[5], (u8)ptr[6], (u8)ptr[7] );
	  }
	}
     #endif // DEBUG

	ccp iso_ptr = buf1;
	WDF_Head_t wh;
	memcpy(&wh,buf1,sizeof(wh));
	ConvertToHostWH(&wh,&wh);

	err = AnalyseWH(f,&wh,false);
	if ( err != ERR_NO_WDF )
	    ft |= FT_A_WDF;

	if (!err)
	{
	    TRACE(" - WDF found -> load first chunk\n");
	    ft |= FT_A_WDF;
	    iso_ptr += sizeof(WDF_Head_t);
	    if ( f->seek_allowed
		&& !ReadAtF(f,wh.chunk_off,&buf2,WDF_MAGIC_SIZE+sizeof(WDF_Chunk_t))
		&& !memcmp(buf2,WDF_MAGIC,WDF_MAGIC_SIZE) )
	    {
		TRACE(" - WDF chunk loaded\n");
		WDF_Chunk_t *wc = (WDF_Chunk_t*)(buf2+WDF_MAGIC_SIZE);
		ConvertToHostWC(wc,wc);
		if ( wh.split_file_index == wc->split_file_index
		    && wc->data_size >= 6
		    && !ReadAtF(f,wc->data_off,&buf2,iso_magic_off+iso_magic_len) )
		{
		    TRACE(" - %d bytes of first chunk loaded\n",
				iso_magic_off + iso_magic_len );
		    iso_ptr = buf2;
		}
	    }
	}

	TRACE("ISO ID6+MAGIC:  \"%c%c%c%c%c%c\"    %02x %02x %02x %02x %02x %02x / %08x\n",
		iso_ptr[0]>=' ' && iso_ptr[0]<0x7f ? iso_ptr[0] : '.',
		iso_ptr[1]>=' ' && iso_ptr[1]<0x7f ? iso_ptr[1] : '.',
		iso_ptr[2]>=' ' && iso_ptr[2]<0x7f ? iso_ptr[2] : '.',
		iso_ptr[3]>=' ' && iso_ptr[3]<0x7f ? iso_ptr[3] : '.',
		iso_ptr[4]>=' ' && iso_ptr[4]<0x7f ? iso_ptr[4] : '.',
		iso_ptr[5]>=' ' && iso_ptr[5]<0x7f ? iso_ptr[5] : '.',
		(u8)iso_ptr[0], (u8)iso_ptr[1], (u8)iso_ptr[2],
		(u8)iso_ptr[3], (u8)iso_ptr[4], (u8)iso_ptr[5],
		*(u32*)(iso_ptr + iso_magic_off) );

	if (!memcmp(iso_ptr,"WBFS",4))
	{
	    WBFS_t wbfs;
	    InitializeWBFS(&wbfs);
	    if (!OpenWBFS(&wbfs,f->fname,false))
	    {
		ft |= FT_ID_WBFS;
		if ( wbfs.used_discs == 1 )
		{
		    WDiscInfo_t dinfo;
		    InitializeWDiscInfo(&dinfo);
		    if (!GetWDiscInfo(&wbfs,&dinfo,0))
			memcpy(f->id6,dinfo.id6,6);
		    ResetWDiscInfo(&dinfo);
		}
	    }
	    ResetWBFS(&wbfs);
	}
	else if (CheckID6(iso_ptr)
		&& (u8)iso_ptr[iso_magic_off+0] == 0x5d
		&& (u8)iso_ptr[iso_magic_off+1] == 0x1c
		&& (u8)iso_ptr[iso_magic_off+2] == 0x9e
		&& (u8)iso_ptr[iso_magic_off+3] == 0xa3 )
	{
	    ft |= FT_ID_ISO|FT_A_ISO;
	    memcpy(f->id6,iso_ptr,6);
	    f->id6[6] = 0;
	    if ( f->st.st_size < ISO_SPLIT_DETECT_SIZE )
		SetupSplitFile(f,OFT_PLAIN,0);
	}
	else
	    ft |= FT_ID_OTHER;
    }
    TRACE("ANALYSE FILETYPE: %04x [%s]\n",ft,f->id6);

    // restore warnings
    f->disable_errors = disable_errors;

    return f->ftype = ft;
}

///////////////////////////////////////////////////////////////////////////////

enumError XPrintErrorFT ( XPARM File_t * f, enumFileType err_mask )
{
    ASSERT(f);
    if ( f->ftype == FT_UNKNOWN )
	AnalyseFT(f);

    enumError stat = ERR_OK;
    enumFileType  and_mask = err_mask &  f->ftype;
    enumFileType nand_mask = err_mask & ~f->ftype;
    TRACE("PRINT FILETYPE ERROR: ft=%04x mask=%04x -> %04x,%04x\n",
		f->ftype, err_mask, and_mask, nand_mask );

    if ( ( f->split_f ? f->split_f[0]->fd : f->fd ) == -1 )
	stat = PrintError( XERROR0, ERR_READ_FAILED,
		"File is not open: %s\n", f->fname );

    else if ( and_mask & FT_ID_DIR )
	stat = PrintError( XERROR0, ERR_WRONG_FILE_TYPE,
		"Is a directory: %s\n", f->fname );

    else if ( nand_mask & FT_A_SEEKABLE )
	stat = PrintError( XERROR0, ERR_WRONG_FILE_TYPE,
		"Wrong file type (not seekable): %s\n", f->fname );

    else if ( nand_mask & (FT_A_REGFILE|FT_A_BLOCKDEV) )
	stat = PrintError( XERROR0, ERR_WRONG_FILE_TYPE,
		"Wrong file type: %s\n", f->fname );

    else if ( nand_mask & FT_ID_WBFS )
	stat = PrintError( XERROR0, ERR_WRONG_FILE_TYPE,
		"Not a WBFS: %s\n", f->fname );

    else if ( nand_mask & FT_ID_ISO || nand_mask & FT_A_ISO )
	stat = PrintError( XERROR0, ERR_WRONG_FILE_TYPE,
		"Not a ISO image: %s\n", f->fname );

    else if ( nand_mask & FT_A_WDF )
	stat = PrintError( XERROR0, ERR_WRONG_FILE_TYPE,
		"Not a WDF: %s\n", f->fname );

    f->last_error = stat;
    if ( f->max_error < stat )
	f->max_error = stat;

    return stat;
}

///////////////////////////////////////////////////////////////////////////////

ccp GetNameFT ( enumFileType ftype, int ignore )
{
    switch ( ftype & FT__ID_MASK )
    {
	case FT_UNKNOWN:
	    return ignore ? 0 : "NO-FILE";

	case FT_ID_DIR:
	    return ignore > 1 ? 0 : "DIR";
	    break;

	case FT_ID_WBFS:
	    return ftype & FT_A_WDISC
			? "WBFS/"
			: ignore > 1
				? 0
				: ftype & FT_A_WDF
					? "WDF+WBFS"
					: "WBFS";

	case FT_ID_ISO:
	    return ftype & FT_A_WDF ? "WDF+ISO" : "ISO";
	    break;

	default:
	    return ignore > 1
			? 0
			: ftype & FT_A_WDF
				? "WDF"
				: "OTHER";
    }
}

///////////////////////////////////////////////////////////////////////////////

enumOFT GetOFT ( SuperFile_t * sf )
{
    ASSERT(sf);
    return sf->wbfs
		? OFT_WBFS
		: sf->wc
			? OFT_WDF
			: OFT_PLAIN;
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////                    copy functions               ///////////////
///////////////////////////////////////////////////////////////////////////////

enumError CopySF ( SuperFile_t * in, SuperFile_t * out, u32 psel )
{
    ASSERT(in);
    ASSERT(out);
    TRACE("---\n");
    TRACE("+++ CopySF(%d->%d,%d) +++\n",GetFD(&in->f),GetFD(&out->f),psel);

    if (out->wbfs)
	return CopyToWBFS(in,out,psel);

    if ( psel != WHOLE_DISC )
    {
	wiidisc_t * disc = wd_open_disc(WrapperReadSF,in);

	if (disc)
	{
	    TRACELINE;
	    SetSizeSF(out,in->file_size);
	    wd_build_disc_usage(disc,psel,wdisc_usage_tab);

	    // write an empty disc header -> makes renaming easier
	    static char disc_header[0x60] = {0};
	    enumError err = WriteSF(out,0,disc_header,sizeof(disc_header));
	    if (err)
		return err;

	    int idx;
	    u64 pr_done = 0, pr_total = 0;
	    if ( out->show_progress )
	    {
		for ( idx = 0; idx < sizeof(wdisc_usage_tab); idx++ )
		    if (wdisc_usage_tab[idx])
			pr_total++;
		PrintProgressSF(0,pr_total,out);
	    }

	    for ( idx = 0; idx < sizeof(wdisc_usage_tab); idx++ )
	    {
		if (wdisc_usage_tab[idx])
		{
		    if ( SIGINT_level > 1 )
			return ERR_INTERRUPT;

		    ASSERT( sizeof(iobuf) >= WII_SECTOR_SIZE );
		    off_t off = (off_t)WII_SECTOR_SIZE * idx;
		    err = ReadSF(in,off,iobuf,WII_SECTOR_SIZE);
		    if (err)
			return err;

		    if ( psel != ALL_PARTITIONS && off == WII_PART_INFO_OFF )
		    {
			// [2do] ? rewrite code 
			wd_fix_partition_table(disc,psel,(u8*)iobuf);
		    }

		    err = WriteSparseSF(out,off,iobuf,WII_SECTOR_SIZE);
		    if (err)
			return err;

		    if ( out->show_progress )
			PrintProgressSF(++pr_done,pr_total,out);

		}
	    }
	    wd_close_disc(disc);
	    if ( out->show_progress || out->show_summary )
		PrintSummarySF(out);
	    return ERR_OK;
	}
    }

    return in->wbfs
		? CopyWBFSDisc(in,out)
		: in->wc
		    ? CopyWDF(in,out)
		    : CopyRaw(&in->f,out);
}

///////////////////////////////////////////////////////////////////////////////

enumError CopyRaw ( File_t * in, SuperFile_t * out )
{
    ASSERT(in);
    ASSERT(out);
    TRACE("---\n");
    TRACE("+++ CopyRaw(%d,%d) +++\n",in->fd,out->f.fd);

    const int align_mask = sizeof(u32)-1;
    ASSERT( (align_mask & align_mask+1) == 0 );

    off_t copy_size = in->st.st_size;
    off_t off       = 0;

    SetSizeSF(out,copy_size);

    if ( out->show_progress )
	PrintProgressSF(0,in->st.st_size,out);

    while ( copy_size > 0 )
    {
	if ( SIGINT_level > 1 )
	    return ERR_INTERRUPT;

	u32 size = sizeof(iobuf) < copy_size ? sizeof(iobuf) : (u32)copy_size;
	enumError err = ReadAtF(in,off,iobuf,size);
	if (err)
	    return err;

	WDF_Hole_t *ptr = (WDF_Hole_t*)iobuf;
	WDF_Hole_t *end = (WDF_Hole_t*)( iobuf + (size & ~3)); // exclude not aligned bytes

	while ( ptr < end )
	{
	    // skip holes
	    while ( ptr < end && !*ptr )
		ptr++;

	    WDF_Hole_t *data_beg = ptr;
	    WDF_Hole_t *data_end = data_beg;
	    while ( ptr < end )
	    {
		while ( ptr < end && *ptr )
		    ptr++;
		data_end = ptr;

		// skip holes
		while ( ptr < end && !*ptr )
		    ptr++;

		// accept only large holes
		if ( (ccp)ptr - (ccp)data_end >= WDF_MIN_HOLE_SIZE )
		    break;
	    }

	    off_t  woff = off+((ccp)data_beg-iobuf);
	    size_t wlen = (ccp)data_end - (ccp)data_beg;
	    err = WriteSF(out,woff,data_beg,wlen);
	    if (err)
		return err;

	    if ( out->show_progress )
		PrintProgressSF(woff+wlen,in->st.st_size,out);
	}

	ASSERT( align_mask == 3 );
	if ( size & align_mask )
	{
	    u32 size3 = size & align_mask;
	    ccp ptr1 = (ccp)end;
	    if ( ptr1[0] || size3 > 1 && ptr1[1] || size3 > 2 && ptr1[2] )
	    {
		off_t woff = off+((ccp)end-iobuf);
		err = WriteSF(out,woff,ptr1,size3);
		if (err)
		    return err;

		if ( out->show_progress )
		    PrintProgressSF(woff+size3,in->st.st_size,out);
	    }
	}

	copy_size -= size;
	off       += size;
    }

    if ( out->show_progress || out->show_summary )
	PrintSummarySF(out);

    return ERR_OK;
}

///////////////////////////////////////////////////////////////////////////////

enumError CopyWDF ( SuperFile_t * in, SuperFile_t * out )
{
    ASSERT(in);
    ASSERT(out);
    TRACE("---\n");
    TRACE("+++ CopyWDF(%d,%d) +++\n",in->f.fd,out->f.fd);

    if ( !in->wc )
	return ERROR0(ERR_INTERNAL,0);

    enumError err = SetSizeSF(out,in->file_size);
    if (err)
	return err;

    u64 pr_done = 0, pr_total = 0;
    if ( out->show_progress )
    {
	int i;
	for ( i = 0; i < in->wc_used; i++ )
	    pr_total += in->wc[i].data_size;
	PrintProgressSF(0,pr_total,out);
    }

    int i;
    for ( i = 0; i < in->wc_used; i++ )
    {
	WDF_Chunk_t *wc = in->wc + i;
	if ( wc->data_size )
	{
	    u64 dest_off = wc->file_pos;
	    u64 src_off  = wc->data_off;
	    u64 size64   = wc->data_size;

	    while ( size64 > 0 )
	    {
		if ( SIGINT_level > 1 )
		    return ERR_INTERRUPT;

		u32 size = sizeof(iobuf);
		if ( size > size64 )
		    size = (u32)size64;

		TRACE("cp #%02d %09llx .. %07x .. %09llx\n",i,src_off,size,dest_off);

		enumError err = ReadAtF(&in->f,src_off,iobuf,size);
		if (err)
		    return err;

		err = WriteSF(out,dest_off,iobuf,size);
		if (err)
		    return err;

		dest_off	+= size;
		src_off		+= size;
		size64		-= size;

		if ( out->show_progress )
		{
		    pr_done += size;
		    PrintProgressSF(pr_done,pr_total,out);
		}
	    }
	}
    }

    if ( out->show_progress || out->show_summary )
	PrintSummarySF(out);

    return ERR_OK;
}

///////////////////////////////////////////////////////////////////////////////

enumError CopyWBFSDisc ( SuperFile_t * in, SuperFile_t * out )
{
    ASSERT(in);
    ASSERT(out);
    TRACE("---\n");
    TRACE("+++ CopyWBFSDisc(%d,%d) +++\n",in->f.fd,out->f.fd);

    if ( !in->wbfs )
	return ERROR0(ERR_INTERNAL,0);

    ASSERT(in->wbfs->disc);
    ASSERT(in->wbfs->disc->header);
    u16 * wlba_tab = in->wbfs->disc->header->wlba_table;
    ASSERT(wlba_tab);

    wbfs_t * w = in->wbfs->wbfs;
    ASSERT(w);

    char * copybuf;
    if ( w->wbfs_sec_sz <= sizeof(iobuf) )
	 copybuf = iobuf;
    else
    {
	copybuf = malloc(w->wbfs_sec_sz);
	if (!copybuf)
	    OUT_OF_MEMORY;
    }
	
    SetSizeSF(out,in->file_size);
    enumError err = ERR_OK;

    u64 pr_done = 0, pr_total = 0;
    if ( out->show_progress )
    {
	int bl;
	for ( bl = 0; bl < w->n_wbfs_sec_per_disc; bl++ )
	    if (ntohs(wlba_tab[bl]))
		pr_total++;
	PrintProgressSF(0,pr_total,out);
    }

    int bl;
    for ( bl = 0; bl < w->n_wbfs_sec_per_disc; bl++ )
    {
	const u32 wlba = ntohs(wlba_tab[bl]);
	if (wlba)
	{
	    err = ReadAtF( &in->f, (off_t)w->wbfs_sec_sz * wlba,
				copybuf, w->wbfs_sec_sz );
	    if (err)
		goto abort;

	    err = WriteSF( out, (off_t)w->wbfs_sec_sz * bl,
				copybuf, w->wbfs_sec_sz );
	    if (err)
		goto abort;

	    if ( out->show_progress )
		PrintProgressSF(++pr_done,pr_total,out);
	}
    }

    if ( out->show_progress || out->show_summary )
	PrintSummarySF(out);

 abort:
    if ( copybuf != iobuf )
	free(copybuf);
    return err;
}

///////////////////////////////////////////////////////////////////////////////

enumError CopyToWBFS ( SuperFile_t * in, SuperFile_t * out, u32 psel )
{
    TRACE("---\n");
    TRACE("+++ CopyToWBFS(%d,%d,%u) +++\n",in->f.fd,out->f.fd,psel);

    if ( !out->wbfs )
	return ERROR0(ERR_INTERNAL,0);

    in->indent		= out->indent;
    in->show_progress	= out->show_progress;
    in->show_summary	= out->show_summary;
    in->show_msec	= out->show_msec;

    if ( AddWDisc(out->wbfs,in,psel) > ERR_WARNING )
	return ERROR0(ERR_WBFS,"Error while creating disc [%s] @%s\n",
			out->f.id6, out->f.fname );

    return ERR_OK;
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////                    diff functions               ///////////////
///////////////////////////////////////////////////////////////////////////////

static void PrintDiff ( off_t off, char *iobuf1, char *iobuf2, size_t iosize )
{
    while ( iosize > 0 )
    {
	if ( *iobuf1 != *iobuf2 )
	{
	    const size_t bl = off/WII_SECTOR_SIZE;
	    printf("! differ at ISO block #%06zu, off=%#09llx     \n", bl, off );
	    off_t old = off;
	    off = (bl+1) * (off_t)WII_SECTOR_SIZE;
	    const size_t skip = off - old;
	    if ( skip >= iosize )
		break;
	    iobuf1 += skip;
	    iobuf2 += skip;
	    iosize -= skip;
	}
	else
	{
	    off++;
	    iobuf1++;
	    iobuf2++;
	    iosize--;
	}
    }
}

///////////////////////////////////////////////////////////////////////////////

enumError DiffSF ( SuperFile_t * f1, SuperFile_t * f2, int long_count, u32 psel )
{
    ASSERT(f1);
    ASSERT(f2);
    ASSERT(IsFileOpen(&f1->f));
    ASSERT(IsFileOpen(&f2->f));
    ASSERT(f1->f.is_reading);
    ASSERT(f2->f.is_reading);

    f1->progress_verb = f2->progress_verb = "compared";

    if ( psel == WHOLE_DISC )
	return DiffRaw(f1,f2,long_count);

    wiidisc_t * d1 = wd_open_disc(WrapperReadSF,f1);
    if (!d1)
    {
	if (!f1->f.disable_errors)
	    ERROR0(ERR_CANT_OPEN,"Can't open disc image: %s\n",f1->f.fname);
	return ERR_CANT_OPEN;
    }

    wiidisc_t * d2 = wd_open_disc(WrapperReadSF,f2);
    if (!d2)
    {
	wd_close_disc(d1);
	if (!f2->f.disable_errors)
	    ERROR0(ERR_CANT_OPEN,"Can't open disc image: %s\n",f2->f.fname);
	return ERR_CANT_OPEN;
    }

    TRACELINE;
    wd_build_disc_usage(d1,psel,wdisc_usage_tab );
    wd_build_disc_usage(d2,psel,wdisc_usage_tab2);

    int idx;
    u64 pr_done = 0, pr_total = 0;
    bool differ = false;

    for ( idx = 0; idx < sizeof(wdisc_usage_tab); idx++ )
    {
	if ( wdisc_usage_tab[idx] != wdisc_usage_tab2[idx] )
	{
	    differ = true;
	    if (!long_count)
		goto abort;
	}
	if ( wdisc_usage_tab[idx] )
	    pr_total++;
    }

    if ( f2->show_progress )
	PrintProgressSF(0,pr_total,f2);

    ASSERT( sizeof(iobuf) >= 2*WII_SECTOR_SIZE );
    char *iobuf1 = iobuf, *iobuf2 = iobuf + WII_SECTOR_SIZE;

    for ( idx = 0; idx < sizeof(wdisc_usage_tab); idx++ )
    {
	if ( SIGINT_level > 1 )
	    return ERR_INTERRUPT;

	if (wdisc_usage_tab[idx])
	{
	    off_t off = (off_t)WII_SECTOR_SIZE * idx;
	    enumError err = ReadSF(f1,off,iobuf1,WII_SECTOR_SIZE);
	    if (err)
		return err;

	    err = ReadSF(f2,off,iobuf2,WII_SECTOR_SIZE);
	    if (err)
		return err;

	    if (memcmp(iobuf1,iobuf2,WII_SECTOR_SIZE))
	    {
		differ = true;
		if (long_count)
		    PrintDiff(off,iobuf1,iobuf2,WII_SECTOR_SIZE);
		if ( long_count < 2 )
		    break;
	    }

	    if ( f2->show_progress )
		PrintProgressSF(++pr_done,pr_total,f2);
	}
    }

    if ( f2->show_progress || f2->show_summary )
	PrintSummarySF(f2);

 abort:
    wd_close_disc(d1);
    wd_close_disc(d2);

    return differ ? ERR_DIFFER : ERR_OK;
}

///////////////////////////////////////////////////////////////////////////////

enumError DiffRaw ( SuperFile_t * f1, SuperFile_t * f2, int long_count )
{
    ASSERT(f1);
    ASSERT(f2);
    ASSERT(IsFileOpen(&f1->f));
    ASSERT(IsFileOpen(&f2->f));
    ASSERT(f1->f.is_reading);
    ASSERT(f2->f.is_reading);

    if ( f1->oft == OFT_WBFS || f2->oft == OFT_WBFS )
    {
	if ( f1->oft == OFT_WBFS )
	    f2->f.read_behind_eof = 2;
	if ( f2->oft == OFT_WBFS )
	    f1->f.read_behind_eof = 2;
    }
    else if ( f1->file_size != f2->file_size )
	return ERR_DIFFER;

    const size_t io_size = sizeof(iobuf)/2;
    ASSERT( (io_size&511) == 0 );
    char *iobuf1 = iobuf, *iobuf2 = iobuf + io_size;

    off_t off = 0;
    off_t total_size = f1->file_size;
    if ( total_size < f2->file_size )
	 total_size = f2->file_size;
    off_t size = total_size;

    if ( f2->show_progress )
	PrintProgressSF(0,total_size,f2);

    bool differ = false;
    while ( size > 0 )
    {
	const size_t cmp_size = io_size < size ? io_size : (size_t)size;

	enumError err;
	err = ReadSF(f1,off,iobuf1,cmp_size);
	if (err)
	    return err;
	err = ReadSF(f2,off,iobuf2,cmp_size);
	if (err)
	    return err;

	if (memcmp(iobuf1,iobuf2,cmp_size))
	{
	    differ = true;
	    if (long_count)
		PrintDiff(off,iobuf1,iobuf2,cmp_size);
	    if ( long_count < 2 )
		break;
	}

	off  += cmp_size;
	size -= cmp_size;

	if ( f2->show_progress )
	    PrintProgressSF(off,total_size,f2);
    }

    if ( f2->show_progress || f2->show_summary )
	PrintSummarySF(f2);

    return differ ? ERR_DIFFER : ERR_OK;
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////                  source iterator                ///////////////
///////////////////////////////////////////////////////////////////////////////

static StringField_t dir_done_list;
static StringField_t file_done_list;

//-----------------------------------------------------------------------------

void InitializeIterator ( Iterator_t * it )
{
    ASSERT(it);
    memset(it,0,sizeof(*it));
    InitializeStringField(&it->source_list);
}

//-----------------------------------------------------------------------------

void ResetIterator ( Iterator_t * it )
{
    ASSERT(it);
    ResetStringField(&it->source_list);
    memset(it,0,sizeof(*it));
}

//-----------------------------------------------------------------------------

static enumError SourceIteratorHelper
	( Iterator_t * it, ccp path, bool collect_fnames )
{
    ASSERT(it);
    ASSERT( it->func || collect_fnames );
    TRACE("SourceIteratorHelper(%p,%s,%d) depth=%d/%d\n",
		it, path, collect_fnames, it->depth, it->max_depth );

    if ( collect_fnames && path && *path == '-' && !path[1] )
    {
	TRACE(" - ADD STDIN\n");
	InsertStringField(&it->source_list,path,false);
	return ERR_OK;
    }

 #ifdef __CYGWIN__
    char goodpath[PATH_MAX];
    NormalizeFilename(goodpath,sizeof(goodpath),path);
    path = goodpath;
 #endif

    char buf[PATH_MAX+10];

    SuperFile_t sf;
    InitializeSF(&sf);
    enumError err = ERR_OK;

    //----- directory part

    if ( !stat(path,&sf.f.st) && S_ISDIR(sf.f.st.st_mode) )
    {
	if ( it->depth >= it->max_depth )
	{
	    ResetSF(&sf,0);
	    return ERR_OK;
	}

	ccp real_path = realpath(path,buf);
	if (!real_path)
	    real_path = path;

	if (InsertStringField(&dir_done_list,real_path,false))
	{
	    DIR * dir = opendir(path);
	    if (dir)
	    {
		char * bufend = buf+sizeof(buf);
		char * dest = StringCopyE(buf,bufend-1,path);
		if ( dest > buf && dest[-1] != '/' )
		    *dest++ = '/';

		it->depth++;

		const enumAction act_non_exist = it->act_non_exist;
		const enumAction act_non_iso   = it->act_non_iso;
		it->act_non_exist = it->act_non_iso = ACT_IGNORE;

		while ( err == ERR_OK && !SIGINT_level )
		{
		    struct dirent * dent = readdir(dir);
		    if (!dent)
			break;
		    ccp n = dent->d_name;
		    if ( n[0] != '.' )
		    {
			StringCopyE(dest,bufend,dent->d_name);
			err = SourceIteratorHelper(it,buf,collect_fnames);
		    }
		}
		closedir(dir);

		it->act_non_exist = act_non_exist;
		it->act_non_iso   = act_non_iso;
		it->depth--;
	    }
	}
	ResetSF(&sf,0);
	return err ? err : SIGINT_level ? ERR_INTERRUPT : ERR_OK;
    }

    //----- file part

    sf.f.disable_errors = it->act_non_exist != ACT_WARN;
    err = OpenSF(&sf,path,it->act_non_iso||it->act_wbfs>=ACT_ALLOW,it->open_modify);
    if ( err != ERR_OK && err != ERR_CANT_OPEN )
    {
    	ResetSF(&sf,0);
	return ERR_OK;
    }
    sf.f.disable_errors = false;

    ccp real_path = realpath( sf.f.path ? sf.f.path : sf.f.fname, buf );
    if (!real_path)
	real_path = path;
    it->real_path = real_path;

    if ( !IsFileOpen(&sf.f) )
    {
	if ( it->act_non_exist >= ACT_ALLOW )
	{
	    if (collect_fnames)
	    {
		InsertStringField(&it->source_list,sf.f.fname,false);
		err = ERR_OK;
	    }
	    else
		err = it->func(&sf,it);
	    ResetSF(&sf,0);
	    return err;
	}
	if ( err != ERR_CANT_OPEN && it->act_non_exist == ACT_WARN )
	    ERROR0(ERR_CANT_OPEN, "Can't open file X: %s\n",path);
	goto abort;
    }
    else if ( it->act_open < ACT_ALLOW
		&& sf.f.st.st_dev == it->open_dev
		&& sf.f.st.st_ino == it->open_ino )
    {
	if ( it->act_open == ACT_WARN )
	    printf(" - Ignore input=output: %s\n",path);
	ResetSF(&sf,0);
	return ERR_OK;
    }
    err = ERR_OK;

    if ( sf.f.ftype & FT_A_WDISC )
    {
	ccp slash = strrchr(path,'/');
	if (slash)
	{
	    StringCat2S(buf,sizeof(buf),it->real_path,slash);
	    real_path = buf;
	}
    }

    if (!sf.f.id6[0])
    {
	if ( sf.f.ftype & FT_ID_WBFS && it->act_wbfs >= ACT_ALLOW )
	{
	    if ( it->act_wbfs >= ACT_EXPAND )
	    {
		WBFS_t wbfs;
		InitializeWBFS(&wbfs);
		if (!SetupWBFS(&wbfs,&sf,false,0))
		{
		    const int max_disc = wbfs.wbfs->max_disc;
		    int fw, slot;
		    for ( slot = max_disc-1; slot >= 0
				&& !wbfs.wbfs->head->disc_table[slot]; slot-- )
			;
		    char fbuf[PATH_MAX+10];
		    snprintf(fbuf,sizeof(fbuf),"%u%n",slot,&fw);
		    char * dest = StringCopyS(fbuf,sizeof(fbuf)-10,path);
		    *dest++ = '/';

		    if ( collect_fnames )
		    {
			// fast scan of wbfs
			WDiscInfo_t wdisk;
			InitializeWDiscInfo(&wdisk);
			for ( slot = 0; slot < max_disc; slot++ )
			{
			    if ( !GetWDiscInfoBySlot(&wbfs,&wdisk,slot)
				&& !IsExcluded(wdisk.id6) )
			    {
				snprintf(dest,fbuf+sizeof(fbuf)-dest,"#%0*u",fw,slot);
				InsertStringField(&it->source_list,fbuf,false);
			    }
			}
			ResetWDiscInfo(&wdisk);
			ResetWBFS(&wbfs);
			ResetSF(&sf,0);
			return ERR_OK;
		    }

		    // make a copy of the disc table because we want close the wbfs
		    u8 discbuf[512];
		    u8 * disc_table = max_disc <= sizeof(discbuf)
					? discbuf
					: malloc(sizeof(discbuf));
		    memcpy(disc_table,wbfs.wbfs->head->disc_table,max_disc);

		    ResetWBFS(&wbfs);
		    ResetSF(&sf,0);

		    for ( slot = 0; slot < max_disc && err == ERR_OK; slot++ )
		    {
			if (disc_table[slot])
			{
			    snprintf(dest,fbuf+sizeof(fbuf)-dest,"#%0*u",fw,slot);
			    err = SourceIteratorHelper(it,fbuf,collect_fnames);
			}
		    }

		    if ( disc_table != discbuf )
			free(disc_table);
		}
		else
		    ResetSF(&sf,0);
		return err ? err : SIGINT_level ? ERR_INTERRUPT : ERR_OK;
	    }
	}
	else if ( it->act_non_iso < ACT_ALLOW )
	{
	    if ( it->act_non_iso == ACT_WARN )
		PrintErrorFT(&sf.f,FT_A_ISO);
	    goto abort;
	}
    }

    if ( InsertStringField(&file_done_list,real_path,false)
	&& ( !sf.f.id6[0] || !IsExcluded(sf.f.id6) ))
    {
	if (collect_fnames)
	{
	    InsertStringField(&it->source_list,sf.f.fname,false);
	    err = ERR_OK;
	}
	else
	    err = it->func(&sf,it);
    }

 abort:
    ResetSF(&sf,0);
    return err ? err : SIGINT_level ? ERR_INTERRUPT : ERR_OK;
}

//-----------------------------------------------------------------------------

enumError SourceIterator
	( Iterator_t * it, bool current_dir_is_default, bool collect_fnames )
{
    ASSERT(it);
    ASSERT( it->func || collect_fnames );
    TRACE("SourceIterator(%p) func=%p, act=%d,%d,%d\n",
		it, it->func,
		it->act_non_exist, it->act_non_iso, it->act_wbfs );

    if ( current_dir_is_default && !source_list.used && !recurse_list.used )
	AppendStringField(&source_list,".",false);

    if ( it->act_wbfs < it->act_non_iso )
	it->act_wbfs = it->act_non_iso;

    InitializeStringField(&dir_done_list);
    InitializeStringField(&file_done_list);

    ccp *ptr, *end;
    enumError err = ERR_OK;

    it->depth = 0;
    it->max_depth = 15;
    for ( ptr = recurse_list.field, end = ptr + recurse_list.used;
		err == ERR_OK && !SIGINT_level && ptr < end; ptr++ )
	err = SourceIteratorHelper(it,*ptr,collect_fnames);

    it->depth = 0;
    it->max_depth = 1;
    for ( ptr = source_list.field, end = ptr + source_list.used;
		err == ERR_OK && !SIGINT_level && ptr < end; ptr++ )
	err = SourceIteratorHelper(it,*ptr,collect_fnames);

    ResetStringField(&dir_done_list);
    ResetStringField(&file_done_list);

    return err;
}

//-----------------------------------------------------------------------------

enumError SourceIteratorCollected ( Iterator_t * it )
{
    ASSERT(it);
    ASSERT(it->func);
    TRACE("SourceIteratorCollected(%p) count=%d\n",it,it->source_list.used);

    ResetStringField(&file_done_list);

    enumError err = ERR_OK;
    int idx;
    for ( idx = 0; idx < it->source_list.used; idx++ )
    {
	it->source_index = idx;
	err = SourceIteratorHelper(it,it->source_list.field[idx],false);
    }
    return err;
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////                          END                    ///////////////
///////////////////////////////////////////////////////////////////////////////

