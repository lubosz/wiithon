// Copyright 2009 Kwiirk
// Modified by Wiimm, 2009
// Licensed under the terms of the GNU GPL, version 2
// http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt

#include "libwbfs.h"
#include <errno.h>

#ifndef WIN32
#define likely(x)       __builtin_expect(!!(x), 1)
#define unlikely(x)     __builtin_expect(!!(x), 0)
#else
#define likely(x)		(x)
#define unlikely(x)		(x)
#endif

#define WBFS_ERROR(x) do {wbfs_error(x);goto error;}while(0)
#define ALIGN_LBA(x) (((x)+p->hd_sec_sz-1)&(~(p->hd_sec_sz-1)))

static int force_mode=0;

void wbfs_set_force_mode(int force)
{
    force_mode = force;
}

static u8 size_to_shift(u32 size)
{
    u8 ret = 0;
    while (size)
    {
	ret++;
	size>>=1;
    }
    return ret-1;
}

#define read_le32_unaligned(x) ((x)[0]|((x)[1]<<8)|((x)[2]<<16)|((x)[3]<<24))

void wbfs_sync(wbfs_t*p);

wbfs_t*wbfs_open_hd(
    rw_sector_callback_t read_hdsector,
    rw_sector_callback_t write_hdsector,
    void *callback_data,
    int hd_sector_size,
    int num_hd_sector __attribute((unused)),
    int reset)
{ // [codeview]
    int i
#ifdef UNUSED_STUFF
    = num_hd_sector
#endif
      , ret;
    u8 *ptr,*tmp_buffer = wbfs_ioalloc(hd_sector_size);
    u8 part_table[16*4];
    ret = read_hdsector(callback_data,0,1,tmp_buffer);
    if (ret)
	return 0;
    //find wbfs partition
    wbfs_memcpy(part_table,tmp_buffer+0x1be,16*4);
    ptr = part_table;
    for (i=0; i<4; i++,ptr+=16)
    {
	u32 part_lba = read_le32_unaligned(ptr+0x8);
	wbfs_head_t *head = (wbfs_head_t *)tmp_buffer;
#ifdef UNUSED_STUFF
	ret =
#endif
	    read_hdsector(callback_data,part_lba,1,tmp_buffer);
	// verify there is the magic.
	if (head->magic == wbfs_htonl(WBFS_MAGIC))
	{
	    wbfs_t *p = wbfs_open_partition(	read_hdsector,
					     write_hdsector,
					     callback_data,
					     hd_sector_size,
					     0,
					     part_lba,reset
					   );
	    return p;
	}
    }
    if (reset)// XXX make a empty hd partition..
    {
    }
    return 0;
}

//
///////////////////////////////////////////////////////////////////////////////

