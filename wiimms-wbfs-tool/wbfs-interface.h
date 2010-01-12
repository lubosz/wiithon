
#ifndef WWT_WBFS_INTERFACE_H
#define WWT_WBFS_INTERFACE_H 1

#include <stdio.h>

#include "types.h"
#include "lib-wdf.h"
#include "libwbfs/libwbfs.h"

//
///////////////////////////////////////////////////////////////////////////////
///////////////                    some constants               ///////////////
///////////////////////////////////////////////////////////////////////////////

enum
{
	MIN_WBFS_SIZE		=  10000000, // minimal WBFS partition size
	MIN_WBFS_SIZE_MIB	=       100, // minimal WBFS partition size
	MAX_WBFS		=	999, // maximal number of WBFS partitions
};

//
///////////////////////////////////////////////////////////////////////////////
///////////////                     partitions                  ///////////////
///////////////////////////////////////////////////////////////////////////////

typedef enum enumPartMode
{
	PM_UNKNOWN,		// not analysed yet
	PM_CANT_READ,		// can't read file
	PM_WRONG_TYPE,		// type must be regular or block
	PM_NO_WBFS_MAGIC,	// no WBFS Magic found
	PM_WBFS_MAGIC_FOUND,	// WBFS Magic found, further test needed
	PM_WBFS_INVALID,	// WBFS Magic found, but not a legal WBFS
//	PM_WBFS_CORRUPTED,	// WBFS with errors found
	PM_WBFS,		// WBFS found, no errors detected

} enumPartMode;

//-----------------------------------------------------------------------------

typedef enum enumPartSource
{
	PS_PARAM,	// set by --part or by parameter
	PS_AUTO,	// set by scanning because --auto is set
	PS_ENV,		// set by scanninc env 'WWT_WBFS'

} enumPartSource;

//-----------------------------------------------------------------------------

typedef struct PartitionInfo_t
{
	int  part_index;

	ccp  path;
	ccp  real_path;
	bool is_block_dev;
	bool is_checked;
	u64  file_size;
	u64  disk_usage;
	enumPartMode part_mode;
	enumPartSource source;

	struct WDiscList_t   * wlist;
	struct PartitionInfo_t * next;

} PartitionInfo_t;

//-----------------------------------------------------------------------------

extern int wbfs_count;

extern PartitionInfo_t *  first_partition_info;
extern PartitionInfo_t ** append_partition_info;

extern int pi_count;
extern PartitionInfo_t * pi_list[MAX_WBFS+1];
extern struct WDiscList_t pi_wlist;
extern u32 pi_free_mib;

extern int opt_part;
extern int opt_auto;
extern int opt_all;

PartitionInfo_t * CreatePartitionInfo ( ccp path, enumPartSource source );
int  AddPartition ( ccp arg, int unused );
int  ScanPartitions ( bool all );
void AddEnvPartitions();
int  AnalysePartitions ( FILE * outfile, bool non_found_is_ok, bool scan_wbfs );
void ScanPartitionGames();

//-----------------------------------------------------------------------------

ParamList_t * CheckParamID6 ( bool unique, bool lookup_title_db );
ParamList_t * SearchParamID6 ( ccp id6 );
int PrintParamID6();

enumError CheckParamRename ( bool rename_id, bool allow_plus, bool allow_index );

//
///////////////////////////////////////////////////////////////////////////////
///////////////               discs & wbfs structs              ///////////////
///////////////////////////////////////////////////////////////////////////////

typedef struct WDiscHeader_t
{
	// -> http://www.wiibrew.org/wiki/Wiidisc#Header

	u8  wii_disc_id;
	u8  game_code[2];
	u8  region_code;
	u8  marker_code[2];

	u8  disc_id;
	u8  disc_version;

	u8  audio_streaming;
	u8  streaming_buffer_size;

	u8  unused1[14];
	u32 magic;		// 0x5D1C9EA3
	u8  unused2[4];

	u8  game_title[64];

	u8  padding[0xa0];	// fill up to 0x100 bytes

} __attribute__ ((packed)) WDiscHeader_t;

//-----------------------------------------------------------------------------


