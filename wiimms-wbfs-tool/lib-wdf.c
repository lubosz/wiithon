
#define _GNU_SOURCE 1

#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <arpa/inet.h>

#include "debug.h"
#include "libwbfs.h"
#include "lib-wdf.h"
#include "wbfs-interface.h"

//
///////////////////////////////////////////////////////////////////////////////
///////////////                         data                    ///////////////
///////////////////////////////////////////////////////////////////////////////

#ifdef DEBUG
    #define WC_GROW_SIZE  10
#else
    #define WC_GROW_SIZE 500
#endif

//
///////////////////////////////////////////////////////////////////////////////
///////////////                      Setup data                 ///////////////
///////////////////////////////////////////////////////////////////////////////
// initialize WH

void InitializeWH ( WDF_Head_t * wh )
{
    ASSERT(wh);

    memset(wh,0,sizeof(*wh));
    memcpy(wh->magic,WDF_MAGIC,sizeof(wh->magic));

    wh->wdf_version = WDF_VERSION;
    wh->split_file_id = 0;
    wh->split_file_num_of = 1;
}

///////////////////////////////////////////////////////////////////////////////
// initialize the WC

void InitializeWC ( WDF_Chunk_t * wc, int n_elem )
{
    ASSERT(wc);
    ASSERT(n_elem>0);

    memset(wc,0,sizeof(*wc)*n_elem);
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////        convert data to network byte order       ///////////////
///////////////////////////////////////////////////////////////////////////////

static u64 hton64 ( u64 data )
{
    u64 result;
    ((u32*)&result)[0] = htonl( (u32)(data >> 32) );
    ((u32*)&result)[1] = htonl( (u32)data );
    return result;
}

#undef CONV32
#undef CONV64
#define CONV32(var) dest->var = htonl(src->var)
#define CONV64(var) dest->var = hton64(src->var)

///////////////////////////////////////////////////////////////////////////////

void ConvertToNetworkWH ( WDF_Head_t * dest, WDF_Head_t * src )
{
    ASSERT(dest);
    ASSERT(src);

    // initialize this again before exporting
    memcpy(dest->magic,WDF_MAGIC,sizeof(dest->magic));

    CONV32(wdf_version);
    CONV32(split_file_id);
    CONV32(split_file_index);
    CONV32(split_file_num_of);
    CONV64(file_size);
    CONV64(data_size);
    CONV32(chunk_split_file);
    CONV32(chunk_n);
    CONV64(chunk_off);
}

///////////////////////////////////////////////////////////////////////////////

void ConvertToNetworkWC ( WDF_Chunk_t * dest, WDF_Chunk_t * src )
{
    ASSERT(dest);
    ASSERT(src);

    CONV32(split_file_index);
    CONV64(file_pos);
    CONV64(data_off);
    CONV64(data_size);
}

///////////////////////////////////////////////////////////////////////////////

// clear defines
#undef CONV32
#undef CONV64

//
///////////////////////////////////////////////////////////////////////////////
///////////////         convert data to host byte order         ///////////////
///////////////////////////////////////////////////////////////////////////////

static u64 ntoh64 ( u64 data )
{
    return (u64)ntohl(((u32*)&data)[0]) << 32 | ntohl(((u32*)&data)[1]);
}

#undef CONV32
#undef CONV64
#define CONV32(var) dest->var = ntohl(src->var)
#define CONV64(var) dest->var = ntoh64(src->var)

///////////////////////////////////////////////////////////////////////////////

void ConvertToHostWH ( WDF_Head_t * dest, WDF_Head_t * src )
{
    ASSERT(dest);
    ASSERT(src);

    CONV32(wdf_version);
    CONV32(split_file_id);
    CONV32(split_file_index);
    CONV32(split_file_num_of);
    CONV64(file_size);
    CONV64(data_size);
    CONV32(chunk_split_file);
    CONV32(chunk_n);
    CONV64(chunk_off);
}

///////////////////////////////////////////////////////////////////////////////

void ConvertToHostWC ( WDF_Chunk_t * dest, WDF_Chunk_t * src )
{
    ASSERT(dest);
    ASSERT(src);

    CONV32(split_file_index);
    CONV64(file_pos);
    CONV64(data_off);
    CONV64(data_size);
}

///////////////////////////////////////////////////////////////////////////////

// clear defines
#undef CONV32
#undef CONV64

//
///////////////////////////////////////////////////////////////////////////////
///////////////                     WDF: helpers                ///////////////
///////////////////////////////////////////////////////////////////////////////
// chunk managment

WDF_Chunk_t * NeedChunkWDF ( SuperFile_t * sf, int index )
{
    ASSERT(sf);
    ASSERT( index >= 0 );
    ASSERT( index <= sf->wc_used );
    ASSERT( sf->wc_used <= sf->wc_size );

    if ( sf->wc_used == sf->wc_size )
    {
	// grow the field

	TRACE("#W# NeedChunkWDF() GROW %d ->%d [use3d=%d]\n",
		sf->wc_size, sf->wc_size+WC_GROW_SIZE, sf->wc_used );

	sf->wc_size += WC_GROW_SIZE;
	sf->wc = realloc(sf->wc,sf->wc_size*sizeof(*sf->wc));
	if (!sf->wc)
	    OUT_OF_MEMORY;
    }
    ASSERT( sf->wc_used < sf->wc_size );

    WDF_Chunk_t * wc = sf->wc + index;

    if ( index < sf->wc_used )
	memmove( wc+1, wc, (sf->wc_used-index)*sizeof(*wc) );

    sf->wc_used++;
    TRACE("#W# NeedChunkWDF() return %p [idx=%d/%d/%d]\n",
		wc, wc-sf->wc, sf->wc_used, sf->wc_size );
    InitializeWC(wc,1);
    return wc;
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////                       read WDF                  ///////////////
///////////////////////////////////////////////////////////////////////////////

enumError SetupReadWDF ( SuperFile_t * sf )
{
    TRACE("#W# SetupReadWDF(%p) wc=%p wbfs=%p\n",sf,sf->wc,sf->wbfs);
    if ( sf->wc || sf->wbfs )
	return ERR_OK;

    ASSERT(sf);
    FreeSF(sf);
    InitializeWH(&sf->wh); // reset data

    if ( sf->f.seek_allowed && sf->f.st.st_size < sizeof(WDF_Head_t) )
	return ERR_NO_WDF;

    WDF_Head_t wh;
    enumError stat = ReadAtF(&sf->f,0,&wh,sizeof(wh));
    if (stat)
	return stat;
    TRACE("#W#  - header read\n");

    //----- test header

    ConvertToHostWH(&wh,&wh);
    stat = AnalyseWH(&sf->f,&wh,true);
    if (stat)
	return stat;

    //----- test chunk table magic

    char magic[WDF_MAGIC_SIZE];
    stat = ReadAtF(&sf->f,wh.chunk_off,magic,sizeof(magic));
    if (stat)
	return stat;

    if (memcmp(magic,WDF_MAGIC,WDF_MAGIC_SIZE))
	goto invalid;

    const int chunk_tab_size = wh.chunk_n * sizeof(WDF_Chunk_t);
    WDF_Chunk_t *wc = malloc(chunk_tab_size);
    if (!wc)
	OUT_OF_MEMORY;

    stat = ReadAtF(&sf->f,wh.chunk_off+WDF_MAGIC_SIZE,wc,chunk_tab_size);
    if (stat)
	return stat;
    TRACE("#W#  - chunk table read\n");

    sf->wc = wc;
    sf->wc_used = sf->wc_size = wh.chunk_n;

    int idx;
    for ( idx = 0; idx < wh.chunk_n; idx++, wc++ )
    {
	ConvertToHostWC(wc,wc);
	if ( wc->split_file_index )
	    goto invalid;
	if ( idx && wc->file_pos < wc[-1].file_pos + wc[-1].data_size )
	    goto invalid;
    }
    TRACE("#W#  - chunk loop exits with ok\n");

    // check last chunk
    wc = sf->wc + sf->wc_used - 1;
    if ( wc->file_pos + wc->data_size != wh.file_size )
	    goto invalid;

    memcpy(&sf->wh,&wh,sizeof(sf->wh));
    sf->file_size	= sf->wh.file_size;
    sf->f.max_off	= sf->wh.chunk_off;
    sf->max_virt_off	= sf->wh.data_size;
    sf->oft		= OFT_WDF;

    TRACE("#W# WDF FOUND!\n");
    return ERR_OK;

 invalid:
    return ERROR0(ERR_WDF_INVALID,"Invalid WDF file\n");
}

///////////////////////////////////////////////////////////////////////////////

enumError ReadWDF ( SuperFile_t * sf, off_t off, void * buf, size_t count )
{
    ASSERT(sf);
    if (!sf->wc)
	return ReadAtF(&sf->f,off,buf,count);

    ASSERT(sf->wc);
    ASSERT(sf->wc_used);
    TRACE("#W# -----\n");
    TRACE(TRACE_RDWR_FORMAT, "#W# ReadWDF()",
		GetFD(&sf->f), GetFP(&sf->f), off, off+count, count, "" );

    if ( off + count > sf->wh.file_size )
    {
	if (!sf->f.read_behind_eof)
	{
	    if ( !sf->f.disable_errors )
		ERROR0( ERR_READ_FAILED, "Read behind eof [%c,%llx+%zx]: %s\n",
		    sf->f.fp ? 'S' : sf->f.fd != -1 ? 'F' : '-',
		    off, count, sf->f.fname );
	    return ERR_READ_FAILED;
	}

	const off_t max_read = sf->wh.file_size > off
					? sf->wh.file_size - off
					: 0;
	ASSERT( count > max_read );

	if ( sf->f.read_behind_eof == 1 )
	{
	    sf->f.read_behind_eof = 2;
	    if ( !sf->f.disable_errors )
		ERROR0( ERR_WARNING, "Read behind eof -> zero filled [%c,%llx+%zx]: %s\n",
		    sf->f.fp ? 'S' : sf->f.fd != -1 ? 'F' : '-',
		    off, count, sf->f.fname );
	}

	size_t fill_count = count - (size_t)max_read;
	count = (size_t)max_read;
	memset((char*)buf+count,0,fill_count);

	if (!count)
	    return ERR_OK;
    }

    // find chunk header
    WDF_Chunk_t * wc = sf->wc;
    const int used_m1 = sf->wc_used - 1;
    int beg = 0, end = used_m1;
    ASSERT( beg <= end );
    while ( beg < end )
    {
	int idx = (beg+end)/2;
	wc = sf->wc + idx;
	if ( off < wc->file_pos )
	    end = idx-1;
	else if ( idx < used_m1 && off >= wc[1].file_pos )
	    beg = idx + 1;
	else
	    beg = end = idx;
    }
    wc = sf->wc + beg;

    noTRACE("#W#  - FOUND #%03d: off=%09llx ds=%llx, off=%09llx\n",
	    beg, wc->file_pos, wc->data_size, off );
    ASSERT( off >= wc->file_pos );
    ASSERT( beg == used_m1 || off < wc[1].file_pos );

    char * dest = buf;
    while ( count > 0 )
    {
	noTRACE("#W# %d/%d count=%d off=%llx,%llx \n",
		beg, sf->wc_used, count, off, wc->file_pos );

	if ( off < wc->file_pos )
	{
	    const u64 max_size = wc->file_pos - off;
	    const u32 fill_size = max_size < count ? (u32)max_size : count;
	    TRACE("#W# >FILL %p +%8x = %p .. %x\n",
		    buf, dest-(ccp)buf, dest, fill_size );
	    memset(dest,0,fill_size);
	    count -= fill_size;
	    off  += fill_size;
	    dest += fill_size;
	    if (!count)
		break;
	}

	if ( off >= wc->file_pos && off < wc->file_pos + wc->data_size )
	{
	    // we want a part of this
	    const u64 delta     = off - wc->file_pos;
	    const u64 max_size  = wc->data_size - delta;
	    const u32 read_size = max_size < count ? (u32)max_size : count;
	    TRACE("#W# >READ %p +%8x = %p .. %x <- %10llx\n",
		    buf, dest-(ccp)buf, dest, read_size, wc->data_off+delta );
	    int stat = ReadAtF(&sf->f,wc->data_off+delta,dest,read_size);
	    if (stat)
		return stat;
	    count -= read_size;
	    off  += read_size;
	    dest += read_size;
	    if (!count)
		break;
	}

	wc++;
	if ( ++beg >= sf->wc_used )
	{
	    TRACE("ERR_WDF_INVALID\n");
	    return ERR_WDF_INVALID;
	}
    }

    TRACE("#W#  - done, dest = %p\n",dest);
    return ERR_OK;
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////                     write WDF                   ///////////////
///////////////////////////////////////////////////////////////////////////////

enumError SetupWriteWDF ( SuperFile_t * sf )
{
    ASSERT(sf);
    TRACE("#W# SetupWriteWDF(%p)\n",sf);

    InitializeWH(&sf->wh);
    sf->oft = OFT_WDF;
    sf->max_virt_off = 0;
    sf->wh.magic[0] = '-'; // write a 'not complete' indicator
    enumError stat = WriteAtF(&sf->f,0,&sf->wh,sizeof(WDF_Head_t));

    sf->wc_used = 0;

    // first chunk with file_pos=0, count=0, off=x
    WDF_Chunk_t * wc = NeedChunkWDF(sf,0);
    wc->data_off = sf->f.file_off;

    TRACE("#W# SetupWriteWDF() returns %d\n",stat);
    return stat;
}

///////////////////////////////////////////////////////////////////////////////

enumError TermWriteWDF ( SuperFile_t * sf )
{
    ASSERT(sf);
    ASSERT(sf->wc);
    TRACE("#W# TermWriteWDF(%p)\n",sf);

    WDF_Chunk_t * wc = sf->wc + sf->wc_used - 1;
    const u64 last_pos = wc->file_pos + wc->data_size;
    if ( sf->file_size < last_pos )
    {
	// correction for double layer discs [2do]
	sf->file_size = last_pos;
    }
    else if ( sf->file_size > last_pos )
    {
	wc = NeedChunkWDF(sf,sf->wc_used);
	wc->file_pos = sf->file_size;
	wc->data_off = sf->f.max_off;
    }

    int i = 0;
    for ( wc = sf->wc; i < sf->wc_used; i++, wc++ )
	ConvertToNetworkWC(wc,wc);

    sf->wh.chunk_n	= sf->wc_used;
    sf->wh.chunk_off	= sf->f.max_off;
    sf->wh.file_size	= sf->file_size;
    sf->wh.data_size	= sf->wh.chunk_off - sizeof(WDF_Head_t);

    WDF_Head_t wh;
    ConvertToNetworkWH(&wh,&sf->wh);

    // write the magic behind the data (use header)
    int stat = WriteAtF( &sf->f, sf->wh.chunk_off, &wh.magic, sizeof(wh.magic) );

    // write the chunk table
    if (!stat)
	stat = WriteF( &sf->f, sf->wc, sf->wh.chunk_n*sizeof(*sf->wc) );

    // write the header
    if (!stat)
	stat = WriteAtF( &sf->f, 0, &wh, sizeof(wh) );

    TRACE("#W# TermWriteWDF() returns %d\n",stat);
    return stat;
}

///////////////////////////////////////////////////////////////////////////////

enumError WriteWDF ( SuperFile_t * sf, off_t off, const void * buf, size_t count )
{
    ASSERT(sf);
    if (!sf->wc)
	return WriteAtF(&sf->f,off,buf,count);

    TRACE("#W# -----\n");
    TRACE(TRACE_RDWR_FORMAT, "#W# WriteWDF()",
		GetFD(&sf->f), GetFP(&sf->f), off, off+count, count,
		off < sf->max_virt_off ? " <" : "" );
    TRACE(" - off = %llx,%llx\n",sf->f.file_off,sf->f.max_off);

    if (!count)
	return ERR_OK;

    // adjust the file size
    const off_t data_end = off + count;
    if ( sf->file_size < data_end )
	sf->file_size = data_end;

    ASSERT( sf->wc_used > 0 );
    const int used_m1 = sf->wc_used - 1;

    if ( off >= sf->max_virt_off )
    {
	// SPECIAL CASE:
	//    the current virtual file will be extended
	//    -> no nned to search chunks

	if ( off == sf->max_virt_off )
	{
	    // maybe an extend of the last chunk -> get the last chunk
	    WDF_Chunk_t * wc = sf->wc + used_m1;
	    if ( wc->data_off + wc->data_size == sf->f.max_off )
	    {
		// adjust max_virt_off
		sf->max_virt_off = off + count;

		// yes, it is the last written chunk
		const enumError stat
		    = WriteAtF(&sf->f,wc->data_off+wc->data_size,buf,count);
		wc->data_size += count;
		return stat;
	    }
	}

	// adjust max_virt_off
	sf->max_virt_off = off + count;

	// create a new chunk at end of file
	WDF_Chunk_t * wc = NeedChunkWDF(sf,sf->wc_used);
	wc->file_pos  = off;
	wc->data_off  = sf->f.max_off;
	wc->data_size = count;
	return WriteAtF(&sf->f,wc->data_off,buf,count);
    }

    // search chunk header with a binary search
    WDF_Chunk_t * wc = sf->wc;
    int beg = 0, end = used_m1;
    ASSERT( beg <= end );
    while ( beg < end )
    {
	int idx = (beg+end)/2;
	wc = sf->wc + idx;
	if ( off < wc->file_pos )
	    end = idx-1;
	else if ( idx < used_m1 && off >= wc[1].file_pos )
	    beg = idx + 1;
	else
	    beg = end = idx;
    }
    wc = sf->wc + beg;

    TRACE("#W#  - FOUND #%03d: off=%09llx ds=%llx, off=%09llx\n",
	    beg, wc->file_pos, wc->data_size, off );
    ASSERT( off >= wc->file_pos );
    ASSERT( beg == used_m1 || off < wc[1].file_pos );

    ccp src = buf;
    while ( count > 0 )
    {
	TRACE("#W# %d/%d count=%d off=%llx,%llx \n",
		beg, sf->wc_used, count, off, wc->file_pos );

	if ( off < wc->file_pos )
	{
	    const u64 max_size = wc->file_pos - off;
	    const u32 wr_size = max_size < count ? (u32)max_size : count;

	    TRACE("#W# >CREATE#%02d    %p +%8tx = %10llx .. +%4x\n",
			beg, buf, src-(ccp)buf, off, wr_size );

	    // create a new chunk
	    wc = NeedChunkWDF(sf,beg);
	    wc->file_pos   = off;
	    wc->data_off  = sf->f.max_off;
	    wc->data_size = wr_size;

	    // write data & return
	    const enumError stat = WriteAtF(&sf->f,wc->data_off,src,wr_size);
	    if (stat)
		return stat;

	    wc++;
	    beg++;

	    count -= wr_size;
	    off  += wr_size;
	    src += wr_size;
	    if (!count)
		break;
	}

	if ( off >= wc->file_pos && off < wc->file_pos + wc->data_size )
	{
	    // we want a part of this
	    const u64 delta     = off - wc->file_pos;
	    const u64 max_size  = wc->data_size - delta;
	    const u32 wr_size = max_size < count ? (u32)max_size : count;

	    TRACE("#W# >OVERWRITE#%02d %p +%8tx = %10llx .. +%4x, delta=%lld\n",
			beg, buf, src-(ccp)buf, off, wr_size, delta );

	    const enumError stat = WriteAtF(&sf->f,wc->data_off+delta,src,wr_size);
	    if (stat)
		return stat;

	    count -= wr_size;
	    off  += wr_size;
	    src += wr_size;
	    if (!count)
		break;
	}

	wc++;
	if ( ++beg >= sf->wc_used )
	    return WriteWDF(sf,off,src,count);
    }
    return ERR_OK;
}

///////////////////////////////////////////////////////////////////////////////

enumError WriteSparseWDF ( SuperFile_t * sf, off_t off, const void * buf, size_t count )
{
    ASSERT(sf);
    if (!sf->wc)
	return WriteSparseAtF(&sf->f,off,buf,count);

    if ( off < sf->max_virt_off )
    {
	// disable sparse check for already existing file areas
	const off_t max_overlap = sf->max_virt_off - off;
	const size_t overlap = count < max_overlap ? count : (size_t) max_overlap;
	const enumError err = WriteWDF(sf,off,buf,overlap);
	count -= overlap;
	if ( err || !count )
	    return err;
	off += overlap;
	buf = (char*)buf + overlap;
    }

    if ( off & 3 || count & 3 )
    {
	// sparse checking is only done with u32 aligned data
	return WriteWDF(sf,off,buf,count);
    }

    TRACE("#W# -----\n");
    TRACE(TRACE_RDWR_FORMAT, "#W# WriteSparseWDF()",
		GetFD(&sf->f), GetFP(&sf->f), off, off+count, count,
		off < sf->max_virt_off ? " <" : "" );

    if (!count)
	return ERR_OK;

    const off_t data_end = off + count;
    if ( sf->file_size < data_end )
	sf->file_size = data_end;

    ccp start = (ccp)buf;
    WDF_Hole_t *ptr = (WDF_Hole_t*)start;
    WDF_Hole_t *end = (WDF_Hole_t*)(start+count);

    // skip leading spaces
    while ( ptr < end && !*ptr )
	ptr++;

    // main loop
    while ( ptr < end )
    {
	// adjust data
	u32 skip_count = (ccp)ptr - start;
	off  += skip_count;
	count -= skip_count;
	ASSERT(count>0);
	start = (ccp)ptr;

	WDF_Hole_t * data_end = ptr;
	while ( ptr < end )
	{
	    // address data block
	    while ( ptr < end && *ptr )
		ptr++;
	    data_end = ptr;

	    // address trailing zero block
	    while ( ptr < end && !*ptr )
		ptr++;

	    // break if zero block is large enough
	    if ( (ccp)ptr - (ccp)data_end >= WDF_MIN_HOLE_SIZE )
		break;
	}

	// write data block
	const u32 chunk_len = (ccp)data_end - start;
	const int stat = WriteWDF(sf,off,start,chunk_len);
	if (stat)
	    return stat;
    }

    return ERR_OK;
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////                          END                    ///////////////
///////////////////////////////////////////////////////////////////////////////

