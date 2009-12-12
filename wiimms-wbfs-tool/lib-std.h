
#ifndef WWT_LIB_STD_H
#define WWT_LIB_STD_H 1

#define _GNU_SOURCE 1

#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <stdio.h>

#include "types.h"
#include "lib-error.h"

//
///////////////////////////////////////////////////////////////////////////////
///////////////                     some defs                   ///////////////
///////////////////////////////////////////////////////////////////////////////

#if defined(DEBUG) || defined(TEST)
    #undef EXTENDED_ERRORS
    #define EXTENDED_ERRORS 1		// undef | 1 | 2
#endif

#if defined(TEST)
    #undef CACHE_ENABLED
    #define CACHE_ENABLED 1		// undef | def
#endif

#ifndef CACHE_ENABLED
    #define CACHE_ENABLED 1		// 0 | 1
#endif

#ifndef EXTENDED_IO_FUNC
    #define EXTENDED_IO_FUNC 1		// 0 | 1
#endif

///////////////////////////////////////////////////////////////////////////////

typedef enum enumProgID
{
	PROG_UNKNOWN,
	PROG_WWT,
	PROG_WIT,
	PROG_ISO2WDF,
	PROG_ISO2WBFS,
	PROG_WDF2ISO,
	PROG_WDF_CAT,
	PROG_WDF_DUMP,

} enumProgID;

typedef enum enumRevID
{
	REVID_UNKNOWN		= 0x00000000,
	REVID_WIIMM		= 0x10000000,
	REVID_WIIMM_TRUNC	= 0x20000000,

} enumRevID;

typedef enum enumSystemID
{
	SYSID_UNKNOWN		= 0x00000000,
	SYSID_I386		= 0x01000000,
	SYSID_X86_64		= 0x02000000,
	SYSID_CYGWIN		= 0x03000000,
	SYSID_APPLE		= 0x04000000,
	SYSID_LINUX		= 0x05000000,
	SYSID_UNIX		= 0x06000000,

} enumSystemID;

///////////////////////////////////////////////////////////////////////////////

#ifdef __CYGWIN__
	#define SYSTEM "cygwin"
	#define SYSTEMID SYSID_CYGWIN
#elif __APPLE__
	#define SYSTEM "mac"
	#define SYSTEMID SYSID_APPLE
#elif __linux__
  #ifdef __i386__
	#define SYSTEM "i386"
	#define SYSTEMID SYSID_I386
  #elif __x86_64__
	#define SYSTEM "x86-64"
	#define SYSTEMID SYSID_X86_64
  #else
	#define SYSTEM "linux"
	#define SYSTEMID SYSID_LINUX
  #endif
#elif __unix__
	#define SYSTEM "unix"
	#define SYSTEMID SYSID_UNIX
#else
	#define SYSTEM "unknown"
	#define SYSTEMID SYSID_UNKNOWN
#endif

///////////////////////////////////////////////////////////////////////////////

#define KiB 1024
#define MiB (1024*1024)
#define GiB (1024*1024*1024)
#define TiB (1024ull*1024*1024*1024)
#define PiB (1024ull*1024*1024*1024*1024)

#define MIN_SPARSE_HOLE_SIZE 1024 // bytes
#define TRACE_SEEK_FORMAT "%-20.20s f=%d,%p %9llx%s\n"
#define TRACE_RDWR_FORMAT "%-20.20s f=%d,%p %9llx..%9llx %8zx%s\n"

#define MAX_SPLIT_FILES		100
#define MIN_SPLIT_SIZE		100000000
#define ISO_SPLIT_DETECT_SIZE	(4ull*GiB)
#define HD_SECTOR_SIZE		0x200

#define DEF_SPLIT_SIZE		4000000000ull
#define DEF_SPLIT_SIZE_WBFS	0xffff8000ull

//
///////////////////////////////////////////////////////////////////////////////
///////////////                       Setup                     ///////////////
///////////////////////////////////////////////////////////////////////////////

void SetupLib ( int argc, char ** argv, ccp p_progname, enumProgID prid );

typedef enumError (*check_opt_func) ( int argc, char ** argv, int mode );

enumError CheckEnvOptions ( ccp varname, check_opt_func, int mode );