typedef struct WDRegionSet_t
{
	u32 region;
	u8  reserved1[12];
	u8  region_byte[8];

} __attribute__ ((packed)) WDRegionSet_t;

//-----------------------------------------------------------------------------

typedef struct WDPartCount_t
{
	u32 n_part;
	u32 off4;

} __attribute__ ((packed)) WDPartCount_t;

//-----------------------------------------------------------------------------

typedef struct WDPartTableEntry_t
{
	u32 off4;
	u32 ptype;

} __attribute__ ((packed)) WDPartTableEntry_t;

//-----------------------------------------------------------------------------

typedef struct WDPartHead_t
{
	u8  ticket[0x2a4];
	u32 tmd_size;
	u32 tmd_off4;
	u32 cert_size;
	u32 cert_off4;
	u32 h3_off4;
	u32 data_off4;
	u32 data_size;

} __attribute__ ((packed)) WDPartHead_t;

//-----------------------------------------------------------------------------

typedef struct WDPartInfo_t
{
	u32 ptable;		// index of partition table
	u32 index;		// index within partition table
	u32 ptype;		// partition type
	off_t off;		// offset of the partition
	off_t size;		// partition size
	WDPartHead_t ph;	// partition header
	u8  part_key[16];	// partition key

} __attribute__ ((packed)) WDPartInfo_t;

//-----------------------------------------------------------------------------

typedef struct WDiscInfo_t
{
	WDiscHeader_t dhead;

	uint disc_index;
	char id6[7];
	u64  size;
	u64  iso_size;
	ccp  region4;
	ccp  region;
	ccp  title;		// from title DB

	// partitions
	u32 n_ptab;			// number f active partition tables
	u32 n_part;			// number or partitions
	WDPartInfo_t	* pinfo;	// field with 'n_part' elements

	// raw data
	WDPartCount_t	pcount[WII_MAX_PART_INFO];
	WDRegionSet_t	regionset;

} WDiscInfo_t;

//-----------------------------------------------------------------------------

typedef struct WDiscListItem_t
{
	u32  size_mib;
	char id6[7];
	char name64[65];
	char region4[5];
	ccp  title;		// ptr into title DB (no free)
	u16  part_index;	// wbfs partition index | 0=ISO, 1=WDF
	u16  n_part;		// number of partitions
	ccp  fname;		// filename, alloced

} WDiscListItem_t;

//-----------------------------------------------------------------------------

typedef struct WDiscList_t
{
	WDiscListItem_t * first_disc;
	u32 used;
	u32 size;
	u32 total_size_mib;
	SortMode sort_mode;

} WDiscList_t;

//-----------------------------------------------------------------------------

typedef struct WBFS_t
{
    // handles

	SuperFile_t * sf;	// attached super file
	bool sf_alloced;	// true if 'sf' is alloced
	wbfs_t * wbfs;		// the pure wbfs handle
	wbfs_disc_t * disc;	// the wbfs disc handle

    // infos calced by CalcWBFSUsage()

	u32 used_discs;
	u32 free_discs;
	u32 total_discs;

	u32 free_blocks;
	u32 used_mib;
	u32 free_mib;
	u32 total_mib;

} WBFS_t;

//-----------------------------------------------------------------------------

typedef struct CheckDisc_t
{
	char id6[7];		// id of the disc
	char no_blocks;		// no valid blocks assigned
	u16  bl_fbt;		// num of blocks marked free in fbt
	u16  bl_overlap;	// num of blocks that overlaps other discs
	u16  bl_invalid;	// num of blocks with invalid blocks
	u16  err_count;		// total count of errors

} CheckDisc_t;

//-----------------------------------------------------------------------------