wbfs_t * wbfs_open_partition
		( rw_sector_callback_t read_hdsector,
		  rw_sector_callback_t write_hdsector,
		  void *callback_data,
		  int hd_sector_size,
		  int num_hd_sector,
		  u32 part_lba,
		  int reset )
{
    //----- alloc mem

    wbfs_t	*p	= wbfs_malloc(sizeof(wbfs_t));
    wbfs_head_t *head	= wbfs_ioalloc(hd_sector_size?hd_sector_size:512);
    if ( !p || !head )
	OUT_OF_MEMORY;

    //----- store head and parameters

    p->head		= head;
    p->part_lba		= part_lba;
    p->read_hdsector	= read_hdsector;
    p->write_hdsector	= write_hdsector;
    p->callback_data	= callback_data;

    //----- setup some wii constants

    p->wii_sec_sz		= WII_SECTOR_SIZE;
    p->wii_sec_sz_s		= size_to_shift(WII_SECTOR_SIZE);
    p->n_wii_sec_per_disc	= WII_SECTORS_DOUBLE_LAYER;

    //----- init/load partition header

    if (reset)
    {
	// if reset: make some calculations and store the result in the header

	wbfs_memset(head,0,hd_sector_size);
	head->magic		= wbfs_htonl(WBFS_MAGIC);
	head->wbfs_version	= WBFS_VERSION;
	head->hd_sec_sz_s	= size_to_shift(hd_sector_size);
	hd_sector_size		= 1 << head->hd_sec_sz_s;
	head->n_hd_sec		= wbfs_htonl(num_hd_sector);

	// ***  this is the old calculation with rounding error
	//p->n_wii_sec		= (num_hd_sector/WII_SECTOR_SIZE)*hd_sector_size;
	// ***  but *here* we can/should use the correct one
	p->n_wii_sec		= num_hd_sector / ( WII_SECTOR_SIZE / hd_sector_size );

	// choose minimum wblk_sz that fits this partition size
	// the max value chooses the maximal supported partition size
	int sz_s;
	for ( sz_s = 6; sz_s < 11; sz_s++ )
	{
	    // ensure that wbfs_sec_sz is big enough to address every blocks using 16 bits
	    if ( p->n_wii_sec < (1<<16) * (1<<sz_s) )
		break;
	}
	head->wbfs_sec_sz_s = sz_s + p->wii_sec_sz_s;
    }
    else
    {
	// no reset: just load header

	read_hdsector(callback_data,p->part_lba,1,head);
    }

    //----- validation tests

    if ( head->magic != wbfs_htonl(WBFS_MAGIC) )
	WBFS_ERROR("bad magic");

    if ( !force_mode
		&& hd_sector_size
		&& head->hd_sec_sz_s != size_to_shift(hd_sector_size))
	WBFS_ERROR("hd sector size doesn't match");

    if ( !force_mode
		&& num_hd_sector
		&& head->n_hd_sec != wbfs_htonl(num_hd_sector) )
	WBFS_ERROR("hd num sector doesn't match");

    //----- transfer head info to main data structure

    p->hd_sec_sz	= 1 << head->hd_sec_sz_s;
    p->hd_sec_sz_s	= head->hd_sec_sz_s;
    p->n_hd_sec		= wbfs_ntohl( head->n_hd_sec );

    //----- base calculations

    // ***********************************************************************
    // *** This calculation has a rounding bug. But we must leave it here  ***
    // *** because 'n_wbfs_sec' -> 'freeblks_lba' are based in this value. ***
    // ***********************************************************************
    p->n_wii_sec	= ( p->n_hd_sec / p->wii_sec_sz ) * p->hd_sec_sz;

    p->wbfs_sec_sz_s	= head->wbfs_sec_sz_s;
    p->wbfs_sec_sz	= 1 << p->wbfs_sec_sz_s;
    p->n_wbfs_sec	= p->n_wii_sec >> ( p->wbfs_sec_sz_s - p->wii_sec_sz_s );
    p->n_wbfs_sec_per_disc
			= p->n_wii_sec_per_disc >> ( p->wbfs_sec_sz_s - p->wii_sec_sz_s );
    p->disc_info_sz	= ALIGN_LBA( sizeof(wbfs_disc_info_t) + p->n_wbfs_sec_per_disc*2 );

    //----- 'free blocks table' calculations

    const u32 fb_memsize= ALIGN_LBA(p->n_wbfs_sec/8);	// memory size of 'freeblks'
    p->freeblks_lba	= ( p->wbfs_sec_sz - p->n_wbfs_sec / 8 ) >> p->hd_sec_sz_s;
    p->freeblks_lba_count
			= fb_memsize >> p->hd_sec_sz_s;

    //----- here we correct the previous wrong calulations

    p->n_wii_sec	= p->n_hd_sec / ( p->wii_sec_sz / p->hd_sec_sz );
    const u32 n_wbfs_sec= p->n_wii_sec >> ( p->wbfs_sec_sz_s - p->wii_sec_sz_s );
    p->n_wbfs_sec	= n_wbfs_sec < 0x10000 ? n_wbfs_sec : 0x10000;

    //----- calculate and fix the needed space for free blocks table

    p->freeblks_size4	= ( p->n_wbfs_sec-1 + 31 ) / 32;
    if ( p->freeblks_size4 > fb_memsize/4 )
    {
	// not enough memory to store complete free blocks table :(
	p->freeblks_size4 = fb_memsize/4;

	// fix the number of WBFS sectors too
	const u32 max_sec = p->freeblks_size4 * 32 + 1; // remember: 1 based
	if ( p->n_wbfs_sec > max_sec )
	     p->n_wbfs_sec = max_sec;
    }
    p->freeblks_mask	= ( 1ull << ( (p->n_wbfs_sec-1) & 31 )) - 1;

    //----- load/setup free block table

    if (!reset)
    {
	// table will alloc and read only if needed
	p->freeblks = 0;
    }
    else
    {
	// init with all free blocks
	p->freeblks = wbfs_ioalloc(fb_memsize);

	// fill complete array with zeros
	wbfs_memset(p->freeblks,0,fb_memsize);

	// fill used area with 0xff
	wbfs_memset(p->freeblks,0xff,p->freeblks_size4*4);

	// fix the last entry
	p->freeblks[p->freeblks_size4-1] = wbfs_htonl(p->freeblks_mask);
    }

    //----- calculate max_disc

    p->max_disc = ( p->freeblks_lba - 1 ) / ( p->disc_info_sz >> p->hd_sec_sz_s );
    if ( p->max_disc > p->hd_sec_sz - sizeof(wbfs_head_t) )
	 p->max_disc = p->hd_sec_sz - sizeof(wbfs_head_t);

    //----- etc

    p->tmp_buffer = wbfs_ioalloc(p->hd_sec_sz);
    p->n_disc_open = 0;
    if (reset)
	wbfs_sync(p);

    return p;

error:
    wbfs_free(p);
    wbfs_iofree(head);
    return 0;
}

