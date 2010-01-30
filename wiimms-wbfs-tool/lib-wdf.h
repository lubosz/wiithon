
#ifndef WWT_LIB_WDF_H
#define WWT_LIB_WDF_H 1

#include "types.h"
#include "libwbfs.h"
#include "lib-std.h"

//
///////////////////////////////////////////////////////////////////////////////
///////////////                  WDF definitions                ///////////////
///////////////////////////////////////////////////////////////////////////////

// First a magic is defined to identify a WDF clearly. The magic should never be
// a possible Wii ISO image identification. Wii ISO images starts with the ID6.
// And so the WDF magic contains one contral character (CTRL-A) within.

#define WDF_MAGIC		"WII\1DISC"
#define WDF_MAGIC_SIZE		8
#define WDF_VERSION		1

// the minimal size of holes in bytes that will be detected.

#define WDF_MIN_HOLE_SIZE	(sizeof(WDF_Chunk_t)+sizeof(WDF_Hole_t))

// WDF hole detection type
typedef u32 WDF_Hole_t;

//
///////////////////////////////////////////////////////////////////////////////
///////////////                 struct WDF_Head_t               ///////////////
///////////////////////////////////////////////////////////////////////////////
// This is the header of a WDF.
// Remember: Within a file the data is stored in network byte order (big endian)

typedef struct WDF_Head_t
{
	// magic and version number
	char magic[WDF_MAGIC_SIZE];	// WDF_MAGIC, what else!
	u32 wdf_version;		// WDF_VERSION

	// split file support
	u32 split_file_id;		// for plausibility checks
	u32 split_file_index;		// zero based index ot this file
	u32 split_file_num_of;		// number of split files

	// virtual file infos
	u64 file_size;			// the size of the virtual file

	// data size of this file
	u64 data_size;			// the ISO data size in this file
					// (without header and chunk table)
	// chunks
	u32 chunk_split_file;		// which spit file contains the chunk table
	u32 chunk_n;			// total number of data chunks
	u64 chunk_off;			// the 'MAGIC + chunk_table' file offset

} __attribute__ ((packed)) WDF_Head_t;

//
///////////////////////////////////////////////////////////////////////////////
///////////////                struct WDF_Chunk_t               ///////////////
///////////////////////////////////////////////////////////////////////////////
// This is the chunk info of WDF.
// Remember: Within a file the data is stored in network byte order (big endian)

typedef struct WDF_Chunk_t
{
	u32 split_file_index;		// which split file conatins that chunk
	u64 file_pos;			// the virtual ISO file position
	u64 data_off;			// the data file offset
	u64 data_size;			// the data size

} __attribute__ ((packed)) WDF_Chunk_t;

//
///////////////////////////////////////////////////////////////////////////////
///////////////                struct SuperFile_t               ///////////////
///////////////////////////////////////////////////////////////////////////////

typedef struct SuperFile_t
{
	// parameters, set by user

	File_t f;			// file handling struct
	enumOFT oft;			// output file mode
	bool enable_fast;		// enables fast prosessing
	bool enable_trunc;		// truncate iso image
	int  indent;			// indent of progress and summary
	bool show_progress;		// show progress info
	bool show_summary;		// show summary statistics
	bool show_msec;			// show milli seconds in statistics

	// internal values: progress

	u32 progress_start_time;	// time of start
	u32 progress_last_view_sec;	// time of last progress viewing
	u32 progress_last_calc_time;	// time of last calculation
	u64 progress_sum_time;		// sum of time weighted intervalls
	u64 progress_time_divisor;	// divisor == sum of weights
	u32 progress_max_wd;		// max width used for progress output
	ccp progress_verb;		// default is "copied"

	// internal values: file handling

	off_t file_size;		// the size of the (virtual) ISO image
	off_t max_virt_off;		// maximal used offset of virtual image

	// WI support

	WDF_Head_t   wh;		// the WDF header
	WDF_Chunk_t *wc;		// field with 'wc_size' elements
	int wc_size;			// number of elements in 'wc'
	int wc_used;			// number of used elements in 'wc'

	// WBFS support (read only)

	struct WBFS_t * wbfs;		// a WBFS

} SuperFile_t;

//
///////////////////////////////////////////////////////////////////////////////
///////////////               interface for SuperFile_t         ///////////////
///////////////////////////////////////////////////////////////////////////////

// initialize the super file
void InitializeSF ( SuperFile_t * sf );

// remove all dynamic data
void FreeSF ( SuperFile_t * sf );

// close file + remove all dynamic data
enumError CloseSF ( SuperFile_t * sf, struct stat * set_time );

// reset == CloseSF() + reset all but user settings
enumError ResetSF ( SuperFile_t * sf, struct stat * set_time );

// remove == ResetSF() + remove all files
enumError RemoveSF ( SuperFile_t * sf );