typedef struct CheckWBFS_t
{
    // handles

	WBFS_t * wbfs;		// attached WBFS

    // data

	off_t  fbt_off;		// offset of fbt
	size_t fbt_size;	// size of fbt
	u32 * cur_fbt;		// current free blocks table (1 bit per block)
	u32 * good_fbt;		// calculated free blocks table (1 bit per block)

	u8  * ubl;		// used blocks (1 byte per block), copy of fbt
	u8  * blc;		// block usage counter
	CheckDisc_t * disc;	// disc list

    // statistics

	u32 err_fbt_used;	// number of wrong used marked blocks
	u32 err_fbt_free;	// number of wrong free marked blocks
	u32 err_fbt_free_wbfs0;	// number of 'err_fbt_free' depend on WBFS v0
	u32 err_no_blocks;	// total num of 'no_blocks' errors
	u32 err_bl_overlap;	// total num of 'bl_overlap' errors
	u32 err_bl_invalid;	// total num of 'bl_invalid' errors
	u32 err_total;		// total of all above

	u32 invalid_disc_count;	// total numer of invalid games

	enumError err;		// status: OK | WARNING | WBFS_INVALID

} CheckWBFS_t;

//
///////////////////////////////////////////////////////////////////////////////
///////////////             discs & wbfs interface              ///////////////
///////////////////////////////////////////////////////////////////////////////

extern int partition_selector;
extern u8 wdisc_usage_tab [WII_MAX_SECTORS];
extern u8 wdisc_usage_tab2[WII_MAX_SECTORS];

int ScanPartitionSelector ( ccp arg );

//-----------------------------------------------------------------------------

void InitializeWBFS	( WBFS_t * w );
enumError ResetWBFS	( WBFS_t * w );
enumError SetupWBFS	( WBFS_t * w, SuperFile_t * sf, bool print_err, int sector_size );
enumError CreateGrowingWBFS
			( WBFS_t * w, SuperFile_t * sf, off_t size, int sector_size );
enumError OpenWBFS	( WBFS_t * w, ccp filename, bool print_err );
enumError FormatWBFS	( WBFS_t * w, ccp filename, bool print_err, int sector_size );
enumError TruncateWBFS	( WBFS_t * w );

enumError CalcWBFSUsage	( WBFS_t * w );

enumError OpenPartWBFS	( WBFS_t * w, struct PartitionInfo_t *  info );
enumError GetFirstWBFS	( WBFS_t * w, struct PartitionInfo_t ** info );
enumError GetNextWBFS	( WBFS_t * w, struct PartitionInfo_t ** info );

enumError DumpWBFS	( WBFS_t * w, FILE * f, int indent, int dump_level, CheckWBFS_t * ck );

//-----------------------------------------------------------------------------

void InitializeCheckWBFS ( CheckWBFS_t * ck );
void ResetCheckWBFS	 ( CheckWBFS_t * ck );
enumError CheckWBFS	 ( CheckWBFS_t * ck, WBFS_t * w, int verbose, FILE * f, int indent );
enumError AutoCheckWBFS	 ( WBFS_t * w, bool ignore_check );

enumError PrintCheckedWBFS ( CheckWBFS_t * ck, FILE * f, int indent );

enumError RepairWBFS
	( CheckWBFS_t * ck, int testmode, RepairMode rm, int verbose, FILE * f, int indent );
enumError CheckRepairWBFS
	( WBFS_t * w, int testmode, RepairMode rm, int verbose, FILE * f, int indent );
enumError RepairFBT
	( WBFS_t * w, int testmode, FILE * f, int indent );

// returns true if 'good_ftb' differ from 'cur_ftb'
bool CalcFBT ( CheckWBFS_t * ck );

//-----------------------------------------------------------------------------

void InitializeWDiscInfo     ( WDiscInfo_t * dinfo );
enumError ResetWDiscInfo     ( WDiscInfo_t * dinfo );
enumError GetWDiscInfo	     ( WBFS_t * w, WDiscInfo_t * dinfo, int disc_index );
enumError GetWDiscInfoBySlot ( WBFS_t * w, WDiscInfo_t * dinfo, u32 disc_slot );
enumError FindWDiscInfo	     ( WBFS_t * w, WDiscInfo_t * dinfo, ccp id6 );

enumError LoadIsoHeader	( WBFS_t * w, WDiscHeader_t * iso_header, wbfs_disc_t * disc );

void CalcWDiscInfo ( WDiscInfo_t * winfo );
enumError CountPartitions ( SuperFile_t * sf, WDiscInfo_t * dinfo );
enumError LoadPartitionInfo ( SuperFile_t * sf, WDiscInfo_t * dinfo, MemMap_t * mm );