///////////////////////////////////////////////////////////////////////////////

void wbfs_sync ( wbfs_t * p )
{
    // writes wbfs header and freeblks (if !=0) to hardisk

    if (p->write_hdsector)
    {
	p->write_hdsector ( p->callback_data, p->part_lba, 1, p->head );

	if (p->freeblks)
	    p->write_hdsector ( p->callback_data,
				p->part_lba + p->freeblks_lba,
				p->freeblks_lba_count,
				p->freeblks );
    }
}

///////////////////////////////////////////////////////////////////////////////

void wbfs_close ( wbfs_t * p )
{
    if (p->n_disc_open)
	WBFS_ERROR("trying to close wbfs while discs still open");

    wbfs_iofree(p->head);
    wbfs_iofree(p->tmp_buffer);
    if (p->freeblks)
	wbfs_iofree(p->freeblks);
    wbfs_free(p);

 error:
    return;
}

///////////////////////////////////////////////////////////////////////////////

wbfs_disc_t * wbfs_open_disc_by_id6 ( wbfs_t* p, u8 * discid )
{
    ASSERT(p);
    ASSERT(discid);
    const u32 disc_info_sz_lba = p->disc_info_sz >> p->hd_sec_sz_s;

    u32 slot;
    for ( slot = 0; slot < p->max_disc; slot++ )
    {
	if (p->head->disc_table[slot])
	{
	    p->read_hdsector(p->callback_data,
			     p->part_lba + 1 + slot * disc_info_sz_lba,
			     1, p->tmp_buffer );

	    if ( wbfs_memcmp(discid,p->tmp_buffer,6) == 0 )
		return wbfs_open_disc_by_slot(p,slot);
	}
    }
    return 0;
}

///////////////////////////////////////////////////////////////////////////////

wbfs_disc_t * wbfs_open_disc_by_slot ( wbfs_t * p, u32 slot )
{
    ASSERT(p);
    if ( slot >= p->max_disc || !p->head->disc_table[slot] )
	return 0;

    wbfs_disc_t * d = wbfs_malloc(sizeof(*d));
    if (!d)
	OUT_OF_MEMORY;
    d->p = p;
    d->slot = slot;
    d->header = wbfs_ioalloc(p->disc_info_sz);
    if (!d->header)
	OUT_OF_MEMORY;

    const u32 disc_info_sz_lba = p->disc_info_sz >> p->hd_sec_sz_s;
    p->read_hdsector (	p->callback_data,
			p->part_lba + 1 + slot * disc_info_sz_lba,
			disc_info_sz_lba,
			d->header );
    p->n_disc_open++;
    return d;
}

///////////////////////////////////////////////////////////////////////////////

void wbfs_sync_disc_header ( wbfs_disc_t * d )
{
    ASSERT(d);
    if ( !d || !d->p || !d->header )
	 return;

    const u32 disc_info_sz_lba = d->p->disc_info_sz >> d->p->hd_sec_sz_s;
    d->p->write_hdsector (
			d->p->callback_data,
			d->p->part_lba + 1 + d->slot * disc_info_sz_lba,
			disc_info_sz_lba,
			d->header );
}