//
///////////////////////////////////////////////////////////////////////////////
///////////////                  EXTENDED_ERRORS                ///////////////
///////////////////////////////////////////////////////////////////////////////

#undef XPARM
#undef XCALL
#undef XERROR0
#undef XERROR1

#if EXTENDED_IO_FUNC

 #define XPARM ccp func, ccp file, uint line,
 #define XCALL func,file,line,
 #define XERROR0 func,file,line,0
 #define XERROR1 func,file,line,errno

 #define ResetFile(f,r)		XResetFile	(__FUNCTION__,__FILE__,__LINE__,f,r)
 #define ClearFile(f,r)		XClearFile	(__FUNCTION__,__FILE__,__LINE__,f,r)
 #define CloseFile(f,r)		XCloseFile	(__FUNCTION__,__FILE__,__LINE__,f,r)
 #define SetFileTime(f,s)	XSetFileTime	(__FUNCTION__,__FILE__,__LINE__,f,s)
 #define OpenFile(f,n,i)	XOpenFile	(__FUNCTION__,__FILE__,__LINE__,f,n,i)
 #define OpenFileModify(f,n,i)	XOpenFileModify	(__FUNCTION__,__FILE__,__LINE__,f,n,i)
 #define CheckCreated(f,d)	XCheckCreated	(__FUNCTION__,__FILE__,__LINE__,f,d)
 #define CreateFile(f,n,i,o)	XCreateFile	(__FUNCTION__,__FILE__,__LINE__,f,n,i,o)
 #define OpenStreamFile(f)	XOpenStreamFile	(__FUNCTION__,__FILE__,__LINE__,f)
 #define SetupSplitFile(f,m,s)	XSetupSplitFile	(__FUNCTION__,__FILE__,__LINE__,f,m,s)
 #define CreateSplitFile(f,i)	XCreateSplitFile(__FUNCTION__,__FILE__,__LINE__,f,i)
 #define FindSplitFile(f,i,o)	XFindSplitFile	(__FUNCTION__,__FILE__,__LINE__,f,i,o)
 #define PrintErrorFT(f,m)	XPrintErrorFT	(__FUNCTION__,__FILE__,__LINE__,f,m)
 #define AnalyseWH(f,h,p)	XAnalyseWH	(__FUNCTION__,__FILE__,__LINE__,f,h,p)
 #define TellF(f)		XTellF		(__FUNCTION__,__FILE__,__LINE__,f)
 #define SeekF(f,o)		XSeekF		(__FUNCTION__,__FILE__,__LINE__,f,o)
 #define SetSizeF(f,o)		XSetSizeF	(__FUNCTION__,__FILE__,__LINE__,f,o)
 #define ReadF(f,b,c)		XReadF		(__FUNCTION__,__FILE__,__LINE__,f,b,c)
 #define WriteF(f,b,c)		XWriteF		(__FUNCTION__,__FILE__,__LINE__,f,b,c)
 #define WriteSparseF(f,b,c)	XWriteSparseF	(__FUNCTION__,__FILE__,__LINE__,f,b,c)
 #define ReadAtF(f,o,b,c)	XReadAtF	(__FUNCTION__,__FILE__,__LINE__,f,o,b,c)
 #define WriteAtF(f,o,b,c)	XWriteAtF	(__FUNCTION__,__FILE__,__LINE__,f,o,b,c)
 #define WriteSparseAtF(f,o,b,c)XWriteSparseAtF	(__FUNCTION__,__FILE__,__LINE__,f,o,b,c)
 #define CreateOutFile(o,f,m,w)	XCreateOutFile	(__FUNCTION__,__FILE__,__LINE__,o,f,m,w)
 #define CloseOutFile(o,s)	XCloseOutFile	(__FUNCTION__,__FILE__,__LINE__,o,s)
 #define RemoveOutFile(o)	XRemoveOutFile	(__FUNCTION__,__FILE__,__LINE__,o)