enumError DumpWDiscInfo
	( WDiscInfo_t * dinfo, WDiscHeader_t * iso_header, FILE * f, int indent );

//-----------------------------------------------------------------------------

WDiscList_t * GenerateWDiscList ( WBFS_t * w, int part_index );
void InitializeWDiscList ( WDiscList_t * wlist );
void ResetWDiscList ( WDiscList_t * wlist );
void FreeWDiscList ( WDiscList_t * wlist );

WDiscListItem_t *  AppendWDiscList ( WDiscList_t * wlist, WDiscInfo_t * winfo );
void CopyWDiscInfo ( WDiscListItem_t * item, WDiscInfo_t * winfo );

void SortWDiscList   ( WDiscList_t * wlist, enum SortMode sort_mode,
			enum SortMode default_sort_mode, int unique );

//-----------------------------------------------------------------------------

enumError OpenWDiscID6	( WBFS_t * w, ccp id6 );
enumError OpenWDiscIndex( WBFS_t * w, u32 index );
enumError OpenWDiscSlot	( WBFS_t * w, u32 slot );
enumError CloseWDisc	( WBFS_t * w );
enumError ExistsWDisc	( WBFS_t * w, ccp id6 );

WDiscHeader_t * GetWDiscHeader ( WBFS_t * w );

enumError AddWDisc	( WBFS_t * w, SuperFile_t * sf, int partition_selector );
enumError ExtractWDisc	( WBFS_t * w, SuperFile_t * sf );
enumError RemoveWDisc	( WBFS_t * w, ccp id6, bool free_slot_only );
enumError RenameWDisc	( WBFS_t * w, ccp new_id6, ccp new_title,
	bool change_wbfs_head, bool change_iso_head, int verbose, int testmode );

int RenameISOHeader ( void * data, ccp fname,
	ccp new_id6, ccp new_title, int verbose, int testmode );


//
///////////////////////////////////////////////////////////////////////////////
///////////////                 source iterator                 ///////////////
///////////////////////////////////////////////////////////////////////////////

struct Iterator_t;
typedef enumError (*IteratorFunc) ( SuperFile_t * sf, struct Iterator_t * it );

//-----------------------------------------------------------------------------

typedef enum enumAction
{
	ACT_WARN,	// ignore with message
	ACT_IGNORE,	// ignore without message
	ACT_ALLOW,	// allow
	ACT_EXPAND,	// allow and expand (wbfs only)

} enumAction;

//-----------------------------------------------------------------------------

typedef struct Iterator_t
{
	int depth;			// current directory depth
	int max_depth;			// maximal directory depth
	IteratorFunc func;		// call back function
	ccp real_path;			// pointer to real_path;

	// options

	bool open_modify;		// open in modify mode
	enumAction act_non_exist;	// action for non existing files
	enumAction act_non_iso;		// action for non iso files
	enumAction act_wbfs;		// action for wbfs files with n(disc) != 1
	enumAction act_open;		// action for open output files

	// source file list
	
	StringField_t source_list;	// collect first than run
	int source_index;		// informative: index of current file

	// user defined parameters, ignores by SourceIterator()

	bool scrub_it;		// SCRUB instead of COPY
	bool update;		// update option set
	bool overwrite;		// overwrite option set
	bool remove_source;	// remove option set
	int  long_count;	// long counter for output
	uint done_count;	// done counter
	uint diff_count;	// diff counter
	uint exists_count;	// 'file alread exists' counter
	WDiscList_t * wlist;	// pointer to WDiscList_t to collect data
	WBFS_t * wbfs;		// open WBFS
	dev_t open_dev;		// dev_t of open output file
	ino_t open_ino;		// ino_t of open output file

} Iterator_t;

//-----------------------------------------------------------------------------

void InitializeIterator ( Iterator_t * it );
void ResetIterator ( Iterator_t * it );

enumError SourceIterator
	( Iterator_t * it, bool current_dir_is_default, bool collect_fnames );

enumError SourceIteratorCollected ( Iterator_t * it );

//
///////////////////////////////////////////////////////////////////////////////
///////////////                          END                    ///////////////
///////////////////////////////////////////////////////////////////////////////

#endif // WWT_WBFS_INTERFACE_H