///////////////////////////////////////////////////////////////////////////////

void wbfs_close_disc ( wbfs_disc_t * d )
{
    ASSERT(d);
    d->p->n_disc_open--;
    wbfs_iofree(d->header);
    wbfs_free(d);
}

///////////////////////////////////////////////////////////////////////////////

// offset is pointing 32bit words to address the whole dvd, although len is in bytes

int wbfs_disc_read ( wbfs_disc_t *d, u32 offset, u8 *data, u32 len )
{ // [codeview]

    wbfs_t *p = d->p;
    u16 wlba = offset>>(p->wbfs_sec_sz_s-2);
    u32 iwlba_shift = p->wbfs_sec_sz_s - p->hd_sec_sz_s;
    u32 lba_mask = (p->wbfs_sec_sz-1)>>(p->hd_sec_sz_s);
    u32 lba = (offset>>(p->hd_sec_sz_s-2))&lba_mask;
    u32 off = offset&((p->hd_sec_sz>>2)-1);
    u16 iwlba = wbfs_ntohs(d->header->wlba_table[wlba]);
    u32 len_copied;
    int err = 0;
    u8  *ptr = data;
    if (unlikely(iwlba==0))
	return 1;
    if (unlikely(off))
    {
	off *= 4;
	err = p->read_hdsector(p->callback_data,
			       p->part_lba + (iwlba<<iwlba_shift) + lba, 1, p->tmp_buffer);
	if (err)
	    return err;
	len_copied = p->hd_sec_sz - off;
	if (likely(len < len_copied))
	    len_copied = len;
	wbfs_memcpy(ptr, p->tmp_buffer + off, len_copied);
	len -= len_copied;
	ptr += len_copied;
	lba++;
	if (unlikely(lba>lba_mask && len))
	{
	    lba = 0;
	    iwlba = wbfs_ntohs(d->header->wlba_table[++wlba]);
	    if (unlikely(iwlba==0))
		return 1;
	}
    }
    while (likely(len>=p->hd_sec_sz))
    {
	u32 nlb = len>>(p->hd_sec_sz_s);

	if (unlikely(lba + nlb > p->wbfs_sec_sz)) // dont cross wbfs sectors..
	    nlb = p->wbfs_sec_sz-lba;
	err = p->read_hdsector(p->callback_data,
			       p->part_lba + (iwlba<<iwlba_shift) + lba, nlb, ptr);
	if (err)
	    return err;
	len -= nlb<<p->hd_sec_sz_s;
	ptr += nlb<<p->hd_sec_sz_s;
	lba += nlb;
	if (unlikely(lba>lba_mask && len))
	{
	    lba = 0;
	    iwlba =wbfs_ntohs(d->header->wlba_table[++wlba]);
	    if (unlikely(iwlba==0))
		return 1;
	}
    }
    if (unlikely(len))
    {
	err = p->read_hdsector(p->callback_data,
			       p->part_lba + (iwlba<<iwlba_shift) + lba, 1, p->tmp_buffer);
	if (err)
	    return err;
	wbfs_memcpy(ptr, p->tmp_buffer, len);
    }
    return 0;
}

///////////////////////////////////////////////////////////////////////////////

u32 wbfs_count_discs ( wbfs_t * p )
{
    u32 i,count=0;
    for ( i = 0; i < p->max_disc; i++ )
	if (p->head->disc_table[i])
	    count++;
    return count;
}

///////////////////////////////////////////////////////////////////////////////

static u32 wbfs_sector_used ( wbfs_t * p, wbfs_disc_info_t * di )
{
    u32 tot_blk = 0, j;
    for ( j = 0; j < p->n_wbfs_sec_per_disc; j++ )
	if (wbfs_ntohs(di->wlba_table[j]))
	    tot_blk++;
    return tot_blk;
}

///////////////////////////////////////////////////////////////////////////////

enumError wbfs_get_disc_info
	( wbfs_t * p, u32 index, u8 * header, int header_size, u32 * size )
{
    u32 slot, count = 0;
    for( slot = 0; slot < p->max_disc; slot++ )
	if (p->head->disc_table[slot])
	    if ( count++ == index )
		return wbfs_get_disc_info_by_slot(p,slot,header,header_size,size);
    return ERR_WDISC_NOT_FOUND;
}