#else

 #define XPARM
 #define XCALL
 #define XERROR0 __FUNCTION__,__FILE__,__LINE__,0
 #define XERROR1 __FUNCTION__,__FILE__,__LINE__,errno

 #define ResetFile(f,r)		XResetFile	(f,r)
 #define ClearFile(f,r)		XClearFile	(f,r)
 #define CloseFile(f,r)		XCloseFile	(f,r)
 #define SetFileTime(f,s)	XSetFileTime	(f,s)
 #define OpenFile(f,n,i)	XOpenFile	(f,n,i)
 #define OpenFileModify(f,n,i)	XOpenFileModify	(f,n,i)
 #define CheckCreated(f,d)	XCheckCreated	(f,d)
 #define CreateFile(f,n,i,o)	XCreateFile	(f,n,i,o)
 #define OpenStreamFile(f)	XOpenStreamFile	(f)
 #define SetupSplitFile(f,m,s)	XSetupSplitFile	(f,m,s)
 #define CreateSplitFile(f,i)	XCreateSplitFile(f,i)
 #define FindSplitFile(f,i,o)	XFindSplitFile	(f,i,o)
 #define PrintErrorFT(f,m)	XPrintErrorFT	(f,m)
 #define AnalyseWH(f,h,p)	XAnalyseWH	(f,h,p)
 #define TellF(f)		XTellF		(f)
 #define SeekF(f,o)		XSeekF		(f,o)
 #define SetSizeF(f,o)		XSetSizeF	(f,o)
 #define ReadF(f,b,c)		XReadF		(f,b,c)
 #define WriteF(f,b,c)		XWriteF		(f,b,c)
 #define WriteSparseF(f,b,c)	XWriteSparseF	(f,b,c)
 #define ReadAtF(f,o,b,c)	XReadAtF	(f,o,b,c)
 #define WriteAtF(f,o,b,c)	XWriteAtF	(f,o,b,c)
 #define WriteSparseAtF(f,o,b,c)XWriteSparseAtF	(f,o,b,c)
 #define CreateOutFile(o,f,m,w)	XCreateOutFile	(o,f,m,w)
 #define CloseOutFile(o,s)	XCloseOutFile	(o,s)
 #define RemoveOutFile(o)	XRemoveOutFile	(o)

#endif

//
///////////////////////////////////////////////////////////////////////////////
///////////////                    timer                        ///////////////
///////////////////////////////////////////////////////////////////////////////

u32 GetTimerMSec();
ccp PrintMSec ( char * buf, int bufsize, u32 msec, bool PrintMSec );

//
///////////////////////////////////////////////////////////////////////////////
///////////////                   file support                  ///////////////
///////////////////////////////////////////////////////////////////////////////

typedef enum enumIOMode
{
	IOM_IS_WBFS		= 0x01, // is a WPFS partition
	IOM_IS_IMAGE		= 0x02, // is a WDF or ISO file
	//IOM_IS_OTHER		= 0x04, // is an other file

	IOM__IS_MASK		= 0x03,
	IOM__IS_DEFAULT		= 0,

	IOM_FORCE_STREAM	= IOM__IS_MASK + 1,
	IOM_NO_STREAM		= 0

} enumIOMode;

extern enumIOMode opt_iomode;

//-----------------------------------------------------------------------------

typedef enum enumOFT
{
	OFT_UNKNOWN,		// not specified yet

	OFT_PLAIN,		// plain (ISO) file
	OFT_WDF,		// WDF file
	OFT_WBFS,		// WBFS disc

	OFT__N,			// number of variants
	OFT__DEFAULT = OFT_WDF	// default value

} enumOFT;

extern enumOFT output_file_type;
extern ccp oft_ext [OFT__N+1]; // NULL terminated list
extern ccp oft_name[OFT__N+1]; // NULL terminated list

enumOFT CalcOFT ( enumOFT force, ccp fname_dest, ccp fname_src, enumOFT def );

//-----------------------------------------------------------------------------

typedef enum enumFileType
{
    // 1. file types

	FT_UNKNOWN	= 0x0000,  // not analysed yet

	FT_ID_DIR	= 0x0001,  // is a directory
	FT_ID_WBFS	= 0x0002,  // file is a WBFS
	FT_ID_ISO	= 0x0004,  // file is a ISO image
	FT_ID_OTHER	= 0x0008,  // file neither a WBFS nor a ISO image
	FT__ID_MASK	= 0x000f,  // mask of all 'FT_ID_' values

    // 2. attributes

	FT_A_ISO	= 0x0100,  // file is a ISO image or a WDISC
	FT_A_WDISC	= 0x0200,  // flag: specific disc of an WBFS file
	FT_A_WDF	= 0x0400,  // flag: file is a packed WDF
	FT_A_REGFILE	= 0x0800,  // flag: file is a regular file
	FT_A_BLOCKDEV	= 0x1000,  // flag: file is a block device
	FT_A_SEEKABLE	= 0x2000,  // flag: using of seek() is possible
	FT_A_WRITING	= 0x4000,  // is opened for writing
	FT__A_MASK	= 0x7f00,  // mask of all 'FT_F_' values

    // 3. mask of all 'FT_ values

	FT__MASK	= FT__ID_MASK | FT__A_MASK,

} enumFileType;

