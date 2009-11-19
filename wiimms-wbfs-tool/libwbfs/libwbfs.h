#ifndef LIBWBFS_H
#define LIBWBFS_H

#include "libwbfs_os.h" // this file is provided by the project wanting to compile libwbfs
#include "wiidisc.h"

#ifdef __cplusplus
extern "C"
{
#endif /* __cplusplus */

///////////////////////////////////////////////////////////////////////////////

typedef u32 be32_t;
typedef u16 be16_t;

#define WBFS_MAGIC ( 'W'<<24 | 'B'<<16 | 'F'<<8 | 'S' )
#define WBFS_VERSION 1
#define WBFS_NO_BLOCK (~(u32)0)

///////////////////////////////////////////////////////////////////////////////

typedef struct wbfs_head
{
    be32_t magic;	// the magic (char*)"WBFS"

    // the 3 main parameters -> they are used to calculate the geometry

    be32_t n_hd_sec;	// total number of hd_sec in this partition
    u8  hd_sec_sz_s;	// sector size in this partition
    u8  wbfs_sec_sz_s;	// size of a wbfs sec

    // more parameters

    u8  wbfs_version;	// informative version number
    u8  padding;
    u8  disc_table[0];	// size depends on hd sector size
}
__attribute((packed)) wbfs_head_t;

//-----------------------------------------------------------------------------

typedef struct wbfs_disc_info
{
    u8 disc_header_copy[0x100];
    be16_t wlba_table[0];   // wbfs_t::n_wbfs_sec_per_disc elements

} wbfs_disc_info_t;

//-----------------------------------------------------------------------------

//  WBFS first wbfs_sector structure:
//
//  -----------
// | wbfs_head |  (hd_sec_sz)
//  -----------
// |	       |
// | disc_info |
// |	       |
//  -----------
// |	       |
// | disc_info |
// |	       |
//  -----------
// |	       |
// | ...       |
// |	       |
//  -----------
// |	       |
// | disc_info |
// |	       |
//  -----------
// |	       |
// |freeblk_tbl|
// |	       |
//  -----------
//

//-----------------------------------------------------------------------------

// callback definition. Return 1 on fatal error
// (callback is supposed to make retries until no hopes..)

typedef int (*rw_sector_callback_t)(void*fp,u32 lba,u32 count,void*iobuf);
typedef void (*progress_callback_t)( u64 status, u64 total, void * callback_data );

//-----------------------------------------------------------------------------

typedef struct wbfs_s
{
	wbfs_head_t *head;

	/* hdsectors, the size of the sector provided by the hosting hard drive */
	u32 hd_sec_sz;
	u8  hd_sec_sz_s;	// the power of two of the last number
	u32 n_hd_sec;		// the number of hd sector in the wbfs partition

	/* standard wii sector (0x8000 bytes) */
	u32 wii_sec_sz;		// always WII_SECTOR_SIZE
	u8  wii_sec_sz_s;	// always 15
	u32 n_wii_sec;
	u32 n_wii_sec_per_disc;	// always WII_SECTORS_DOUBLE_LAYER

	/* The size of a wbfs sector */
	u32 wbfs_sec_sz;
	u32 wbfs_sec_sz_s;
	u16 n_wbfs_sec;		// this must fit in 16 bit!
	u16 n_wbfs_sec_per_disc;// size of the lookup table

	u32 part_lba;		// the lba of the wbfs header

	/* virtual methods to read write the partition */
	rw_sector_callback_t read_hdsector;
	rw_sector_callback_t write_hdsector;
	void *callback_data;

	u16 max_disc;		// maximal number of possible discs
	u32 freeblks_lba;	// the hd sector of the free blocks table
	u32 freeblks_lba_count;	// number of hd sector used by free blocks table
	u32 freeblks_size4;	// size in u32 of free blocks table
	u32 freeblks_mask;	// mask for last used u32 of freeblks
	u32 * freeblks;		// if not NULL: copy of free blocks table

	u16 disc_info_sz;

	u8  *tmp_buffer;  // pre-allocated buffer for unaligned read

	u32 n_disc_open;

} wbfs_t;

//-----------------------------------------------------------------------------

typedef struct wbfs_disc_s
{
	wbfs_t *p;
	wbfs_disc_info_t * header;	// pointer to wii header
	int slot;			// disc slot, range= 0 .. wbfs_t::max_disc-1

} wbfs_disc_t;

//-----------------------------------------------------------------------------

/*! @brief open a MSDOS partitionned harddrive. This tries to find a wbfs partition into the harddrive
   @param read_hdsector,write_hdsector: accessors to a harddrive
   @hd_sector_size: size of the hd sector. Can be set to zero if the partition in already initialized
   @num_hd_sector:  number of sectors in this disc. Can be set to zero if the partition in already initialized
   @reset: not implemented, This will format the whole harddrive with one wbfs partition that fits the whole disk.
   calls wbfs_error() to have textual meaning of errors
   @return NULL in case of error
*/
wbfs_t * wbfs_open_hd(rw_sector_callback_t read_hdsector,
		      rw_sector_callback_t write_hdsector,
		      void *callback_data,
		      int hd_sector_size, int num_hd_sector, int reset);

//-----------------------------------------------------------------------------

/*! @brief open a wbfs partition
   @param read_hdsector,write_hdsector: accessors to the partition
   @hd_sector_size: size of the hd sector. Can be set to zero if the partition in already initialized
   @num_hd_sector:  number of sectors in this partition. Can be set to zero if the partition in already initialized
   @partition_lba:  The partitio offset if you provided accessors to the whole disc.
   @reset: initialize the partition with an empty wbfs.
   calls wbfs_error() to have textual meaning of errors
   @return NULL in case of error
*/
wbfs_t*wbfs_open_partition(rw_sector_callback_t read_hdsector,
			   rw_sector_callback_t write_hdsector,
			   void *callback_data,
			   int hd_sector_size, int num_hd_sector, u32 partition_lba, int reset);


//-----------------------------------------------------------------------------

void wbfs_close ( wbfs_t * p );
void wbfs_sync  ( wbfs_t * p );

wbfs_disc_t * wbfs_open_disc_by_slot ( wbfs_t * p, u32 split );
wbfs_disc_t * wbfs_open_disc_by_id6  ( wbfs_t * p, u8 * id6 );
void wbfs_sync_disc_header ( wbfs_disc_t * d );
void wbfs_close_disc ( wbfs_disc_t * d );

//-----------------------------------------------------------------------------

/*! @brief accessor to the wii disc
  @param d: a pointer to already open disc
  @param offset: an offset inside the disc, *points 32bit words*, allowing to access 16GB data
  @param len: The length of the data to fetch, in *bytes*
 */
// offset is pointing 32bit words to address the whole dvd, although len is in bytes
int wbfs_disc_read(wbfs_disc_t*d,u32 offset, u8 *data, u32 len);

/*! @return the number of discs inside the paritition */
u32 wbfs_count_discs(wbfs_t*p);

enumError wbfs_get_disc_info
		( wbfs_t*p, u32 idx,  u8 *header, int header_size, u32 *size );
enumError wbfs_get_disc_info_by_slot
		( wbfs_t*p, u32 slot, u8 *header, int header_size, u32 *size );

/*! get the number of unuseds block of the partition.
  to be multiplied by p->wbfs_sec_sz (use 64bit multiplication) to have the number in bytes
*/
u32 wbfs_count_unusedblocks ( wbfs_t * p );

/******************* write access  ******************/

void wbfs_load_freeblocks ( wbfs_t * p );
void wbfs_free_block	  ( wbfs_t * p, int bl );
void wbfs_use_block	  ( wbfs_t * p, int bl );

/*! add a wii dvd inside the partition
  @param read_src_wii_disc: a callback to access the wii dvd. offsets are in 32bit, len in bytes!
  @callback_data: private data passed to the callback
  @spinner: a pointer to a function that is regulary called to update a progress bar.
  @sel: selects which partitions to copy.
  @copy_1_1: makes a 1:1 copy, whenever a game would not use the wii disc format, and some data is hidden outside the filesystem.
 */
u32 wbfs_add_disc(wbfs_t*p,read_wiidisc_callback_t read_src_wii_disc,
		  void *callback_data,
		  progress_callback_t spinner,
		  partition_selector_t sel,
		  int copy_1_1
		 );

u32 wbfs_estimate_disc(wbfs_t*p,read_wiidisc_callback_t read_src_wii_disc, void *callback_data,
		       partition_selector_t sel);

// remove a disc from partition
u32 wbfs_rm_disc ( wbfs_t * p, u8 * discid, int free_slot_only );

/*! rename a wiidvd inside a partition */
u32 wbfs_ren_disc(wbfs_t*p, u8* discid, u8* newname);

/*! edit a wiidvd diskid */
u32 wbfs_nid_disc(wbfs_t*p, u8* discid, u8* newid);

/*! trim the file-system to its minimum size
  This allows to use wbfs as a wiidisc container
 */
u32 wbfs_trim(wbfs_t*p);

/*! extract a disc from the wbfs, unused sectors are just untouched, allowing descent filesystem to only really usefull space to store the disc.
Even if the filesize is 4.7GB, the disc usage will be less.
 */
u32 wbfs_extract_disc(wbfs_disc_t*d, rw_sector_callback_t write_dst_wii_sector,void *callback_data,progress_callback_t spinner);

/*! extract a file from the wii disc filesystem.
  E.G. Allows to extract the opening.bnr to install a game as a system menu channel
 */
u32 wbfs_extract_file(wbfs_disc_t*d, char *path);

// remove some sanity checks
void wbfs_set_force_mode(int force);


/* OS specific functions provided by libwbfs_<os>.c */

wbfs_t *wbfs_try_open(char *disk, char *partition, int reset);
wbfs_t *wbfs_try_open_partition(char *fn, int reset);

void *wbfs_open_file_for_read(char*filename);
void *wbfs_open_file_for_write(char*filename);
int wbfs_read_file(void*handle, int len, void *buf);
void wbfs_close_file(void *handle);
void wbfs_file_reserve_space(void*handle,long long size);
void wbfs_file_truncate(void *handle,long long size);
int wbfs_read_wii_file(void *_handle, u32 _offset, u32 count, void *buf);
int wbfs_write_wii_sector_file(void *_handle, u32 lba, u32 count, void *buf);

///////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
}
#endif /* __cplusplus */

#endif // LIBWBFS_H