///////////////////////////////////////////////////////////////////////////////

enumError wbfs_get_disc_info_by_slot
	( wbfs_t * p, u32 slot, u8 * header, int header_size, u32 * size )
{
    ASSERT(p);
    if ( slot >= p->max_disc || !p->head->disc_table[slot] )
	return ERR_WDISC_NOT_FOUND;

    const u32 disc_info_sz_lba = p->disc_info_sz >> p->hd_sec_sz_s;
    p->read_hdsector(	p->callback_data,
			p->part_lba + 1 + slot * disc_info_sz_lba,
			1,
			p->tmp_buffer );


    const u32 magic = wbfs_ntohl(*(u32*)(p->tmp_buffer+24));
    if ( magic != 0x5D1C9EA3 )
    {
	p->head->disc_table[slot] = 0;
	return ERR_WARNING;
    }

    if (header_size > (int)p->hd_sec_sz)
	header_size = p->hd_sec_sz;
    memcpy( header, p->tmp_buffer, header_size );
    
    if (size)
    {
	u32 sec_used;
	u8 * header = wbfs_ioalloc(p->disc_info_sz);

	p->read_hdsector (  p->callback_data,
			    p->part_lba + 1 + slot * disc_info_sz_lba,
			    disc_info_sz_lba,
			    header );

	sec_used = wbfs_sector_used(p,(wbfs_disc_info_t *)header);
	wbfs_iofree(header);
	*size = sec_used << (p->wbfs_sec_sz_s-2);
    }
    return ERR_OK;
}

///////////////////////////////////////////////////////////////////////////////

void wbfs_load_freeblocks ( wbfs_t * p )
{
    if (p->freeblks)
	return;

    p->freeblks = wbfs_ioalloc( p->freeblks_lba_count * p->hd_sec_sz );
    if (!p->freeblks)
	OUT_OF_MEMORY;

    p->read_hdsector( p->callback_data,
		      p->part_lba + p->freeblks_lba,
		      p->freeblks_lba_count,
		      p->freeblks );

    // [fbt-bug]
    // fix the last entry
    p->freeblks[p->freeblks_size4-1] &= wbfs_htonl(p->freeblks_mask);
}

///////////////////////////////////////////////////////////////////////////////

u32 wbfs_count_unusedblocks ( wbfs_t * p )
{
    u32 i, j, count = 0;

    wbfs_load_freeblocks(p);

// [fbt-bug]
    for ( i = 0; i < p->freeblks_size4; i++ )
    {
	u32 v = wbfs_ntohl(p->freeblks[i]);
	if (v == ~(u32)0)
	    count+=32;
	else if (v!=0)
	    for (j=0; j<32; j++)
		if (v & (1<<j))
		    count++;
    }
    return count;
}

///////////////////////////////////////////////////////////////////////////////
// [fbt-bug]

static int block_used ( u8 *used, u32 i, u32 wblk_sz )
{
    u32 k;
    i *= wblk_sz;
    for ( k = 0; k < wblk_sz; k++ )
	if ( i + k < WII_SECTORS_DOUBLE_LAYER && used[i+k] )
	    return 1;
    return 0;
}

///////////////////////////////////////////////////////////////////////////////

static u32 alloc_block ( wbfs_t * p )
{
    u32 i;
// [fbt-bug]
    for ( i = 0; i < p->freeblks_size4; i++ )
    {
	u32 v = wbfs_ntohl(p->freeblks[i]);
	if ( v != 0 )
	{
	    u32 j;
	    for ( j = 0; j < 32; j++ )
		if ( v & 1<<j )
		{
		    p->freeblks[i] = wbfs_htonl( v & ~(1<<j) );
		    return i*32 + j + 1;
		}
	}
    }
    return WBFS_NO_BLOCK;
}

///////////////////////////////////////////////////////////////////////////////
// [fbt-bug]

static u32 find_last_used_block ( wbfs_t * p )
{
    int i;
    // [fbt-bug]
    for ( i = p->freeblks_size4 - 1; i >= 0; i-- )
    {
	u32 v = wbfs_ntohl(p->freeblks[i]);
	if ( i == p->freeblks_size4 - 1 )
	    v |= ~p->freeblks_mask;

	if ( v != ~(u32)0 )
	{
	    int j;
	    for ( j = 31; j >= 0; j-- )
		if ( !(v & 1<<j) )
		    return i*32 + j + 1;
	}
    }
    return 0;
}