//-----------------------------------------------------------------------------

#if CACHE_ENABLED

 typedef struct FileCache_t
 {
	off_t	off;			// file offset
	size_t	count;			// size of cached data
	ccp	data;			// pointer to cached data (alloced)
	struct FileCache_t * next;	// NULL or pointer to next element

 } FileCache_t;

#endif

//-----------------------------------------------------------------------------

typedef struct File_t
{
	// file handles and status

	int fd;			// file handle, -1=invalid
	FILE * fp;		// stream handle, 0=invalid
	struct stat st;		// file status after OpenFile()
	int  active_open_flags;	// active open flags.
	enumFileType ftype;	// the type of the file
	bool is_reading;	// file opened in read mode;
	bool is_writing;	// file opened in write mode;
	bool is_stdfile;	// file is stdin or stdout
	bool seek_allowed;	// seek is allowed (regular file or block device)
	char id6[7];		// ID6 of a iso image

	// file names, alloced

	ccp fname;		// current virtual filename
	ccp path;		// not NULL: path of real file (not realpath)
	ccp rename;		// not NULL: rename rename to fname if closed
	ccp outname;		// not NULL: hint for a good output filename
				// outname is without path/directory or extension

	// options set by user, not resetted by ResetFile()

	int  open_flags;	// proposed open flags; if zero then ignore
	bool disable_errors;	// don't print error messages

	// error codes

	enumError last_error;	// error code of last operation
	enumError max_error;	// max error code since open/create

	// offset handling

	off_t file_off;	// current real file offset
	off_t cur_off;	// current virtual file offset
	off_t max_off;	// max file offset
	int   read_behind_eof;	// 0:disallow, 1:allow+print warning, 2:allow silently

 #if CACHE_ENABLED

	// cache

	bool is_caching;	// true if cache is active
	FileCache_t *cache;	// data cache
	FileCache_t *cur_cache;	// pointer to current cache entry
 #endif

	// split file support

	struct File_t **split_f; // list with pointers to the split files
	int split_used;		 // number of used split files in 'split_f'
	off_t split_filesize;	 // max file size for new files
	ccp split_fname_format;	 // format with '%u' at the end for 'fname'
	ccp split_rename_format; // format with '%u' at the end for 'rename'

	// wbfs vars

	u32 sector_size;	// size of one hd sector, default = 512

	// statistics

	u32 tell_count;		// number of successfull tell operations
	u32 seek_count;		// number of successfull seek operations
	u32 setsize_count;	// number of successfull set-size operations
	u32 read_count;		// number of successfull read operations
	u32 write_count;	// number of successfull write operations
	u64 bytes_read;		// number of bytes read
	u64 bytes_written;	// number of bytes written

} File_t;

//-----------------------------------------------------------------------------

// initialize, reset and close files
void InitializeFile	( File_t * f );
enumError XResetFile	( XPARM File_t * f, bool remove_file );
enumError XClearFile	( XPARM File_t * f, bool remove_file );
enumError XCloseFile	( XPARM File_t * f, bool remove_file );
enumError XSetFileTime	( XPARM File_t * f, struct stat * st );

// open files
enumError XOpenFile       ( XPARM File_t * f, ccp fname, enumIOMode iomode );
enumError XOpenFileModify ( XPARM File_t * f, ccp fname, enumIOMode iomode );
enumError XCreateFile     ( XPARM File_t * f, ccp fname, enumIOMode iomode, int overwrite );
enumError XCheckCreated   ( XPARM             ccp fname, bool disable_errors );
enumError XOpenStreamFile ( XPARM File_t * f );
enumError XSetupSplitFile ( XPARM File_t *f, enumOFT oft, off_t file_size );
enumError XCreateSplitFile( XPARM File_t *f, uint split_idx );
enumError XFindSplitFile  ( XPARM File_t *f, uint * index, off_t * off );