// setup reading
enumError SetupReadSF   ( SuperFile_t * sf );		// all files
enumError SetupReadISO  ( SuperFile_t * sf );		// only iso images
enumError SetupReadWBFS ( SuperFile_t * sf );		// setup wbfs/disc reading
enumError OpenSF
	( SuperFile_t * sf, ccp fname, bool allow_non_iso, bool open_modify );

// setup writing
enumError SetupWriteSF	( SuperFile_t * sf, enumOFT );	// setup writing
enumError SetupWriteWBFS( SuperFile_t * sf );		// setup wbfs/disc writing

// filename helper
void SubstFileNameSF ( SuperFile_t * fo, SuperFile_t * fi, ccp f_name );

// main read and write functions
enumError ReadSF	( SuperFile_t * sf, off_t off, void * buf, size_t count );
enumError WriteSF	( SuperFile_t * sf, off_t off, const void * buf, size_t count );
enumError WriteSparseSF	( SuperFile_t * sf, off_t off, const void * buf, size_t count );
enumError SetSizeSF	( SuperFile_t * sf, off_t off );

// read and write wrappers
int WrapperReadISO	  ( void * p_sf, u32 offset, u32 count, void * iobuf );
int WrapperReadSF	  ( void * p_sf, u32 offset, u32 count, void * iobuf );
int WrapperWriteDirectISO ( void * p_sf, u32 lba,    u32 count, void * iobuf );
int WrapperWriteSparseISO ( void * p_sf, u32 lba,    u32 count, void * iobuf );
int WrapperWriteDirectSF  ( void * p_sf, u32 lba,    u32 count, void * iobuf );
int WrapperWriteSparseSF  ( void * p_sf, u32 lba,    u32 count, void * iobuf );

// progress and statistics
void CopyProgressSF ( SuperFile_t * dest, SuperFile_t * src );
void PrintProgressSF ( u64 done, u64 total, void * param );
void PrintSummarySF ( SuperFile_t * sf );

// find file type
enumFileType AnalyseFT ( File_t * f );
enumError XPrintErrorFT ( XPARM File_t * f, enumFileType err_mask );
ccp GetNameFT ( enumFileType ftype, int ignore );
enumOFT GetOFT ( SuperFile_t * sf );
u32 CountUsedIsoBlocksSF ( SuperFile_t * sf, u32 psel );
u32 CountUsedBlocks ( u8 * usage_tab, u32 block_size );

// copy functions
enumError CopySF	( SuperFile_t * in, SuperFile_t * out, u32 psel );
enumError CopyRaw	(      File_t * in, SuperFile_t * out );
enumError CopyWDF	( SuperFile_t * in, SuperFile_t * out );
enumError CopyWBFSDisc	( SuperFile_t * in, SuperFile_t * out );
enumError CopyToWBFS	( SuperFile_t * in, SuperFile_t * out, u32 psel );

// diff functions
enumError DiffSF	( SuperFile_t * f1, SuperFile_t * f2, int long_count, u32 psel );
enumError DiffRaw	( SuperFile_t * f1, SuperFile_t * f2, int long_count );

//
///////////////////////////////////////////////////////////////////////////////
///////////////               interface for WDF_Head_t          ///////////////
///////////////////////////////////////////////////////////////////////////////

// initialize WH
void InitializeWH ( WDF_Head_t * wh );

// convert WH data, src + dest may point to same structure
void ConvertToNetworkWH ( WDF_Head_t * dest, WDF_Head_t * src );
void ConvertToHostWH    ( WDF_Head_t * dest, WDF_Head_t * src );

///////////////////////////////////////////////////////////////////////////////
///////////////               interface for WDF_Chunk_t         ///////////////
///////////////////////////////////////////////////////////////////////////////

// initialize WC
void InitializeWC ( WDF_Chunk_t * wc, int n_elem );

// convert WC data, src + dest may point to same structure
void ConvertToNetworkWC ( WDF_Chunk_t * dest, WDF_Chunk_t * src );
void ConvertToHostWC    ( WDF_Chunk_t * dest, WDF_Chunk_t * src );

//
///////////////////////////////////////////////////////////////////////////////
///////////////               interface for WDF files           ///////////////
///////////////////////////////////////////////////////////////////////////////

// WDF reading support
enumError SetupReadWDF	( SuperFile_t * sf );
enumError ReadWDF	( SuperFile_t * sf, off_t off, void * buf, size_t size );

// WDF writing support
enumError SetupWriteWDF	( SuperFile_t * sf );
enumError TermWriteWDF	( SuperFile_t * sf );
enumError WriteWDF	( SuperFile_t * sf, off_t off, const void * buf, size_t size );
enumError WriteSparseWDF( SuperFile_t * sf, off_t off, const void * buf, size_t size );

// chunk managment
WDF_Chunk_t * NeedChunkWDF ( SuperFile_t * sf, int at_index );

//
///////////////////////////////////////////////////////////////////////////////
///////////////                          END                    ///////////////
///////////////////////////////////////////////////////////////////////////////

#endif // WWT_LIB_WDF_H