///////////////////////////////////////////////////////////////////////////////
// [fbt-bug]

void wbfs_free_block ( wbfs_t *p, int bl )
{
    // [fbt-bug]
    if ( bl > 0 && bl < p->n_wbfs_sec )
    {
	const u32 i = (bl-1) / 32;
	const u32 j = (bl-1) & 31;
	const u32 v = wbfs_ntohl(p->freeblks[i]);
	p->freeblks[i] = wbfs_htonl( v | (1<<j) );
    }
}

///////////////////////////////////////////////////////////////////////////////
// [fbt-bug]

void wbfs_use_block ( wbfs_t *p, int bl )
{
    // [fbt-bug]
    if ( bl > 0 && bl < p->n_wbfs_sec )
    {
	const u32 i = (bl-1) / 32;
	const u32 j = (bl-1) & 31;
	const u32 v = wbfs_ntohl(p->freeblks[i]);
	p->freeblks[i] = wbfs_htonl( v & ~(1<<j) );
    }
}

///////////////////////////////////////////////////////////////////////////////

u32 wbfs_add_disc
(
    wbfs_t *p,
    read_wiidisc_callback_t read_src_wii_disc,
    void *callback_data,
    progress_callback_t spinner,
    partition_selector_t sel,
    int copy_1_1
)
{
    int i, discn;
    u32 tot, cur;
    u32 wii_sec_per_wbfs_sect = 1 << (p->wbfs_sec_sz_s-p->wii_sec_sz_s);
    wiidisc_t *d = 0;
    u8 *used = 0;
    wbfs_disc_info_t *info = 0;
    u8* copy_buffer = 0;
    int disc_info_sz_lba;
    used = wbfs_malloc(p->n_wii_sec_per_disc);

    if (!used)
	WBFS_ERROR("unable to alloc memory");

    if ( sel == WHOLE_DISC )
	copy_1_1 = 1;

 // [codeview]
 
    if (!copy_1_1)
    {
	d = wd_open_disc(read_src_wii_disc, callback_data);
	if (!d)
	    WBFS_ERROR("unable to open wii disc");
	wd_build_disc_usage(d, sel, used);
	wd_close_disc(d);
	d = 0;
    }

    for ( i = 0; i < p->max_disc; i++) // find a free slot.
	if (p->head->disc_table[i] == 0)
	    break;

    if (i == p->max_disc)
	WBFS_ERROR("no space left on device (table full)");

    p->head->disc_table[i] = 1;
    discn = i;
    wbfs_load_freeblocks(p);

    // build disc info
    info = wbfs_ioalloc(p->disc_info_sz);
    if (!info)
	OUT_OF_MEMORY;
    memset(info,0,p->disc_info_sz);
    read_src_wii_disc(callback_data, 0, 0x100, info->disc_header_copy);

    copy_buffer = wbfs_ioalloc(p->wbfs_sec_sz);
    if (!copy_buffer)
	WBFS_ERROR("alloc memory");

    tot = 0;
    cur = 0;

    if (spinner)
    {
	// count total number to write for spinner
	for (i = 0; i < p->n_wbfs_sec_per_disc; i++)
	    if (copy_1_1 || block_used(used, i, wii_sec_per_wbfs_sect))
		tot++;
	spinner(0,tot,callback_data);
    }

    for (i = 0; i < p->n_wbfs_sec_per_disc; i++)
    {
	u32 bl = 0;
	if (copy_1_1 || block_used(used, i, wii_sec_per_wbfs_sect))
	{
	    bl = alloc_block(p);
	    // [fbt-bug]
	    if ( bl == WBFS_NO_BLOCK )
	    {
		// free disc slot
		p->head->disc_table[discn] = 0;

		// free already allocated blocks
		int j;
		for ( j = 0; j < i; j++ )
		{
		    bl = wbfs_ntohs(info->wlba_table[j]);
		    if (bl)
			wbfs_free_block(p,bl);
		}
		wbfs_sync(p);
		WBFS_ERROR("no space left on device (disc full)");
	    }

	    if (read_src_wii_disc(callback_data, i * (p->wbfs_sec_sz >> 2), p->wbfs_sec_sz, copy_buffer))
		WBFS_ERROR("error reading disc");

	    // fix the partition table.
	    if (i == (0x40000 >> p->wbfs_sec_sz_s))
		wd_fix_partition_table( d, sel,
			copy_buffer + (0x40000 & (p->wbfs_sec_sz - 1)));

	    p->write_hdsector(p->callback_data, p->part_lba + bl * (p->wbfs_sec_sz / p->hd_sec_sz),
			      p->wbfs_sec_sz / p->hd_sec_sz, copy_buffer);

	    if (spinner)
		spinner(++cur,tot,callback_data);
	}

	info->wlba_table[i] = wbfs_htons(bl);
    }

    // write disc info
    disc_info_sz_lba = p->disc_info_sz >> p->hd_sec_sz_s;
    p->write_hdsector(p->callback_data, p->part_lba + 1 + discn * disc_info_sz_lba,disc_info_sz_lba, info);
    wbfs_sync(p);

error:
    if (d)
	wd_close_disc(d);
    if (used)
	wbfs_free(used);
    if (info)
	wbfs_iofree(info);
    if (copy_buffer)
	wbfs_iofree(copy_buffer);

    return 0;
}

