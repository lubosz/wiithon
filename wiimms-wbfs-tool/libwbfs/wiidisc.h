#ifndef WIIDISC_H
#define WIIDISC_H

#include <stdio.h>
#include "libwbfs_os.h"

///////////////////////////////////////////////////////////////////////////////

#ifdef __cplusplus
extern "C"
{
#endif /* __cplusplus */
#if 0 //removes extra automatic indentation by editors
}
#endif

///////////////////////////////////////////////////////////////////////////////

// callback definition. Return 1 on fatal error
// (callback is supposed to make retries until no hopes..)
// offset points 32bit words, count counts bytes

typedef int (*read_wiidisc_callback_t)( void *fp, u32 offset, u32 count, void* iobuf );

///////////////////////////////////////////////////////////////////////////////

enum // some constants
{
    WII_SECTOR_SIZE		= 0x8000,
    WII_SECTORS_SINGLE_LAYER	= 143432,
    WII_SECTORS_DOUBLE_LAYER	= 2 * WII_SECTORS_SINGLE_LAYER,
    WII_MAX_SECTORS		= WII_SECTORS_DOUBLE_LAYER,

    WII_TITLE_OFF		= 0x20,
    WII_TITLE_SIZE		= 0x40,
};

///////////////////////////////////////////////////////////////////////////////

typedef enum
{
    GAME_PARTITION_TYPE		= 0,
    UPDATE_PARTITION_TYPE	= 1,
    CHANNEL_PARTITION_TYPE	= 2,

    // value in between selects partition types of that value

    WHOLE_DISC			= -6,   // copy whole disc
    ALL_PARTITIONS		= -5,   // copy all partitions

    REMOVE_GAME_PARTITION	= -4,	// all but GAME_PARTITION_TYPE
    REMOVE_UPDATE_PARTITION	= -3,	// all but UPDATE_PARTITION_TYPE
    REMOVE_CHANNEL_PARTITION	= -2,	// all but CHANNEL_PARTITION_TYPE
				//-1 = reserved as error indicator

} partition_selector_t;

///////////////////////////////////////////////////////////////////////////////

typedef struct wiidisc_s
{
    read_wiidisc_callback_t read;	// read-data-function
    void *fp;				// file handle (black box)
    u8 *sector_usage_table;		// if not NULL: calculate usage
					// size = WII_MAX_SECTORS

    // everything points 32bit words.
    u32 disc_raw_offset;
    u32 partition_raw_offset;
    u32 partition_data_offset;
    u32 partition_data_size;
    u32 partition_block;

    u8 *tmp_buffer;			// temp buffer with WII_SECTOR_SIZE bytes
    u8 *tmp_buffer2;			// temp buffer with WII_SECTOR_SIZE bytes
    u8 disc_key[16];
    int dont_decrypt;

    partition_selector_t part_sel;

    char *extract_pathname;
    u8  *extracted_buffer;

} wiidisc_t;

///////////////////////////////////////////////////////////////////////////////

void decrypt_title_key ( u8 *tik, u8 *title_key );

wiidisc_t *wd_open_disc( read_wiidisc_callback_t read, void*fp );

void wd_close_disc( wiidisc_t * );

// returns a buffer allocated with wbfs_ioalloc() or NULL if not found of alloc error
u8 * wd_extract_file
	( wiidisc_t * d, partition_selector_t partition_type, char * pathname );

void wd_build_disc_usage
	( wiidisc_t * d, partition_selector_t selector, u8 * usage_table );

// effectively remove not copied partition from the partition table.
void wd_fix_partition_table
	( wiidisc_t * d, partition_selector_t selector, u8 * partition_table );

int wd_rename
(
	void * data,		// pointer to ISO data
	const char * new_id,	// if !NULL: take the first 6 chars as ID
	const char * new_title	// if !NULL: take the first 0x39 chars as title
);

///////////////////////////////////////////////////////////////////////////////

#if 0
{
#endif
#ifdef __cplusplus
}
#endif /* __cplusplus */

///////////////////////////////////////////////////////////////////////////////

#endif // WIIDISC_H