// copy filedesc
void CopyFD ( File_t * dest, File_t * src );

// cache support
#if CACHE_ENABLED
 void DefineCachedArea    ( File_t * f, off_t off, size_t count );
 void DefineCachedAreaISO ( File_t * f, bool head_only );
#endif

struct WDF_Head_t;
enumError XAnalyseWH ( XPARM File_t * f, struct WDF_Head_t * wh, bool print_err );

enumError StatFile ( struct stat * st, ccp fname, int fd );

//-----------------------------------------------------------------------------
// file io with error messages

enumError XTellF	 ( XPARM File_t * f );
enumError XSeekF	 ( XPARM File_t * f, off_t off );
enumError XSetSizeF	 ( XPARM File_t * f, off_t off );
enumError XReadF	 ( XPARM File_t * f,                    void * iobuf, size_t count );
enumError XWriteF	 ( XPARM File_t * f,              const void * iobuf, size_t count );
enumError XWriteSparseF  ( XPARM File_t * f,              const void * iobuf, size_t count );
enumError XReadAtF	 ( XPARM File_t * f, off_t off,       void * iobuf, size_t count );
enumError XWriteAtF	 ( XPARM File_t * f, off_t off, const void * iobuf, size_t count );
enumError XWriteSparseAtF( XPARM File_t * f, off_t off, const void * iobuf, size_t count );

//-----------------------------------------------------------------------------
// wrapper functions

int WrapperReadSector  ( void * handle, u32 lba, u32 count, void * iobuf );
int WrapperWriteSector ( void * handle, u32 lba, u32 count, void * iobuf );

//-----------------------------------------------------------------------------
// split file support

int CalcSplitFilename ( char * buf, size_t buf_size, ccp path, enumOFT oft );
char * AllocSplitFilename ( ccp path, enumOFT oft );

//-----------------------------------------------------------------------------
// filename generation

char * NormalizeFileName ( char * buf, char * buf_end, ccp source, bool allow_slash );

void SetFileName      ( File_t * f, ccp source, bool allow_slash );
void GenFileName      ( File_t * f, ccp path, ccp name, ccp title, ccp id6, ccp ext );
void GenDestFileName  ( File_t * f, ccp dest, ccp default_name, ccp ext, ccp * rm_ext );
void GenImageFileName ( File_t * f, ccp dest, ccp default_name, enumOFT oft );

//-----------------------------------------------------------------------------
// etc

int    GetFD ( File_t * f );
FILE * GetFP ( File_t * f );
char   GetFT ( File_t * f );

bool IsFileOpen ( File_t * f );
bool IsFileSplitted ( File_t * f );

bool IsDirectory ( ccp fname, bool answer_if_empty );

//
///////////////////////////////////////////////////////////////////////////////
///////////////                string functions                 ///////////////
///////////////////////////////////////////////////////////////////////////////

extern const char EmptyString[];
extern const char MinusString[];
extern const char LongSep[]; // 160 * '-' + NULL

//-----

// frees string if str is not NULL|EmptyString|MinusString
void FreeString ( ccp str );

//-----

// StringCopy(), StringCopyE(), StringCat*()
//	RESULT: end of copied string pointing to NULL.
//	'src*' may be a NULL pointer.

char * StringCopyS ( char * buf, size_t bufsize, ccp src );
char * StringCat2S ( char * buf, size_t bufsize, ccp src1, ccp src2 );
char * StringCat3S ( char * buf, size_t bufsize, ccp src1, ccp src2, ccp src3 );

char * StringCopyE ( char * buf, char * buf_end, ccp src );
char * StringCat2E ( char * buf, char * buf_end, ccp src1, ccp src2 );
char * StringCat3E ( char * buf, char * buf_end, ccp src1, ccp src2, ccp src3 );

//-----

int  CheckID	    ( ccp id4_or_6 );		// check up to 7 chars
int  CheckIDnocase  ( ccp id4_or_6 );		// check up to 7 chars, ignoring case
bool CheckID6	    ( const void * id6  );	// exactly the first 6 bytes are checked
int  CountIDChars   ( ccp id );			// count number of allowed ID characters
char * ScanID	    ( char * destbuf7, int * destlen, ccp source );