///////////////////////////////////////////////////////////////////////////////

u32 wbfs_ren_disc(wbfs_t*p, u8* discid, u8* newname)
{ // [codeview]
    wbfs_disc_t *d = wbfs_open_disc_by_id6(p, discid);
    int disc_info_sz_lba = p->disc_info_sz>>p->hd_sec_sz_s;

    if (!d)
	return 1;

    memset(d->header->disc_header_copy+0x20, 0, 0x40);
    strncpy((char*)d->header->disc_header_copy+0x20, (char*)newname, 0x39);
    d->header->disc_header_copy[0x20+0x39] = '\0'; //force last char to 0

    p->write_hdsector (	p->callback_data,
			p->part_lba + 1 + d->slot * disc_info_sz_lba,
			disc_info_sz_lba,
			d->header);

    wbfs_close_disc(d);
    wbfs_sync(p);
    return 0;
}

///////////////////////////////////////////////////////////////////////////////

u32 wbfs_nid_disc(wbfs_t*p, u8* discid, u8* newid)
{ // [codeview]
    wbfs_disc_t *d = wbfs_open_disc_by_id6(p, discid);
    int disc_info_sz_lba = p->disc_info_sz >> p->hd_sec_sz_s;

    if (!d)
	return 1;

    if (strlen((const char *)newid) > 0x6)
	return 1;

    strcpy((char *)(d->header->disc_header_copy+0x0), (const char *)newid);

    p->write_hdsector(p->callback_data,
		      p->part_lba + 1 + d->slot * disc_info_sz_lba,
		      disc_info_sz_lba,
		      d->header );

    wbfs_close_disc(d);
    wbfs_sync(p);
    return 0;
}

///////////////////////////////////////////////////////////////////////////////

u32 wbfs_estimate_disc
(
    wbfs_t *p, read_wiidisc_callback_t read_src_wii_disc,
    void *callback_data,
    partition_selector_t sel
)
{ // [codeview]
    u8 *b;
    int i;
    u32 tot;
    u32 wii_sec_per_wbfs_sect = 1 << (p->wbfs_sec_sz_s-p->wii_sec_sz_s);
    wiidisc_t *d = 0;
    u8 *used = 0;
    wbfs_disc_info_t *info = 0;

    tot = 0;

    used = wbfs_malloc(p->n_wii_sec_per_disc);
    if (!used)
	WBFS_ERROR("unable to alloc memory");

    d = wd_open_disc(read_src_wii_disc, callback_data);
    if (!d)
	WBFS_ERROR("unable to open wii disc");

    wd_build_disc_usage(d,sel,used);
    wd_close_disc(d);
    d = 0;

    info = wbfs_ioalloc(p->disc_info_sz);
    b = (u8 *)info;
    read_src_wii_disc(callback_data, 0, 0x100, info->disc_header_copy);


    for (i = 0; i < p->n_wbfs_sec_per_disc; i++)
	if (block_used(used, i, wii_sec_per_wbfs_sect))
	    tot++;

error:
    if (d)
	wd_close_disc(d);

    if (used)
	wbfs_free(used);

    if (info)
	wbfs_iofree(info);

    return tot * ((p->wbfs_sec_sz / p->hd_sec_sz) * 512);
}

