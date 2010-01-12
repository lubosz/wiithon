
#define _GNU_SOURCE 1

#include <sys/types.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <stdlib.h>
#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include <errno.h>
#include <ctype.h>
#include <signal.h>
#include <utime.h>

#if defined(__CYGWIN__)
  #include <cygwin/fs.h>
  #include <io.h>
  //#include <locale.h>
#elif defined(__APPLE__)
  #include <sys/disk.h>
#elif defined(__linux__)
  #include <linux/fs.h>
#endif

#include "libwbfs.h"
#include "types.h"
#include "debug.h"
#include "version.h"
#include "lib-std.h"
#include "lib-wdf.h"
#include "wbfs-interface.h"

//
///////////////////////////////////////////////////////////////////////////////
///////////////                       Setup                     ///////////////
///////////////////////////////////////////////////////////////////////////////

enumProgID prog_id		= PROG_UNKNOWN;
u32 revision_id			= SYSTEMID + REVISION_NUM;
ccp progname			= "?";
ccp search_path[5]		= {0};
ccp lang_info			= 0;
volatile int SIGINT_level	= 0;
volatile int verbose		= 0;
int progress			= 0;
SortMode sort_mode		= SORT_DEFAULT;
RepairMode repair_mode		= REPAIR_NONE;
char escape_char		= '%';
enumOFT output_file_type	= OFT_UNKNOWN;

#ifdef __CYGWIN__
 bool use_utf8			= false;
#else
 bool use_utf8			= true;
#endif

char iobuf[0x100000];

StringField_t source_list;
StringField_t recurse_list;
StringField_t created_files;

///////////////////////////////////////////////////////////////////////////////

static void sig_handler ( int signum )
{
    static const char usr_msg[] =
	"\n"
	"\t****************************************************************\n"
	"\t***  SIGNAL USR%d CATCHED: VERBOSE LEVEL %s TO %-2d      ***\n"
	"\t***  THE EFFECT IS DELAYED UNTIL BEGINNING OF THE NEXT JOB.  ***\n"
	"\t****************************************************************\n";

    fflush(stdout);
    switch(signum)
    {
      case SIGINT:
      case SIGTERM:
	SIGINT_level++;
	TRACE("#SIGNAL# INT/TERM, level = %d\n",SIGINT_level);

	switch(SIGINT_level)
	{
	  case 1:
	    fprintf(stderr,
		"\n"
		"\t****************************************************************\n"
		"\t***  PROGRAM INTERRUPTED BY USER (LEVEL=%d).                  ***\n"
		"\t***  PROGRAM WILL TERMINATE AFTER CURRENT JOB HAS FINISHED.  ***\n"
		"\t****************************************************************\n"
		, SIGINT_level );
	    break;

	  case 2:
	    fprintf(stderr,
		"\n"
		"\t*********************************************************\n"
		"\t***  PROGRAM INTERRUPTED BY USER (LEVEL=%d).           ***\n"
		"\t***  PROGRAM WILL TRY TO TERMINATE NOW WITH CLEANUP.  ***\n"
		"\t*********************************************************\n"
		, SIGINT_level );
	    break;

	  default:
	    fprintf(stderr,
		"\n"
		"\t*************************************************************\n"
		"\t***  PROGRAM INTERRUPTED BY USER (LEVEL=%d).               ***\n"
		"\t***  PROGRAM WILL TERMINATE IMMEDIATELY WITHOUT CLEANUP.  ***\n"
		"\t*************************************************************\n"
		, SIGINT_level );
	    fflush(stderr);
	    exit(ERR_INTERRUPT);
	  }
	  break;

      case SIGUSR1:
	if ( verbose >= 0 )
	    verbose--;
	TRACE("#SIGNAL# USR1: verbose = %d\n",verbose);
	fprintf(stderr,usr_msg,1,"DECREASED",verbose);
	break;

      case SIGUSR2:
	if ( verbose < 4 )
	    verbose++;
	TRACE("#SIGNAL# USR2: verbose = %d\n",verbose);
	fprintf(stderr,usr_msg,2,"INCREASED",verbose);
	break;

      default:
	TRACE("#SIGNAL# %d\n",signum);
    }
    fflush(stderr);
}

///////////////////////////////////////////////////////////////////////////////

void SetupLib ( int argc, char ** argv, ccp p_progname, enumProgID prid )
{
 #ifdef DEBUG
    if (!TRACE_FILE)
    {
	char fname[100];
	snprintf(fname,sizeof(fname),"_trace-%s.tmp",p_progname);
	TRACE_FILE = fopen(fname,"w");
	if (!TRACE_FILE)
	    fprintf(stderr,"open TRACE_FILE failed: %s\n",fname);
    }
 #endif

    TRACE_SIZEOF(bool);
    TRACE_SIZEOF(short);
    TRACE_SIZEOF(int);
    TRACE_SIZEOF(long);
    TRACE_SIZEOF(long long);
    TRACE_SIZEOF(size_t);
    TRACE_SIZEOF(off_t);

    TRACE_SIZEOF(u8);
    TRACE_SIZEOF(u16);
    TRACE_SIZEOF(u32);
    TRACE_SIZEOF(u64);
    TRACE_SIZEOF(s8);
    TRACE_SIZEOF(s16);
    TRACE_SIZEOF(s32);
    TRACE_SIZEOF(s64);

    TRACE_SIZEOF(StringField_t);
    TRACE_SIZEOF(StringList_t);
    TRACE_SIZEOF(CommandTab_t);
    TRACE_SIZEOF(ParamList_t);
    TRACE_SIZEOF(PartitionInfo_t);
    TRACE_SIZEOF(MemMapItem_t);
    TRACE_SIZEOF(MemMap_t);

    TRACE_SIZEOF(FileCache_t);
    TRACE_SIZEOF(File_t);
    TRACE_SIZEOF(SuperFile_t);

    TRACE_SIZEOF(WDF_Hole_t);
    TRACE_SIZEOF(WDF_Head_t);
    TRACE_SIZEOF(WDF_Chunk_t);

    TRACE_SIZEOF(WBFS_t);
    TRACE_SIZEOF(CheckDisc_t);
    TRACE_SIZEOF(CheckWBFS_t);

    TRACE_SIZEOF(WDiscHeader_t);
    TRACE_SIZEOF(WDRegionSet_t);
    TRACE_SIZEOF(WDPartCount_t);
    TRACE_SIZEOF(WDPartTableEntry_t);
    TRACE_SIZEOF(WDPartHead_t);
    TRACE_SIZEOF(WDPartInfo_t);
    TRACE_SIZEOF(WDiscInfo_t);
    TRACE_SIZEOF(WDiscListItem_t);
    TRACE_SIZEOF(WDiscList_t);

    ASSERT( 1 == sizeof(u8) );
    ASSERT( 2 == sizeof(u16) );
    ASSERT( 4 == sizeof(u32) );
    ASSERT( 8 == sizeof(u64) );
    ASSERT( 1 == sizeof(s8) );
    ASSERT( 2 == sizeof(s16) );
    ASSERT( 4 == sizeof(s32) );
    ASSERT( 8 == sizeof(s64) );

    ASSERT( sizeof(WDiscHeader_t) == 0x100 );

    //----- setup textmode for cygwin stdout+stderr 

    #if defined(__CYGWIN__)
	setmode(fileno(stdout),O_TEXT);
	setmode(fileno(stderr),O_TEXT);
	//setlocale(LC_ALL,"en_US.utf-8");
    #endif

    //----- setup prog id

    prog_id = prid;

    #ifdef WIIMM_TRUNC
	revision_id = (prid << 20) + SYSTEMID + REVISION_NUM + REVID_WIIMM_TRUNC;
    #elif defined(WIIMM)
	revision_id = (prid << 20) + SYSTEMID + REVISION_NUM + REVID_WIIMM;
    #else
	revision_id = (prid << 20) + SYSTEMID + REVISION_NUM + REVID_UNKNOWN;
    #endif

    //----- setup progname

    if ( argc > 0 && *argv && **argv )
	p_progname = *argv;
    progname = strrchr(p_progname,'/');
    progname = progname ? progname+1 : p_progname;
    argv[0] = (char*)progname;

    TRACE("##PROG## REV-ID=%08x, PROG-ID=%d, PROG-NAME=%s\n",
		revision_id, prog_id, progname );

    //----- setup signals

    static const int sigtab[] = { SIGTERM, SIGINT, SIGUSR1, SIGUSR2, -1 };
    int i;
    for ( i = 0; sigtab[i] >= 0; i++ )
    {
	struct sigaction sa;
	memset(&sa,0,sizeof(sa));
	sa.sa_handler = &sig_handler;
	sigaction(sigtab[i],&sa,0);
    }

    //----- setup search_path

    ccp *sp = search_path, *sp2;
    ASSERT( sizeof(search_path)/sizeof(*search_path) > 4 );

    // determine program path
    char proc_path[30];
    snprintf(proc_path,sizeof(proc_path),"/proc/%u/exe",getpid());
    TRACE("PROC-PATH: %s\n",proc_path);

    static char share[] = "/share/wwt/";
    static char local_share[] = "/usr/local/share/wwt/";

    char path[PATH_MAX];
    if (readlink(proc_path,path,sizeof(path)))
    {
	// program path found!
	TRACE("PROG-PATH: %s\n",path);

	char * file_ptr = strrchr(path,'/');
	if ( file_ptr )
	{
	    // seems to be a real path -> terminate string behind '/'
	    *++file_ptr = 0;
	    *sp = strdup(path);
	    if (!*sp)
		OUT_OF_MEMORY;
	    TRACE("SEARCH_PATH[%d] = %s\n",sp-search_path,*sp);
	    sp++;

	    if ( file_ptr-5 >= path && !memcmp(file_ptr-4,"/bin/",5) )
	    {
		StringCopyS(file_ptr-5,sizeof(path),share);
		*sp = strdup(path);
		if (!*sp)
		    OUT_OF_MEMORY;
		TRACE("SEARCH_PATH[%d] = %s\n",sp-search_path,*sp);
		sp++;
	    }
	}
    }

    // insert 'local_share' if not already done

    for ( sp2 = search_path; sp2 < sp && strcmp(*sp2,local_share); sp2++ )
	;
    if ( sp2 == sp )
    {
	*sp = strdup(local_share);
	if (!*sp)
	    OUT_OF_MEMORY;
	TRACE("SEARCH_PATH[%d] = %s\n",sp-search_path,*sp);
	sp++;
    }

    // insert CWD if not already done
    getcwd(path,sizeof(path)-1);
    strcat(path,"/");
    for ( sp2 = search_path; sp2 < sp && strcmp(*sp2,path); sp2++ )
	;
    if ( sp2 == sp )
    {
	*sp = strdup("./");
	if (!*sp)
	    OUT_OF_MEMORY;
	TRACE("SEARCH_PATH[%d] = %s\n",sp-search_path,*sp);
	sp++;
    }

    *sp = 0;
    ASSERT( sp - search_path < sizeof(search_path)/sizeof(*search_path) );

    //----- setup language info

    char * lc_ctype = getenv("LC_CTYPE");
    if (lc_ctype)
    {
	char * lc_ctype_end = lc_ctype;
	while ( *lc_ctype_end >= 'a' && *lc_ctype_end <= 'z' )
	    lc_ctype_end++;
	const int len = lc_ctype_end - lc_ctype;
	if ( len > 0 )
	{
	    char * temp = malloc(len+1);
	    if (!temp)
		OUT_OF_MEMORY;
	    memcpy(temp,lc_ctype,len);
	    temp[len] = 0;
	    lang_info = temp;
	    TRACE("LANG_INFO = %s\n",lang_info);
	}
    }
}

///////////////////////////////////////////////////////////////////////////////