char * ScanNumU32   ( ccp arg, u32 * p_stat, u32 * p_num,            u32 min, u32 max );
char * ScanRangeU32 ( ccp arg, u32 * p_stat, u32 * p_n1, u32 * p_n2, u32 min, u32 max );

///////////////////////////////////////////////////////////////////////////////
///////////////                     scan size                   ///////////////
///////////////////////////////////////////////////////////////////////////////

u64 ScanSizeFactor ( char ch_factor, int force_base );

char * ScanSizeTerm ( double * num, ccp source,
		      u64 default_factor, int force_base );

char * ScanSize ( double * num, ccp source,
		  u64 default_factor1, u64 default_factor2, int force_base );

char * ScanSizeU32 ( u32 * num, ccp source,
		     u64 default_factor1, u64 default_factor2, int force_base );

char * ScanSizeU64 ( u64 * num, ccp source,
		     u64 default_factor1, u64 default_factor2, int force_base );

enumError ScanSizeOpt
	( double * num, ccp source,
	  u64 default_factor1, u64 default_factor2, int force_base,
	  ccp opt_name, u64 min, u64 max, bool print_err );

enumError ScanSizeOptU64
	( u64 * num, ccp source, u64 default_factor1, int force_base,
	  ccp opt_name, u64 min, u64 max, u32 multiple, u32 pow2, bool print_err );

enumError ScanSizeOptU32
	( u32 * num, ccp source, u64 default_factor1, int force_base,
	  ccp opt_name, u64 min, u64 max, u32 multiple, u32 pow2, bool print_err );

//
///////////////////////////////////////////////////////////////////////////////
///////////////              string fields & lists              ///////////////
///////////////////////////////////////////////////////////////////////////////

typedef struct StringField_t
{
	ccp * field;	// pointer to the string field
	uint used;	// number of used titles in the title field
	uint size;	// number of allocated pointer in 'field'

} StringField_t;

//-----------------------------------------------------------------------------

void InitializeStringField ( StringField_t * sf );
void ResetStringField ( StringField_t * sf );

// return: pointer to matched key if the key is in the field.
ccp FindStringField ( StringField_t * sf, ccp key );

// return: true if item inserted/deleted
bool InsertStringField ( StringField_t * sf, ccp key, bool move_key );
bool RemoveStringField ( StringField_t * sf, ccp key );

// append at the and an do not sort
void AppendStringField ( StringField_t * sf, ccp key, bool move_key );

// return the index of the (next) item
uint FindStringFieldHelper ( StringField_t * sf, bool * found, ccp key );

///////////////////////////////////////////////////////////////////////////////

typedef struct StringList_t
{
	ccp str;
	struct StringList_t * next;

} StringList_t;

///////////////////////////////////////////////////////////////////////////////

typedef struct ParamList_t
{
	char * arg;
	char id6[7];
	char selector[7];
	int count;
	struct ParamList_t * next;

} ParamList_t;

extern uint n_param;
extern ParamList_t * first_param;
extern ParamList_t ** append_param;

///////////////////////////////////////////////////////////////////////////////

void AtFileHelper ( ccp arg, int mode, int (*func)(ccp arg,int mode) );

ParamList_t * AppendParam ( ccp arg, int is_temp );
int AddParam ( ccp arg, int is_temp );

//
///////////////////////////////////////////////////////////////////////////////
///////////////              string substitutions               ///////////////
///////////////////////////////////////////////////////////////////////////////

typedef struct SubstString_t
{
	char c1, c2;		// up to 2 codes (lower+upper case)
	bool allow_slash;	// true: allow slash in replacement
	ccp  str;		// pointer to string

} SubstString_t;

char * SubstString ( char * buf, size_t bufsize, SubstString_t * tab, ccp source );
int ScanEscapeChar ( ccp arg );

//
///////////////////////////////////////////////////////////////////////////////
///////////////                   Memory Maps                   ///////////////
///////////////////////////////////////////////////////////////////////////////

typedef struct MemMapItem_t
{
	off_t off;
	off_t size;
	u8    overlap;
	char  info[63];

} MemMapItem_t;