///////////////////////////////////////////////////////////////////////////////

u32 wbfs_rm_disc ( wbfs_t * p, u8 * discid, int free_slot_only )
{
    wbfs_disc_t *d = wbfs_open_disc_by_id6(p,discid);
    if (!d)
	return 1;
    int discn = d->slot;

    if (!free_slot_only)
    {
	wbfs_load_freeblocks(p);
	int i;
	for ( i=0; i< p->n_wbfs_sec_per_disc; i++)
	{
	    u32 iwlba = wbfs_ntohs(d->header->wlba_table[i]);
	    if (iwlba)
		wbfs_free_block(p,iwlba);
	}
	memset(d->header,0,p->disc_info_sz);
	const u32 disc_info_sz_lba = p->disc_info_sz >> p->hd_sec_sz_s;
	p->write_hdsector(
			p->callback_data,
			p->part_lba + 1 + discn * disc_info_sz_lba,
			disc_info_sz_lba,
			d->header );
    }

    p->head->disc_table[discn] = 0;
    wbfs_close_disc(d);
    wbfs_sync(p);
    return 0;
}

///////////////////////////////////////////////////////////////////////////////

u32 wbfs_trim ( wbfs_t * p )
{
    // trim the file-system to its minimum size

    wbfs_load_freeblocks(p);
    
    u32 max_block = find_last_used_block(p) + 1;
    p->n_hd_sec = max_block << p->wbfs_sec_sz_s - p->hd_sec_sz_s;
    p->head->n_hd_sec = wbfs_htonl(p->n_hd_sec);

    TRACE("max_block=%u, n_hd_sec=%u\n",max_block,p->n_hd_sec);
 
    // mrk all blocks 'used'
    // [fbt-bug]
    memset(p->freeblks,0,p->freeblks_size4*4);
    wbfs_sync(p);

    // os layer will truncate the file.
    return max_block;
}

///////////////////////////////////////////////////////////////////////////////
// data extraction

u32 wbfs_extract_disc
	( wbfs_disc_t*d, rw_sector_callback_t write_dst_wii_sector,
	  void *callback_data,progress_callback_t spinner)
{
    // [codeview]

    wbfs_t *p = d->p;
    u8* copy_buffer = 0;
    int tot = 0, cur = 0;
    int i;
    int filling_info = 0;

    int src_wbs_nlb=p->wbfs_sec_sz/p->hd_sec_sz;
    int dst_wbs_nlb=p->wbfs_sec_sz/p->wii_sec_sz;

    copy_buffer = wbfs_ioalloc(p->wbfs_sec_sz);

    if (!copy_buffer)
	WBFS_ERROR("alloc memory");

    if (spinner)
    {
	// count total number to write for spinner
	for (i = 0; i < p->n_wbfs_sec_per_disc; i++)
	{
	    if (wbfs_ntohs(d->header->wlba_table[i]))
		tot++;
	}
	spinner(0,tot,callback_data);
    }

    for (i = 0; i < p->n_wbfs_sec_per_disc; i++)
    {
	u32 iwlba = wbfs_ntohs(d->header->wlba_table[i]);
	if (iwlba)
	{
	    cur++;
	    if (spinner)
		spinner(cur,tot,callback_data);

	    if (p->read_hdsector(p->callback_data, p->part_lba + iwlba*src_wbs_nlb, src_wbs_nlb, copy_buffer))
		WBFS_ERROR("reading disc");
	    if (write_dst_wii_sector(callback_data, i*dst_wbs_nlb, dst_wbs_nlb, copy_buffer))
		WBFS_ERROR("writing disc");
	}
	else
	{
	    switch (filling_info)
	    {
		case 0:
		    if (cur == tot)
			filling_info = 1;
		    break;

		case 1:
		    //fprintf(stderr, "Filling empty space in extracted image. Please wait...\n");
		    filling_info = 2;
		    break;

		case 2:
		default:
		    break;
	    }
	}
    }
    wbfs_iofree(copy_buffer);
    return 0;
error:
    return 1;
}

///////////////////////////////////////////////////////////////////////////////

// u32 wbfs_extract_file ( wbfs_disc_t * d, char *path );