enumError CheckEnvOptions ( ccp varname, check_opt_func func, int mode )
{
    TRACE("CheckEnvOptions(%s,%p,%d)\n",varname,func,mode);

    ccp env = getenv(varname);
    if ( !env || !*env )
	return ERR_OK;

    TRACE("env[%s] = %s\n",varname,env);

    const int envlen = strlen(env);
    char * buf = malloc(envlen+1);
    if (!buf)
	OUT_OF_MEMORY;
    char * dest = buf;

    int argc = 1; // argv[0] = progname
    ccp src = env;
    while (*src)
    {
	while ( *src > 0 && *src <= ' ' ) // skip blanks & control
	    src++;

	if (!*src)
	    break;

	argc++;
	while ( *(u8*)src > ' ' )
	    *dest++ = *src++;
	*dest++ = 0;
	ASSERT( dest <= buf+envlen+1 );
    }
    TRACE("argc = %d\n",argc);

    char ** argv = malloc((argc+1)*sizeof(*argv));
    if (!argv)
	OUT_OF_MEMORY;
    argv[0] = (char*)progname;
    argv[argc] = 0;
    dest = buf;
    int i;
    for ( i = 1; i < argc; i++ )
    {
	TRACE("argv[%d] = %s\n",i,dest);
	argv[i] = dest;
	while (*dest)
	    dest++;
	dest++;
	ASSERT( dest <= buf+envlen+1 );
    }

    enumError stat = func(argc,argv,mode);
    if (stat)
	fprintf(stderr,
	    "Errors above while scanning the environment variable '%s'\n",varname);

    // don't free() because is's possible that there are pointers to arguments
    //free(argv);
    //free(buf);

    return stat;
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////                  error messages                 ///////////////
///////////////////////////////////////////////////////////////////////////////

ccp GetErrorName ( int stat )
{
    switch(stat)
    {
	case ERR_OK:			return "OK";
	case ERR_DIFFER:		return "FILES DIFFER";
	case ERR_WARNING:		return "WARNING";

	case ERR_NO_WDF:		return "NO WDF";
	case ERR_WDF_VERSION:		return "WDF VERSION NOT SUPPORTED";
	case ERR_WDF_SPLIT:		return "SPLITTED WDF NOT SUPPORTED";
	case ERR_WDF_INVALID:		return "INVALID WDF";

	case ERR_WDISC_NOT_FOUND:	return "WDISC NOT FOUND";
	case ERR_NO_WBFS_FOUND:		return "NO WBFS FOUND";
	case ERR_TO_MUCH_WBFS_FOUND:	return "TO MUCH WBFS FOUND";
	case ERR_WBFS_INVALID:		return "INVALID WBFS";

	case ERR_ALREADY_EXISTS:	return "FILE ALREADY EXISTS";
	case ERR_CANT_OPEN:		return "CAN'T OPEN FILE";
	case ERR_CANT_CREATE:		return "CAN'T CREATE FILE";
	case ERR_CANT_CREATE_DIR:	return "CAN'T CREATE DIRECTORY";
	case ERR_WRONG_FILE_TYPE:	return "WRONG FILE TYPE";
	case ERR_READ_FAILED:		return "READ FILE FAILED";
	case ERR_REMOVE_FAILED:		return "REMOVE FILE FAILED";
	case ERR_WRITE_FAILED:		return "WRITE FILE FAILED";

	case ERR_WBFS:			return "WBFS ERROR";

	case ERR_MISSING_PARAM:		return "MISSING PARAMETERS";
	case ERR_SEMANTIC:		return "SEMANTIC ERROR";
	case ERR_SYNTAX:		return "SYNTAX ERROR";

	case ERR_INTERRUPT:		return "INTERRUPT";

	case ERR_NOT_IMPLEMENTED:	return "NOT IMPLEMENTED YET";
	case ERR_INTERNAL:		return "INTERNAL ERROR";
	case ERR_OUT_OF_MEMORY:		return "OUT OF MEMORY";
	case ERR_FATAL:			return "FATAL ERROR";
    }
    return "?";
}

///////////////////////////////////////////////////////////////////////////////

ccp GetErrorText ( int stat )
{
    switch(stat)
    {
	case ERR_OK:			return "Ok";
	case ERR_DIFFER:		return "Files differ";
	case ERR_WARNING:		return "Warning";

	case ERR_NO_WDF:		return "File is not a WDF";
	case ERR_WDF_VERSION:		return "WDF version not supported";
	case ERR_WDF_SPLIT:		return "Splitted WDF not supported";
	case ERR_WDF_INVALID:		return "Invalid WDF";

	case ERR_WDISC_NOT_FOUND:	return "Wii disc not found";
	case ERR_NO_WBFS_FOUND:		return "No WBFS found";
	case ERR_TO_MUCH_WBFS_FOUND:	return "To much WBFS found";
	case ERR_WBFS_INVALID:		return "Invalid WBFS";

	case ERR_ALREADY_EXISTS:	return "File already exists";
	case ERR_CANT_OPEN:		return "Can't open file";
	case ERR_CANT_CREATE:		return "Can't create file";
	case ERR_CANT_CREATE_DIR:	return "Can't create directory";
	case ERR_WRONG_FILE_TYPE:	return "Wrong type of file";
	case ERR_READ_FAILED:		return "Reading from file failed";
	case ERR_REMOVE_FAILED:		return "Removing a file failed";
	case ERR_WRITE_FAILED:		return "Writing to file failed";

	case ERR_WBFS:			return "WBFS error";

	case ERR_MISSING_PARAM:		return "Missing parameters";
	case ERR_SEMANTIC:		return "Semantic error";
	case ERR_SYNTAX:		return "Syntax error";

	case ERR_INTERRUPT:		return "Program interrupted";

	case ERR_NOT_IMPLEMENTED:	return "Not implemented yet";
	case ERR_INTERNAL:		return "Internal error";
	case ERR_OUT_OF_MEMORY:		return "Allocation of dynamc memory failed";
	case ERR_FATAL:			return "Fatal error";
    }
    return "?";
}

///////////////////////////////////////////////////////////////////////////////

enumError last_error = ERR_OK;
enumError max_error  = ERR_OK;
u32 error_count = 0;

///////////////////////////////////////////////////////////////////////////////

int PrintError ( ccp func, ccp file, uint line,
		int syserr, enumError err_code, ccp format, ... )
{
    fflush(stdout);
    char msg[1000];
    const int plen = strlen(progname)+2;

    if (format)
    {
	va_list arg;
	va_start(arg,format);
	vsnprintf(msg,sizeof(msg),format,arg);
	msg[sizeof(msg)-2] = 0;
	va_end(arg);

	const int mlen = strlen(msg);
	if ( mlen > 0 && msg[mlen-1] != '\n' )
	{
	    msg[mlen]   = '\n';
	    msg[mlen+1] = 0;
	}
    }
    else
	StringCat2S(msg,sizeof(msg),GetErrorText(err_code),"\n");

    ccp prefix = err_code == ERR_OK ? "" : err_code <= ERR_WARNING ? "! " : "!! ";

 #ifdef DEBUG
    TRACE("%s%s #%d [%s] in %s() @ %s#%d\n",
		prefix, err_code <= ERR_WARNING ? "WARNING" : "ERROR",
		err_code, GetErrorName(err_code), func, file, line );
    TRACE("%s%*s%s",prefix,plen,"",msg);
    if (syserr)
	TRACE("!! ERRNO=%d: %s\n",syserr,strerror(syserr));
    fflush(TRACE_FILE);
 #endif

 #if defined(EXTENDED_ERRORS)
    if ( err_code > ERR_WARNING )
 #else
    if ( err_code >= ERR_NOT_IMPLEMENTED )
 #endif
    {
	if ( err_code > ERR_WARNING )
	    fprintf(stderr,"%s%s: ERROR #%d [%s] in %s() @ %s#%d\n",
		prefix, progname, err_code, GetErrorName(err_code), func, file, line );
	else
	    fprintf(stderr,"%s%s: WARNING in %s() @ %s#%d\n",
		prefix, progname, func, file, line );

     #if defined(EXTENDED_ERRORS) && EXTENDED_ERRORS > 1
	fprintf(stderr,"%s -> %s/%s?annotate=%d#l%d\n",
		prefix, URI_VIEWVC, file, REVISION_NEXT, line );
     #endif

	fprintf(stderr, "%s%*s%s", prefix, plen,"", msg );
    }
    else
	fprintf(stderr,"%s%s: %s",prefix,progname,msg);

    if (syserr)
	fprintf(stderr,"%s%*s-> %s\n",prefix,plen,"",strerror(syserr));
    fflush(stderr);

    if ( err_code > ERR_OK )
	error_count++;

    last_error = err_code;
    if ( max_error < err_code )
	max_error = err_code;

    if ( err_code > ERR_NOT_IMPLEMENTED )
	exit(err_code);

    return err_code;
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////                    timer                        ///////////////
///////////////////////////////////////////////////////////////////////////////

u32 GetTimerMSec()
{
    struct timeval tval;
    gettimeofday(&tval,NULL);

    static time_t timebase = 0;
    if (!timebase)
	timebase = tval.tv_sec;

    return ( tval.tv_sec - timebase ) * 1000 + tval.tv_usec/1000;
}

///////////////////////////////////////////////////////////////////////////////

ccp PrintMSec ( char * buf, int bufsize, u32 msec, bool PrintMSec )
{
    if (PrintMSec)
	snprintf(buf,bufsize,"%02d:%02d:%02d.%03d",
	    msec/3600000, msec/60000%60, msec/1000%60, msec%1000 );
    else
	snprintf(buf,bufsize,"%02d:%02d:%02d",
	    msec/3600000, msec/60000%60, msec/1000%60 );
    ccp ptr = buf;
    int colon_counter = 0;
    while ( *ptr == '0' || *ptr == ':' && !colon_counter++ )
	ptr++;
    return *ptr == ':' ? ptr-1 : ptr;
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////                   file support                  ///////////////
///////////////////////////////////////////////////////////////////////////////

enumIOMode opt_iomode = IOM__IS_DEFAULT | IOM_FORCE_STREAM;

///////////////////////////////////////////////////////////////////////////////

static int valid_offset ( int fd, off_t off )
{
    //TRACE(" - valid_offset(%d,%llu=%#x)\n",fd,off,off);
    char ch;
    if (lseek(fd,off,SEEK_SET) == (off_t)-1 )
	return 0;
    return read(fd,&ch,1) == 1;
}

//-----------------------------------------------------------------------------

static off_t GetBlockDevSize ( int fd )
{
    TRACE("GetBlockDevSize(%d)\n",fd);

 #ifdef BLKGETSIZE64
    TRACE(" - try BLKGETSIZE64\n");
    {
	unsigned long long size64 = 0;
	if ( ioctl(fd, BLKGETSIZE64, &size64 ) >= 0 && size64 )
	    return size64;
    }
 #endif

 #ifdef DKIOCGETBLOCKCOUNT
    TRACE(" - try DKIOCGETBLOCKCOUNT\n");
    {
	unsigned long long size64 = 0;
	if ( ioctl(fd, DKIOCGETBLOCKCOUNT, &size64 ) >= 0  && size64 )
	    return size64 << 9;
    }
 #endif

 #ifdef BLKGETSIZE
    TRACE(" - try BLKGETSIZE\n");
    {
	unsigned long size32 = 0;
	if ( ioctl(fd, BLKGETSIZE, &size32 ) >= 0 && size32 )
	    return (off_t)size32 << 9;
    }
 #endif

    TRACE(" - try lseek(SEEK_END)\n");
    {
	off_t off = 0;
	off = lseek(fd,0,SEEK_END);
	if ( off && off != (off_t)-1 )
	{
	    lseek(fd,0,SEEK_SET);
	    return off;
	}
    }

    TRACE(" - try binary search\n");
    off_t low, high;
    for ( low = 0, high = GiB; high > low && valid_offset(fd,high); high *= 2 )
	low = high;

    while ( low < high - 1 )
    {
	const off_t mid = (low + high) / 2;
	if (valid_offset(fd,mid))
	    low = mid;
	else
	    high = mid;
    }
    lseek(fd,0,SEEK_SET);
    return low + 1;
}

///////////////////////////////////////////////////////////////////////////////

enumError StatFile ( struct stat * st, ccp fname, int fd )
{
    ASSERT(st);

    TRACE("StatFile(%s,%d)\n",fname?fname:"",fd);

    // normalize parameters
    if ( fname && *fname )
	fd = -1;
    else
	fname = 0;

    if ( fname ? stat(fname,st) : fstat(fd,st) )
    {
	memset(st,0,sizeof(*st));
	return ERR_WARNING;
    }

    TRACE(" - st_dev:     %llu\n",st->st_dev);
    TRACE(" - st_ino:     %llu\n",st->st_ino);
    TRACE(" - st_mode:    %u\n",st->st_mode);
    TRACE(" - st_nlink:   %u\n",st->st_nlink);
    TRACE(" - st_uid:     %u\n",st->st_uid);
    TRACE(" - st_gid:     %u\n",st->st_gid);
    TRACE(" - st_rdev:    %llu\n",st->st_rdev);
    TRACE(" - st_size:    %llu\n",st->st_size);
    TRACE(" - st_blksize: %llu\n",(u64)st->st_blksize);
    TRACE(" - st_blocks:  %llu\n",st->st_blocks);
    TRACE(" - st_atime:   %llu\n",(u64)st->st_atime);
    TRACE(" - st_mtime:   %llu\n",(u64)st->st_mtime);
    TRACE(" - st_ctime:   %llu\n",(u64)st->st_ctime);

    if ( !st->st_size && ( S_ISREG(st->st_mode) || S_ISBLK(st->st_mode)) )
    {
	if (fname)
	    fd = open(fname,O_RDONLY);

	if ( fd != -1 )
	{
	    if (S_ISBLK(st->st_mode))
	    {
		st->st_size = GetBlockDevSize(fd);
		TRACE(" + st_size:    %llu\n",st->st_size);
	    }

	    if (!st->st_size)
	    {
		st->st_size = lseek(fd,0,SEEK_END);
		TRACE(" + st_size:    %llu\n",st->st_size);
		lseek(fd,0,SEEK_SET);
	    }
	    
	    if (fname)
		close(fd);
	}
    }

    return ERR_OK;
}

///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////
// initialize, reset and close files

void InitializeFile ( File_t * f )
{
    TRACE("#F# InitializeFile(%p)\n",f);
    ASSERT(f);
    ASSERT(ERR_OK==0);

    memset(f,0,sizeof(*f));
    f->fd = -1;
    f->sector_size = 512;
    f->fname = EmptyString;
    f->split_fname_format = EmptyString;

    // normalize 'opt_iomode'
    opt_iomode = opt_iomode & IOM__IS_MASK | IOM_FORCE_STREAM;
    
 #ifdef __CYGWIN__
    opt_iomode |= IOM_IS_WBFS;
 #endif
}

///////////////////////////////////////////////////////////////////////////////

enumError XResetFile ( XPARM File_t * f, bool remove_file )
{
    TRACE("#F# ResetFile(%p,%d)\n",f,remove_file);
    ASSERT(f);
    enumError stat = XClearFile( XCALL f, remove_file );

    // save user settungs
    const bool open_flags	= f->open_flags;
    const bool disable_errors	= f->disable_errors;
    const bool create_directory	= f->create_directory;

    InitializeFile(f);

    // restore user settings
    f->open_flags	= open_flags;
    f->disable_errors	= disable_errors;
    f->create_directory	= create_directory;

    return stat;
}

///////////////////////////////////////////////////////////////////////////////

enumError XClearFile ( XPARM File_t * f, bool remove_file )
{
    ASSERT(f);
    TRACE("#F# ClearFile(%p,%d) fd=%d fp=%p\n",f,remove_file,f->fd,f->fp);

    enumError err = ERR_OK;
    if (f->split_f)
    {
	File_t **end, **ptr = f->split_f;
	for ( end = ptr + f->split_used; ptr < end; ptr++ )
	{
	    enumError err1 = XClearFile( XCALL *ptr, remove_file );
	    free(*ptr);
	    if ( err < err1 )
		err = err1;
	}
	free(f->split_f);
	f->split_f = 0;
	remove_file = false;
    };
    f->split_used = 0;

    enumError err1 = XCloseFile( XCALL f, remove_file );
    if ( err < err1 )
	err = err1;

    FreeString(f->fname);		f->fname		= EmptyString;
    FreeString(f->path);		f->path			= 0;
    FreeString(f->rename);		f->rename		= 0;
    FreeString(f->outname);		f->outname		= 0;
    FreeString(f->split_fname_format);	f->split_fname_format	= EmptyString;
    FreeString(f->split_rename_format);	f->split_rename_format	= 0;

    ASSERT(!f->is_caching);
    ASSERT(!f->cache);
    ASSERT(!f->cur_cache);

    f->last_error = err;
    if ( f->max_error < err )
	f->max_error = err;
    return err;
}

///////////////////////////////////////////////////////////////////////////////

enumError XCloseFile ( XPARM File_t * f, bool remove_file )
{
    ASSERT(f);
    TRACE("#F# CloseFile(%p,%d) fd=%d fp=%p\n",f,remove_file,f->fd,f->fp);

    bool close_err = false;
    if ( f->fp )
	close_err = fclose(f->fp) != 0;
    else if ( f->fd != -1 )
	close_err = close(f->fd) != 0;

    f->fp =  0;
    f->fd = -1;

    enumError err = ERR_OK;
    if (close_err)
    {
	err = f->is_writing ? ERR_WRITE_FAILED : ERR_READ_FAILED;
	if (!f->disable_errors)
	    PrintError( XERROR1, err,
		"Close file failed: %s\n", f->fname );
    }

    if (f->split_f)
    {
	File_t **end, **ptr = f->split_f;
	for ( end = ptr + f->split_used; ptr < end; ptr++ )
	{
	    TRACE("#S#%d# close %s\n",ptr-f->split_f,(*ptr)->fname);
	    enumError err1 = XCloseFile( XCALL *ptr, remove_file );
	    if ( err < err1 )
		err = err1;
	}
    }
    else if ( !f->is_stdfile && S_ISREG(f->st.st_mode) )
    {
	ccp path = f->path ? f->path : f->fname;
	if ( remove_file && path && *path )
	{
	    TRACE("REMOVE: %s\n",path);
	    unlink(path);
	}
	else if (f->rename)
	{
	    TRACE("RENAME: %s\n",path);
	    TRACE("    TO: %s\n",f->rename);
	    if (rename(path,f->rename))
	    {
		if (!f->disable_errors)
		    PrintError( XERROR1, ERR_CANT_CREATE,
			"Can't create file: %s\n", f->rename );
		if ( err < ERR_CANT_CREATE )
		    err = ERR_CANT_CREATE;
		unlink(path);
	    }
	    else
	    {
		FreeString(f->path);
		f->path = f->rename;
		f->rename = 0;
	    }
	}
    }

    f->is_caching = false;
    while (f->cache)
    {
	FileCache_t * ptr = f->cache;
	f->cache = ptr->next;
	free((char*)ptr->data);
	free(ptr);
    }
    f->cur_cache = 0;

    f->cur_off = f->file_off = 0;

    f->last_error = err;
    if ( f->max_error < err )
	f->max_error = err;
    return err;
}

///////////////////////////////////////////////////////////////////////////////

enumError XSetFileTime ( XPARM File_t * f, struct stat * st )
{
    // try to change time and ignore error messages

    ASSERT(f);

    enumError err = ERR_OK;
    if (st)
    {
	err = XCloseFile( XCALL f, false );

	struct utimbuf ubuf;
	ubuf.actime  = st->st_atime;
	ubuf.modtime = st->st_mtime;

	if (f->split_f)
	{
	    File_t **end, **ptr = f->split_f;
	    for ( end = ptr + f->split_used; ptr < end; ptr++ )
		utime((*ptr)->fname,&ubuf);
	}
	else
	    utime(f->fname,&ubuf);
    }
    return err;
}

///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////

static enumError XOpenFileHelper
	( XPARM File_t * f, enumIOMode iomode, int default_flags, int force_flags )
{
    ASSERT(f);
    TRACE("#F# OpenFileHelper(%p,%x,%x,%x) dis=%d, mkdir=%d\n",
		f, iomode, default_flags, force_flags,
		f->disable_errors, f->create_directory );

 #ifdef O_LARGEFILE
    TRACE("FORCE O_LARGEFILE\n");
    force_flags |= O_LARGEFILE;
 #endif

    f->active_open_flags = ( f->open_flags ? f->open_flags : default_flags )
			 | force_flags;

    const int mode_mask = O_RDONLY|O_WRONLY|O_RDWR;
    int mode = f->active_open_flags & mode_mask;
    if ( !mode || mode == O_RDONLY )
    {
	mode = O_RDONLY;
	f->is_reading = true;
    }
    else if ( mode == O_WRONLY )
    {
	f->is_writing = true;
    }
    else
    {
	mode = O_RDWR;
	f->is_reading = true;
	f->is_writing = true;
    }
    f->active_open_flags = f->active_open_flags & ~mode_mask | mode;

    if ( f->fd == -1 )
    {
	TRACE("open %s, create-dir=%d\n",f->fname,f->create_directory);
     #ifdef __CYGWIN__
	char * temp = AllocNormalizedFilename(f->fname);
	TRACE("open %p %p %s\n",f->fname,temp,temp);
	//FreeString(f->fname); // [2do] [memleak] -> forces a stack dump -- mhhm
	f->fname = temp;
     #endif
	f->fd = open( f->fname, f->active_open_flags, 0666 );
	if ( f->fd == -1 && f->create_directory )
	{
	    const enumError err = CreatePath(f->fname);
	    if (err)
		return err;
	    f->fd = open( f->fname, f->active_open_flags, 0666 );
	}
    }
    TRACE("#F# OpenFile '%s' fd=%d, dis=%d\n", f->fname, f->fd, f->disable_errors );

    if ( f->fd == -1 )
    {
	if ( f->active_open_flags & O_CREAT )
	{
	    f->max_error = f->last_error = ERR_CANT_CREATE;
	    if (!f->disable_errors)
		PrintError( XERROR1, f->last_error,
				"Can't create file: %s\n",f->fname);
	}
	else
	{
	    f->max_error = f->last_error = ERR_CANT_OPEN;
	    if (!f->disable_errors)
		PrintError( XERROR1, f->last_error,
				"Can't open file: %s\n",f->fname);
	}
    }
    else if (StatFile(&f->st,0,f->fd))
    {
	close(f->fd);
	f->fd = -1;
	f->max_error = f->last_error = ERR_READ_FAILED;
	if (!f->disable_errors)
	    PrintError( XERROR1, f->last_error,"Can't stat file: %s\n",f->fname);
    }
    else
    {
	f->seek_allowed = S_ISREG(f->st.st_mode) || S_ISBLK(f->st.st_mode);
	if ( iomode & opt_iomode )
	    XOpenStreamFile(XCALL f);
    }

    TRACE("#F# OpenFileHelper(%p) returns %d, fd=%d, fp=%p, seek-allowed=%d\n",
		f, f->last_error, GetFD(f), GetFP(f), f->seek_allowed );
    return f->last_error;
}

///////////////////////////////////////////////////////////////////////////////

enumError XOpenFile ( XPARM File_t * f, ccp fname, enumIOMode iomode )
{
    ASSERT(f);

    if (!fname)
    {
	fname = f->fname;
	f->fname = 0;
    }

    XResetFile( XCALL f, false );

    f->is_stdfile = fname[0] == '-' && !fname[1];
    if (f->is_stdfile)
    {
	f->fd    = dup(fileno(stdin));
	f->fname = strdup("- (stdin)");
    }
    else
	f->fname = strdup(fname);

    return XOpenFileHelper(XCALL f,iomode,O_RDONLY,O_RDONLY);
}

///////////////////////////////////////////////////////////////////////////////

enumError XOpenFileModify ( XPARM File_t * f, ccp fname, enumIOMode iomode )
{
    ASSERT(f);

    if (!fname)
    {
	fname = f->fname;
	f->fname = 0;
    }

    XResetFile( XCALL f, false );

    f->fname = strdup(fname);
    return XOpenFileHelper(XCALL f,iomode,O_RDWR,O_RDWR);
}

///////////////////////////////////////////////////////////////////////////////

enumError XCheckCreated ( XPARM ccp fname, bool disable_errors )
{
    if (!InsertStringField(&created_files,fname,false))
    {
	if (!disable_errors)
	    PrintError( XERROR0, ERR_CANT_CREATE,
		"File already created: %s\n", fname );
	return ERR_CANT_CREATE;
    }
    return ERR_OK;
}

///////////////////////////////////////////////////////////////////////////////

enumError XCreateFile ( XPARM File_t * f, ccp fname, enumIOMode iomode, int overwrite )
{
    ASSERT(f);

    if (!fname)
    {
	fname = f->fname;
	f->fname = 0;
    }

    XResetFile( XCALL f, false );

    f->is_stdfile = fname[0] == '-' && !fname[1];
    if (f->is_stdfile)
    {
	f->fd    = dup(fileno(stdout));
	f->fname = strdup("- (stdout)");

	return XOpenFileHelper(XCALL f, iomode,
			O_CREAT|O_WRONLY|O_TRUNC|O_EXCL,
			O_CREAT );
    }

    if (!stat(fname,&f->st))
    {
	if ( overwrite < 0 || f->disable_errors )
	    return ERR_ALREADY_EXISTS;

	if (!S_ISREG(f->st.st_mode))
	    return PrintError( XERROR0, ERR_WRONG_FILE_TYPE,
		"Not a plain file: %s\n", fname );

	if (!overwrite)
	    return PrintError( XERROR0, ERR_ALREADY_EXISTS,
		"File already exists: %s\n", fname );
    }

    TRACE("#F# CREATE: '%s' mkdir=%d\n",fname,f->create_directory);

    int flen = strlen(fname);
    if ( flen >= PATH_MAX )
    {
	// no temp name possible

	f->fname = strdup(fname);
	return XOpenFileHelper(XCALL f, iomode,
			O_CREAT|O_WRONLY|O_TRUNC|O_EXCL,
			O_CREAT );
    }

    const bool disable_errors = f->disable_errors;
    TRACE("dis=%d\n",disable_errors);
    f->disable_errors = true;

    char fbuf[PATH_MAX+20], *XXXXXX;
    if ( flen >= 7 && !memcmp(fname+flen-7,".XXXXXX",7) )
    {
	memcpy(fbuf,fname,flen);
	fbuf[flen] = 0;
	XXXXXX = fbuf + flen - 6;
    }
    else
    {
	if (XCheckCreated(XCALL fname,disable_errors))
	    goto abort;

	f->rename = strdup(fname);

	ccp name = strrchr(fname,'/');
	name = name ? name+1 : fname;
	memcpy(fbuf,fname,name-fname);
	char * dest = fbuf + (name-fname);
	ASSERT( dest < fbuf + PATH_MAX );

	*dest++ = '.';
	dest = StringCopyE(dest,fbuf+PATH_MAX,name);
	*dest++ = '.';
	XXXXXX = dest;
	*dest++ = 'X';
	*dest++ = 'X';
	*dest++ = 'X';
	*dest++ = 'X';
	*dest++ = 'X';
	*dest++ = 'X';
	*dest = 0;

	ASSERT( dest < fbuf + sizeof(fbuf) );
	TRACE("#F# TEMP:   '%s'\n",fbuf);
    }

    const int open_flags = O_WRONLY|O_CREAT|O_TRUNC|O_EXCL;

    //---------------------------------------------------------
    // I have seen the glibc function __gen_tempname() ;)
    //---------------------------------------------------------

    struct timeval tval;
    gettimeofday(&tval,NULL);
    u64 random_time_bits = (u64) tval.tv_usec << 16 ^ tval.tv_sec;
    u64 value = random_time_bits ^ getpid();

    static char letters[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
			    "abcdefghijklmnopqrstuvwxyz"
			    "0123456789";

    int i;
    for ( i = 0; i < 100; value += 7777, i++ )
    {
	u64 v = value;
	XXXXXX[0] = letters[v%62]; v /= 62;
	XXXXXX[1] = letters[v%62]; v /= 62;
	XXXXXX[2] = letters[v%62]; v /= 62;
	XXXXXX[3] = letters[v%62]; v /= 62;
	XXXXXX[4] = letters[v%62]; v /= 62;
	XXXXXX[5] = letters[v%62];

	f->fname = fbuf; // temporary assignment
	const enumError err = XOpenFileHelper(XCALL f,iomode,open_flags,open_flags);
	if ( err == ERR_OK || err == ERR_CANT_CREATE_DIR )
	{
	    f->fname = strdup(fbuf);
	    f->disable_errors = disable_errors;
	    return f->last_error = f->max_error = err;
	}
	f->fname = 0;
	XResetFile( XCALL f, false );
    }

    // cleanup
    f->fname = EmptyString;
    memset(&f->st,0,sizeof(f->st));

    if (!disable_errors)
	PrintError( XERROR0, ERR_CANT_CREATE,
			"Can't create temp file: %s\n", fname );

 abort:
    f->max_error = f->last_error = ERR_CANT_CREATE;
    f->disable_errors = disable_errors;
    TRACE("#F# CreateFile(%p) returns %d, fd=%d, fp=%p\n",
		f, f->last_error, f->fd, f->fp );
    return f->last_error;
}

///////////////////////////////////////////////////////////////////////////////

enumError XOpenStreamFile ( XPARM File_t * f )
{
    ASSERT(f);
    TRACE("#F# OpenStreamFile(%p) fd=%d, fp=%p\n",f,f->fd,f->fp);

    f->last_error = 0;
    if ( f->fd != -1 || !f->fp )
    {
	// flag 'b' is set for compatibilitiy only, linux ignores it
	ccp mode = !f->is_writing ? "rb" : f->is_reading ? "r+b" : "wb";
	TRACE("#F# open mode: '%s'\n",mode);
	f->fp = fdopen(f->fd,mode);
	if (!f->fp)
	{
	    f->last_error = ERR_CANT_OPEN;
	    if ( f->max_error < f->last_error )
		f->max_error = f->last_error;
	    if (!f->disable_errors)
		PrintError( XERROR1,  f->last_error, "Can't open file stream: %s\n",
			f->fname );
	}
	else
	    SeekF(f,f->file_off);
    }

    noTRACE("#F# OpenStreamFile(%p) returns %d, fd=%d, fp=%p, off=%llx\n",
		f, f->last_error, GetFD(f), GetFP(f), f->file_off );
    return f->last_error;
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////
// file name generation

char * NormalizeFileName ( char * buf, char * end, ccp source, bool allow_slash )
{
    ASSERT(buf);
    ASSERT(end);
    ASSERT( buf <= end );
    char * dest = buf;
    TRACE("NormalizeFileName(%s,%d)\n",source,allow_slash);

    if (source)
    {
	bool skip_space = true;
	while ( *source && dest < end )
	{
	    unsigned char ch = *source++;
	    if ( ch == ':' )
	    {
		if (!skip_space)
		    *dest++ = ' ';
		*dest++ = '-';
		*dest++ = ' ';
		skip_space = true;
	    }
	    else
	    {
		if ( isalnum(ch)
			|| !use_utf8 &&
			    (
				   ch == 0xe4 // ä
				|| ch == 0xf6 // ö
				|| ch == 0xfc // ü
				|| ch == 0xdf // ß
				|| ch == 0xc4 // A
				|| ch == 0xd6 // Ö
				|| ch == 0xdc // Ü
			    )
			|| strchr("_+-=%'\"$%&,.!()[]{}<>ÄÖÜäöüß",ch)
			|| ch == '/' && allow_slash )
		{
		    *dest++ = ch;
		    skip_space = false;
		}
		else if (!skip_space)
		{
		    *dest++ = ' ';
		    skip_space = true;
		}
	    }
	}
    }
    if ( dest > buf && dest[-1] == ' ' )
	dest--;

    ASSERT( dest <= end );
    return dest;
}

///////////////////////////////////////////////////////////////////////////////

void SetFileName ( File_t * f, ccp source, bool allow_slash )
{
    char fbuf[PATH_MAX];
    char * dest = NormalizeFileName(fbuf, fbuf+sizeof(fbuf)-1, source, allow_slash );
    *dest++ = 0;
    const int len = dest - fbuf;

    FreeString(f->fname);
    if ( len <= 1 )
	f->fname = EmptyString;
    else
    {
	dest = malloc(len);
	if (!dest)
	    OUT_OF_MEMORY;
	memcpy(dest,fbuf,len);
	f->fname = dest;
    }
}

///////////////////////////////////////////////////////////////////////////////

void GenFileName ( File_t * f, ccp path, ccp name, ccp title, ccp id6, ccp ext )
{
    ASSERT(f);

    TRACE("GenFileName(,p=%s,n=%s,i=%s,e=%s)\n",
		path ? path : "",
		name ? name : "",
		id6  ? id6  : "",
		ext  ? ext  : "" );

    FreeString(f->fname);
    f->fname = EmptyString;

    //----- check stdout

    f->is_stdfile = name && name[0] == '-' && !name[1];
    if (f->is_stdfile)
    {
	f->fname = MinusString;
	return;
    }

    //----- evaluate 'path'

    char fbuf[PATH_MAX+20];

    if ( name && *name == '/' )
	path = 0;

    int plen = path ? strlen(path) : 0;
    if ( plen > PATH_MAX )
    {
	if (!realpath(path,fbuf))
	    strcpy(fbuf,"./");
	plen = strlen(fbuf);
    }
    else if (plen)
	memcpy(fbuf,path,plen);

    char * dest = fbuf + plen;
    if ( plen && dest[-1] != '/' )
	*dest++ = '/';

    TRACE(" >PATH: |%.*s|\n",dest-fbuf,fbuf);

    //----- evaluate 'name'

    char * end  = fbuf + sizeof(fbuf) -  15; // space for "[123456].ext"

    if (name)
    {
	// just copy it
	dest = StringCopyE(dest,end,name);
	TRACE(" >NAME: |%.*s|\n",dest-fbuf,fbuf);
    }
    else
    {
	dest = NormalizeFileName(dest,end,title,false);
	TRACE(" >TITL: |%.*s|\n",dest-fbuf,fbuf);

	if ( id6 && *id6 )
	{
	    dest += snprintf(dest,end-dest,"%s[%s]",
			dest > fbuf && dest[-1] == '/' ? "" : " ", id6 );
	    TRACE(" >ID6:  |%.*s|\n",dest-fbuf,fbuf);
	}
    }

    //----- ext handling

    if (ext)
    {
	const int elen = strlen(ext);
	if ( elen > 0
	    && ( dest - elen <= fbuf || memcmp(dest-elen,ext,elen) )
	    && dest + elen < end )
	{
	    TRACE("add ext %s\n",ext);
	    memcpy(dest,ext,elen);
	    dest += elen;
	    TRACE(" >EXT:  |%.*s|\n",dest-fbuf,fbuf);
	}
    }

    //----- term

    *dest = 0;
    f->fname = strdup(fbuf);
    TRACE("FNAME:      %s\n",fbuf);
}

///////////////////////////////////////////////////////////////////////////////

void GenDestFileName
	( File_t * f, ccp dest, ccp default_name, ccp ext, ccp * rm_ext )
{
    char fbuf[PATH_MAX];
    if ( rm_ext && default_name )
    {
	const size_t name_len = strlen(default_name);
	for(;;)
	{
	    ccp rm = *rm_ext++;
	    if (!rm)
		break;

	    const size_t rm_len = strlen(rm);
	    const size_t cut_len = name_len - rm_len;
	    if ( rm_len && rm_len <= name_len && !strcasecmp(rm,default_name+cut_len) )
	    {
		// got it!

		if ( cut_len < sizeof(fbuf) )
		{
		    memcpy(fbuf,default_name,cut_len);
		    fbuf[cut_len] = 0;
		    default_name = fbuf;
		}
		break; // remove maximal 1 extension
	    }
	}
    }

    if ( IsDirectory(dest,true) )
    {
	if ( dest && *dest && default_name )
	{
	    ccp file_part = strrchr(default_name,'/');
	    if ( file_part )
		default_name = file_part + 1;
	}
	GenFileName(f,dest,default_name,0,0,ext);
    }
    else
	GenFileName(f,0,dest,0,0,0);
}

///////////////////////////////////////////////////////////////////////////////

void GenImageFileName ( File_t * f, ccp dest, ccp default_name, enumOFT oft )
{
    ccp ext = (uint)oft < OFT__N ? oft_ext[oft] : 0;
    GenDestFileName(f,dest,default_name,ext,oft_ext);
}

///////////////////////////////////////////////////////////////////////////////

ccp oft_ext [OFT__N+1] = { "\0", ".iso", ".wdf", ".wbfs", 0 };
ccp oft_name[OFT__N+1] = { "?",   "ISO",  "WDF",  "WBFS", 0 };

///////////////////////////////////////////////////////////////////////////////

enumOFT CalcOFT ( enumOFT force, ccp fname_dest, ccp fname_src, enumOFT def )
{
    if ( force > OFT_UNKNOWN && force < OFT__N )
	return force;

    ccp fname = IsDirectory(fname_dest,true) ? fname_src : fname_dest;
    if (fname)
    {
	const size_t len = strlen(fname);
	if ( len >= 4 )
	{
	    if ( !strcasecmp(fname+len-4,".wdf") )
		return OFT_WDF;

	    if ( !strcasecmp(fname+len-4,".iso") )
		return OFT_PLAIN;

	    if ( len >= 5 && !strcasecmp(fname+len-5,".wbfs") )
		return OFT_WBFS;
	}
    }

    if ( def > OFT_UNKNOWN && def < OFT__N )
	return def;

    return OFT__DEFAULT;
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////

enumError XSetupSplitFile ( XPARM File_t *f, enumOFT oft, off_t split_size )
{
    ASSERT(f);
    if (f->split_f)
	return ERR_OK;

    if ( f->fd == -1 || !S_ISREG(f->st.st_mode) )
    {
	if (!f->disable_errors)
	    ERROR0(ERR_WARNING,
		"Split file support not possible: %s\n", f->fname );
	return ERR_WARNING;
    }

    // at very first: setup split file format

    FreeString(f->split_fname_format);
    FreeString(f->split_rename_format);
    if (f->rename)
    {
	f->split_fname_format = AllocSplitFilename(f->fname,OFT_PLAIN);
	f->split_rename_format = AllocSplitFilename(f->rename,oft);
    }
    else
	f->split_fname_format = AllocSplitFilename(f->fname,oft);

    char fname[PATH_MAX];

    if (!f->is_writing)
    {
	// for read only files: test if split files available
	snprintf(fname,sizeof(fname),f->split_fname_format,1);
	struct stat st;
	if (stat(fname,&st))
	    return ERR_OK; // no split files found -> return
    }

    File_t ** list = calloc(MAX_SPLIT_FILES,sizeof(*list));
    if (!list)
	OUT_OF_MEMORY;

    File_t * first;
    *list = first = malloc(sizeof(File_t));
    if (!first)
	OUT_OF_MEMORY;

    // copy all but cache
    memcpy(first,f,sizeof(File_t));

    first->is_caching = false;
    first->cache = 0;
    first->cur_cache = 0;

    const bool have_stream = f->fp != 0;
    f->fp =  0;
    f->fd = -1;
    f->split_f = list;
    f->split_used = 1;

    if (f->rename)
    {
	// fname is only informative -> use the final name
	f->fname = strdup(f->rename);
	f->rename = 0;
    }
    else
	f->fname = strdup(f->fname);
    if (f->path)
	f->path = strdup(f->path);

    if ( oft == OFT_WBFS )
    {
	f->split_filesize  = split_size ? split_size : DEF_SPLIT_SIZE_WBFS;
	f->split_filesize &= ~0x7fffull;
    }
    else
	f->split_filesize = split_size ? split_size : DEF_SPLIT_SIZE;

    first->split_filesize = first->st.st_size;
    first->split_fname_format = EmptyString;
    first->split_rename_format = 0;
    first->outname = 0;

    TRACE("#S#   Split setup, size=%llu, fname=%s\n",
	f->split_filesize, f->fname );
    TRACE("#S#0# split setup, size=%llu, fname=%s\n",
	first->split_filesize, first->fname );

    noTRACE(" fname:   %p %p\n",f->fname,first->fname);
    noTRACE(" path:    %p %p\n",f->path,first->path);
    noTRACE(" rename:  %p %p\n",f->rename,first->rename);
    noTRACE(" outname: %p %p\n",f->outname,first->outname);
    noTRACE(" split-fname-format:  %s\n",f->split_fname_format);
    noTRACE(" split-rename-format: %s\n",f->split_rename_format);

    if (f->is_reading)
    {
	int idx;
	for ( idx = 1; idx < MAX_SPLIT_FILES; idx++ )
	{
	    snprintf(fname,sizeof(fname),f->split_fname_format,idx);
	    struct stat st;
	    if (stat(fname,&st))
		break;

	    File_t * fi = malloc(sizeof(*f));
	    if (!fi)
		OUT_OF_MEMORY;
	    InitializeFile(fi);
	    fi->open_flags = f->active_open_flags;
	    fi->fname = strdup(fname);
	    enumError err = XOpenFileHelper( XCALL fi,
				have_stream ? IOM_FORCE_STREAM : IOM_NO_STREAM,
				f->active_open_flags, f->active_open_flags );
	    if (err)
	    {
		CloseFile(fi,false);
		free(fi);
		return err;
	    }

	    if (f->split_rename_format)
	    {
		ASSERT(!fi->rename);
		snprintf(fname,sizeof(fname),f->split_rename_format,idx);
		fi->rename = strdup(fname);
	    }

	    fi->split_filesize = fi->st.st_size;
	    TRACE("#S#%u# Open %s, ssize=%llx\n",idx,fname,fi->split_filesize);
	    f->st.st_size += fi->st.st_size;
	    f->split_f[idx] = fi;
	}
	f->split_used = idx;
    }

    File_t * fi = f->split_f[f->split_used-1];
    ASSERT(fi);
    if ( fi->split_filesize < f->split_filesize )
    {
	TRACE("#S#%u# new ssize: %llx -> %llx\n",
		f->split_used-1, fi->split_filesize, f->split_filesize );
	fi->split_filesize = f->split_filesize;
    }

 #ifdef DEBUG
    {
	int i;
	for ( i = 0; i < f->split_used; i++ )
	    TRACE(" - %2d: ssize= %9llx\n",i,f->split_f[i]->split_filesize);
    }
 #endif

    return ERR_OK;
}

///////////////////////////////////////////////////////////////////////////////

enumError XCreateSplitFile ( XPARM File_t *f, uint split_idx )
{
    ASSERT( f );
    ASSERT( f->split_f );
    ASSERT( split_idx > 0 );
    TRACE("#S# CreateSplitFile() %u/%u/%u",split_idx,f->split_used,MAX_SPLIT_FILES);

    if ( split_idx > MAX_SPLIT_FILES )
    {
	if ( !f->disable_errors )
	    PrintError( XERROR1, ERR_WRITE_FAILED,
			"Max number of split files (%d,off=%llx) reached: %s\n",
			MAX_SPLIT_FILES, f->file_off, f->fname );

	    f->last_error = ERR_WRITE_FAILED;
	    if ( f->max_error < f->last_error )
		f->max_error = f->last_error;
	    return ERR_WRITE_FAILED;
    }

    while ( f->split_used <= split_idx )
    {
	File_t ** ptr = f->split_f + f->split_used;
	ASSERT(!*ptr);

	File_t * prev;
	if ( f->split_used > 0 )
	{
	    prev = ptr[-1];
	    if ( prev->is_writing )
		SetSizeF(prev,prev->split_filesize);
	}
	else
	    prev = 0;

	char fname[PATH_MAX];
	snprintf(fname,sizeof(fname),f->split_fname_format,f->split_used++);
	TRACE("#S#%u# Create %s\n",f->split_used-1,fname);

	File_t * f2 = malloc(sizeof(File_t));
	if (!f2)
	    OUT_OF_MEMORY;
	InitializeFile(f2);
	*ptr = f2;
	const int flags = O_CREAT|O_WRONLY|O_TRUNC|O_EXCL|f->active_open_flags;
	f2->fname = strdup(fname);
	enumError err
	    = XOpenFileHelper( XCALL f2,
				prev && prev->fp ? IOM_FORCE_STREAM : IOM_NO_STREAM,
				flags, flags );
	if (err)
	    return err;
	f2->split_filesize = f->split_filesize;
	if (f->split_rename_format)
	{
	    ASSERT(!f2->rename);
	    snprintf(fname,sizeof(fname),f->split_rename_format,f->split_used-1);
	    f2->rename = strdup(fname);
	}
    }
    return ERR_OK;
}

///////////////////////////////////////////////////////////////////////////////

enumError XFindSplitFile ( XPARM File_t *f, uint * p_index, off_t * p_off )
{
    ASSERT( f );
    ASSERT( f->split_f );
    ASSERT(p_index);
    ASSERT(p_off);
    off_t off = *p_off;
    TRACE("#S# XFindSplitFile(off=%llx) %u/%u",off,f->split_used,MAX_SPLIT_FILES);

    File_t ** ptr = f->split_f;
    for (;;)
    {
	if (!*ptr)
	{
	    enumError err = XCreateSplitFile( XCALL f, ptr-f->split_f );
	    if (err)
		return err;
	}

	File_t *cur = *ptr;
	ASSERT(cur);
	if ( off <= cur->split_filesize )
	{
	    *p_index = ptr - f->split_f;
	    *p_off = off;
	    return ERR_OK;
	}

	// skip this file
	off -= cur->split_filesize;
	ptr++;
    }
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////

void DefineCachedArea ( File_t * f, off_t off, size_t count )
{
    // this whole function assumes that count is small and that the hole
    // cache size is less than MAX(size_t)

    ASSERT(f);

    f->cur_cache = 0;
    f->is_caching = f->fd != -1 && f->is_reading && !f->is_writing;
    TRACE("DefineCachedArea(,%llx,%zx) fd=%d rw=%d,%d is_caching=%d\n",
		off, count, f->fd, f->is_reading, f->is_writing, f->is_caching );
    if (!f->is_caching)
	return;

    off_t off_end = (( off + count + f->st.st_blksize - 1 )
			/ f->st.st_blksize ) * f->st.st_blksize;
    off = ( off / f->st.st_blksize ) * f->st.st_blksize;
    count = (size_t)(off_end - off );

    FileCache_t **pptr;
    for ( pptr = &f->cache; *pptr; pptr = &(*pptr)->next )
    {
	FileCache_t * ptr = *pptr;
	if ( off_end < ptr->off )
	    break;

	off_t ptr_end = ptr->off + ptr->count;
	if ( off < ptr_end || off == ptr_end && !ptr->data )
	{
	    // extend this cache element
	    if (ptr->data)
	    {
		// already cached -> try a smaller area
		if ( off_end > ptr_end )
		    DefineCachedArea(f,ptr_end,off_end-ptr_end);
		return;
	    }

	    off_t new_end = ptr->off + ptr->count;
	    if ( new_end < off_end )
		new_end = off_end;

	    if ( ptr->off < off )
		 ptr->off = off;
	    ptr->count = new_end - ptr->off;
	    TRACE("#F# CACHE ENTRY extended: o=%10llx n=%9zx\n",ptr->off,ptr->count);
	    return;
	}
    }

    // insert a new cache element
    FileCache_t * ptr = calloc(1,sizeof(FileCache_t));
    if (!ptr)
	OUT_OF_MEMORY;
    ptr->off   = off;
    ptr->count = count;
    ptr->next  = *pptr;
    *pptr = ptr;
    TRACE("#F# CACHE ENTRY inserted: o=%10llx n=%9zx\n",ptr->off,ptr->count);
}

//-----------------------------------------------------------------------------

void DefineCachedAreaISO ( File_t * f, bool head_only )
{
    ASSERT(f);
    if (head_only)
    {
	DefineCachedArea(f,0,0x100);
    }
    else
    {
	DefineCachedArea(f,0x0000000ull,0x200000);
	DefineCachedArea(f,0xf800000ull,0x800000);
    }
}

///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////

enumError XAnalyseWH ( XPARM File_t * f, WDF_Head_t * wh, bool print_err )
{
    ASSERT(wh);
    TRACE("AnalyseWH()\n");

    if (memcmp(wh->magic,WDF_MAGIC,WDF_MAGIC_SIZE))
    {
	TRACE(" - magic failed\n");
	return ERR_NO_WDF;
    }

    if (!f->seek_allowed)
    {
	TRACE(" - seek not allowed\n");
	return print_err
		? PrintError( XERROR0, ERR_WRONG_FILE_TYPE,
			"Wrong file type: %s\n", f->fname )
		: ERR_WRONG_FILE_TYPE;
    }

    if ( wh->wdf_version != WDF_VERSION )
    {
	TRACE(" - wrong WDF version\n");
	return print_err
		? PrintError( XERROR0, ERR_WDF_VERSION,
			"Only WDF version %x supported but not %x.\n",
			WDF_VERSION, wh->wdf_version )
		: ERR_WDF_VERSION;
    }

    if ( wh->split_file_index >= wh->split_file_num_of )
    {
	TRACE(" - invalid 'split_file_index'\n");
	goto invalid;
    }

    if ( wh->split_file_num_of != 1 )
    {
	TRACE(" - split files not supported\n");
	return print_err
		? PrintError( XERROR0, ERR_WDF_SPLIT,
			"Splitted WDF files not supported yet.\n" )
		: ERR_WDF_SPLIT;
    }

    const u32 chunk_tab_size = wh->chunk_n * sizeof(WDF_Chunk_t);
    if ( f->st.st_size < wh->chunk_off + WDF_MAGIC_SIZE + chunk_tab_size )
    {
	// file size to short -> maybe a splitted file
	XSetupSplitFile(XCALL f,OFT_UNKNOWN,0);
    }

    if ( wh->chunk_off != wh->data_size + sizeof(WDF_Head_t)
	|| wh->chunk_off + WDF_MAGIC_SIZE + chunk_tab_size != f->st.st_size )
    {
	TRACE(" - file size error\n");
	TRACE("   - %llx ? %llx = %llx + %x\n",
		wh->chunk_off, wh->data_size + sizeof(WDF_Head_t),
		wh->data_size, sizeof(WDF_Head_t) );
	TRACE("   - %llx + %x + %x = %llx ? %llx\n",
		wh->chunk_off, WDF_MAGIC_SIZE, chunk_tab_size,
		wh->chunk_off + WDF_MAGIC_SIZE + chunk_tab_size,
		f->st.st_size );
     invalid:
	return print_err
		? PrintError( XERROR0, ERR_WDF_INVALID, "Invalid WDF file\n" )
		: ERR_WDF_INVALID;
    }

    TRACE(" - OK\n");
    return ERR_OK;
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////

static FileCache_t * XCacheHelper ( XPARM File_t * f, off_t off, size_t count )
{
    // This function does the following:
    // a) look into the cahce table to find if (off,count) is part of an
    //    cache entry. I so, the result is a pointer to the first affected
    //    cache entrie. If not NULL returns.
    // b) All cache entires up to off are filled with data. If 'off' is part
    //    of an entry this entry is filled completly.
    // c) If the result is not NULL a seek or a seek simulation is done.

    ASSERT(f);
    f->last_error = ERR_OK;
    if (!f->is_caching)
	return 0;

    // cur_cache is always pointing to the last used and loaded cache entry
    ASSERT( !f->cur_cache || f->cur_cache->data );

    FileCache_t * cptr = f->cur_cache;
    if ( !cptr || off < cptr->off )
	cptr = f->cache;

    f->is_caching = false; // disable cache access for sub calls
    while (cptr)
    {
	if (!cptr->data)
	{
	    // cache must be filled
	    char * data = malloc(cptr->count);
	    if (!data)
		OUT_OF_MEMORY;
	    cptr->data = data;
	    TRACE(TRACE_RDWR_FORMAT, "#F# FILL CACHE",
		GetFD(f), GetFP(f), cptr->off, cptr->off+cptr->count, cptr->count, "" );
	    const enumError stat = XReadAtF(XCALL f,cptr->off,data,cptr->count);
	    if (stat)
	    {
		cptr = 0;
		break;
	    }
	}
	if ( off < cptr->off + cptr->count )
	    break;
	cptr = cptr->next;
    }
    f->is_caching = true; // restore cache access

    if (cptr)
    {
	// cache entry found!
	ASSERT( off < cptr->off + cptr->count );

	f->cur_off = off;
	f->cur_cache = cptr; // save the current ptr
	ASSERT(cptr->data);

	TRACE(TRACE_RDWR_FORMAT, "#F# CACHE FOUND",
		GetFD(f), GetFP(f), cptr->off, cptr->off+cptr->count, cptr->count, "" );
    }

    return cptr;
}

///////////////////////////////////////////////////////////////////////////////

enumError XTellF ( XPARM File_t * f )
{
    ASSERT(f);

    if (f->split_f)
    {
	// file pos is pure virtual
	return f->cur_off;
    }

    f->file_off = f->fp
		    ? ftello(f->fp)
		    : f->fd != -1
			? lseek(f->fd,(off_t)0,SEEK_CUR)
			: (off_t)-1;

    if ( f->file_off == (off_t)-1 )
    {
	f->last_error = f->is_writing ? ERR_WRITE_FAILED : ERR_READ_FAILED;
	if ( f->max_error < f->last_error )
	    f->max_error = f->last_error;
	if (!f->disable_errors)
	    PrintError( XERROR1, f->last_error, "Tell failed [%c=%d]: %s\n",
			GetFT(f), GetFD(f), f->fname );
    }
    else
    {
	f->last_error = ERR_OK;
	f->tell_count++;
	if ( f->max_off < f->file_off )
	    f->max_off = f->file_off;
    }

    TRACE(TRACE_SEEK_FORMAT, "#F# TellF()", GetFD(f), GetFP(f), f->file_off, "" );
    f->cur_off = f->file_off;
    return f->last_error;
}

///////////////////////////////////////////////////////////////////////////////

enumError XSeekF ( XPARM File_t * f, off_t off )
{
    ASSERT(f);

    // sync virtual off
    f->cur_off = f->file_off;

    // if we are already at off and pure reading or pure writing -> all done
    if ( off == f->file_off && f->is_writing != f->is_reading )
	return f->last_error = ERR_OK;

    if (f->is_caching)
    {
	FileCache_t * cptr = XCacheHelper(XCALL f,off,0);
	if (cptr)
	    return f->last_error; // all done
    }

    if (f->split_f)
    {
	// file pos is pure virtual
	f->cur_off = off;
	return ERR_OK;
    }

    if ( !f->seek_allowed && !f->is_writing && off >= f->file_off )
    {
	// simulate seek with read operations
	off_t skip_size = off - f->file_off;
	TRACE(TRACE_RDWR_FORMAT, "#F# SEEK SIMULATION",
			GetFD(f), GetFP(f), f->file_off, f->file_off+skip_size, (u32)skip_size, "" );

	while (skip_size)
	{
	    if (SIGINT_level>1)
		return ERR_INTERRUPT;

	    const size_t max_read = skip_size < sizeof(iobuf)
				  ? (size_t)skip_size : sizeof(iobuf);
	    const enumError stat = XReadF(XCALL f,iobuf,max_read);
	    if (stat)
		return stat;
	    skip_size -= max_read;
	    noTRACE("R+W-Count: %llu + %llu\n",f->bytes_read,f->bytes_written);
	}
	ASSERT( SIGINT_level || off == f->file_off );
	ASSERT( SIGINT_level || off == f->cur_off );
	return ERR_OK;
    }

    if ( !f->seek_allowed && f->is_caching )
    {
	fprintf(stderr,
		"\n"
		"***********************************************************************\n"
		"*****  It seems, that the caching area for the game is to small!  *****\n"
		"*****  Please report this to the author.                          *****\n"
		"*****  Technical data: ID=%-6s  OFF=%10llx                  *****\n"
		"***********************************************************************\n"
		"\n",
		f->id6, off );
    }

    TRACE(TRACE_SEEK_FORMAT, "#F# SeekF()",
		GetFD(f), GetFP(f), off, off < f->max_off ? " <" : "" );

    const bool err = f->fp
			? fseeko(f->fp,off,SEEK_SET) == (off_t)-1
			: f->fd == -1 || lseek(f->fd,off,SEEK_SET) == (off_t)-1;

    if (err)
    {
	f->last_error = f->is_writing ? ERR_WRITE_FAILED : ERR_READ_FAILED;
	if ( f->max_error < f->last_error )
	    f->max_error = f->last_error;
	if (!f->disable_errors)
	    PrintError( XERROR1, f->last_error,
			"Seek failed [%c=%d,%llx]: %s\n",
			GetFT(f), GetFD(f), off, f->fname );
	f->file_off = (off_t)-1;
    }
    else
    {
	f->seek_count++;
	if ( f->max_off < f->file_off )
	    f->max_off = f->file_off;
    }

    f->cur_off = f->file_off = off;
    return f->last_error;
}

///////////////////////////////////////////////////////////////////////////////

enumError XSetSizeF ( XPARM File_t * f, off_t off )
{
    ASSERT(f);
    TRACE(TRACE_SEEK_FORMAT, "#F# SetSizeF()",
		GetFD(f), GetFP(f), off,
		off < f->max_off ? " <" : off > f->max_off ? " >" : "" );

    if (f->split_f)
    {
	f->max_off = off;

	uint index;
	enumError err = XFindSplitFile( XCALL f, &index, &off );
	if (err)
	    return err;
	ASSERT( index < MAX_SPLIT_FILES );
	File_t ** ptr = f->split_f + index;
	ASSERT(*ptr);
	XSetSizeF(XCALL *ptr,off);

	int count = f->split_used - index;
	f->split_used = index+1;
	while ( count-- > 1 )
	{
	    ptr++;
	    ASSERT(*ptr);
	    XCloseFile( XCALL *ptr, true );
	    free(*ptr);
	    *ptr = 0;
	}
	return ERR_OK;
    }

    //--------------------------------------------------

    if (f->fp)
	fflush(f->fp); // [2do] ? error handling

    if (ftruncate(f->fd,off))
    {
	f->last_error = ERR_WRITE_FAILED;
	if ( f->max_error < f->last_error )
	    f->max_error = f->last_error;
	if (!f->disable_errors)
	    PrintError( XERROR1, f->last_error,
			"Set file size failed [%c=%d,%llx]: %s\n",
			GetFT(f), GetFD(f), off, f->fname );
    }
    else
    {
	TRACE("fd=%d truncated to %llx\n",f->fd,off);
	f->setsize_count++;
	if ( f->max_off < off )
	    f->max_off = off;
    }
    return f->last_error;
}

///////////////////////////////////////////////////////////////////////////////

enumError XReadF ( XPARM File_t * f, void * iobuf, size_t count )
{
    ASSERT(f);

    if (f->is_caching)
    {
	off_t my_off = f->cur_off;
	while (count)
	{
	    FileCache_t * cptr = XCacheHelper(XCALL f,my_off,count);
	    if (f->last_error)
		return f->last_error;
	    if (!cptr)
		break;

	    // there is an overlap
	    ASSERT( my_off + count > cptr->off );
	    ASSERT( cptr->off + cptr->count > my_off );

	    if ( cptr->off > my_off )
	    {
		// read data from file

		const size_t size = cptr->off - my_off;
		f->is_caching = false; // disable cache operations
		const enumError stat = XReadAtF(XCALL f,my_off,iobuf,size);
		f->is_caching = true; // restore cache operations
		if (stat)
		    return stat;
		iobuf = (void*)( (char*)iobuf + size );
		count -= size;
		my_off += size;
	    }

	    if ( count > 0 )
	    {
		ASSERT( my_off >= cptr->off );
		ASSERT( my_off <  cptr->off + cptr->count );
		ASSERT( cptr->data );
		const u32 delta = my_off - cptr->off;
		ASSERT ( delta < cptr->count );
		u32 size = cptr->count - delta;
		if ( size > count )
		    size = count;
		TRACE(TRACE_RDWR_FORMAT, "#F# COPY FROM CACHE",
			GetFD(f), GetFP(f), my_off, my_off+size, size, "" );
		memcpy(iobuf,cptr->data+delta,size);
		iobuf = (void*)( (char*)iobuf + size );
		count -= size;
		my_off += size;
		f->bytes_read += size;
	    }

	    f->cur_off = my_off;
	    if (!count)
		return ERR_OK;
	}
    }

    //--------------------------------------------------

    if (f->split_f)
    {
	TRACE("#S# ---\n");
	TRACE(TRACE_RDWR_FORMAT, "#S#   ReadF()",
		GetFD(f), GetFP(f), f->cur_off, f->cur_off+count, count,
		f->cur_off < f->max_off ? " <" : "" );

	File_t ** ptr = f->split_f;
	off_t off = f->cur_off;
	f->cur_off = 0;

	while ( count > 0 )
	{
	    if (!*ptr)
	    {
		ptr--;
		f->cur_off += off + count;
		f->bytes_read += count;
		return XReadAtF( XCALL *ptr, off, iobuf, count );
	    }

	    File_t *cur = *ptr;
	    ASSERT(cur);
	    TRACE("#S#%d# off=%llx cur_of=%llx count=%zx fsize=%llx\n",
			ptr-f->split_f, off, f->cur_off, count, cur->split_filesize );

	    if ( off < cur->split_filesize )
	    {
		// read from this file
		const off_t max_count = cur->split_filesize - off;
		const size_t stream_count = count < max_count ? count : (size_t)max_count;
		enumError err = XReadAtF( XCALL cur, off, iobuf, stream_count );
		if (err)
		    return err;
		f->bytes_read += stream_count;
		count -= stream_count;
		iobuf = (char*)iobuf + stream_count;
		f->cur_off += off + stream_count;
		off = 0;
	    }
	    else
	    {
		// skip this file
		f->cur_off += cur->split_filesize;
		off -= cur->split_filesize;
	    }
	    ptr++;
	}
	if ( f->max_off < f->cur_off )
	    f->max_off = f->cur_off;

	TRACE("#S#x# off=%9llx cur_of=%9llx count=%zx\n", off, f->cur_off, count );
	return ERR_OK;
    }

    //--------------------------------------------------

    if ( f->cur_off != f->file_off )
    {
	const int stat = XSeekF(XCALL f,f->cur_off);
	if (stat)
	    return stat;
    }

    ASSERT( f->cur_off == f->file_off );
    TRACE(TRACE_RDWR_FORMAT, "#F# ReadF()",
		GetFD(f), GetFP(f), f->cur_off, f->cur_off+count, count,
		f->cur_off < f->max_off ? " <" : "" );

    if ( f->read_behind_eof && ( f->st.st_size > 0 || f->is_writing ) )
    {
	const off_t max_read = f->st.st_size > f->file_off
					? f->st.st_size - f->file_off
					: 0;

	TRACE("read_behind_eof=%d, st_size=%llx, count=%x, max_read=%x\n",
		f->read_behind_eof, f->st.st_size, count, max_read );

	if ( count > max_read )
	{
	    if ( f->read_behind_eof == 1 )
	    {
		f->read_behind_eof = 2;
		if ( !f->disable_errors )
		    PrintError( XERROR0, ERR_WARNING,
			"Read behind eof -> zero filled [%c=%d,%llx+%zx]: %s\n",
			GetFT(f), GetFD(f),
			f->file_off, count, f->fname );
	    }
	    size_t fill_count = count - (size_t)max_read;
	    count = (size_t)max_read;
	    memset(iobuf+count,0,fill_count);

	    if (!count)
		return ERR_OK;
	}
    }

    bool err;
    if (f->fp)
	err = count && fread(iobuf,count,1,f->fp) != 1;
    else if ( f->fd != -1 )
    {
	err = false;
	size_t size = count;
	while (size)
	{
	    ssize_t rstat = read(f->fd,iobuf,size);
	    if ( rstat <= 0 )
	    {
		err = true;
		break;
	    }
	    size -= rstat;
	    iobuf = (void*)( (char*)iobuf + rstat );
	}
    }
    else
    {
	err = true;
	errno = 0;
    }

    if (err)
    {
	if ( !f->disable_errors && f->last_error != ERR_READ_FAILED )
	    PrintError( XERROR1, ERR_READ_FAILED,
			"Read failed [%c=%d,%llx+%zx]: %s\n",
			GetFT(f), GetFD(f),
			f->file_off, count, f->fname );
	f->last_error = ERR_READ_FAILED;
	if ( f->max_error < f->last_error )
	    f->max_error = f->last_error;
	f->file_off = (off_t)-1;
    }
    else
    {
	f->read_count++;
	f->bytes_read += count;
	f->file_off += count;
	if ( f->max_off < f->file_off )
	    f->max_off = f->file_off;
    }

    f->cur_off = f->file_off;
    return ERR_OK;
}

///////////////////////////////////////////////////////////////////////////////

enumError XWriteF ( XPARM File_t * f, const void * iobuf, size_t count )
{
    ASSERT(f);

    if (f->split_f)
    {
	TRACE("#S# ---\n");
	TRACE(TRACE_RDWR_FORMAT, "#S#   WriteF()",
		GetFD(f), GetFP(f), f->cur_off, f->cur_off+count, count,
		f->cur_off < f->max_off ? " <" : "" );

	File_t ** ptr = f->split_f;
	off_t off = f->cur_off;
	f->cur_off = 0;

	while ( count > 0 )
	{
	    if (!*ptr)
	    {
		enumError err = XCreateSplitFile( XCALL f, ptr-f->split_f );
		if (err)
		    return err;
	    }

	    File_t *cur = *ptr;
	    ASSERT(cur);
	    TRACE("#S#%d# off=%llx cur_of=%llx count=%zx fsize=%llx\n",
			ptr-f->split_f, off, f->cur_off, count, cur->split_filesize );

	    if ( off < cur->split_filesize )
	    {
		// write to this file
		const off_t max_count = cur->split_filesize - off;
		const size_t stream_count = count < max_count ? count : (size_t)max_count;
		enumError err = XWriteAtF( XCALL cur, off, iobuf, stream_count );
		if (err)
		    return err;
		f->bytes_written += stream_count;
		count -= stream_count;
		iobuf = (char*)iobuf + stream_count;
		f->cur_off += off + stream_count;
		off = 0;
	    }
	    else
	    {
		// skip this file
		f->cur_off += cur->split_filesize;
		off -= cur->split_filesize;
	    }
	    ptr++;
	}
	if ( f->max_off < f->cur_off )
	    f->max_off = f->cur_off;

	TRACE("#S#x# off=%9llx cur_of=%9llx count=%zx\n", off, f->cur_off, count );
	return ERR_OK;
    }

    //--------------------------------------------------

    ASSERT( f->cur_off == f->file_off ); // no cache while writing
    TRACE(TRACE_RDWR_FORMAT, "#F# WriteF()",
		GetFD(f), GetFP(f), f->file_off, f->file_off+count, count,
		f->file_off < f->max_off ? " <" : "" );

    bool err;
    if (f->fp)
	err = count && fwrite(iobuf,count,1,f->fp) != 1;
    else if ( f->fd != -1 )
    {
	err = false;
	size_t size = count;
	while (size)
	{
	    ssize_t wstat = write(f->fd,iobuf,size);
	    if ( wstat <= 0 )
	    {
		err = true;
		break;
	    }
	    size -= wstat;
	    iobuf = (void*)( (char*)iobuf + wstat );
	}
    }
    else
    {
	err = true;
	errno = 0;
    }

    if (err)
    {
	if ( !f->disable_errors && f->last_error != ERR_WRITE_FAILED )
	    PrintError( XERROR1, ERR_WRITE_FAILED,
			"Write failed [%c=%d,%llx+%zx]: %s\n",
			GetFT(f), GetFD(f),
			f->file_off, count, f->fname );
	f->last_error = ERR_WRITE_FAILED;
	if ( f->max_error < f->last_error )
	    f->max_error = f->last_error;
	f->file_off = (off_t)-1;
    }
    else
    {
	f->write_count++;
	f->bytes_written += count;
	f->file_off += count;
	if ( f->max_off < f->file_off )
	    f->max_off = f->file_off;
    }

    f->cur_off = f->file_off;
    return ERR_OK;
}

///////////////////////////////////////////////////////////////////////////////

enumError XWriteSparseF ( XPARM File_t * f, const void * iobuf, size_t count )
{
    ASSERT(f);
    const int align_mask = sizeof(u32)-1;
    ASSERT( (align_mask & align_mask+1) == 0 );

    if ( (__PTRDIFF_TYPE__)iobuf & align_mask || count & align_mask
	|| f->file_off == (off_t)-1 || f->file_off < f->max_off )
    {
	// cond 1+2) sparse checking is only with u32 aligned data allowed
	// cond 3+4) disable sparse check if writing to unknown or existing file areas

	return WriteF(f,iobuf,count);
    }

    TRACE(TRACE_RDWR_FORMAT, "#F# WriteSparseF()",
		GetFD(f), GetFP(f), f->file_off, f->file_off+count, count,
		f->file_off < f->max_off ? " <" : "" );

    // the u32 optimation works because off and size are a multiple of sizeof(u32)
    const u32 * ptr = iobuf;
    const u32 * end = (const u32 *)( (ccp)ptr + count );
    const int bsize = MIN_SPARSE_HOLE_SIZE/sizeof(*ptr);

    // skip leading zeros
    while ( ptr < end && !*ptr )
	ptr++;

    // save start of output
    const u32 * beg = ptr;
    off_t off = f->file_off + ( (ccp)ptr - (ccp)iobuf );

    // [2do] only disk blocks (e.g. multiple of 4096) are of interest
    //		-> lstat().st_blksize

    while ( ptr < end )
    {
	while ( ptr + bsize < end && ptr[bsize-1] )
	{
	    // a little optimation
	    ptr += bsize;
	}

	// scan non zero words
	while ( ptr < end && *ptr )
	    ptr++;
	const u32 * zero_beg = ptr;

	// scan zero words
	while ( ptr < end && !*ptr )
	    ptr++;

	if ( ptr == end || ptr - zero_beg > bsize )
	{
	    // a block with at least 'bsize' zeros found *or* 'end' reached

	    // write non zero block and skip zero block
	    const enumError stat = XWriteAtF(XCALL f,off,beg,(ccp)zero_beg-(ccp)beg);
	    if (stat)
		return stat;

	    // adjust data
	    off += (ccp)ptr - (ccp)beg;
	    beg = ptr;
	}
    }

    return ERR_OK;
}

///////////////////////////////////////////////////////////////////////////////

enumError XReadAtF ( XPARM File_t * f, off_t off, void * iobuf, size_t count )
{
    ASSERT(f);
    noTRACE("#F# ReadAtF(fd=%d,o=%llx,%p,n=%zx)\n",f->fd,off,iobuf,count);
    const enumError stat = XSeekF(XCALL f,off);
    return stat ? stat : XReadF(XCALL f,iobuf,count);
}

///////////////////////////////////////////////////////////////////////////////

enumError XWriteAtF ( XPARM File_t * f, off_t off, const void * iobuf, size_t count )
{
    ASSERT(f);
    noTRACE("#F# WriteAtF(fd=%d,o=%llx,%p,n=%zx)\n",f->fd,off,iobuf,count);
    const enumError stat = XSeekF(XCALL f,off);
    return stat ? stat : XWriteF(XCALL f,iobuf,count);
}

///////////////////////////////////////////////////////////////////////////////

enumError XWriteSparseAtF ( XPARM File_t * f, off_t off, const void * iobuf, size_t count )
{
    ASSERT(f);
    noTRACE("#F# WriteSparseAtF(fd=%d,o=%llx,%p,n=%zx)\n",f->fd,off,iobuf,count);
    const enumError stat = XSeekF(XCALL f,off);
    return stat ? stat : XWriteSparseF(XCALL f,iobuf,count);
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////

int WrapperReadSector ( void * handle, u32 lba, u32 count, void * iobuf )
{
    ASSERT(handle);
    SuperFile_t * sf = (SuperFile_t*)handle;

    TRACE("WrapperReadSector(fd=%d,lba=%x,count=%x) sector-size=%u\n",
		GetFD(&sf->f), lba, count, sf->f.sector_size );

    if (SIGINT_level>1)
	return ERR_INTERRUPT;

    return ReadAtF(
		&sf->f,
		(off_t)lba * sf->f.sector_size,
		iobuf,
		count * sf->f.sector_size );
}

///////////////////////////////////////////////////////////////////////////////

int WrapperWriteSector ( void * handle, u32 lba, u32 count, void * iobuf )
{
    ASSERT(handle);
    SuperFile_t * sf = (SuperFile_t*)handle;

    TRACE("WBFS: WrapperWriteSector(fd=%d,lba=%x,count=%x) sector-size=%u\n",
		GetFD(&sf->f), lba, count, sf->f.sector_size );

    if (SIGINT_level>1)
	return ERR_INTERRUPT;

    return WriteAtF(
		&sf->f,
		(off_t)lba * sf->f.sector_size,
		iobuf,
		count * sf->f.sector_size );
}

///////////////////////////////////////////////////////////////////////////////

int GetFD ( File_t * f )
{
    return !f ? -1 : f->split_used > 0 ? f->split_f[0]->fd : f->fd;
}

///////////////////////////////////////////////////////////////////////////////

FILE * GetFP ( File_t * f )
{
    return !f ? 0 : f->split_used > 0 ? f->split_f[0]->fp : f->fp;
}

///////////////////////////////////////////////////////////////////////////////

char GetFT ( File_t * f )
{
    if (!f)
	return '%';

    if ( f->split_used > 0 )
	f = f->split_f[0];

    return f->fp ? 'S' : f->fd != -1 ? 'F' : '-';
}

///////////////////////////////////////////////////////////////////////////////

bool IsFileOpen ( File_t * f )
{
    return f && ( f->split_used > 0 ? f->split_f[0]->fd : f->fd ) != -1;
}

///////////////////////////////////////////////////////////////////////////////

bool IsFileSplitted ( File_t * f )
{
    return f && f->split_used > 0;
}

///////////////////////////////////////////////////////////////////////////////

bool IsDirectory ( ccp fname, bool answer_if_empty )
{
    if ( !fname || !*fname )
	return answer_if_empty;

    if ( *fname == '-' && !fname[1] )
	return false;

    if ( fname[strlen(fname)-1] == '/' )
	return true;

    struct stat st;
    return !stat(fname,&st) && S_ISDIR(st.st_mode);
}

///////////////////////////////////////////////////////////////////////////////

enumError CreatePath ( ccp fname )
{
    TRACE("CreatePath(%s)\n",fname);

    char buf[PATH_MAX], *dest = buf;
    StringCopyS(buf,sizeof(buf),fname);
    
    for(;;)
    {
	while ( *dest && *dest != '/' )
	    dest++;
	if (!*dest)
	    break;

	*dest = 0;
	if ( mkdir(buf,0777) && errno != EEXIST )
	{
	    TRACE("CREATE-DIR: %s -> err=%d (ENOTDIR=%d)\n",buf,errno,ENOTDIR);
	    if ( errno == ENOTDIR )
	    {
		while ( dest > buf && *dest != '/' )
		    dest--;
		if ( dest > buf )
		    *dest = 0;
	    }
	    return ERROR1( ERR_CANT_CREATE_DIR,
		errno == ENOTDIR
			? "Not a directory: %s\n"
			: "Can't create directory: %s\n", buf );
	}
	TRACE("CREATE-DIR: %s -> OK\n",buf);
	*dest++ = '/';
    }
    return ERR_OK;
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////               split file support                ///////////////
///////////////////////////////////////////////////////////////////////////////

int CalcSplitFilename ( char * buf, size_t buf_size, ccp path, enumOFT oft )
{
    const int needed_space = oft == OFT_WBFS ? 4 : 5;
    const int max_path_len = PATH_MAX - needed_space;

    if (!path)
	path = "";
    TRACE("CalcSplitFilename(%s,%d)\n",path,oft);

    size_t plen = strlen(path);
    if ( plen > 0 && oft == OFT_WBFS )
	plen--;
    if ( plen > max_path_len )
	plen = max_path_len;
    ccp path_end = path + plen;

    char * dest = buf;
    if ( buf_size > needed_space )
    {
	char * end = dest + buf_size - needed_space;
	while ( dest < end && path < path_end )
	{
	    if ( *path == '%' )
	    {
		*dest++ = '%';
		*dest++ = '%';
		path++;
	    }
	    else
		*dest++	= *path++;
	}

	if ( oft != OFT_WBFS )
	    *dest++ = '.';
	*dest++ = '%';
	*dest++ = 'u';
    }
    *dest = 0;
    return dest-buf;
}

//-----------------------------------------------------------------------------

char * AllocSplitFilename ( ccp path, enumOFT oft )
{
    char buf[2*PATH_MAX];
    CalcSplitFilename(buf,sizeof(buf),path,oft);
    return strdup(buf);
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////                  cygwin support                 ///////////////
///////////////////////////////////////////////////////////////////////////////

#ifdef __CYGWIN__

 int NormalizeFilename ( char * buf, size_t bufsize, ccp src )
 {
    static char prefix[] = "/cygdrive/";

    if ( bufsize < sizeof(prefix) + 5 )
    {
	*buf = 0;
	return 0;
    }

    char * end = buf + bufsize - 1;
    char * dest = buf;

    if (   ( *src >= 'a' && *src <= 'z' || *src >= 'A' && *src <= 'Z' )
	&& src[1] == ':'
	&& ( src[2] == 0 || src[2] == '/' || src[2] == '\\' ))
    {
	memcpy(buf,prefix,sizeof(prefix));
	dest = buf + sizeof(prefix)-1;
	*dest++ = tolower(*src);
	*dest = 0;
	if (IsDirectory(buf,false))
	{
	    *dest++ = '/';
	    src += 2;
	    if (*src)
		src++;
	}
	else
	    dest = buf;
    }
    ASSERT( dest < buf + bufsize );

    while ( dest < end && *src )
	if ( *src == '\\' )
	{
	    *dest++ = '/';
	    src++;
	}
	else
	    *dest++ = *src++;

    *dest = 0;
    ASSERT( dest < buf + bufsize );
    return dest - buf;
 }

#endif // __CYGWIN__

///////////////////////////////////////////////////////////////////////////////

#ifdef __CYGWIN__

 char * AllocNormalizedFilename ( ccp source )
 {
    char buf[PATH_MAX];
    const int len = NormalizeFilename(buf,sizeof(buf),source);
    char * result = malloc(len+1);
    if (!result)
	OUT_OF_MEMORY;
    memcpy(result,buf,len+1);
    ASSERT(buf[len]==0);
    return result;
 }

#endif // __CYGWIN__

//
///////////////////////////////////////////////////////////////////////////////
///////////////                string functions                 ///////////////
///////////////////////////////////////////////////////////////////////////////

const char EmptyString[] = "";
const char MinusString[] = "-";

const char LongSep[] = // 160 * '-' + NULL
	"----------------------------------------"
	"----------------------------------------"
	"----------------------------------------"
	"----------------------------------------";

///////////////////////////////////////////////////////////////////////////////

void FreeString ( ccp str )
{
    noTRACE("FreeString(%p) EmptyString=%p MinusString=%p\n",
	    str, EmptyString, MinusString );
    if ( str && str != EmptyString && str != MinusString )
	free((char*)str);
}

///////////////////////////////////////////////////////////////////////////////

char * StringCopyE ( char * buf, char * buf_end, ccp src )
{
    // RESULT: end of copied string pointing to NULL
    // 'src' may be a NULL pointer.

    ASSERT(buf);
    ASSERT(buf<buf_end);
    buf_end--;

    if (src)
	while( buf < buf_end && *src )
	    *buf++ = *src++;

    *buf = 0;
    return buf;
}

//-----------------------------------------------------------------------------

char * StringCopyS ( char * buf, size_t buf_size, ccp src )
{
    return StringCopyE(buf,buf+buf_size,src);
}

///////////////////////////////////////////////////////////////////////////////

char * StringCat2E ( char * buf, char * buf_end, ccp src1, ccp src2 )
{
    // RESULT: end of copied string pointing to NULL
    // 'src*' may be a NULL pointer.

    ASSERT(buf);
    ASSERT(buf<buf_end);
    buf_end--;

    if (src1)
	while( buf < buf_end && *src1 )
	    *buf++ = *src1++;

    if (src2)
	while( buf < buf_end && *src2 )
	    *buf++ = *src2++;

    *buf = 0;
    return buf;
}

//-----------------------------------------------------------------------------

char * StringCat2S ( char * buf, size_t buf_size, ccp src1, ccp src2 )
{
    return StringCat2E(buf,buf+buf_size,src1,src2);
}

///////////////////////////////////////////////////////////////////////////////

char * StringCat3E ( char * buf, char * buf_end, ccp src1, ccp src2, ccp src3 )
{
    // RESULT: end of copied string pointing to NULL
    // 'src*' may be a NULL pointer.

    ASSERT(buf);
    ASSERT(buf<buf_end);
    buf_end--;

    if (src1)
	while( buf < buf_end && *src1 )
	    *buf++ = *src1++;

    if (src2)
	while( buf < buf_end && *src2 )
	    *buf++ = *src2++;

    if (src3)
	while( buf < buf_end && *src3 )
	    *buf++ = *src3++;

    *buf = 0;
    return buf;
}

//-----------------------------------------------------------------------------

char * StringCat3S ( char * buf, size_t buf_size, ccp src1, ccp src2, ccp src3 )
{
    return StringCat3E(buf,buf+buf_size,src1,src2,src3);
}

///////////////////////////////////////////////////////////////////////////////

int CheckID ( ccp id4_or_6 )
{
    ccp ptr = id4_or_6;
    ccp end = ptr + 7;
    while ( ptr < end && ( *ptr >= 'A' && *ptr <= 'Z'
			|| *ptr >= '0' && *ptr <= '9' ))
	ptr++;

    const int len = ptr - id4_or_6;
    return len == 4 || len == 6 ? len : 0;
}

///////////////////////////////////////////////////////////////////////////////

int CheckIDnocase ( ccp id4_or_6 )
{
    ccp ptr = id4_or_6;
    ccp end = ptr + 7;
    while ( ptr < end && ( *ptr >= 'A' && *ptr <= 'Z'
			|| *ptr >= 'a' && *ptr <= 'z'
			|| *ptr >= '0' && *ptr <= '9' ))
	ptr++;

    const int len = ptr - id4_or_6;
    return len == 4 || len == 6 ? len : 0;
}

///////////////////////////////////////////////////////////////////////////////

bool CheckID6 ( const void * id6 )
{
    ccp ptr = (ccp)id6;
    ccp end = ptr + 6;
    while ( ptr < end && ( *ptr >= 'A' && *ptr <= 'Z'
			|| *ptr >= '0' && *ptr <= '9' ))
	ptr++;

    return ptr - (ccp)id6 == 6;
}

///////////////////////////////////////////////////////////////////////////////

int CountIDChars ( ccp id )
{
    ccp ptr = id;
    while ( *ptr >= 'A' && *ptr <= 'Z' || *ptr >= '0' && *ptr <= '9' )
	ptr++;

    return ptr - id;
}

///////////////////////////////////////////////////////////////////////////////

char * ScanID ( char * destbuf7, int * destlen, ccp source )
{
    ASSERT(destbuf7);

    memset(destbuf7,0,7);
    ccp id_start = 0;
    if (source)
    {
	ccp src = source;

	// skip CTRL and SPACES
	while ( *src > 0 && *src <= ' ' )
	    src++;

	if ( ( *src == '*' || *src == '+' ) && ( !src[1] || src[1] == '=' ) )
	{
	    if (destlen)
		*destlen = 1;
	    return src[1] == '=' && src[2] ? (char*)src+2 : 0;
	}

	// scan first word
	const int id_len = CheckID(src);

	if ( id_len == 4 )
	{
	    TRACE("4 chars found:%.6s\n",id_start);
	    id_start = src;
	    src += id_len;

	    // skip CTRL and SPACES
	    while ( *src > 0 && *src <= ' ' )
		src++;

	    if (!*src)
	    {
		memcpy(destbuf7,id_start,4);
		if (destlen)
		    *destlen = 4;
		return 0;
	    }
	    id_start = 0;
	}
	else if ( id_len == 6 )
	{
	    // we have found an ID6 canidat
	    TRACE("6 chars found:%.6s\n",id_start);
	    id_start = src;
	    src += id_len;

	    // skip CTRL and SPACES
	    while ( *src > 0 && *src <= ' ' )
		src++;

	    if ( !*src || *src == '=' )
	    {
		if ( *src == '=' )
		    src++;

		// pure 'ID6' or 'ID6 = name found
		memcpy(destbuf7,id_start,6);
		if (destlen)
		    *destlen = 6;
		return *src ? (char*)src : 0;
	    }
	}

	// scan for latest '...[ID6]...'
	while (*src)
	{
	    while ( *src && *src != '[' ) // ]
		src++;

	    if ( *src == '[' && src[7] == ']' && CheckID(++src) == 6 )
	    {
		id_start = src;
		src += 8;
	    }
	    if (*src)
		src++;
	}
    }
    if (id_start)
	memcpy(destbuf7,id_start,6);
    if (destlen)
	*destlen = id_start ? 6 : 0;
    return 0;
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////			    scan size			///////////////
///////////////////////////////////////////////////////////////////////////////

u64 ScanSizeFactor ( char ch_factor, int force_base )
{
    if ( force_base == 1000 )
    {
	switch(ch_factor)
	{
	    case 'b': case 'c': return             1;
	    case 'k': case 'K': return          1000;
	    case 'm': case 'M': return       1000000;
	    case 'g': case 'G': return    1000000000;
	    case 't': case 'T': return 1000000000000ull;
	}
    }
    else if ( force_base == 1024 )
    {
	switch(ch_factor)
	{
	    case 'b': case 'c': return   1;
	    case 'k': case 'K': return KiB;
	    case 'm': case 'M': return MiB;
	    case 'g': case 'G': return GiB;
	    case 't': case 'T': return TiB;
	}
    }
    else
    {
	switch(ch_factor)
	{
	    case 'b':
	    case 'c': return             1;
	    case 'k': return          1000;
	    case 'm': return       1000000;
	    case 'g': return    1000000000;
	    case 't': return 1000000000000ull;

	    case 'K': return KiB;
	    case 'M': return MiB;
	    case 'G': return GiB;
	    case 'T': return TiB;
	}
    }
    return 0;
}

//-----------------------------------------------------------------------------

char * ScanSizeTerm ( double * num, ccp source, u64 default_factor, int force_base )
{
    ASSERT(source);

    char * end;
    double d = strtod(source,&end);
    if ( end > source )
    {
	// something was read
	u64 factor = ScanSizeFactor(*end,force_base);
	if (factor)
	    end++;
	else
	    factor = default_factor;

	if (factor)
	    d *= factor;
	else
	    end = (char*)source;
    }

    if (num)
	*num = d;

    return end;
}

//-----------------------------------------------------------------------------

char * ScanSize ( double * num, ccp source,
		  u64 default_factor1, u64 default_factor2, int force_base )
{
    ASSERT(source);
    TRACE("ScanSize(df=%llx,%llx, base=%u)\n",
			default_factor1, default_factor2, force_base );

    double sum = 0.0;
    bool add = true;
    char * end = 0;
    for (;;)
    {
	double term;
	end = ScanSizeTerm(&term,source,default_factor1,force_base);
	if ( end == source )
	    break;
	if (add)
	    sum += term;
	else
	    sum -= term;

	while ( *end > 0 && *end <= ' ' )
	    end++;

	if ( *end == '+' )
	    add = true;
	else if ( *end == '-' )
	    add = false;
	else
	    break;

	source = end+1;
	while ( *source > 0 && *source <= ' ' )
	    source++;

	if ( !*source && default_factor2 )
	{
	    if (add)
		sum += default_factor2;
	    else
		sum -= default_factor2;
	    end = (char*)source;
	    break;
	}

	default_factor1 = default_factor2;
    }

    if (num)
	*num = sum;

    return end;
}

//-----------------------------------------------------------------------------

char * ScanSizeU32 ( u32 * num, ccp source,
		     u64 default_factor1, u64 default_factor2, int force_base )
{
    double d;
    char * end = ScanSize(&d,source,default_factor1,default_factor2,force_base);
    //d = ceil(d+0.5);
    if ( d < 0 || d > ~(u32)0 )
	end = (char*)source;
    else if (num)
	*num = (u32)d;

    return end;
}

//-----------------------------------------------------------------------------

char * ScanSizeU64 ( u64 * num, ccp source,
		     u64 default_factor1, u64 default_factor2, int force_base )
{
    double d;
    char * end = ScanSize(&d,source,default_factor1,default_factor2,force_base);
    //d = ceil(d+0.5);
    if ( d < 0 || d > ~(u64)0 )
	end = (char*)source;
    else if (num)
	*num = (u64)d;

    return end;
}

///////////////////////////////////////////////////////////////////////////////

enumError ScanSizeOpt
	( double * num, ccp source,
	  u64 default_factor1, u64 default_factor2, int force_base,
	  ccp opt_name, u64 min, u64 max, bool print_err )
{
    double d;
    char * end = ScanSize(&d,source,default_factor1,default_factor2,force_base);

 #ifdef DEBUG
    {
	u64 size = d;
	TRACE("--%s %8.6g ~ llu ~ %llu GiB ~ %llu GB\n",
		opt_name, d, size, (size+GiB/2)/GiB, (size+500000000)/1000000000 );
    }
 #endif

    enumError err = ERR_OK;

    if ( source == end || *end )
    {
	err = ERR_SYNTAX;
	if (print_err)
	    ERROR0(ERR_SYNTAX,
			"Illegal number for option --%s: %s\n",
			opt_name, source );
    }
    else if ( min > 0 && d < min )
    {
	err = ERR_SYNTAX;
	if (print_err)
	    ERROR0(ERR_SEMANTIC,
			"--%s to small (must not <%llu): %s\n",
			opt_name, min, source );
    }
    else if ( max > 0 && d > max )
    {
	err = ERR_SYNTAX;
	if (print_err)
	    ERROR0(ERR_SEMANTIC,
			"--%s to large (must not >%llu): %s\n",
			opt_name, max, source );
    }

    if ( num && !err )
	*num = d;
    return err;
}

//-----------------------------------------------------------------------------

enumError ScanSizeOptU64
	( u64 * num, ccp source, u64 default_factor1, int force_base,
	  ccp opt_name, u64 min, u64 max, u32 multiple, u32 pow2, bool print_err )
{
    if (!max)
	max = ~(u64)0;

    if ( pow2 && !force_base )
    {
	// try base 1024 first without error messages
	u64 val;
	if (!ScanSizeOptU64( &val, source, default_factor1, 1024,
				opt_name, min,max, multiple, pow2, false ))
	{
	    if (num)
		*num = val;
	    return ERR_OK;
	}
    }

    double d = 0.0;
    enumError err = ScanSizeOpt(&d,source,default_factor1,
				multiple ? multiple : 1,
				force_base,opt_name,min,max,print_err);

    u64 val;
    if ( d < 0.0 )
    {
	val = 0;
	err = ERR_SEMANTIC;
	if (print_err)
	    ERROR0(ERR_SEMANTIC, "--%s: negative values not allowed: %s\n",
			opt_name, source );
    }
    else
	val = d;

    if ( err == ERR_OK && pow2 > 0 )
    {
	int shift_count = 0;
	u64 shift_val = val;
	if (val)
	{
	    while (!(shift_val&1))
	    {
		shift_count++;
		shift_val >>= 1;
	    }
	}

	if ( shift_val != 1 || shift_count/pow2*pow2 != shift_count )
	{
	    err = ERR_SEMANTIC;
	    if (print_err)
		ERROR0(ERR_SYNTAX,
			"--%s: must be a power of %d but not %llu\n",
			opt_name, 1<<pow2, val );
	}
    }

    if ( err == ERR_OK && multiple > 1 )
    {
	u64 xval = val / multiple * multiple;
	if ( xval != val )
	{
	    if ( min > 0 && xval < min )
		xval += multiple;

	    if (print_err)
		ERROR0(ERR_WARNING,
			"--%s: must be a multiple of %u -> use %llu instead of %llu.\n",
			opt_name, multiple, xval, val );
	    val = xval;
	}
    }

    if ( num && !err )
	*num = val;
    return err;
}

//-----------------------------------------------------------------------------

enumError ScanSizeOptU32
	( u32 * num, ccp source, u64 default_factor1, int force_base,
	  ccp opt_name, u64 min, u64 max, u32 multiple, u32 pow2, bool print_err )
{
    if ( !max || max > ~(u32)0 )
	max = ~(u32)0;

    u64 val;
    enumError err = ScanSizeOptU64( &val, source, default_factor1, force_base,
				opt_name, min, max, multiple, pow2, print_err );

    if ( num && !err )
	*num = (u32)val;
    return err;
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////			  scan num/range		///////////////
///////////////////////////////////////////////////////////////////////////////

char * ScanNumU32 ( ccp arg, u32 * p_stat, u32 * p_num, u32 min, u32 max )
{
    ASSERT(arg);
    ASSERT(p_num);
    TRACE("ScanNumU32(%s)\n",arg);

    while ( *arg > 0 && *arg <= ' ' )
	arg++;

    char * end;
    u32 num = strtoul(arg,&end,0);
    u32 stat = end > arg;
    if (stat)
    {
	if ( num < min )
	    num = min;
	else if ( num > max )
	    num = max;

	while ( *end > 0 && *end <= ' ' )
	    end++;
    }
    else
	num = 0;

    if (p_stat)
	*p_stat = stat;
    *p_num = num;

    TRACE("END ScanNumU32() stat=%u, n=%u ->%s\n",stat,num,arg);
    return end;
}

///////////////////////////////////////////////////////////////////////////////

char * ScanRangeU32 ( ccp arg, u32 * p_stat, u32 * p_n1, u32 * p_n2, u32 min, u32 max )
{
    ASSERT(arg);
    ASSERT(p_n1);
    ASSERT(p_n2);
    TRACE("ScanRangeU32(%s)\n",arg);

    int stat = 0;
    u32 n1 = ~(u32)0, n2 = 0;

    while ( *arg > 0 && *arg <= ' ' )
	arg++;

    if ( *arg == '-' )
	n1 = min;
    else
    {
	char * end;
	u32 num = strtoul(arg,&end,0);
	if ( arg == end )
	    goto abort;

	stat = 1;
	arg = end;
	n1 = num;

	while ( *arg > 0 && *arg <= ' ' )
	    arg++;
    }

    if ( *arg != '-' )
    {
	stat = 1;
	n2 = n1;
	goto abort;
    }
    arg++;

    while ( *arg > 0 && *arg <= ' ' )
	arg++;

    char * end;
    n2 = strtoul(arg,&end,0);
    if ( end == arg )
	n2 = max;
    stat = 2;
    arg = end;

 abort:

    if ( stat > 0 )
    {
	if ( n1 < min )
	    n1 = min;
	if ( n2 > max )
	    n2 = max;
    }

    if ( !stat || n1 > n2 )
    {
	stat = 0;
	n1 = ~(u32)0;
	n2 = 0;
    }

    if (p_stat)
	*p_stat = stat;
    *p_n1 = n1;
    *p_n2 = n2;

    while ( *arg > 0 && *arg <= ' ' )
	arg++;

    TRACE("END ScanRangeU32() stat=%u, n=%u..%u ->%s\n",stat,n1,n2,arg);
    return (char*)arg;
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////                  CommandTab_t                   ///////////////
///////////////////////////////////////////////////////////////////////////////

CommandTab_t * ScanCommand ( int * p_stat, ccp arg, CommandTab_t * cmd_tab )
{
    ASSERT(arg);
    char cmd_buf[COMMAND_MAX];

    char *dest = cmd_buf;
    char *end  = cmd_buf + sizeof(cmd_buf) - 1;
    while ( *arg && dest < end )
	*dest++ = toupper(*arg++);
    *dest = 0;
    const int cmd_len = dest - cmd_buf;

    int abbrev_count = 0;
    CommandTab_t *ct, *cmd_ct = 0, *abbrev_ct = 0;
    for ( ct = cmd_tab; ct->name1; ct++ )
    {
	if ( !strcmp(ct->name1,cmd_buf) || ct->name2 && !strcmp(ct->name2,cmd_buf) )
	{
	    cmd_ct = ct;
	    break;
	}
	if ( !memcmp(ct->name1,cmd_buf,cmd_len)
		|| ct->name2 && !memcmp(ct->name2,cmd_buf,cmd_len) )
	{
	    abbrev_ct = ct;
	    abbrev_count++;
	}
    }

    if (cmd_ct)
	abbrev_count = 0;
    else if ( abbrev_count == 1 )
	cmd_ct = abbrev_ct;
    else if (!abbrev_count)
	abbrev_count = -1;

    if (p_stat)
	*p_stat = abbrev_count;

    return cmd_ct;
}

///////////////////////////////////////////////////////////////////////////////

int ScanCommandList ( ccp arg, CommandTab_t * cmd_tab )
{
    ASSERT(arg);

    char cmd_buf[COMMAND_MAX];
    char *end  = cmd_buf + sizeof(cmd_buf) - 1;

    int result = 0;
    for (;;)
    {
	while ( *arg > 0 && *arg <= ' ' || *arg == ',' )
	    arg++;

	if (!*arg)
	    return result;

	char *dest = cmd_buf;
	while ( *arg > ' ' && *arg != ',' && dest < end )
	    *dest++ = *arg++;
	*dest = 0;

	CommandTab_t * cptr = ScanCommand(0,cmd_buf,cmd_tab);
	if (!cptr)
	    return -1;

	if (cptr->mode)
	    result = cptr->id;
	else
	    result |= cptr->id;
    }
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////                    sort mode                    ///////////////
///////////////////////////////////////////////////////////////////////////////

SortMode ScanSortMode ( ccp arg )
{
    static CommandTab_t tab[] =
    {
	{ SORT_NONE,	"NONE",		"-",	0 },
	{ SORT_ID,	"ID",		0,	0 },
	{ SORT_NAME,	"NAME",		"N",	0 },
	{ SORT_TITLE,	"TITLE",	"T",	0 },
	{ SORT_FILE,	"FILE",		"F",	0 },
	{ SORT_SIZE,	"SIZE",		0,	0 },
	{ SORT_REGION,	"REGION",	0,	0 },
	{ SORT_WBFS,	"WBFS",		0,	0 },
	{ SORT_NPART,	"NPART",	0,	0 },
	{ SORT_DEFAULT,	"DEFAULT",	0,	0 },
	{ 0,0,0,0 }
    };

    CommandTab_t * cmd = ScanCommand(0,arg,tab);
    if (cmd)
	return cmd->id;

    ERROR0(ERR_SYNTAX,"Illegal sort mode (option --sort): '%s'\n",arg);
    return SORT__ERROR;
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////                   repair mode                   ///////////////
///////////////////////////////////////////////////////////////////////////////

RepairMode ScanRepairMode ( ccp arg )
{
    static CommandTab_t tab[] =
    {
	{ REPAIR_NONE,		"NONE",		"-",	1 },
	{ REPAIR_FBT,		"FBT",		"F",	0 },
	{ REPAIR_RM_INVALID,	"RM-INVALID",	"RI",	0 },
	{ REPAIR_RM_OVERLAP,	"RM-OVERLAP",	"RO",	0 },
	{ REPAIR_RM_FREE,	"RM-FREE",	"RF",	0 },
	{ REPAIR_RM_EMPTY,	"RM-EMPTY",	"RE",	0 },
	{ REPAIR_RM_ALL,	"RM-ALL",	"RA",	0 },
	{ REPAIR_ALL,		"ALL",		"*",	0 },
	{ 0,0,0,0 }
    };

    int stat = ScanCommandList(arg,tab);
    if ( stat != -1 )
	return stat;

    ERROR0(ERR_SYNTAX,"Illegal repair mode (option --repair): '%s'\n",arg);
    return REPAIR__ERROR;
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////              string lists & fields              ///////////////
///////////////////////////////////////////////////////////////////////////////

void InitializeStringField ( StringField_t * sf )
{
    ASSERT(sf);
    memset(sf,0,sizeof(*sf));
}

///////////////////////////////////////////////////////////////////////////////

void ResetStringField ( StringField_t * sf )
{
    ASSERT(sf);
    if ( sf && sf->used > 0 )
    {
	ASSERT(sf->field);
	ccp *ptr = sf->field, *end;
	for ( end = ptr + sf->used; ptr < end; ptr++ )
	    free((char*)*ptr);
	free(sf->field);
    }
    InitializeStringField(sf);
}

///////////////////////////////////////////////////////////////////////////////

ccp FindStringField ( StringField_t * sf, ccp key )
{
    bool found;
    int idx = FindStringFieldHelper(sf,&found,key);
    return found ? sf->field[idx] : 0;
}

///////////////////////////////////////////////////////////////////////////////

bool InsertStringField ( StringField_t * sf, ccp key, bool move_key )
{
    if (!key)
	return 0;

    bool found;
    int idx = FindStringFieldHelper(sf,&found,key);
    if (found)
    {
	if (move_key)
	    free((char*)key);
    }
    else
    {
	ASSERT( sf->used <= sf->size );
	if ( sf->used == sf->size )
	{
	    sf->size += 0x100;
	    sf->field = realloc(sf->field,sf->size*sizeof(ccp));
	}
	TRACE("InsertStringField(%s,%d) %d/%d/%d\n",key,move_key,idx,sf->used,sf->size);
	ASSERT( idx <= sf->used );
	ccp * dest = sf->field + idx;
	memmove(dest+1,dest,(sf->used-idx)*sizeof(ccp));
	sf->used++;
	*dest = move_key ? key : strdup(key);
    }

    return !found;
}

///////////////////////////////////////////////////////////////////////////////

bool RemoveStringField ( StringField_t * sf, ccp key )
{
    bool found;
    uint idx = FindStringFieldHelper(sf,&found,key);
    if (found)
    {
	sf->used--;
	ASSERT( idx <= sf->used );
	ccp * dest = sf->field + idx;
	free((char*)dest);
	memmove(dest,dest+1,(sf->used-idx)*sizeof(ccp));
    }
    return found;
}

///////////////////////////////////////////////////////////////////////////////

void AppendStringField ( StringField_t * sf, ccp key, bool move_key )
{
    if (key)
    {
	ASSERT( sf->used <= sf->size );
	if ( sf->used == sf->size )
	{
	    sf->size += 0x100;
	    sf->field = realloc(sf->field,sf->size*sizeof(ccp));
	}
	TRACE("AppendStringField(%s,%d) %d/%d\n",key,move_key,sf->used,sf->size);
	ccp * dest = sf->field + sf->used++;
	*dest = move_key ? key : strdup(key);
    }
}

///////////////////////////////////////////////////////////////////////////////

uint FindStringFieldHelper ( StringField_t * sf, bool * p_found, ccp key )
{
    ASSERT(sf);

    int beg = 0;
    if ( sf && key )
    {
	int end = sf->used - 1;
	while ( beg <= end )
	{
	    uint idx = (beg+end)/2;
	    int stat = strcmp(key,sf->field[idx]);
	    if ( stat < 0 )
		end = idx - 1 ;
	    else if ( stat > 0 )
		beg = idx + 1;
	    else
	    {
		TRACE("FindStringFieldHelper(%s) FOUND=%d/%d/%d\n",
			key, idx, sf->used, sf->size );
		if (p_found)
		    *p_found = true;
		return idx;
	    }
	}
    }

    TRACE("FindStringFieldHelper(%s) failed=%d/%d/%d\n",
		key, beg, sf->used, sf->size );

    if (p_found)
	*p_found = false;
    return beg;
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////                  string lists                   ///////////////
///////////////////////////////////////////////////////////////////////////////

void AtFileHelper ( ccp arg, int mode, int (*func) ( ccp arg, int mode ) )
{
    if ( !arg || !*arg || !func )
	return;

    TRACE("AtFileHelper(%s)\n",arg);
    if ( *arg != '@' )
    {
	func(arg,mode);
	return;
    }

    FILE * f;
    const bool use_stdin = arg[1] == '-' && !arg[2];
    if (use_stdin)
	f = stdin;
    else
    {
     #ifdef __CYGWIN__
	char buf[PATH_MAX];
	NormalizeFilename(buf,sizeof(buf),arg+1);
	f = fopen(buf,"r");
     #else
	f = fopen(arg+1,"r");
     #endif
	if (!f)
	    func(arg,mode);
    }

    if (f)
    {
	const int bufsize = 1000;
	char buf[bufsize+1];

	while (fgets(buf,bufsize,f))
	{
	    char * ptr = buf;
	    while (*ptr)
		ptr++;
	    if ( ptr > buf && ptr[-1] == '\n' )
		ptr--;
	    if ( ptr > buf && ptr[-1] == '\r' )
		ptr--;
	    *ptr = 0;
	    func(buf,true);
	}
	fclose(f);
    }
}

///////////////////////////////////////////////////////////////////////////////

uint n_param = 0, id6_param_found = 0;
ParamList_t * first_param = 0;
ParamList_t ** append_param = &first_param;

///////////////////////////////////////////////////////////////////////////////

ParamList_t * AppendParam ( ccp arg, int is_temp )
{
    if ( !arg || !*arg )
	return 0;

    TRACE("ARG#%02d: %s\n",n_param,arg);

    static ParamList_t * pool = 0;
    static int n_pool = 0;

    if (!n_pool)
    {
	const int alloc_count = 100;
	pool = (ParamList_t*) calloc(alloc_count,sizeof(ParamList_t));
	if (!pool)
	    OUT_OF_MEMORY;
	n_pool = 100;
    }

    n_pool--;
    ParamList_t * param = pool++;
    if (is_temp)
    {
	param->arg = strdup(arg);
	if (!param->arg)
	    OUT_OF_MEMORY;
    }
    else
	param->arg = (char*)arg;
    param->count = 0;
    param->next  = 0;
    noTRACE("INS: A=%p->%p P=%p &N=%p->%p\n",
	    append_param, *append_param,
	    param, &param->next, param->next );
    *append_param = param;
    append_param = &param->next;
    noTRACE("  => A=%p->%p\n", append_param, *append_param );
    n_param++;

    return param;
}

///////////////////////////////////////////////////////////////////////////////

int AddParam ( ccp arg, int is_temp )
{
    return AppendParam(arg,is_temp) ? 0 : 1;
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////              string substitutions               ///////////////
///////////////////////////////////////////////////////////////////////////////

char * SubstString
	( char * buf, size_t bufsize, SubstString_t * tab, ccp source, int * count )
{
    ASSERT(buf);
    ASSERT(bufsize > 1);
    ASSERT(tab);
    TRACE("SubstString(%s)\n",source);

    char tempbuf[PATH_MAX];
    int conv_count = 0;

    char *dest = buf;
    char *end = buf + bufsize + 1;
    if (source)
	while ( dest < end && *source )
	{
	    if ( *source != escape_char || *++source == escape_char )
	    {
		*dest++ = *source++;
		continue;
	    }
	    ccp start = source - 1;

	    u32 p1, p2, stat;
	    source = ScanRangeU32(source,&stat,&p1,&p2,0,~(u32)0);
	    if ( stat == 1 )
		p1 = 0;
	    else if ( stat < 1 )
	    {
		p1 = 0;
		p2 = ~(u32)0;
	    }

	    char ch = *source++;
	    int convert = 0;
	    if ( ch == 'u' || ch == 'U' )
	    {
		convert++;
		ch = *source++;
	    }
	    else if ( ch == 'l' || ch == 'L' )
	    {
		convert--;
		ch = *source++;
	    }
	    if (!ch)
		break;

	    size_t count = source - start;

	    SubstString_t * ptr;
	    for ( ptr = tab; ptr->c1; ptr++ )
		if ( ch == ptr->c1 || ch == ptr->c2 )
		{
		    if (ptr->str)
		    {
			const size_t slen = strlen(ptr->str);
			if ( p1 > slen )
			    p1 = slen;
			if ( p2 > slen )
			    p2 = slen;
			count = p2 - p1;
			start = ptr->str+p1;
			conv_count++;
		    }
		    else
			count = 0;
		    break;
		}

	    if (!ptr->c1) // invalid conversion
		convert = 0;

	    if ( count > sizeof(tempbuf)-1 )
		 count = sizeof(tempbuf)-1;
	    TRACE("COPY '%.*s' conv=%d\n",count,start,convert);
	    if ( convert > 0 )
	    {
		char * tp = tempbuf;
		while ( count-- > 0 )
		    *tp++ = toupper(*start++);
		*tp = 0;
	    }
	    else if ( convert < 0 )
	    {
		char * tp = tempbuf;
		while ( count-- > 0 )
		    *tp++ = tolower(*start++);
		*tp = 0;
	    }
	    else
	    {
		memcpy(tempbuf,start,count);
		tempbuf[count] = 0;
	    }
	    dest = NormalizeFileName(dest,end,tempbuf,ptr->allow_slash);
	}

    if (count)
	*count = conv_count;
    *dest = 0;
    return dest;
}

///////////////////////////////////////////////////////////////////////////////

int ScanEscapeChar ( ccp arg )
{
    if ( arg && strlen(arg) > 1 )
    {
	ERROR0(ERR_SYNTAX,"Illegal character (option --esc): '%s'\n",arg);
	return -1;
    }

    escape_char = arg ? *arg : 0;
    return (unsigned char)escape_char;
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////                   Memory Maps                   ///////////////
///////////////////////////////////////////////////////////////////////////////

void InitializeMemMap ( MemMap_t * mm )
{
    ASSERT(mm);
    memset(mm,0,sizeof(*mm));
}

///////////////////////////////////////////////////////////////////////////////

void ResetMemMap ( MemMap_t * mm )
{
    ASSERT(mm);

    uint i;
    if (mm->field)
    {
	for ( i = 0; i < mm->used; i++ )
	    free(mm->field[i]);
	free(mm->field);
    }
    memset(mm,0,sizeof(*mm));
}

///////////////////////////////////////////////////////////////////////////////

MemMapItem_t * InsertMemMap ( MemMap_t * mm, off_t off, off_t size )
{
    ASSERT(mm);
    uint idx = FindMemMapHelper(mm,off,size);

    ASSERT( mm->used <= mm->size );
    if ( mm->used == mm->size )
    {
	mm->size += 64;
	mm->field = realloc(mm->field,mm->size*sizeof(MemMapItem_t*));
    }

    ASSERT( idx <= mm->used );
    MemMapItem_t ** dest = mm->field + idx;
    memmove(dest+1,dest,(mm->used-idx)*sizeof(MemMapItem_t*));
    mm->used++;

    MemMapItem_t * mi = malloc(sizeof(MemMapItem_t));
    if (!mi)
	OUT_OF_MEMORY;
    mi->off  = off;
    mi->size = size;
    mi->overlap = 0;
    *dest = mi;
    return mi;
}

///////////////////////////////////////////////////////////////////////////////

uint FindMemMapHelper ( MemMap_t * mm, off_t off, off_t size )
{
    ASSERT(mm);

    int beg = 0;
    int end = mm->used - 1;
    while ( beg <= end )
    {
	uint idx = (beg+end)/2;
	MemMapItem_t * mi = mm->field[idx];
	if ( off < mi->off )
	    end = idx - 1 ;
	else if ( off > mi->off )
	    beg = idx + 1;
	else if ( size < mi->size )
	    end = idx - 1 ;
	else if ( size > mi->size )
	    beg = idx + 1;
	else
	{
	    TRACE("FindMemMapHelper(%llx,%llx) FOUND=%d/%d/%d\n",
		    off, size, idx, mm->used, mm->size );
	    return idx;
	}
    }

     TRACE("FindStringFieldHelper(%llx,%llx) failed=%d/%d/%d\n",
		off, size, beg, mm->used, mm->size );
    return beg;
}

///////////////////////////////////////////////////////////////////////////////

uint CalcoverlapMemMap ( MemMap_t * mm )
{
    ASSERT(mm);

    uint i, count = 0;
    MemMapItem_t * prev = 0;
    for ( i = 0; i < mm->used; i++ )
    {
	MemMapItem_t * ptr = mm->field[i];
	ptr->overlap = 0;
	if ( prev && ptr->off < prev->off + prev->size )
	{
	    ptr ->overlap |= 1;
	    prev->overlap |= 2;
	    count++;
	}
	prev = ptr;
    }
    return count;
}

///////////////////////////////////////////////////////////////////////////////

void PrintMemMap ( MemMap_t * mm, FILE * f, int indent )
{
    ASSERT(mm);
    if ( !f || !mm->used )
	return;

    CalcoverlapMemMap(mm);

    if ( indent < 0 )
	indent = 0;
    else if ( indent > 50 )
	indent = 50;

    static char ovl[][3] = { "  ", "!.", ".!", "!!" };

    int i, max_ilen = 0;
    for ( i = 0; i < mm->used; i++ )
    {
	MemMapItem_t * ptr = mm->field[i];
	ptr->info[sizeof(ptr->info)-1] = 0;
	const int ilen = strlen(ptr->info);
	if ( max_ilen < ilen )
	    max_ilen = ilen;
    }

    fprintf(f,"%*s      unused :   off(beg) ..   off(end) :      size : info\n%*s%.*s\n",
	    indent, "", indent, "", max_ilen+54, LongSep );

    off_t max_end = 0;
    for ( i = 0; i < mm->used; i++ )
    {
	MemMapItem_t * ptr = mm->field[i];
	const u64 end = ptr->off + ptr->size;
	if ( ptr->off > max_end )
	    fprintf(f,"%*s%s%10llx :%11llx ..%11llx :%10llx : %s\n",
		indent, "", ovl[ptr->overlap&3], ptr->off - max_end,
		ptr->off, end, ptr->size, ptr->info );
	else
	    fprintf(f,"%*s%s           :%11llx ..%11llx :%10llx : %s\n",
		indent, "", ovl[ptr->overlap&3],
		ptr->off, end, ptr->size, ptr->info );
	if ( max_end < end )
	    max_end = end;
    }
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////                    random mumbers               ///////////////
///////////////////////////////////////////////////////////////////////////////
// thanx to Donald Knuth

const u32 RANDOM32_C_ADD = 2 * 197731421; // 2 Primzahlen
const u32 RANDOM32_COUNT_BASE = 4294967; // Primzahl == ~UINT_MAX32/1000;

static int random32_a_index = -1;	// Index in die a-Tabelle
static u32 random32_count = 1;		// Abwaerts-Zähler bis zum Wechsel von a,c
static u32 random32_a,
	      random32_c,
	      random32_X;		// Die letzten Werte

static u32 random32_a_tab[] =		// Init-Tabelle
{
    0xbb40e62d, 0x3dc8f2f5, 0xdc024635, 0x7a5b6c8d,
    0x583feb95, 0x91e06dbd, 0xa7ec03f5, 0
};

//-----------------------------------------------------------------------------

u32 Random32 ( u32 max )
{
    if (!--random32_count)
    {
	// Neue Berechnung von random32_a und random32_c faellig

	if ( random32_a_index < 0 )
	{
	    // allererste Initialisierung auf Zeitbasis
	    Seed32Time();
	}
	else
	{
	    random32_c += RANDOM32_C_ADD;
	    random32_a = random32_a_tab[++random32_a_index];
	    if (!random32_a)
	    {
		random32_a_index = 0;
		random32_a = random32_a_tab[0];
	    }

	    random32_count = RANDOM32_COUNT_BASE;
	}
    }

    // Jetzt erfolgt die eigentliche Berechnung

    random32_X = random32_a * random32_X + random32_c;

    if (!max)
	return random32_X;

    return ( (u64)max * random32_X ) >> 32;
}

//-----------------------------------------------------------------------------

u64 Seed32Time ()
{
    struct timeval tval;
    gettimeofday(&tval,NULL);
    const u64 random_time_bits = (u64) tval.tv_usec << 16 ^ tval.tv_sec;
    return Seed32( ( random_time_bits ^ getpid() ) * 197731421u );
}

//-----------------------------------------------------------------------------

u64 Seed32 ( u64 base )
{
    uint a_tab_len = 0;
    while (random32_a_tab[a_tab_len])
	a_tab_len++;
    const u32 base32 = base / a_tab_len;

    random32_a_index	= base % a_tab_len;
    random32_a		= random32_a_tab[random32_a_index];
    random32_c		= ( base32 & 15 ) * RANDOM32_C_ADD + 1;
    random32_X		= base32 ^ ( base >> 32 );
    random32_count	= RANDOM32_COUNT_BASE;

    return base;
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////                     END                         ///////////////
///////////////////////////////////////////////////////////////////////////////