//-----------------------------------------------------------------------------

typedef struct MemMap_t
{
	MemMapItem_t ** field;	// pointer to the item field
	uint used;		// number of used titles in the item field
	uint size;		// number of allocated pointer in 'field'

} MemMap_t;

//-----------------------------------------------------------------------------
//	Memory maps allow duplicate entries.
//	The off+size pair is used as key.
//	The entries are sorted by off and size (small values first).
//-----------------------------------------------------------------------------

void InitializeMemMap ( MemMap_t * mm );
void ResetMemMap ( MemMap_t * mm );

// Return: pointer to the first matched key (=off,size) if the key is in the field.
//MemMapItem_t * FindMemMap ( MemMap_t * mm, off_t off, off_t size );

// Return pointer to new item (never NULL)
MemMapItem_t * InsertMemMap ( MemMap_t * mm, off_t off, off_t size );

// Remove all entires witk key. Return number of delete entries
//uint RemoveMemMap ( MemMap_t * mm, off_t off, off_t size );

// Return the index of the found or next item
uint FindMemMapHelper ( MemMap_t * mm, off_t off, off_t size );

// Calculate overlaps. Return number of items with overlap.
uint CalcoverlapMemMap ( MemMap_t * mm );

// Print out memory map
void PrintMemMap ( MemMap_t * mm, FILE * f, int indent );

//
///////////////////////////////////////////////////////////////////////////////
///////////////                     etc                         ///////////////
///////////////////////////////////////////////////////////////////////////////

typedef enum SortMode
{
	SORT_NONE,	// == 0
	SORT_ID,
	SORT_NAME,
	SORT_TITLE,
	SORT_FILE,
	SORT_SIZE,
	SORT_REGION,
	SORT_WBFS,
	SORT_NPART,
	SORT_DEFAULT,

	SORT__ERROR = -1 // not a mode but an error message

} SortMode;

extern SortMode sort_mode;

SortMode ScanSortMode ( ccp arg );

///////////////////////////////////////////////////////////////////////////////

typedef enum RepairMode
{
	REPAIR_NONE		=     0,

	REPAIR_FBT		= 0x001, // repair free blocks table

	REPAIR_RM_INVALID	= 0x010, // remove discs with invalid blocks
	REPAIR_RM_OVERLAP	= 0x020, // remove discs with overlaped blocks
	REPAIR_RM_FREE		= 0x040, // remove discs with free marked blocks
	REPAIR_RM_EMPTY		= 0x080, // remove discs with no valid blocks
	REPAIR_RM_ALL		= 0x0f0, // remove all discs with errors

	REPAIR_ALL		= 0x0f1, // repair all

	REPAIR__ERROR	= -1 // not a mode but an error message

} RepairMode;

extern RepairMode repair_mode;

RepairMode ScanRepairMode ( ccp arg );

///////////////////////////////////////////////////////////////////////////////

#define COMMAND_MAX 100

typedef struct CommandTab_t
{
	int  id;
	ccp  name1;
	ccp  name2;
	uint mode;	// -> allowed_options;

} CommandTab_t;

CommandTab_t * ScanCommand ( int * stat, ccp arg, CommandTab_t * tab );
int ScanCommandList ( ccp arg, CommandTab_t * cmd_tab );

///////////////////////////////////////////////////////////////////////////////
///////////////                     vars                        ///////////////
///////////////////////////////////////////////////////////////////////////////

extern enumProgID prog_id;
extern u32 revision_id;
extern ccp progname;
extern ccp search_path[];
extern ccp lang_info;
extern volatile int SIGINT_level;
extern volatile int verbose;
extern int progress;
extern bool use_utf8;
extern char escape_char;
extern char iobuf[0x100000];

extern StringField_t source_list;
extern StringField_t recurse_list;
extern StringField_t created_files;

///////////////////////////////////////////////////////////////////////////////
///////////////                    random mumbers               ///////////////
///////////////////////////////////////////////////////////////////////////////

u32 Random32 ( u32 max );
u64 Seed32Time();
u64 Seed32 ( u64 base );

//
///////////////////////////////////////////////////////////////////////////////
///////////////                     END                         ///////////////
///////////////////////////////////////////////////////////////////////////////

#endif // WWT_LIB_STD_H 1
