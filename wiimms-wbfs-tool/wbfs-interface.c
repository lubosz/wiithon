
#define _GNU_SOURCE 1

#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
#include <ctype.h>
#include <errno.h>
#include <dirent.h>
#include <time.h>

#include "libwbfs/wiidisc.h"

#include "debug.h"
#include "wbfs-interface.h"
#include "titles.h"

//
///////////////////////////////////////////////////////////////////////////////
///////////////                     partitions                  ///////////////
///////////////////////////////////////////////////////////////////////////////

PartitionInfo_t *  first_partition_info = 0;
PartitionInfo_t ** append_partition_info = &first_partition_info;

int pi_count = 0;
PartitionInfo_t * pi_list[MAX_WBFS+1];
WDiscList_t pi_wlist = {0,0,0,0};
u32 pi_free_mib = 0;

int opt_part	= 0;
int opt_auto	= 0;
int opt_all	= 0;

u8 wdisc_usage_tab [WII_MAX_SECTORS];
u8 wdisc_usage_tab2[WII_MAX_SECTORS];

///////////////////////////////////////////////////////////////////////////////

PartitionInfo_t * CreatePartitionInfo ( ccp path, enumPartSource source )
{
    char real_path_buf[PATH_MAX];
    ccp real_path = real_path_buf;
    if (!realpath(path,real_path_buf))
    {
	TRACE("CAN'T DETERMINE REAL PATH: %s\n",path);
	real_path = path;
    }

    PartitionInfo_t * info = first_partition_info;
    while ( info && strcmp(info->real_path,real_path) )
	info = info->next;

    if (!info)
    {
	// new entry

	PartitionInfo_t * info = malloc(sizeof(PartitionInfo_t));
	if (!info)
	    OUT_OF_MEMORY;
	memset(info,0,sizeof(PartitionInfo_t));
	info->path = strdup(path);
	info->real_path = strdup(real_path);
	if ( !info->path || !info->real_path )
	    OUT_OF_MEMORY;
	info->part_mode = PM_UNKNOWN;
	info->source = source;
	*append_partition_info = info;
	append_partition_info = &info->next;
	TRACE("PARTITION inserted: %s\n",real_path);
    }
    else if ( source == PS_PARAM )
    {
	// overrides previous definition

	info->source = source;
	free((char*)info->path);
	info->path = strdup(path);
	if (!info->path)
	    OUT_OF_MEMORY;
	TRACE("PARTITION redefined: %s\n",real_path);
    }
    return info;
}

///////////////////////////////////////////////////////////////////////////////

int AddPartition ( ccp arg, int unused )
{
    if (opt_part++)
	opt_all++;
    CreatePartitionInfo(arg,PS_PARAM);
    return 0;
}

///////////////////////////////////////////////////////////////////////////////

int ScanPartitions ( bool all )
{
    opt_auto++;
    opt_all += all;

    int count = 0;

    static char prefix[] = "/dev/";
    const int bufsize = 100;
    char buf[bufsize+1];
    char buf2[bufsize+1+sizeof(prefix)];
    strcpy(buf2,prefix);

    FILE * f = fopen("/proc/partitions","r");
    if (f)
    {
	TRACE("SCAN /proc/partitions\n");

	// skip first line
	fgets(buf,bufsize,f);

	while (fgets(buf,bufsize,f))
	{
	    char * ptr = buf;
	    while (*ptr)
		ptr++;
	    if ( ptr > buf )
	    {
		ptr--;
		while ( ptr > buf && (u8)*ptr <= ' ' )
		    ptr--;
		ptr[1] = 0;
		while ( ptr > buf && isalnum(*ptr) )
		    ptr--;
		if (*++ptr)
		{
		    strcpy(buf2+sizeof(prefix)-1,ptr);
		    CreatePartitionInfo(buf2,PS_AUTO);
		}
	    }
	}
	fclose(f);
    }
    else
    {
     #if __APPLE__
	static char dev_prefix[] = "disk";
     #else
	static char dev_prefix[] = "sd";
     #endif
	static size_t len_prefix   = sizeof(dev_prefix)-1;

	DIR * dir = opendir("/dev");
	if (dir)
	{
	    for (;;)
	    {
		struct dirent * dent = readdir(dir);
		if (!dent)
		    break;
	     #ifdef _DIRENT_HAVE_D_TYPE
		if ( dent->d_type == DT_BLK
			&& !memcmp(dent->d_name,dev_prefix,len_prefix))
	     #else
		if (!memcmp(dent->d_name,dev_prefix,len_prefix))
	     #endif
		{
		    StringCopyE(buf2+sizeof(prefix)-1,buf2+sizeof(buf2),dent->d_name);
		    CreatePartitionInfo(buf2,PS_AUTO);
		}
	    }
	    closedir(dir);
	}
    }
    return count;
}

///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////

void AddEnvPartitions()
{
    TRACE("AddEnvPartitions() PART1=%d, AUTO=%d, all=%d, first=%p\n",
	opt_part, opt_auto, opt_all, first_partition_info );

    if ( !first_partition_info && !opt_part && !opt_auto )
    {
	TRACE("lookup environment var 'WWT_WBFS'");
	char * env = getenv("WWT_WBFS");
	if ( env && *env )
	{
	    char * ptr = env;
	    for(;;)
	    {
		env = ptr;
		while ( *ptr && *ptr != ';' )
		    ptr++;
		if ( ptr > env )
		{
		    char ch = *ptr;
		    *ptr = 0;
		    CreatePartitionInfo(env,PS_ENV);
		    opt_all++;
		    *ptr = ch;
		}
		if (!*ptr)
		    break;
		ptr++;
	    }
	}
    }
}

///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////

int wbfs_count = 0; // number of wbfs partitions

int AnalysePartitions ( FILE * outfile, bool non_found_is_ok, bool scan_wbfs )
{
    ASSERT(outfile);
    TRACE("AnalysePartitions(,%d,%d) PART1=%d, AUTO=%d, all=%d, first=%p\n",
	non_found_is_ok, scan_wbfs,
	opt_part, opt_auto, opt_all, first_partition_info );

    AddEnvPartitions();

    // standalone --all enables --auto
    if ( opt_all && !opt_part && !opt_auto )
	ScanPartitions(false);

    int stat = ERR_OK;
    wbfs_count = 0; // number of wbfs partitions

    WBFS_t wbfs;
    InitializeWBFS(&wbfs);
    PartitionInfo_t * info;
    for ( info = first_partition_info; info; info = info->next )
    {
	TRACE("Analyse partition %s, mode=%d, source=%d\n",
		info->path, info->part_mode, info->source);
	TRACE(" - realpath: %s\n",info->real_path);

	if ( info->part_mode == PM_UNKNOWN )
	{
	    ccp read_error = 0;
	    File_t F;
	    InitializeFile(&F);
	    F.disable_errors = info->source != PS_PARAM;
	    enumError stat = OpenFile(&F,info->real_path,IOM_IS_WBFS);
	    if (stat)
	    {
		read_error = ""; // message already printed
		goto _done;
	    }

	    TRACE(" - st_mode=%x reg=%d dir=%d chr=%d blk=%d fifo=%d link=%s sock=%d\n",
		    F.st.st_mode,
		    S_ISREG(F.st.st_mode),
		    S_ISDIR(F.st.st_mode),
		    S_ISCHR(F.st.st_mode),
		    S_ISBLK(F.st.st_mode),
		    S_ISFIFO(F.st.st_mode),
		    S_ISLNK(F.st.st_mode),
		    S_ISCHR(F.st.st_mode),
		    S_ISSOCK(F.st.st_mode) );

	    if (S_ISREG(F.st.st_mode))
	    {
		TRACE(" -> regular file\n");
		info->is_block_dev = false;
	    }
	    else if (S_ISBLK(F.st.st_mode))
	    {
		TRACE(" -> block mode\n");
		info->is_block_dev = true;
	    }
	    else
	    {
		info->part_mode = PM_WRONG_TYPE;
		read_error = "Neither regular file nor block device: %s\n";
		goto _done;
	    }

	    TRACE("sizeof: st_size=%d st_blksize=%d st_blocks=%d\n",
			sizeof(F.st.st_size),
			sizeof(F.st.st_blksize), sizeof(F.st.st_blocks) );
	    TRACE("st_blksize=%d st_blocks=%d\n",F.st.st_blksize, F.st.st_blocks );
	    info->file_size  = F.st.st_size;
	    info->disk_usage = 512ull * F.st.st_blocks;
	    TRACE(" - file-size:  %13lld = %5lld GiB\n",info->file_size,info->file_size/GiB);
	    TRACE(" - disk-usage: %13lld = %5lld GiB\n",info->disk_usage,info->disk_usage/GiB);

	    char magic_buf[4];
	    stat = ReadF(&F,magic_buf,sizeof(magic_buf));
	    if (stat)
	    {
		read_error = "Can't read WBFS magic: %s\n";
		goto _done;
	    }

	    if (memcmp(magic_buf,"WBFS",sizeof(magic_buf)))
	    {
		info->part_mode = PM_NO_WBFS_MAGIC;
		read_error = "No WBFS magic found: %s\n";
		goto _done;
	    }

	    info->part_mode = PM_WBFS_MAGIC_FOUND;
	    wbfs_count++;

	    if (!info->file_size)
	    {
		// second try: use lseek() (needed for block devices)
		info->file_size = lseek(F.fd,0,SEEK_END);
		if ( info->file_size == (off_t)-1 )
		    info->file_size = 0;
		TRACE(" - file-size:  %13lld = %5lld GiB\n",info->file_size,info->file_size/GiB);
	    }

	    if (scan_wbfs)
	    {
		OpenPartWBFS(&wbfs,info);
		ResetWBFS(&wbfs);
	    }

	_done:;
	    int syserr = errno;
	    ClearFile(&F,false);

	    if (read_error)
	    {
		TRACE(read_error," -> ",info->real_path);
		if ( info->part_mode < PM_CANT_READ )
		    info->part_mode = PM_CANT_READ;
		if ( *read_error && info->source == PS_PARAM )
		    stat = ERROR(syserr,ERR_READ_FAILED,read_error,info->real_path);
	    }
	}
    }
    ASSERT( !wbfs.wbfs && !wbfs.sf ); // wbfs is closed!

    TRACE("*** %d WBFS partition(s) found\n",wbfs_count);

    if ( !wbfs_count )
    {
	if ( !non_found_is_ok || verbose >= 1 )
	    ERROR0(ERR_NO_WBFS_FOUND,"no WBFS partitions found -> abort\n");
	if ( !non_found_is_ok && !stat )
	    stat = ERR_NO_WBFS_FOUND;
    }
    else if ( stat )
    {
	fprintf(outfile,"%d WBFS partition%s found\n",
			wbfs_count, wbfs_count == 1 ? "" : "s" );
	ERROR0(ERR_WARNING,"Abort because of read errors while scanning\n");
    }
    else if ( wbfs_count > 1 )
    {
	if ( !opt_all )
	    stat = ERROR0(ERR_TO_MUCH_WBFS_FOUND,
			"%d (more than 1) WBFS partitions found -> abort.\n",wbfs_count);
	else if ( verbose >= 1 )
	    fprintf(outfile,"%d WBFS partition%s found\n",
			wbfs_count, wbfs_count == 1 ? "" : "s" );
    }
    else if ( verbose > 0 )
    {
	fprintf(outfile,"One WBFS partition found.\n");
    }

    return stat;
}

///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////

void ScanPartitionGames()
{
    int pi_disc_count = 0;
    pi_free_mib = 0;

    WBFS_t wbfs;
    InitializeWBFS(&wbfs);
    PartitionInfo_t * info;
    enumError stat;
    for ( stat = GetFirstWBFS(&wbfs,&info); !stat; stat = GetNextWBFS(&wbfs,&info) )
    {
	if ( !info->part_index || !info->wlist )
	{
	    if ( pi_count >= MAX_WBFS )
	    {
		ERROR0(ERR_TO_MUCH_WBFS_FOUND,"Too much (>%d) WBFS partitions\n",MAX_WBFS);
		break;
	    }

	    info->part_index = ++pi_count;
	    pi_list[pi_count] = info;
	    info->part_index = pi_count;
	    info->wlist = GenerateWDiscList(&wbfs,pi_count);
	}
	pi_disc_count += info->wlist->used;
	pi_free_mib += wbfs.free_mib;
    }

    if ( pi_wlist.used != pi_disc_count )
    {
	ResetWDiscList(&pi_wlist);
	pi_wlist.sort_mode = SORT_NONE;
	pi_wlist.used = pi_wlist.size = pi_disc_count;
	pi_wlist.first_disc = calloc(pi_disc_count,sizeof(WDiscListItem_t));
	if (!pi_wlist.first_disc)
	    OUT_OF_MEMORY;

	WDiscListItem_t * dest = pi_wlist.first_disc;
	int i;
	for ( i = 1; i <= pi_count; i++ )
	{
	    WDiscList_t * wlist = pi_list[i]->wlist;
	    ASSERT(wlist);
	    ASSERT( dest-pi_wlist.first_disc + wlist->used <= pi_disc_count );
	    memcpy(dest,wlist->first_disc,wlist->used*sizeof(*dest));
	    dest += wlist->used;
	    pi_wlist.total_size_mib += wlist->total_size_mib;
	}
	ASSERT ( dest == pi_wlist.first_disc + pi_disc_count );
    }
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////

ParamList_t * CheckParamID6 ( bool unique, bool lookup_title_db )
{
    // Checks each parameter for an ID6.
    // Illegal parameters are removed.
    // Function result is the new number of parameters.

 #ifdef DEBUG
    {
	TRACE("START CheckParamID6(%d,%d) n_param=%d\n",
		unique, lookup_title_db, n_param );
	ParamList_t * p;
	for ( p = first_param; p; p = p->next )
	    TRACE(" | P=%p ARG=%p,%s\n",p,p->arg,p->arg);
    }
 #endif

    bool id6_scanned = false;

    // get first old parameter
    ParamList_t * param = first_param;

    // reset list
    n_param = 0;
    id6_param_found = 0;
    first_param = 0;
    append_param = &first_param;

    noTRACE("C-0: A=%p->%p P=%p &N=%p->%p\n",
	    append_param, *append_param,
	    param, param ? &param->next : 0,
	    param ? param->next : 0 );

    while (param)
    {
	int id_len;
	param->arg = ScanID(param->id6,&id_len,param->arg);
	if (id_len)
	    id6_param_found++;

	if ( id_len == 1 )
	{
	    TRACE(" - ID6 '+|*' found, already scanned = %d\n",id6_scanned);
	    if (!id6_scanned)
	    {
		id6_scanned = true;
		ScanPartitionGames();
		SortWDiscList(&pi_wlist,sort_mode,SORT_TITLE,true);

		int i;
		WDiscListItem_t * witem;
		for ( i = pi_wlist.used, witem = pi_wlist.first_disc; i-- > 0; witem++ )
		{
		    if ( !IsExcluded(witem->id6)
			&& ( !unique || !SearchParamID6(witem->id6) ))
		    {
			// append with dummy 'arg' ...
			ParamList_t * p = AppendParam(witem->id6,false);
			p->arg = param->arg;
			memcpy(p->id6,witem->id6,6);
			p->id6[6] = 0;
		    }
		}
	    }
	}

	if (IsExcluded(param->id6))
	    param->id6[0] = 0;

	if ( param->id6[0] )
	{
	    if ( param->arg && param->arg[0] )
	    {
		// normalize arg

		bool skip_blank = true;
		char *src, *dest;
		for ( src = dest = param->arg; *src; src++ )
		{
		    const char ch = *(u8*)src < ' ' ? ' ' : *src;
		    if ( ch != ' ' )
		    {
			*dest++ = ch;
			skip_blank = false;
		    }
		    else if (!skip_blank)
		    {
			*dest++ = ch;
			skip_blank = true;
		    }
		}
		if ( dest > param->arg && dest[-1] == ' ' )
		    dest--;
		*dest = 0;
	    }

	    if (unique)
	    {
		ParamList_t * found = SearchParamID6(param->id6);
		if (found)
		{
		    param->id6[0] = 0; // disable this
		    if ( param->arg && *param->arg )
		    {
			// last non empty arg overides previous!
			found->arg = param->arg;
		    }
		}
	    }
	}

	if ( param->id6[0] )
	{
	    // check arg
	    if ( !param->arg || !param->arg[0] )
	    {
		param->arg = 0;
		if (lookup_title_db)
		    param->arg = (char*)GetTitle(param->id6,0);
	    }

	    // normalize ID6
	    char * id6ptr = param->id6;
	    int i;
	    for ( i=0; i<6; i++, id6ptr++ )
		*id6ptr = toupper(*id6ptr);
	    ASSERT( id6ptr == param->id6 + 6 );
	    *id6ptr = 0;

	    // reset counter
	    param->count = 0;

	    // append parameter
	    noTRACE("CHK: A=%p->%p P=%p &N=%p->%p\n",
		    append_param, *append_param,
		    param, &param->next, param->next );
	    *append_param = param;
	    append_param = &param->next;
	    param = param->next;
	    *append_param = 0;
	    noTRACE("  => A=%p->%p P=%p &N=%p->%p\n",
		    append_param, *append_param,
		    param, (param?&param->next:0), (param?param->next:0) );
	    n_param++;
	}
	else
	{
	    // do *not* free 'current' or 'current->arg'
	    param = param->next;
	    noTRACE("  == A=%p->%p P=%p &N=%p->%p\n",
		    append_param, *append_param,
		    param, (param?&param->next:0), (param?param->next:0) );
	}
    }

 #ifdef DEBUG
    {
	TRACE("TERM CheckParamID6(%d,%d) n_param=%d\n",
		unique, lookup_title_db, n_param );
	ParamList_t * p;
	for ( p = first_param; p; p = p->next )
	    TRACE(" | P=%p ID6=%s ARG=%p,%s\n",p,p->id6,p->arg,p->arg);
    }
 #endif

    return first_param;
}

///////////////////////////////////////////////////////////////////////////////

ParamList_t * SearchParamID6 ( ccp id6 )
{
    ParamList_t * search;
    for ( search = first_param; search; search = search->next )
    {
	if (!memcmp(search->id6,id6,6))
	    return search;
    }
    return 0;
}

///////////////////////////////////////////////////////////////////////////////

int PrintParamID6()
{
    ParamList_t * param;
    for ( param = first_param; param; param = param->next )
	if ( *param->id6 )
	{
	    if ( param->arg && *param->arg )
		printf("%s=%s\n",param->id6,param->arg);
	    else
		printf("%s\n",param->id6);
	}
    return ERR_OK;
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////

enumError CheckParamRename ( bool rename_id, bool allow_plus, bool allow_index )
{
    int syntax_count = 0, semantic_count = 0;
    ParamList_t * param;
    for ( param = first_param; param; param = param->next )
    {
	memset(param->selector,0,sizeof(param->selector));
	memset(param->id6,0,sizeof(param->id6));

	char * arg = (char*)param->arg;
	if (!arg)
	    continue;

	while ( *arg > 0 &&*arg <= ' ' )
	    arg++;

	long index = -1;
	if ( allow_plus && ( *arg == '+' || *arg == '*' ) )
	{
	    param->selector[0] = '+';
	    arg++;
	}
	else if ( CheckIDnocase(arg) == 6 )
	{
	    // ID6 found
	    int i;
	    for ( i = 0; i < 6; i++ )
		param->selector[i] = toupper(*arg++);
	}
	else if ( allow_index && *arg == '#' )
	{
	    // a slot index;
	    index = strtoul(arg+1,&arg,0);
	    snprintf(param->selector,sizeof(param->selector),"#%lu",index);
	}
	else if ( allow_index )
	{
	    char * start = arg;
	    index = strtoul(arg,&arg,0);
	    if ( arg == start )
	    {
		ERROR0(ERR_SEMANTIC,
			"ID6 or INDEX or #SLOT expected: %s\n", param->arg );
		syntax_count++;
		continue;
	    }
	    snprintf(param->selector,sizeof(param->selector),"$%lu",index);
	}
	else
	{
	    ERROR0(ERR_SEMANTIC,
		    "ID6 expected: %s\n", param->arg );
	    syntax_count++;
	    continue;
	}

	if ( index >= 0 && wbfs_count != 1 )
	{
	    ERROR0(ERR_SEMANTIC,
		"Slot or disc index is only allowed if exact 1 WBFS is selected: %s\n",
		param->arg );
	    semantic_count++;
	    continue;
	}

	if ( index > 99999 )
	{
	    ERROR0(ERR_SEMANTIC,
		"Slot or disc index to large: %s\n", param->arg );
	    semantic_count++;
	    continue;
	}

	while ( *arg > 0 &&*arg <= ' ' )
	    arg++;

	if ( *arg != '=' )
	{
	    ERROR0(ERR_SYNTAX,"Missing '=': %s -> %s\n", param->arg, arg );
	    syntax_count++;
	    continue;
	}

	arg++;
	bool scan_title = !rename_id;
	if (rename_id)
	{
	    while ( *arg > 0 &&*arg <= ' ' )
		arg++;

	    if ( *arg != ',' )
	    {
		if ( CheckIDnocase(arg) != 6 )
		{
		    ERROR0(ERR_SYNTAX,"Missing ID6: %s -> %s\n", param->arg, arg );
		    syntax_count++;
		    continue;
		}
		int i;
		for ( i = 0; i < 6; i++ )
		    param->id6[i] = toupper(*arg++);
		while ( *arg > 0 &&*arg <= ' ' )
		    arg++;
	    }

	    if ( *arg == ',' )
	    {
		arg++;
		scan_title = true;
	    }
	}

	if (scan_title)
	{
	    if (!*arg)
	    {
		ERROR0(ERR_SYNTAX,"Missing title: %s -> %s\n", param->arg, arg );
		syntax_count++;
		continue;
	    }
	    param->arg = arg;
	}
	else
	    param->arg = 0;
    }

    return syntax_count ? ERR_SYNTAX : semantic_count ? ERR_SEMANTIC : ERR_OK;
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////                access WBPS partitions           ///////////////
///////////////////////////////////////////////////////////////////////////////

int partition_selector = ALL_PARTITIONS;

//-----------------------------------------------------------------------------

int ScanPartitionSelector ( ccp arg )
{
    static CommandTab_t tab[] =
    {
	{ GAME_PARTITION_TYPE,		"GAME",		"G",		0 },
	{ UPDATE_PARTITION_TYPE,	"UPDATE",	"U",		0 },
	{ CHANNEL_PARTITION_TYPE,	"CHANNEL",	"C",		0 },

	{ WHOLE_DISC,			"WHOLE",	"RAW",		0 },
	{ WHOLE_DISC,			"1:1",		0,		0 },
	{ ALL_PARTITIONS,		"ALL",		"*",		0 },

	{ REMOVE_GAME_PARTITION,	"NO-GAME",	"NOGAME",	0 },
	{ REMOVE_UPDATE_PARTITION,	"NO-UPDATE",	"NOUPDATE",	0 },
	{ REMOVE_CHANNEL_PARTITION,	"NO-CHANNEL",	"NOCHANNEL",	0 },

	{ 0,0,0,0 }
    };

    CommandTab_t * cmd = ScanCommand(0,arg,tab);
    if (cmd)
	return cmd->id;

    // try if arg is a number
    char * end;
    ulong num = strtoul(arg,&end,10);
    if ( end != arg && !*end )
	return num;

    ERROR0(ERR_SYNTAX,"Illegal partition selector (option --psel): '%s'\n",arg);
    return -1;
}

///////////////////////////////////////////////////////////////////////////////

void InitializeWBFS ( WBFS_t * w )
{
    ASSERT(w);
    memset(w,0,sizeof(*w));
}

///////////////////////////////////////////////////////////////////////////////

enumError ResetWBFS ( WBFS_t * w )
{
    ASSERT(w);
    TRACE("ResetWBFS() fd=%d, alloced=%d\n", w->sf ? GetFD(&w->sf->f) : -2, w->sf_alloced );

    CloseWDisc(w);

    if (w->wbfs)
	wbfs_close(w->wbfs);

    enumError err = ERR_OK;
    if (w->sf)
    {
	w->sf->wbfs = 0;
	if (w->sf_alloced)
	{
	    err = ResetSF(w->sf,0);
	    free(w->sf);
	}
    }

    InitializeWBFS(w);
    return err;
}

///////////////////////////////////////////////////////////////////////////////

enumError SetupWBFS ( WBFS_t * w, SuperFile_t * sf,
			bool print_err, int sector_size, bool recover )
{
    ASSERT(w);
    ASSERT(sf);
    TRACE("SetupWBFS(%p,%d,%d,%d) fd=%d\n",
		sf, print_err, sector_size, recover, GetFD(&sf->f) );

    ResetWBFS(w);
    w->sf = sf;

    if (S_ISREG(sf->f.st.st_mode))
    {
	char format[2*PATH_MAX], fname[PATH_MAX];
	CalcSplitFilename(format,sizeof(format),sf->f.fname,OFT_WBFS);
	snprintf(fname,sizeof(fname),format,1);
	struct stat st;
	if (!stat(fname,&st))
	    SetupSplitFile(&sf->f,OFT_WBFS,0);
    }

    TRACELINE;
    int reset, n_sector;
    if ( sector_size > 0 )
    {
	n_sector = (u32)( sf->f.st.st_size / sector_size );
	reset = recover ? 1 : 2;
    }
    else
    {
	TRACELINE;
	char buf[HD_SECTOR_SIZE];
	enumError err = ReadAtF(&sf->f,0,&buf,sizeof(buf));
	if (err)
	    return err;

	TRACELINE;
	wbfs_head_t * whead = (wbfs_head_t*)buf;
	sector_size = 1 << whead->hd_sec_sz_s;
	n_sector    = 0; // not 'whead->n_hd_sec'
	reset	    = 0;
    }
    sf->f.sector_size = sector_size;

    TRACELINE;
    ASSERT(!w->wbfs);
    TRACE("CALL wbfs_open_partition(ss=%u,ns=%u,reset=%d)\n",
		sector_size, n_sector, reset );
    w->wbfs = wbfs_open_partition( WrapperReadSector,
				   WrapperWriteSector,
				   sf,
				   sector_size,
				   n_sector,
				   0, // partition_lba = index of partiton sector
				   reset );
    TRACELINE;
    if (!w->wbfs)
    {
	TRACE("!! can't open WBFS %s\n",sf->f.fname);
	if (print_err)
	{
	    if (reset)
		ERROR0(ERR_WBFS,"Can't format WBFS partition: %s\n",sf->f.fname);
	    else
		ERROR0(ERR_WBFS_INVALID,"Invalid WBFS partition: %s\n",sf->f.fname);
	}
	return ERR_WBFS_INVALID;
    }

    TRACELINE;
    wbfs_load_id_list(w->wbfs,1);
    CalcWBFSUsage(w);

 #ifdef DEBUG
    TRACE("WBFS %s\n\n",sf->f.fname);
    DumpWBFS(w,TRACE_FILE,15,0,0);
 #endif

    return ERR_OK;
}

///////////////////////////////////////////////////////////////////////////////

enumError CreateGrowingWBFS ( WBFS_t * w, SuperFile_t * sf, off_t size, int sector_size )
{
    ASSERT(w);
    ASSERT(sf);
    ASSERT(size);
    ASSERT(sector_size);
    TRACE("CreateGrowingWBFS(%p,%p,%d)\n",w,sf,sector_size);

    ResetWBFS(w);
    w->sf = sf;

    TRACELINE;
    int n_sector = (u32)( size / sector_size );
    sf->f.sector_size = sector_size;
    sf->f.read_behind_eof = 2;

    TRACELINE;
    ASSERT(!w->wbfs);
    TRACE("CALL wbfs_open_partition(ss=%u,ns=%u,reset=2)\n",
		sector_size, n_sector );
    w->wbfs = wbfs_open_partition( WrapperReadSector,
				   WrapperWriteSector,
				   sf,
				   sector_size,
				   n_sector,
				   0, // partition_lba = index of partiton sector
				   1 );
    TRACELINE;
    if (!w->wbfs)
    {
	TRACE("!! can't create WBFS %s\n",sf->f.fname);
	return ERROR0(ERR_WBFS,"Can't create WBFS partition: %s\n",sf->f.fname);
    }

    TRACELINE;
    CalcWBFSUsage(w);

 #ifdef DEBUG
    TRACE("WBFS %s\n\n",sf->f.fname);
    DumpWBFS(w,TRACE_FILE,15,0,0);
 #endif

    return ERR_OK;
}

///////////////////////////////////////////////////////////////////////////////

static enumError OpenWBFSHelper
	( WBFS_t * w, ccp filename, bool print_err, int sector_size, bool recover )
{
    ASSERT(w);
    TRACE("OpenFileWBFS(%s,%d,%d,%d)\n",
		filename, print_err, sector_size, recover );

    SuperFile_t * sf = malloc(sizeof(SuperFile_t));
    if (!sf)
	OUT_OF_MEMORY;
    InitializeSF(sf);
    sf->f.disable_errors = !print_err;
    enumError err = OpenFileModify(&sf->f,filename,IOM_IS_WBFS);
    if (err)
	goto abort;
    sf->f.disable_errors = false;

    err = SetupWBFS(w,sf,print_err,sector_size,recover);
    if (err)
	goto abort;

    w->sf_alloced = true;
    return ERR_OK;

 abort:
    ResetWBFS(w);
    ResetSF(sf,0);
    free(sf);
    return err;
}

///////////////////////////////////////////////////////////////////////////////

enumError OpenWBFS ( WBFS_t * w, ccp filename, bool print_err )
{
    return OpenWBFSHelper(w,filename,print_err,0,false);
}

///////////////////////////////////////////////////////////////////////////////

enumError FormatWBFS
    ( WBFS_t * w, ccp filename, bool print_err, int sector_size, bool recover )
{
    if ( sector_size < 512 )
	sector_size = 512;
    return OpenWBFSHelper(w,filename,print_err,sector_size,recover);
}

///////////////////////////////////////////////////////////////////////////////

enumError TruncateWBFS ( WBFS_t * w )
{
    ASSERT(w);
    TRACE("TruncateWBFS() fd=%d\n", w->sf ? GetFD(&w->sf->f) : -2 );

    enumError err = CloseWDisc(w);
    if ( w->wbfs && w->sf )
    {
	wbfs_trim(w->wbfs);
	const u64 cut = (u64)w->wbfs->n_hd_sec * w->wbfs->hd_sec_sz;
	TRACE(" - cut = %u * %u = %llu = %llx/hex\n",
		w->wbfs->n_hd_sec, w->wbfs->hd_sec_sz, cut, cut );
	SetSizeF(&w->sf->f,cut);
    }
    return err;
}

///////////////////////////////////////////////////////////////////////////////

enumError CalcWBFSUsage ( WBFS_t * w )
{
    ASSERT(w);
    if (!w->wbfs)
    {
	w->used_discs	= 0;
	w->total_discs	= 0;
	w->free_discs	= 0;
	w->free_mib	= 0;
	w->total_mib	= 0;
	w->used_mib	= 0;
	return ERR_NO_WBFS_FOUND;
    }

    w->used_discs	= wbfs_count_discs(w->wbfs);
    w->total_discs	= w->wbfs->max_disc;
    w->free_discs	= w->total_discs - w->used_discs;

    u32 free_count	= wbfs_count_unusedblocks(w->wbfs);
    w->free_blocks	= free_count;
    w->free_mib		= ( (u64)w->wbfs->wbfs_sec_sz * free_count ) / MiB; // round down!
    w->total_mib	= ( (u64)w->wbfs->wbfs_sec_sz * w->wbfs->n_wbfs_sec + MiB/2 ) / MiB;
    w->used_mib		= w->total_mib - w->free_mib;

    return ERR_OK;
}

///////////////////////////////////////////////////////////////////////////////

enumError SyncWBFS ( WBFS_t * w )
{
    ASSERT(w);
    if (!w->wbfs)
	return ERR_OK;

    wbfs_sync(w->wbfs);
    return CalcWBFSUsage(w);
}

///////////////////////////////////////////////////////////////////////////////

enumError OpenPartWBFS ( WBFS_t * w, PartitionInfo_t * info )
{
    ASSERT(info);
    if ( !info || info->part_mode < PM_WBFS_MAGIC_FOUND )
    {
	ResetWBFS(w);
	return ERR_NO_WBFS_FOUND;
    }

    const enumError err
	= OpenWBFSHelper(w,info->real_path,info->source==PS_PARAM,0,0);
    if (err)
    {
	info->part_mode = PM_WBFS_INVALID;
	return err;
    }

    info->part_mode = PM_WBFS;
    return ERR_OK;
}

///////////////////////////////////////////////////////////////////////////////

static enumError GetWBFSHelper ( WBFS_t * w, PartitionInfo_t ** p_info )
{
    ResetWBFS(w);

    if (p_info)
    {
	PartitionInfo_t * info;
	for ( info = *p_info; info; info = info->next )
	    if ( OpenPartWBFS(w,info) == ERR_OK )
	    {
		*p_info = info;
		return ERR_OK;
	    }
	*p_info = 0;
    }
    return ERR_NO_WBFS_FOUND;
}

//-----------------------------------------------------------------------------

enumError GetFirstWBFS ( WBFS_t * w, PartitionInfo_t ** info )
{
    if (info)
	*info = first_partition_info;
    return GetWBFSHelper(w,info);
}

//-----------------------------------------------------------------------------

enumError GetNextWBFS ( WBFS_t * w, PartitionInfo_t ** info )
{
    if ( info && *info )
	*info = (*info)->next;
    return GetWBFSHelper(w,info);
}

///////////////////////////////////////////////////////////////////////////////

enumError DumpWBFS
	( WBFS_t * wbfs, FILE * f, int indent, int dump_level, CheckWBFS_t * ck )
{
    ASSERT(wbfs);
    char buf[100];

    if ( !f || !wbfs )
	return ERROR0(ERR_INTERNAL,0);

    const bool check_it = dump_level >= 999;
    if ( dump_level >= 999 )
	dump_level -= 1000;

    wbfs_t * w = wbfs->wbfs;
    if (!w)
	return ERR_NO_WBFS_FOUND;

    if ( indent < 0 )
	indent = 0;
    else if ( indent > 100 )
	indent = 100;

    wbfs_head_t * head = w->head;
    if (head)
    {
	fprintf(f,"%*sWBFS-Header:\n", indent,"");
	ccp magic = (ccp)&head->magic;
	fprintf(f,"%*s  WBFS MAGIC: %10x %02x %02x %02x =         '%c%c%c%c'\n",
			indent,"",
			magic[0], magic[1], magic[2], magic[3],
			magic[0] >= ' ' && magic[0] < 0x7f ? magic[0] : '.',
			magic[1] >= ' ' && magic[1] < 0x7f ? magic[1] : '.',
			magic[2] >= ' ' && magic[2] < 0x7f ? magic[2] : '.',
			magic[3] >= ' ' && magic[3] < 0x7f ? magic[3] : '.' );

	fprintf(f,"%*s  WBFS VERSION:     %#13x =%15u\n", indent,"",
			head->wbfs_version, head->wbfs_version );

	fprintf(f,"%*s  hd sectors:       %#13x =%15u\n", indent,"",
			(u32)htonl(head->n_hd_sec), (u32)htonl(head->n_hd_sec) );
	u32 n = 1 << head->hd_sec_sz_s;
	fprintf(f,"%*s  hd sector size:     %#11x =%15u =    2^%u\n", indent,"",
			n, n, head->hd_sec_sz_s );
	n = 1 << head->wbfs_sec_sz_s;
	fprintf(f,"%*s  WBFS sector size:   %#11x =%15u =    2^%u\n\n", indent,"",
			n, n, head->wbfs_sec_sz_s );

	ASSERT(sizeof(buf)>=60);
	fprintf(f,"%*s  Disc table (slot usage):\n", indent,"" );
	u8 * dt = head->disc_table;
	int count = w->max_disc, idx = 0;
	while ( count > 0 )
	{
	    const int max = 50;
	    int i, n = count < max ? count : max;
	    char * dest = buf;
	    for ( i = 0; i < n; i++ )
	    {
		if (!(i%10))
		    *dest++ = ' ';
		*dest++ = *dt++ ? '#' : '.';
	    }
	    *dest = 0;
	    fprintf( f, "%*s    %3d..%3d:%s\n", indent,"", idx, idx+n-1, buf );
	    idx += n;
	    count -= n;
	}
	fputs("\n",f);
    }
    else
	fprintf(f,"%*s!! NO WBFS HEADER DEFINED !!\n\n", indent,"");

    fprintf(f,"%*shd sector size:       %#11x =%15u =    2^%u\n", indent,"",
		w->hd_sec_sz, w->hd_sec_sz, w->hd_sec_sz_s );
    fprintf(f,"%*shd num of sectors:    %#11x =%15u\n", indent,"",
		w->n_hd_sec, w->n_hd_sec );
    u64 hd_total = (u64)w->hd_sec_sz * w->n_hd_sec;
    fprintf(f,"%*shd total size:    %#15llx =%15llu =%8llu MiB\n\n", indent,"",
		hd_total, hd_total, ( hd_total + MiB/2 ) / MiB  );

    fprintf(f,"%*swii sector size:      %#11x =%15u =    2^%u\n", indent,"",
		w->wii_sec_sz, w->wii_sec_sz, w->wii_sec_sz_s );
    fprintf(f,"%*swii sectors/disc:     %#11x =%15u\n", indent,"",
		w->n_wii_sec_per_disc, w->n_wii_sec_per_disc  );
    fprintf(f,"%*swii num of sectors:   %#11x =%15u\n", indent,"",
		w->n_wii_sec, w->n_wii_sec );
    u64 wii_total =(u64)w->wii_sec_sz * w->n_wii_sec;
    fprintf(f,"%*swii total size:   %#15llx =%15llu =%8llu MiB\n\n", indent,"",
		wii_total, wii_total, ( wii_total + MiB/2 ) / MiB  );

     const u32 NSEC  = w->n_wbfs_sec;
     const u32 NSEC2 = w->n_wbfs_sec / 2;
    const u32 used_blocks = NSEC - wbfs->free_blocks;
    const u32 used_perc   = NSEC ? ( 100 * used_blocks       + NSEC2 ) / NSEC : 0;
    const u32 free_perc   = NSEC ? ( 100 * wbfs->free_blocks + NSEC2 ) / NSEC : 0;
     const u64 wbfs_used  = (u64)w->wbfs_sec_sz * used_blocks;
     const u64 wbfs_free  = (u64)w->wbfs_sec_sz * wbfs->free_blocks;
     const u64 wbfs_total = (u64)w->wbfs_sec_sz * NSEC;
    const u32 used_mib    = ( wbfs_used  + MiB/2 ) / MiB;
    const u32 free_mib    = ( wbfs_free  + MiB/2 ) / MiB;
    const u32 total_mib   = ( wbfs_total + MiB/2 ) / MiB;

    fprintf(f,"%*swbfs block size:      %#11x =%15u =    2^%u\n", indent,"",
		w->wbfs_sec_sz, w->wbfs_sec_sz, w->wbfs_sec_sz_s );
    fprintf(f,"%*swbfs blocks/disc:     %#11x =%15u\n", indent,"",
		w->n_wbfs_sec_per_disc, w->n_wbfs_sec_per_disc );
    fprintf(f,"%*swbfs free blocks:     %#11x =%15u =%8u MiB = %3u%%\n", indent,"",
		wbfs->free_blocks, wbfs->free_blocks, free_mib, free_perc );
    fprintf(f,"%*swbfs used blocks:     %#11x =%15u =%8u MiB = %3u%%\n", indent,"",
		used_blocks, used_blocks, used_mib, used_perc );
    fprintf(f,"%*swbfs total blocks:    %#11x =%15u =%8u MiB = 100%%\n", indent,"",
		w->n_wbfs_sec, w->n_wbfs_sec, total_mib );
    fprintf(f,"%*swbfs total size:  %#15llx =%15llu =%8u MiB\n\n", indent,"",
		wbfs_total, wbfs_total, total_mib  );

    fprintf(f,"%*spartition lba:        %#11x =%15u\n", indent,"",
		w->part_lba, w->part_lba );
    fprintf(f,"%*sfree blocks lba:      %#11x =%15u\n", indent,"",
		w->freeblks_lba, w->freeblks_lba );
    const u32 fb_lb_size = w->freeblks_lba_count * w->hd_sec_sz;
    fprintf(f,"%*sfree blocks lba size: %#11x =%15u =  %u blocks\n", indent,"",
		fb_lb_size, fb_lb_size, w->freeblks_lba_count );
    fprintf(f,"%*sfree blocks size:     %#11x =%15u\n", indent,"",
		w->freeblks_size4 * 4, w->freeblks_size4 * 4 );
    fprintf(f,"%*sfb last u32 mask:     %#11x =%15u\n", indent,"",
		w->freeblks_mask, w->freeblks_mask );
    fprintf(f,"%*sdisc info size:       %#11x =%15u\n\n", indent,"",
		w->disc_info_sz, w->disc_info_sz );

    fprintf(f,"%*sused slots (wii discs):  %8u =%14u%%\n", indent,"",
		wbfs->used_discs, 100 * wbfs->used_discs / w->max_disc );
    fprintf(f,"%*stotal slots (wii discs): %8u =%14u%%\n", indent,"",
		 w->max_disc, 100 );

    MemMap_t mm;
    MemMapItem_t * mi;
    InitializeMemMap(&mm);

    if ( dump_level > 0 )
    {
	ASSERT(w);
	const u32 sec_per_disc = w->n_wbfs_sec_per_disc;
	const u32 wii_sec_per_wbfs_sect
			= 1 << ( w->wbfs_sec_sz_s - w->wii_sec_sz_s );
	const off_t sec_size  = w->wbfs_sec_sz;
	const off_t sec_delta = w->part_lba * w->hd_sec_sz;

	u32 slot;
	WDiscInfo_t dinfo;
	for ( slot = 0; slot < w->max_disc; slot++ )
	{
	    noTRACE("---");
	    noTRACE(">> SLOT = %d/%d\n",slot,w->max_disc);
	    if ( ck && ck->disc && !ck->disc[slot].err_count )
		continue;

	    wbfs_disc_t * d = wbfs_open_disc_by_slot(w,slot);
	    if (!d)
		continue;

	    WDiscHeader_t ihead;
	    LoadIsoHeader(wbfs,&ihead,d);

	    if ( GetWDiscInfoBySlot(wbfs,&dinfo,slot) != ERR_OK )
		fprintf(f,"\n%*s!! NO INFO ABOUT DISC #%d AVAILABE !!\n", indent,"", slot);
	    else
	    {
		fprintf(f,"\n%*sDump of Wii disc at slot #%d of %d:\n", indent,"",
		    slot, w->max_disc );
		DumpWDiscInfo(&dinfo,&ihead,f,indent+2);
		if ( w->head->disc_table[slot] & 2 )
		    fprintf(f,"%*s>>> DISC MARKED AS INVALID! <<<\n",indent,"");
	    }

	    if ( dump_level > 1 )
	    {
		int ind = indent + 3;
		fprintf(f,"\n%*sWii disc memory mapping:\n\n"
		    "%*s   mapping index :    wbfs blocks :      disc offset range :     size\n"
		    "%*s----------------------------------------------------------------------\n",
		    ind-1,"", ind,"", ind,"" );
		u16 * tab = d->header->wlba_table;

		u8 used[0x10000];
		memset(used,0,sizeof(used));
		ASSERT( sec_per_disc < sizeof(used) );

		int idx = 0;
		for (;;)
		{
		    while ( idx < sec_per_disc && !tab[idx] )
			idx++;
		    if ( idx == sec_per_disc )
			break;
		    const u32 start = idx;
		    int delta = ntohs(tab[idx])-idx;
		    while ( idx < sec_per_disc )
		    {
			u32 wlba = ntohs(tab[idx]);
			if (!wlba)
			    break;
			if ( wlba < sizeof(used) )
			    used[wlba] = 1;
			if ( wlba-idx != delta )
			    break;
			idx++;
		    }

		    off_t off  = start * wii_sec_per_wbfs_sect * (u64)WII_SECTOR_SIZE;
		    off_t size = (idx-start) * wii_sec_per_wbfs_sect * (u64)WII_SECTOR_SIZE;

		    if ( start == idx - 1 )
		    	fprintf(f,"%*s%11u      : %9u      :%10llx ..%10llx :%9llx\n",
			    ind,"",
			    start,
			    start + delta,
			    off,
			    off + size,
			    size );
		    else
		    	fprintf(f,"%*s%7u ..%6u : %5u .. %5u :%10llx ..%10llx :%9llx\n",
			    ind,"",
			    start,
			    idx - 1,
			    start + delta,
			    idx - 1 + delta,
			    off,
			    off + size,
			    size );
		}

		if ( dump_level > 2 )
		{
		    mi = InsertMemMap(&mm, w->hd_sec_sz+slot*w->disc_info_sz,
				sizeof(d->header->disc_header_copy)
				+ sizeof(*d->header->wlba_table) * w->n_wbfs_sec_per_disc );
		    snprintf(mi->info,sizeof(mi->info),
				"Inode of slot #%03u [%s]",slot,dinfo.id6);

		    int idx = 0, segment = 0;
		    for ( ;; segment++ )
		    {
			while ( idx < NSEC && !used[idx] )
			    idx++;
			if ( idx == NSEC )
			    break;
			const u32 start = idx;
			while ( idx < NSEC && used[idx] )
			    idx++;

			const int n = idx - start;
			mi = InsertMemMap(&mm, start*sec_size+sec_delta, n*sec_size );
			if (segment)
			    snprintf(mi->info,sizeof(mi->info),
				"%4u block%s -> disc #%03u.%u [%s]",
				n, n == 1 ? " " : "s", slot, segment, dinfo.id6 );
			else
			    snprintf(mi->info,sizeof(mi->info),
				"%4u block%s -> disc #%03u   [%s]",
				n, n == 1 ? " " : "s", slot, dinfo.id6 );
		    }
		}
	    }
	    wbfs_close_disc(d);
	}
    }
    fputc('\n',f);

    if ( dump_level > 2 )
    {
	mi = InsertMemMap(&mm,0,sizeof(wbfs_head_t));
	StringCopyS(mi->info,sizeof(mi->info),"WBFS header");

	mi = InsertMemMap(&mm,sizeof(wbfs_head_t),w->max_disc);
	StringCopyS(mi->info,sizeof(mi->info),"Disc table");

	int slot = 0;
	for (;;)
	{
	    int start = slot;
	    while ( slot < w->max_disc && !head->disc_table[slot] )
		slot++;
	    int count = slot - start;
	    if (count)
	    {
		mi = InsertMemMap(&mm, w->hd_sec_sz + start * w->disc_info_sz,
					count * w->disc_info_sz );
		if ( count > 1 )
		    snprintf(mi->info,sizeof(mi->info),
				"%d unused inodes, slots #%03u..#%03u",
				count, start, slot-1 );
		else
		    snprintf(mi->info,sizeof(mi->info),
				"Unused inode, slot #%03u",start);
	    }
	    if ( slot == w->max_disc )
		break;
	    slot++;
	}

	const off_t fbt_off  = ( w->part_lba + w->freeblks_lba ) * w->hd_sec_sz;
	mi = InsertMemMap(&mm,fbt_off,w->freeblks_size4*4);
	StringCopyS(mi->info,sizeof(mi->info),"Free blocks table");

	mi = InsertMemMap(&mm,w->wbfs_sec_sz,0);
	StringCopyS(mi->info,sizeof(mi->info),"-- end of management block #0 --");

	if ( wbfs_total < hd_total )
	{
	    mi = InsertMemMap(&mm,wbfs_total,0);
	    StringCopyS(mi->info,sizeof(mi->info),"-- end of WBFS data --");
	}

	mi = InsertMemMap(&mm,hd_total,0);
	StringCopyS(mi->info,sizeof(mi->info),"-- end of WBFS device/file --");

	fprintf(f,"\f\n%*sWBFS Memory Map:\n\n", indent,"" );
	PrintMemMap(&mm,f,indent+1);

	fputc('\n',f);
    }
    ResetMemMap(&mm);

    if ( check_it && isatty(fileno(f)) )
    {
	CheckWBFS_t ck;
	InitializeCheckWBFS(&ck);
	if (CheckWBFS(&ck,wbfs,0,f,1))
	    fprintf(f,"   -> use command \"CHECK -vv\" for a verbose report!\n\n");
	ResetCheckWBFS(&ck);
    }

    return ERR_OK;
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////                     Check WBFS                  ///////////////
///////////////////////////////////////////////////////////////////////////////

void InitializeCheckWBFS ( CheckWBFS_t * ck )
{
    ASSERT(ck);
    memset(ck,0,sizeof(*ck));
}

///////////////////////////////////////////////////////////////////////////////

void ResetCheckWBFS ( CheckWBFS_t * ck )
{
    ASSERT(ck);
    free(ck->cur_fbt);
    free(ck->good_fbt);
    free(ck->ubl);
    free(ck->blc);
    free(ck->disc);
    InitializeCheckWBFS(ck);
}

///////////////////////////////////////////////////////////////////////////////

enumError CheckWBFS
	( CheckWBFS_t * ck, WBFS_t * wbfs, int verbose, FILE * f, int indent )
{
    ASSERT(ck);
    ASSERT(wbfs);

    enum { SHOW_SUM, SHOW_DETAILS, PRINT_DUMP, PRINT_EXT_DUMP, PRINT_FULL_DUMP };

    ResetCheckWBFS(ck);
    if ( !wbfs || !wbfs->wbfs || !wbfs->sf || !IsFileOpen(&wbfs->sf->f) )
	return ERROR0(ERR_INTERNAL,0);

    ck->wbfs = wbfs;
    wbfs_t * w = wbfs->wbfs;

    if (!f)
	verbose = -1;

    if ( indent < 0 )
	indent = 0;
    else if ( indent > 50 )
	indent = 50;

    ck->fbt_off  = ( w->part_lba + w->freeblks_lba ) * w->hd_sec_sz;
    ck->fbt_size = w->freeblks_lba_count * w->hd_sec_sz;

    //---------- calculate number of sectors

    const u32 N_SEC = w->n_wbfs_sec;

    u32 ALLOC_SEC = ck->fbt_size * 8;
    if ( ALLOC_SEC < N_SEC )
	ALLOC_SEC = N_SEC;

    u32 WBFS0_SEC = N_SEC;	// used sectors

    if ( w->head->wbfs_version == 0 )
    {
	// the old wbfs versions have calculation errors
	//  - because a rounding error 'n_wii_sec' is sometimes to short
	//	=> 'n_wbfs_sec' is to short
	//	=> free blocks table may be too small
	//  - block search uses only (n_wbfs_sec/32)*32 blocks

	// this is the old buggy calcualtion
	u32 n_wii_sec  = ( w->n_hd_sec / w->wii_sec_sz ) * w->hd_sec_sz;
	WBFS0_SEC = n_wii_sec >> ( w->wbfs_sec_sz_s - w->wii_sec_sz_s );

	WBFS0_SEC = ( WBFS0_SEC / 32 ) * 32 + 1;

	if ( WBFS0_SEC > N_SEC )
	     WBFS0_SEC = N_SEC;
    }
    TRACE("N-SEC=%u, WBFS0-SEC=%u, ALLOC-SEC=%u\n",N_SEC,WBFS0_SEC,ALLOC_SEC);

    //---------- alloctate data

    u32 * fbt  = malloc(ck->fbt_size);
    u8  * ubl  = calloc(ALLOC_SEC,1);
    u8  * blc  = calloc(ALLOC_SEC,1);
    CheckDisc_t * disc = calloc(w->max_disc,sizeof(*disc));
    if ( !fbt || !ubl || !blc || !disc )
	return OUT_OF_MEMORY;

    ck->cur_fbt	= fbt;
    ck->ubl	= ubl;
    ck->blc	= blc;
    ck->disc	= disc;

    //---------- load free blocks table

    enumError err = ReadAtF(&wbfs->sf->f,ck->fbt_off,fbt,ck->fbt_size);
    if (err)
	return err;

    int i, j, bl = 1;
    for ( i = 0; i < w->freeblks_size4; i++ )
    {
	u32 v = wbfs_ntohl(fbt[i]);
	if ( v == ~(u32)0 )
	    bl += 32;
	else
	    for ( j = 0; j < 32; j++, bl++ )
		if ( !(v & 1<<j) )
		    ubl[bl] = 1;
    }

    //---------- scan discs

    if ( verbose >= SHOW_DETAILS )
	fprintf(f,"%*s* Scan %d discs in %d slots.\n",
			indent,"", wbfs->used_discs, w->max_disc );
    u32 slot;
    for ( slot = 0; slot < w->max_disc; slot++ )
    {
	wbfs_disc_t * d = wbfs_open_disc_by_slot(w,slot);
	if (!d)
	    continue;

	u16 * wlba_tab = d->header->wlba_table;
	ASSERT(wlba_tab);

	int bl;
	for ( bl = 0; bl < w->n_wbfs_sec_per_disc; bl++ )
	{
	    const u32 wlba = ntohs(wlba_tab[bl]);
	    if ( wlba > 0 && wlba < N_SEC && blc[wlba] < 255 )
		blc[wlba]++;
	}

	wbfs_close_disc(d);
    }

    //---------- check for disc errors

    if ( verbose >= SHOW_DETAILS )
	fprintf(f,"%*s* Check for disc block errors.\n", indent,"" );

    u32 total_err_invalid   = 0;
    u32 total_err_no_blocks = 0;
    u32 invalid_disc_count  = 0;
    bool sync = false;

    for ( slot = 0; slot < w->max_disc; slot++ )
    {
	wbfs_disc_t * d = wbfs_open_disc_by_slot(w,slot);
	if (!d)
	    continue;

	CheckDisc_t * g = disc + slot;
	memcpy(g->id6,d->header->disc_header_copy,6);

	u16 * wlba_tab = d->header->wlba_table;
	ASSERT(wlba_tab);

	int bl;
	u32 invalid_game = 0, block_count = 0;
	for ( bl = 0; bl < w->n_wbfs_sec_per_disc; bl++ )
	{
	    const u32 wlba = ntohs(wlba_tab[bl]);
	    if ( wlba >= N_SEC )
	    {
		invalid_game = 1;
		g->err_count++;
		g->bl_invalid++;
		total_err_invalid++;
		if ( verbose >= SHOW_DETAILS )
		    fprintf(f,"%*s  - #%d=%s/%u: invalid WBFS block #%u for block!\n",
				indent,"", slot, g->id6, bl, wlba );
	    }
	    else if ( wlba )
	    {
		block_count++;
		if ( !ubl[wlba] )
		{
		    invalid_game = 1;
		    g->err_count++;
		    g->bl_fbt++;
		    if ( verbose >= SHOW_DETAILS )
			fprintf(f,"%*s  - #%d=%s/%u: WBFS block #%u marked as free!\n",
				    indent,"", slot, g->id6, bl, wlba );
		}

		if ( blc[wlba] > 1 )
		{
		    invalid_game = 1;
		    g->err_count++;
		    g->bl_overlap++;
		    if ( verbose >= SHOW_DETAILS )
			fprintf(f,"%*s  - #%d=%s/%u: WBFS block #%u is used %u times!\n",
				    indent,"", slot, g->id6, bl, wlba, blc[wlba] );
		}
	    }
	}

	if (!block_count)
	{
	    invalid_game = 1;
	    g->no_blocks = 1;
	    g->err_count++;
	    total_err_no_blocks++;
	    if ( verbose >= SHOW_DETAILS )
		fprintf(f,"%*s  - #%d=%s: no valid WBFS block!\n", indent,"", slot, g->id6 );
	}

	if (invalid_game)
	{
	    invalid_disc_count += invalid_game;
	    ASSERT(w->head);
	    if ( !(w->head->disc_table[slot] & 2) )
	    {
		w->head->disc_table[slot] |= 2;
		sync = true;
	    }
	}

	wbfs_close_disc(d);
    }

    //---------- check free blocks table.

    if ( verbose >= SHOW_DETAILS )
	fprintf(f,"%*s* Check free blocks table.\n", indent,"" );

    u32 total_err_overlap  = 0;
    for ( bl = 0; bl < N_SEC; bl++ )
	if ( blc[bl] > 1 )
	    total_err_overlap++;

    u32 total_err_fbt_used = 0;
    u32 total_err_fbt_free = 0;
    u32 total_err_fbt_free_wbfs0 = 0;

    for ( bl = 1; bl < N_SEC; )
    {
	if ( blc[bl] && !ubl[bl] )
	{
	    const int start_bl = bl;
	    while ( bl < N_SEC && blc[bl] && !ubl[bl] )
		bl++;
	    const int count = bl - start_bl;
	    total_err_fbt_used += count;
	    if ( verbose >= SHOW_DETAILS )
	    {
		if ( count > 1 )
		    fprintf(f,"%*s  - %d used WBFS sectors #%u .. #%u marked as 'free'!\n",
				indent,"", count, start_bl, bl-1 );
		else
		    fprintf(f,"%*s  - Used WBFS sector #%u marked as 'free'!\n",
				indent,"", bl );
	    }
	}
	else if ( !blc[bl] && ubl[bl] )
	{
	    const int start_bl = bl;
	    while ( bl < N_SEC && !blc[bl] && ubl[bl] )
		bl++;
	    const int count = bl - start_bl;
	    total_err_fbt_free += count;

	    int wbfs0_count = 0;
	    if ( bl > WBFS0_SEC )
	    {
		const int max = bl - WBFS0_SEC;
		wbfs0_count = count < max ? count : max;
	    }

	    if ( verbose >= SHOW_DETAILS )
	    {
		if ( count > 1 )
		    fprintf(f,"%*s  - %d free WBFS sectors #%u .. #%u marked as 'used'!\n",
				indent,"", count, start_bl, bl-1 );
		else
		    fprintf(f,"%*s  - Free WBFS sector #%u marked as 'used'!\n",
				indent,"", bl );
		if ( wbfs0_count && !total_err_fbt_free_wbfs0 )
		    fprintf(f,"%*sNote: Free sectors >= #%u are marked 'used' because a bug in libwbfs v0.\n",
				indent+6,"", WBFS0_SEC );
	    }

	    total_err_fbt_free_wbfs0 += wbfs0_count;
	}
	else
	    bl++;
    }

    if (sync)
	wbfs_sync(w);

    //---------- summary

    ck->err_fbt_used		= total_err_fbt_used;
    ck->err_fbt_free		= total_err_fbt_free;
    ck->err_fbt_free_wbfs0	= total_err_fbt_free_wbfs0;
    ck->err_no_blocks		= total_err_no_blocks;
    ck->err_bl_overlap		= total_err_overlap;
    ck->err_bl_invalid		= total_err_invalid;
    ck->invalid_disc_count	= invalid_disc_count;

    ck->err_total = total_err_fbt_used
		  + total_err_fbt_free
		  + total_err_no_blocks
		  + total_err_overlap
		  + total_err_invalid;

    ck->err = ck->err_fbt_used || ck->err_bl_overlap
		? ERR_WBFS_INVALID
		: ck->err_total
			? ERR_WARNING
			: ERR_OK;

    if ( ck->err_total && verbose >= PRINT_DUMP )
    {
	printf("\f\nWBFS DUMP:\n\n");
	DumpWBFS(wbfs,f,indent,
		verbose >= PRINT_FULL_DUMP ? 3 : 2,
		verbose >= PRINT_EXT_DUMP  ? 0 : ck );
    }

    if ( ck->err_total && verbose >= SHOW_SUM || verbose >= SHOW_DETAILS )
    {
	printf("\f\n");
	PrintCheckedWBFS(ck,f,indent);
    }

    return ck->err;
}

///////////////////////////////////////////////////////////////////////////////

enumError AutoCheckWBFS	( WBFS_t * wbfs, bool ignore_check )
{
    ASSERT(wbfs);
    ASSERT(wbfs->wbfs);

    CheckWBFS_t ck;
    InitializeCheckWBFS(&ck);
    enumError err = CheckWBFS(&ck,wbfs,-1,0,0);
    if (err)
    {
	PrintCheckedWBFS(&ck,stdout,1);
	if ( !ignore_check && err > ERR_WARNING )
	    printf(" >> To avoid this automatic check use the option --no-check.\n"
		   " >> To ignore the results of this check use option --force.\n"
		   "\n" );
    }
    ResetCheckWBFS(&ck);
    return ignore_check ? ERR_OK : err;
}

///////////////////////////////////////////////////////////////////////////////

enumError PrintCheckedWBFS ( CheckWBFS_t * ck, FILE * f, int indent )
{
    ASSERT(ck);
    if ( !ck->wbfs || !ck->cur_fbt || !f )
	return ERR_OK;

    if ( indent < 0 )
	indent = 0;
    else if ( indent > 50 )
	indent = 50;

    if ( ck->err_total )
    {
	fprintf(f,"%*s* Summary of WBFS Check: %u error%s found:\n",
		indent,"", ck->err_total, ck->err_total == 1 ? "" : "s" );
	if (ck->err_fbt_used)
	    fprintf(f,"%*s%5u used WBFS sector%s marked as free!\n",
		indent,"", ck->err_fbt_used, ck->err_fbt_used == 1 ? "" : "s" );
	if (ck->err_fbt_free)
	{
	    fprintf(f,"%*s%5u free WBFS sector%s marked as used!\n",
		indent,"", ck->err_fbt_free, ck->err_fbt_free == 1 ? "" : "s" );
	    if (ck->err_fbt_free_wbfs0)
		fprintf(f,"%*sNote: %u error%s are based on a bug in libwbfs v0.\n",
		    indent+6,"", ck->err_fbt_free_wbfs0,
		    ck->err_fbt_free_wbfs0 == 1 ? "" : "s" );
	}
	if (ck->err_bl_overlap)
	    fprintf(f,"%*s%5u WBFS sector%s are used by 2 or more discs!\n",
		indent,"", ck->err_bl_overlap, ck->err_bl_overlap == 1 ? "" : "s" );
	if (ck->err_bl_invalid)
	    fprintf(f,"%*s%5u invalid WBFS block reference%s found!\n",
		indent,"", ck->err_bl_invalid, ck->err_bl_invalid == 1 ? "" : "s" );
	if (ck->err_no_blocks)
	    fprintf(f,"%*s%5u disc%s no valid WBFS blocks!\n",
		indent,"", ck->err_no_blocks, ck->err_no_blocks == 1 ? " has" : "s have" );
	if (ck->invalid_disc_count)
	    fprintf(f,"%*s  Total: %u disc%s invalid!\n",
		indent,"", ck->invalid_disc_count,
		ck->invalid_disc_count == 1 ? " is" : "s are" );
	fputc('\n',f);
    }
    else
	fprintf(f,"%*s* Summary of WBFS check: no errors found.\n", indent,"" );

    return ck->err_total ? ERR_WBFS_INVALID : ERR_OK;
}

///////////////////////////////////////////////////////////////////////////////

enumError RepairWBFS ( CheckWBFS_t * ck, int testmode,
	RepairMode rm, int verbose, FILE * f, int indent )
{
    TRACE("RepairWBFS(%p,%d,%x,%d,%p,%d)\n",
		ck, testmode, rm, verbose, f, indent );

    ASSERT(ck);
    ASSERT(ck->wbfs);
    ASSERT(ck->wbfs->sf);
    ASSERT(ck->cur_fbt);

    wbfs_t * w = ck->wbfs->wbfs;
    ASSERT(w);

    u32 repair_count = 0, sync = 0;
    if (!f)
	verbose = -1;
    else if ( testmode && verbose < 0 )
	verbose = 0;

    TRACELINE;
    if ( rm & REPAIR_RM_ALL )
    {
	int slot;
	for ( slot = 0; slot < w->max_disc; slot++ )
	{
	    CheckDisc_t * disc = ck->disc + slot;
	    if ( w->head->disc_table[slot]
		&& (   rm & REPAIR_RM_INVALID && disc->bl_invalid
		    || rm & REPAIR_RM_OVERLAP && disc->bl_overlap
		    || rm & REPAIR_RM_FREE    && disc->bl_fbt
		    || rm & REPAIR_RM_EMPTY   && disc->no_blocks
		   ))
	    {
		if ( verbose >= 0 )
		{
		    ccp title = GetTitle(disc->id6,0);
		    fprintf(f,"%*s* %sDrop disc at slot #%u, id=%s%s%s\n",
			indent,"", testmode ? "WOULD " : "", slot, disc->id6,
			title ? ", " : "", title ? title : "" );
		}

		if (!testmode)
		{
		    w->head->disc_table[slot] = 0;
		    sync++;
		}
		repair_count++;
	    }
	}
    }

    TRACELINE;
    if ( rm & REPAIR_FBT )
    {
	TRACELINE;
	if ( CalcFBT(ck) )
	{
	    TRACELINE;
	    if ( verbose >= 0 )
		fprintf(f,"%*s* %sStore fixed 'free blocks table' (%zd bytes).\n",
		    indent,"", testmode ? "WOULD " : "", ck->fbt_size );

	    if (!testmode)
	    {
		TRACELINE;
		enumError err = WriteAtF( &ck->wbfs->sf->f,
					    ck->fbt_off, ck->good_fbt, ck->fbt_size );
		if (err)
		    return err;
		memcpy(ck->cur_fbt,ck->good_fbt,ck->fbt_size);
		if (w->freeblks)
		{
		    free(w->freeblks);
		    w->freeblks = 0;
		}
		sync++;
	    }
	    repair_count++;
	}

	TRACELINE;
	if ( w->head->wbfs_version < WBFS_VERSION )
	{
	    if ( verbose >= 0 )
		fprintf(f,"%*s* %sSet WBFS version from %u to %u.\n",
		    indent,"", testmode ? "WOULD " : "",
		    w->head->wbfs_version,  WBFS_VERSION );
	    if (!testmode)
	    {
		w->head->wbfs_version = WBFS_VERSION;
		sync++;
	    }
	    repair_count++;
	}
    }

    TRACELINE;
    if (sync)
	wbfs_sync(w);

    TRACELINE;
    if ( verbose >= 0 && repair_count )
	fputc('\n',f);

    TRACELINE;
    return ERR_OK;
}

///////////////////////////////////////////////////////////////////////////////

enumError CheckRepairWBFS ( WBFS_t * wbfs, int testmode,
	RepairMode rm, int verbose, FILE * f, int indent )
{
    ASSERT(wbfs);

    CheckWBFS_t ck;
    InitializeCheckWBFS(&ck);
    enumError err = CheckWBFS(&ck,wbfs,-1,0,0);
    if ( err == ERR_WARNING || err == ERR_WBFS_INVALID )
	err = RepairWBFS(&ck,testmode,rm,verbose,f,indent);
    ResetCheckWBFS(&ck);
    return err;
}

///////////////////////////////////////////////////////////////////////////////

enumError RepairFBT ( WBFS_t * w, int testmode, FILE * f, int indent )
{
    return CheckRepairWBFS(w,testmode,REPAIR_FBT,0,f,indent);
}

///////////////////////////////////////////////////////////////////////////////

bool CalcFBT ( CheckWBFS_t * ck )
{
    ASSERT(ck);
    if ( !ck->wbfs || !ck->wbfs->wbfs || !ck->cur_fbt )
	return ERROR0(ERR_INTERNAL,0);

    if (!ck->good_fbt)
    {
	ck->good_fbt = malloc(ck->fbt_size);
	if (!ck->good_fbt)
	    OUT_OF_MEMORY;
    }

    memset(ck->good_fbt,0,ck->fbt_size);

    const u32 MAX_BL = ck->wbfs->wbfs->n_wbfs_sec - 2;
    u32 * fbt = ck->good_fbt;
    int bl;
    for ( bl = 0; bl <= MAX_BL; bl++ )
	if (!ck->blc[bl+1])
	    fbt[bl/32] |= 1 << (bl&31);

    for ( bl = 0; bl < ck->fbt_size/4; bl++ )
	fbt[bl] = htonl(fbt[bl]);

    return memcmp(ck->cur_fbt,ck->good_fbt,ck->fbt_size);
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////                     WiiDiscInfo                 ///////////////
///////////////////////////////////////////////////////////////////////////////

void InitializeWDiscInfo ( WDiscInfo_t * dinfo )
{
    memset(dinfo,0,sizeof(*dinfo));
}

///////////////////////////////////////////////////////////////////////////////

enumError ResetWDiscInfo ( WDiscInfo_t * dinfo )
{
    // nothing to do
    if (dinfo->pinfo)
	free(dinfo->pinfo);
    InitializeWDiscInfo(dinfo);
    return ERR_OK;
}

///////////////////////////////////////////////////////////////////////////////

enumError GetWDiscInfo ( WBFS_t * w, WDiscInfo_t * dinfo, int disc_index )
{
    ASSERT(w);
    if ( !w || !w->wbfs || !dinfo )
	return ERROR0(ERR_INTERNAL,0);

    u32 size4;
    const enumError err = wbfs_get_disc_info ( w->wbfs, disc_index,
			    (u8*)&dinfo->dhead, sizeof(dinfo->dhead), &size4 );

    if (err)
    {
	memset(dinfo,0,sizeof(*dinfo));
	return err;
    }

    CalcWDiscInfo(dinfo);
    dinfo->disc_index = disc_index;
    dinfo->size  = (u64)size4 * 4;

    return ERR_OK;
}

///////////////////////////////////////////////////////////////////////////////

enumError GetWDiscInfoBySlot ( WBFS_t * w, WDiscInfo_t * dinfo, u32 disc_slot )
{
    ASSERT(w);
    if ( !w || !w->wbfs || !dinfo )
	return ERROR0(ERR_INTERNAL,0);

    memset(dinfo,0,sizeof(*dinfo));

    u32 size4;
    const enumError err = wbfs_get_disc_info_by_slot ( w->wbfs, disc_slot,
			    (u8*)&dinfo->dhead, sizeof(dinfo->dhead), &size4 );

    if (err)
    {
	TRACE("GetWDiscInfoBySlot() err=%d, magic=%x\n",err,dinfo->dhead.magic);
	return err;
    }

    CalcWDiscInfo(dinfo);
    dinfo->disc_index = disc_slot;
    dinfo->size  = (u64)size4 * 4;

    return ERR_OK;
}

///////////////////////////////////////////////////////////////////////////////

enumError FindWDiscInfo ( WBFS_t * w, WDiscInfo_t * dinfo, ccp id6 )
{
    // [2do] is this done by the wbfs subsystem?
    ASSERT(w);
    ASSERT(dinfo);
    ASSERT(id6);
    if ( !w || !w->wbfs || !dinfo || !id6 || strlen(id6) != 6 )
	return ERROR0(ERR_INTERNAL,0);

    int i;
    for ( i = 0; i < w->used_discs; i++ )
    {
	if ( GetWDiscInfo(w,dinfo,i) == ERR_OK
	    && !memcmp(id6,&dinfo->dhead.wii_disc_id,6) )
		return ERR_OK;
    }
    return ERR_WDISC_NOT_FOUND;
}

///////////////////////////////////////////////////////////////////////////////

enumError LoadIsoHeader	( WBFS_t * w, WDiscHeader_t * iso_header, wbfs_disc_t * disc )
{
    ASSERT(w);
    ASSERT(iso_header);

    if ( !w || !w->sf || !w->wbfs || !iso_header )
	return ERROR0(ERR_INTERNAL,0);

    memset(iso_header,0,sizeof(*iso_header));
    if (!disc)
    {
	disc = w->disc;
	if (!disc)
	    return ERR_OK;
    }

    u16 wlba = ntohs(disc->header->wlba_table[0]);
    if (!wlba)
	return ERR_OK;

    char buf[HD_SECTOR_SIZE]; // read whole hd sector
    enumError err = ReadSF(w->sf, wlba * (off_t)w->wbfs->wbfs_sec_sz,
			buf, sizeof(buf) );
    if (!err)
	memcpy(iso_header,buf,sizeof(*iso_header));
    return err;
}

///////////////////////////////////////////////////////////////////////////////

void CalcWDiscInfo ( WDiscInfo_t * dinfo )
{
    ASSERT(dinfo);

    memcpy(dinfo->id6,&dinfo->dhead.wii_disc_id,6);
    dinfo->id6[6] = 0;
    dinfo->title = GetTitle(dinfo->id6,0);
    dinfo->disc_index = 0;
    dinfo->size  = 0;

    ccp * tptr = GetRegionInfo(dinfo->dhead.region_code);
    dinfo->region4 = *tptr++;
    dinfo->region  = *tptr;
}

///////////////////////////////////////////////////////////////////////////////

void CopyWDiscInfo ( WDiscListItem_t * item, WDiscInfo_t * dinfo )
{
    ASSERT(item);
    ASSERT(dinfo);

    memset(item,0,sizeof(*item));

    memcpy(item->id6,&dinfo->dhead.wii_disc_id,6);
    item->size_mib = (u32)(( dinfo->size + MiB/2 ) / MiB );
    memcpy(item->name64,dinfo->dhead.game_title,64);
    memcpy(item->region4,dinfo->region4,4);
    item->title  = dinfo->title;
    item->n_part = dinfo->n_part;
    item->xtime  = SelectTimeOfInode(&dinfo->dhead.iinfo,opt_print_time);
}

///////////////////////////////////////////////////////////////////////////////

enumError CountPartitions ( SuperFile_t * sf, WDiscInfo_t * dinfo )
{
    ASSERT(sf);
    ASSERT(dinfo);

    if ( dinfo->pinfo )
	return ERR_OK;

    enumError err = ReadSF(sf,WII_PART_INFO_OFF,dinfo->pcount,sizeof(dinfo->pcount));
    if (err)
	return err;

    int i, np = 0, nt = 0;
    WDPartCount_t *pc;
    for ( i = 0, pc = dinfo->pcount; i < WII_MAX_PART_INFO; i++, pc++ )
    {
	pc->off4   = ntohl(pc->off4);
	pc->n_part = ntohl(pc->n_part);
	if ( pc->n_part > WII_MAX_PART_TABLE )
	    pc->n_part = WII_MAX_PART_TABLE;
	np += pc->n_part;
	if ( pc->n_part > 0 )
	    nt++;
    }

    dinfo->n_ptab = nt;
    dinfo->n_part = np;
    return ERR_OK;
}

///////////////////////////////////////////////////////////////////////////////

enumError LoadPartitionInfo
	( SuperFile_t * sf, WDiscInfo_t * dinfo, MemMap_t * mm )
{
    ASSERT(sf);
    ASSERT(dinfo);

    if ( dinfo->pinfo )
	return ERR_OK;

    dinfo->iso_size = sf->file_size;
    MemMapItem_t * mi;
    if (mm)
    {
	mi = InsertMemMap(mm,sf->file_size,0);
	StringCopyS(mi->info,sizeof(mi->info),"-- end of ISO file --");
    }

    enumError err = ReadSF(sf,WII_REGION_OFF,&dinfo->regionset,sizeof(dinfo->regionset));
    if (err)
	return err;
    dinfo->regionset.region = ntohl(dinfo->regionset.region);
    if (mm)
    {
	mi = InsertMemMap(mm,WII_REGION_OFF,sizeof(dinfo->regionset));
	StringCopyS(mi->info,sizeof(mi->info),"Region settings");
    }

    err = ReadSF(sf,WII_PART_INFO_OFF,dinfo->pcount,sizeof(dinfo->pcount));
    if (err)
	return err;
    if (mm)
    {
	mi = InsertMemMap(mm,WII_PART_INFO_OFF,sizeof(dinfo->pcount));
	StringCopyS(mi->info,sizeof(mi->info),"Partition table header");
    }

    err = CountPartitions(sf,dinfo);
    if (err)
	return err;

    dinfo->pinfo = calloc(dinfo->n_part,sizeof(*dinfo->pinfo));
    if (!dinfo->pinfo)
	OUT_OF_MEMORY;
    WDPartInfo_t *pi = dinfo->pinfo;

    WDPartTableEntry_t wdpte[WII_MAX_PART_TABLE];

    int i;
    WDPartCount_t *pc;
    for ( i = 0, pc = dinfo->pcount; i < WII_MAX_PART_INFO; i++, pc++ )
    {
	u32 npt = pc->n_part;
	ASSERT( npt <= WII_MAX_PART_TABLE );
	if ( npt > 0 )
	{
	    err = ReadSF(sf, (off_t)pc->off4<<2, wdpte, sizeof(*wdpte)*npt);
	    if (err)
		return err;
	    if (mm)
	    {
		mi = InsertMemMap(mm,(off_t)pc->off4<<2,sizeof(*wdpte)*npt);
		snprintf(mi->info,sizeof(mi->info),
			"Partition table #%d with %d partiton%s",
				i, npt, npt==1 ? "" : "s" );
	    }

	    int j;
	    WDPartTableEntry_t * wdpt = wdpte;
	    for ( j = 0; j < npt; j++, wdpt++ )
	    {
		pi->ptable = i;
		pi->index  = j;
		pi->ptype  = ntohl(wdpt->ptype);
		pi->off    = (off_t)ntohl(wdpt->off4)<<2;

		if (mm)
		{
		    mi = InsertMemMap(mm,pi->off,sizeof(pi->ph));
		    snprintf(mi->info,sizeof(mi->info),
			"P.%d.%d: header",i,j);
		}

		if ( pi->off + sizeof(pi->ph) <= dinfo->iso_size )
		{
		    err = ReadSF(sf, pi->off, &pi->ph, sizeof(pi->ph));
		    if (err)
			return err;

		    pi->ph.tmd_off4  = ntohl(pi->ph.tmd_off4);
		    pi->ph.tmd_size  = ntohl(pi->ph.tmd_size);
		    pi->ph.cert_size = ntohl(pi->ph.cert_size);
		    pi->ph.cert_off4 = ntohl(pi->ph.cert_off4);
		    pi->ph.h3_off4   = ntohl(pi->ph.h3_off4);
		    pi->ph.data_off4 = ntohl(pi->ph.data_off4);
		    pi->ph.data_size = ntohl(pi->ph.data_size);

		    pi->size = (off_t)pi->ph.data_off4 + pi->ph.data_size << 2;
		    off_t temp;
		    temp = ((off_t)pi->ph.tmd_off4 << 2) + pi->ph.tmd_size;
		    if ( pi->size < temp )
			pi->size = temp;
		    temp = ((off_t)pi->ph.cert_off4 << 2) + pi->ph.cert_size;
		    if ( pi->size < temp )
			pi->size = temp;
		    temp = ((off_t)pi->ph.h3_off4 << 2) + WII_H3_SIZE;
		    if ( pi->size < temp )
			pi->size = temp;

	//	    if ( pi->off + pi->size > dinfo->iso_size )
	//		pi->size = 0;

		    decrypt_title_key(pi->ph.ticket,pi->part_key);

		    if (mm)
		    {
			mi = InsertMemMap(mm,
				pi->off + ((off_t)pi->ph.tmd_off4<<2),
				pi->ph.tmd_size );
			snprintf(mi->info,sizeof(mi->info),
				"P.%d.%d: tmd",i,j);

			mi = InsertMemMap(mm,
				pi->off + ((off_t)pi->ph.cert_off4<<2),
				pi->ph.cert_size );
			snprintf(mi->info,sizeof(mi->info),
				"P.%d.%d: cert",i,j);

			mi = InsertMemMap(mm,
				pi->off + ((off_t)pi->ph.h3_off4<<2),
				WII_H3_SIZE );
			snprintf(mi->info,sizeof(mi->info),
				"P.%d.%d: h3",i,j);

			mi = InsertMemMap(mm,
				pi->off + ((off_t)pi->ph.data_off4<<2),
				(off_t)pi->ph.data_size<<2 );
			snprintf(mi->info,sizeof(mi->info),
				"P.%d.%d: data",i,j);
		    }
		}
		pi++;
	    }
	}
    }
    ASSERT( pi - dinfo->pinfo == dinfo->n_part );

    return ERR_OK;
}

///////////////////////////////////////////////////////////////////////////////

static void DumpTimestamp ( FILE * f, int indent, ccp head, u64 xtime )
{
    time_t tim = wbfs_ntoh64(xtime);
    if (tim)
    {
	struct tm * tm = localtime(&tim);
	char timbuf[40];
	strftime(timbuf,sizeof(timbuf),"%F %T",tm);
	fprintf(f,"%*s%-12s%s\n", indent, "", head, timbuf );
    }

}

//-----------------------------------------------------------------------------

enumError DumpWDiscInfo
	( WDiscInfo_t * di, WDiscHeader_t * ih, FILE * f, int indent )
{
    if ( !di || !f )
	return ERROR0(ERR_INTERNAL,0);

    if ( indent < 0 )
	indent = 0;
    else if ( indent > 100 )
	indent = 100;

    fprintf(f,"%*swbfs name:  %6s, %.64s\n",
		indent, "", (ccp)&di->dhead.wii_disc_id, (ccp)di->dhead.game_title );
    if (ih)
	fprintf(f,"%*siso name:   %6s, %.64s\n",
		indent, "", (ccp)&ih->wii_disc_id, (ccp)ih->game_title );
    if ( ih && strcmp((ccp)&di->dhead.wii_disc_id,(ccp)&ih->wii_disc_id) )
    {
	if (di->title)
	    fprintf(f,"%*swbfs title: %s\n", indent, "", (ccp)di->title );
	ccp title = GetTitle((ccp)&ih->wii_disc_id,0);
	if (title)
	    fprintf(f,"%*siso title:  %s\n", indent, "", (ccp)di->title );
    }
    else if (di->title)
	fprintf(f,"%*stitle:      %s\n", indent, "", (ccp)di->title );
    fprintf(f,"%*sregion:     %s [%s]\n", indent, "", di->region, di->region4 );
    fprintf(f,"%*ssize:       %lld MiB\n", indent, "", ( di->size + MiB/2 ) / MiB );

    DumpTimestamp(f,indent,"i-time:",di->dhead.iinfo.itime);
    DumpTimestamp(f,indent,"m-time:",di->dhead.iinfo.mtime);
    DumpTimestamp(f,indent,"c-time:",di->dhead.iinfo.ctime);
    DumpTimestamp(f,indent,"a-time:",di->dhead.iinfo.atime);

    u32 load_count = ntohl(di->dhead.iinfo.load_count);
    if (load_count)
	fprintf(f,"%*sload count: %u\n", indent, "", load_count );

    return ERR_OK;
}

///////////////////////////////////////////////////////////////////////////////

WDiscList_t * GenerateWDiscList ( WBFS_t * w, int part_index )
{
    ASSERT(w);
    if ( !w || !w->wbfs )
    {
	ERROR0(ERR_INTERNAL,0);
	return 0;
    }

    WDiscList_t * wlist = malloc(sizeof(WDiscList_t));
    if (!wlist)
	OUT_OF_MEMORY;
    wlist->first_disc = calloc(w->used_discs,sizeof(WDiscListItem_t));
    if (!wlist->first_disc)
	OUT_OF_MEMORY;
    wlist->total_size_mib = 0;

    WDiscInfo_t dinfo;
    WDiscListItem_t * item = wlist->first_disc;

    int slot;
    for ( slot = 0; slot < w->total_discs; slot++ )
    {
	if ( GetWDiscInfoBySlot(w,&dinfo,slot) == ERR_OK )
	{
	    memcpy(item->id6,&dinfo.dhead.wii_disc_id,6);
	    if (!IsExcluded(item->id6))
	    {
		CopyWDiscInfo(item,&dinfo);
		item->part_index = part_index;
		wlist->total_size_mib += item->size_mib;
		item++;
	    }
	}
    }

    wlist->used = item - wlist->first_disc;
    return wlist;
}

///////////////////////////////////////////////////////////////////////////////

void InitializeWDiscList ( WDiscList_t * wlist )
{
    ASSERT(wlist);
    memset(wlist,0,sizeof(*wlist));
}

///////////////////////////////////////////////////////////////////////////////

void ResetWDiscList ( WDiscList_t * wlist )
{
    ASSERT(wlist);

    if ( wlist->first_disc )
    {
	WDiscListItem_t * ptr = wlist->first_disc;
	WDiscListItem_t * end = ptr + wlist->used;
	for ( ; ptr < end; ptr++ )
	    free((char*)ptr->fname);
	free(wlist->first_disc);
    }
    InitializeWDiscList(wlist);
}

///////////////////////////////////////////////////////////////////////////////

WDiscListItem_t * AppendWDiscList ( WDiscList_t * wlist, WDiscInfo_t * dinfo )
{
    ASSERT(wlist);
    ASSERT( wlist->used <= wlist->size );
    if ( wlist->used == wlist->size )
    {
	wlist->size += 200;
	wlist->first_disc = realloc(wlist->first_disc,
				wlist->size*sizeof(*wlist->first_disc));
	if (!wlist->first_disc)
	    OUT_OF_MEMORY;
    }
    wlist->sort_mode = SORT_NONE;
    WDiscListItem_t * item = wlist->first_disc + wlist->used++;
    CopyWDiscInfo(item,dinfo);
    return item;
}

///////////////////////////////////////////////////////////////////////////////

void FreeWDiscList ( WDiscList_t * wlist )
{
    ASSERT(wlist);
    ResetWDiscList(wlist);
    free(wlist);
}

///////////////////////////////////////////////////////////////////////////////

ccp RegionTable[] =
{
	// -> http://www.wiibrew.org/wiki/Title_Database#Region_Codes

	/*A*/ "ALL ", "All",
	/*B*/ "-?- ", "-?-",
	/*C*/ "-?- ", "-?-",
	/*D*/ "GERM", "German",
	/*E*/ "NTSC", "NTSC",
	/*F*/ "FREN", "French",
	/*G*/ "-?- ", "-?-",
	/*H*/ "-?- ", "-?-",
	/*I*/ "ITAL", "Italian",
	/*J*/ "JAPA", "Japan",
	/*K*/ "KORE", "Korea",
	/*L*/ "J>PL", "Japan->PAL",
	/*M*/ "A>PL", "America->PAL",
	/*N*/ "J>US", "Japan->NTSC",
	/*O*/ "-?- ", "-?-",
	/*P*/ "PAL ", "PAL",
	/*Q*/ "KO/J", "Korea (japanese)",
	/*R*/ "-?- ", "-?-",
	/*S*/ "SPAN", "Spanish",
	/*T*/ "KO/E", "Korea (english)",
	/*U*/ "-?- ", "-?-",
	/*V*/ "-?- ", "-?-",
	/*W*/ "-?- ", "-?-",
	/*X*/ "RF  ", "Region free",
	/*Y*/ "-?- ", "-?-",
	/*Z*/ "-?- ", "-?-",

	/*?*/ "-?- ", "-?-" // illegal region_code
};

//-----------------------------------------------------------------------------

ccp * GetRegionInfo ( char region_code )
{
    region_code = toupper(region_code);
    if ( region_code < 'A' || region_code > 'Z' )
	region_code = 'Z' + 1;
    return RegionTable + 2 * (region_code-'A');
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////                      sorting                    ///////////////
///////////////////////////////////////////////////////////////////////////////

typedef int (*compare_func) (const void *, const void *);

//-----------------------------------------------------------------------------

static int sort_by_title ( const void * va, const void * vb )
{
    const WDiscListItem_t * a = (const WDiscListItem_t *)va;
    const WDiscListItem_t * b = (const WDiscListItem_t *)vb;

    int stat = strcasecmp( a->title ? a->title : a->name64,
			   b->title ? b->title : b->name64 );
    if (!stat)
    {
	stat = strcasecmp(a->name64,b->name64);
	if (!stat)
	{
	    stat = strcmp(a->id6,b->id6);
	    if (!stat)
	    {
		stat = strcmp(	a->fname ? a->fname : "" ,
				b->fname ? b->fname : "" );
		if (!stat)
		    stat = a->part_index - b->part_index;
	    }
	}
    }
    return stat;
}

//-----------------------------------------------------------------------------

static int sort_by_id ( const void * va, const void * vb )
{
    const WDiscListItem_t * a = (const WDiscListItem_t *)va;
    const WDiscListItem_t * b = (const WDiscListItem_t *)vb;

    const int stat = strcmp(a->id6,b->id6);
    return stat ? stat : sort_by_title(va,vb);
}

//-----------------------------------------------------------------------------

static int sort_by_name ( const void * va, const void * vb )
{
    const WDiscListItem_t * a = (const WDiscListItem_t *)va;
    const WDiscListItem_t * b = (const WDiscListItem_t *)vb;

    const int stat = strcasecmp(a->name64,b->name64);
    return stat ? stat : sort_by_title(va,vb);
}

//-----------------------------------------------------------------------------

static int sort_by_file ( const void * va, const void * vb )
{
    const WDiscListItem_t * a = (const WDiscListItem_t *)va;
    const WDiscListItem_t * b = (const WDiscListItem_t *)vb;

    const int stat = strcmp( a->fname ? a->fname : "" ,
			     b->fname ? b->fname : "" );
    return stat ? stat : sort_by_title(va,vb);
}

//-----------------------------------------------------------------------------

static int sort_by_size ( const void * va, const void * vb )
{
    const WDiscListItem_t * a = (const WDiscListItem_t *)va;
    const WDiscListItem_t * b = (const WDiscListItem_t *)vb;

    const int stat = a->size_mib - b->size_mib;
    return stat ? stat : sort_by_title(va,vb);
}

//-----------------------------------------------------------------------------

static int sort_by_date ( const void * va, const void * vb )
{
    const WDiscListItem_t * a = (const WDiscListItem_t *)va;
    const WDiscListItem_t * b = (const WDiscListItem_t *)vb;

    const int stat = a->xtime < b->xtime ? -1 : a->xtime > b->xtime;
    return stat ? stat : sort_by_title(va,vb);
}

//-----------------------------------------------------------------------------

static int sort_by_region ( const void * va, const void * vb )
{
    const WDiscListItem_t * a = (const WDiscListItem_t *)va;
    const WDiscListItem_t * b = (const WDiscListItem_t *)vb;

    const int stat = strcmp(a->region4,b->region4);
    return stat ? stat : sort_by_id(va,vb);
}

//-----------------------------------------------------------------------------

static int sort_by_wbfs ( const void * va, const void * vb )
{
    const WDiscListItem_t * a = (const WDiscListItem_t *)va;
    const WDiscListItem_t * b = (const WDiscListItem_t *)vb;

    const int stat = a->part_index - b->part_index;
    return stat ? stat : sort_by_title(va,vb);
}

//-----------------------------------------------------------------------------

static int sort_by_npart ( const void * va, const void * vb )
{
    const WDiscListItem_t * a = (const WDiscListItem_t *)va;
    const WDiscListItem_t * b = (const WDiscListItem_t *)vb;

    const int stat = a->n_part - b->n_part;
    return stat ? stat : sort_by_title(va,vb);
}

///////////////////////////////////////////////////////////////////////////////

void ReverseWDiscList ( WDiscList_t * wlist )
{
    if (! wlist || wlist->used < 2 )
	return;

    ASSERT(wlist->first_disc);

    WDiscListItem_t *a, *b, temp;
    for ( a = wlist->first_disc, b = a + wlist->used-1; a < b; a++, b-- )
    {
	memcpy( &temp, a,     sizeof(WDiscListItem_t) );
	memcpy( a,     b,     sizeof(WDiscListItem_t) );
	memcpy( b,     &temp, sizeof(WDiscListItem_t) );
    }
}

///////////////////////////////////////////////////////////////////////////////

void SortWDiscList ( WDiscList_t * wlist,
	SortMode sort_mode, SortMode default_sort_mode, int unique )
{
    if (!wlist)
	return;

    TRACE("SortWDiscList(%p, s=%d,%d, u=%d) prev=%d\n",
		wlist, sort_mode, default_sort_mode, unique, wlist->sort_mode );

    if ( (uint)(sort_mode&SORT__MODE_MASK) >= SORT_DEFAULT )
    {
	sort_mode = (uint)default_sort_mode >= SORT_DEFAULT
			? wlist->sort_mode
			: default_sort_mode | sort_mode & SORT_REVERSE;
    }

    if ( wlist->used < 2 )
    {
	wlist->sort_mode = sort_mode;
	return;
    }

    compare_func func = 0;
    SortMode umode = SORT_ID;
    switch( sort_mode & SORT__MODE_MASK )
    {
	case SORT_ID:		func = sort_by_id; break;
	case SORT_NAME:		func = sort_by_name;	umode = SORT_NAME; break;
	case SORT_TITLE:	func = sort_by_title;	umode = SORT_TITLE; break;
	case SORT_FILE:		func = sort_by_file; break;
	case SORT_SIZE:		func = sort_by_size;	umode = SORT_SIZE; break;
	case SORT_DATE:		func = sort_by_date; break;
	case SORT_REGION:	func = sort_by_region;	umode = SORT_REGION; break;
	case SORT_WBFS:		func = sort_by_wbfs; break;
	case SORT_NPART:	func = sort_by_npart; break;
	default:		break;
    }

    if (unique)
    {
	SortWDiscList(wlist,umode,umode,false);

	WDiscListItem_t *src, *dest, *end, *prev = 0;
	src = dest = wlist->first_disc;
	end = src + wlist->used;
	wlist->total_size_mib = 0;
	for ( ; src < end; src++ )
	{
	    if ( !prev
		|| memcmp(src->id6,prev->id6,6)
		|| unique < 2 &&
		    (  memcmp(src->name64,prev->name64,64)
		    || memcmp(src->region4,prev->region4,4)
		    || src->size_mib != prev->size_mib ))
	    {
		if ( dest != src )
		    memcpy(dest,src,sizeof(*dest));
		wlist->total_size_mib += dest->size_mib;
		prev = dest++;
	    }
	    else
		free((char*)src->fname);
	}
	wlist->used = dest - wlist->first_disc;
    }

    if ( func && wlist->sort_mode != sort_mode )
    {
	wlist->sort_mode = sort_mode;
	qsort(wlist->first_disc,wlist->used,sizeof(*wlist->first_disc),func);
	if ( sort_mode & SORT_REVERSE )
	    ReverseWDiscList(wlist);
    }
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////                 access to WBFS dics             ///////////////
///////////////////////////////////////////////////////////////////////////////

enumError OpenWDiscID6 ( WBFS_t * w, ccp id6 )
{
    ASSERT(w);
    CloseWDisc(w);

    if ( !w || !w->wbfs || !id6 || strlen(id6) != 6 )
	return ERROR0(ERR_INTERNAL,0);

    w->disc = wbfs_open_disc_by_id6(w->wbfs,(u8*)id6);
    return w->disc ? ERR_OK : ERR_WDISC_NOT_FOUND;
}

///////////////////////////////////////////////////////////////////////////////

enumError OpenWDiscIndex ( WBFS_t * wbfs, u32 index )
{
    ASSERT(wbfs);

    if ( !wbfs || !wbfs->wbfs )
	return ERROR0(ERR_INTERNAL,0);

    wbfs_t *w = wbfs->wbfs;

    u32 slot;
    for ( slot = 0; slot < w->max_disc; slot++ )
	if ( w->head->disc_table[slot] && !index-- )
	    return OpenWDiscSlot(wbfs,slot);

    CloseWDisc(wbfs);
    return ERR_WDISC_NOT_FOUND;
}

///////////////////////////////////////////////////////////////////////////////

enumError OpenWDiscSlot ( WBFS_t * w, u32 slot )
{
    ASSERT(w);
    CloseWDisc(w);

    if ( !w || !w->wbfs )
	return ERROR0(ERR_INTERNAL,0);

    w->disc = wbfs_open_disc_by_slot(w->wbfs,slot);
    return w->disc ? ERR_OK : ERR_WDISC_NOT_FOUND;
}

///////////////////////////////////////////////////////////////////////////////

enumError CloseWDisc ( WBFS_t * w )
{
    ASSERT(w);
    if (w->disc)
    {
	wbfs_close_disc(w->disc);
	w->disc = 0;
    }
    return ERR_OK;
}

///////////////////////////////////////////////////////////////////////////////

enumError ExistsWDisc ( WBFS_t * w, ccp id6 )
{
    ASSERT(w);

    if ( !w || !w->wbfs || !id6 || strlen(id6) != 6 )
	return ERROR0(ERR_INTERNAL,0);

    return wbfs_find_slot(w->wbfs,(u8*)id6) < 0
		? ERR_WDISC_NOT_FOUND
		: ERR_OK;
}

///////////////////////////////////////////////////////////////////////////////

WDiscHeader_t * GetWDiscHeader ( WBFS_t * w )
{
    return w && w->disc && w->disc->header
		?  (WDiscHeader_t*)w->disc->header
		: 0;
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////                      AddWDisc()                 ///////////////
///////////////////////////////////////////////////////////////////////////////

enumError AddWDisc ( WBFS_t * w, SuperFile_t * sf, partition_selector_t psel )
{
    if ( !w || !w->wbfs || !w->sf || !sf )
	return ERROR0(ERR_INTERNAL,0);

    TRACE("AddWDisc(w=%p,sf=%p,psel=%d) progress=%d,%d\n",
		w, sf, psel, sf->show_progress, sf->show_summary );

    // this is needed for detailed error messages
    const enumError saved_max_error = max_error;
    max_error = 0;

    wbfs_param_t par;
    memset(&par,0,sizeof(par));
    par.read_src_wii_disc	= WrapperReadSF;
    par.callback_data		= sf;
    par.spinner			= sf->show_progress ? PrintProgressSF : 0;
    par.sel			= psel;
    par.copy_1_1		= psel == WHOLE_DISC;
    par.iinfo.mtime		= wbfs_hton64(sf->f.st.st_mtime);

    enumError err = ERR_OK;
    if (wbfs_add_disc_param(w->wbfs,&par))
    {
	err = ERR_WBFS;
	if (!w->sf->f.disable_errors)
	    ERROR0(err,"Error while adding disc [%s]: %s\n",
		    sf->f.id6, w->sf->f.fname );
    }

    // catch read/write errors
    err = max_error = max_error > err ? max_error : err;
    if ( max_error < saved_max_error )
	max_error = saved_max_error;

    PrintSummarySF(sf);

    // calculate the wbfs usage again
    CalcWBFSUsage(w);

    TRACE("AddWDisc() returns err=%d [%s]\n",err,GetErrorName(err));
    return err;
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////                    ExtractWDisc()               ///////////////
///////////////////////////////////////////////////////////////////////////////

enumError ExtractWDisc ( WBFS_t * w, SuperFile_t * sf )
{
    TRACE("ExtractWDisc(%p,%p)\n",w,sf);
    if ( !w || !w->wbfs | !w->sf || !w->disc || !sf )
	return ERROR0(ERR_INTERNAL,0);

    if (sf->wbfs)
    {
	// change roles
	sf->wbfs->sf = sf;
	w->sf->wbfs = w;
	return AddWDisc(sf->wbfs,w->sf,ALL_PARTITIONS);
    }

    sf->file_size = sf->enable_trunc
			? 0llu
			: (off_t)WII_SECTORS_SINGLE_LAYER *WII_SECTOR_SIZE;

    // this is needed for detailed error messages
    const enumError saved_max_error = max_error;
    max_error = 0;

    int ex_stat = 0;
    enumError err = ERR_OK;
    if ( sf->oft != OFT_PLAIN )
    {
	// write an empty disc header -> makes renaming easier
	static char disc_header[0x60] = {0};
	err = WriteWDF(sf,0,disc_header,sizeof(disc_header));

	ex_stat = wbfs_extract_disc( w->disc,
		sf->enable_fast ? WrapperWriteDirectSF : WrapperWriteSparseSF,
		sf, sf->show_progress ? PrintProgressSF : 0 );
    }
    else
    {
	ex_stat = wbfs_extract_disc( w->disc,
		    sf->enable_fast ? WrapperWriteDirectISO : WrapperWriteSparseISO,
		    sf, sf->show_progress ? PrintProgressSF : 0 );

	TRACE("EX DONE: err=%d trunc=%d", err, sf->enable_trunc );
	TRACE("  OFF: max_off=%llx - file_size=%llx = %llx\n",
		sf->f.max_off, sf->file_size, sf->f.max_off - sf->file_size );

	if ( !ex_stat && sf->f.max_off < sf->file_size )
	{
	    err = SetSizeF(&sf->f,sf->file_size);
	    TRACE("  OFF: max_off=%llx - file_size=%llx = %llx\n",
		sf->f.max_off, sf->file_size, sf->f.max_off - sf->file_size );
	    ASSERT( err || sf->f.max_off == sf->file_size );
	}
    }

    if (!err)
    {
	if ( w->sf && w->sf->f.is_writing )
	    wbfs_sync_disc_header(w->disc);

	err = max_error;
	if ( !err && ex_stat )
	{
	    err = ERR_WBFS;
	    if (!w->sf->f.disable_errors)
		ERROR0(err,"Error while extracting disc [%s]: %s\n",
			sf->f.id6, w->sf->f.fname );
	}
    }

    if ( max_error < saved_max_error )
	max_error = saved_max_error;

    PrintSummarySF(sf);

    TRACE("ExtractWDisc() returns err=%d [%s]\n",err,GetErrorName(err));
    return err;
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////                    RemoveWDisc()                ///////////////
///////////////////////////////////////////////////////////////////////////////

enumError RemoveWDisc ( WBFS_t * w, ccp id6, bool free_slot_only )
{
    TRACE("RemoveWDisc(%p,%s,%d)\n",w,id6?id6:"-",free_slot_only);
    if ( !w || !w->wbfs || !w->sf || !id6 || strlen(id6) != 6 )
	return ERROR0(ERR_INTERNAL,0);

    // this is needed for detailed error messages
    const enumError saved_max_error = max_error;
    max_error = 0;

    // remove the disc
    enumError err = ERR_OK;
    if (wbfs_rm_disc(w->wbfs,(u8*)id6,free_slot_only))
    {
	err = ERR_WDISC_NOT_FOUND;
	if (!w->sf->f.disable_errors)
	    ERROR0(err,"Can't remove disc non existing [%s]: %s\n",
		id6, w->sf->f.fname );
    }

 #ifdef DEBUG
    DumpWBFS(w,TRACE_FILE,15,0,0);
 #endif

    // check if the disc is really removed
    if (!ExistsWDisc(w,id6))
    {
	err = ERR_REMOVE_FAILED;
	if (!w->sf->f.disable_errors)
	    ERROR0(err,"Can't remove disc [%s]: %s\n",
		id6, w->sf->f.fname );
    }

    // catch read/write errors
    err = max_error = max_error > err ? max_error : err;
    if ( max_error < saved_max_error )
	max_error = saved_max_error;

    // calculate the wbfs usage again
    CalcWBFSUsage(w);

    TRACE("RemoveWDisc(%s) returns err=%d [%s]\n",id6,err,GetErrorName(err));
    return err;
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////                    RenameWDisc()                ///////////////
///////////////////////////////////////////////////////////////////////////////

enumError RenameWDisc
	( WBFS_t * wbfs, ccp set_id6, ccp set_title,
		bool change_wbfs_head, bool change_iso_head,
		int verbose, int testmode )
{
    ASSERT(wbfs);
    ASSERT(wbfs->wbfs);
    ASSERT(wbfs->disc);
    ASSERT(wbfs->disc->header);

    TRACE("RenameWDisc(%p,%.6s,%s,%d,%d,v=%d,tm=%d)\n",
		wbfs, set_id6 ? set_id6 : "-",
		set_title ? set_title : "-",
		change_wbfs_head, change_iso_head, verbose, testmode );

    if ( !wbfs || !wbfs->wbfs || !wbfs->sf )
	return ERROR0(ERR_INTERNAL,0);

    if ( !set_id6 || strlen(set_id6) < 6 )
	set_id6 = 0; // invalid id6

    if ( !set_title || !*set_title )
	set_title = 0; // invalid title

    if ( !set_id6 && !set_title )
	return ERR_OK; // nothing to do

    if ( !change_wbfs_head && !change_iso_head )
	change_wbfs_head = change_iso_head = true;

    WDiscHeader_t * whead = (WDiscHeader_t*)wbfs->disc->header;
    char w_id6[7], n_id6[7];
    memset(w_id6,0,sizeof(w_id6));
    StringCopyS(w_id6,sizeof(w_id6),(ccp)&whead->wii_disc_id);
    memcpy(n_id6,w_id6,sizeof(n_id6));

    if ( testmode || verbose >= 0 )
    {
	ccp mode = !change_wbfs_head
			? "(ISO header only)"
			: !change_iso_head
				? "(WBFS header only)"
				: "(WBFS+ISO header)";
	printf(" - %sModify %s [%s] %s\n",
		testmode ? "WOULD " : "", mode, w_id6, wbfs->sf->f.fname );
    }

    if (set_id6)
    {
	memcpy(n_id6,set_id6,6);
	set_id6 = n_id6;
	if ( testmode || verbose >= 0 )
	    printf("   - %sRename ID to `%s'\n", testmode ? "WOULD " : "", set_id6 );
    }

    if (set_title)
    {
	WDiscHeader_t ihead;
	LoadIsoHeader(wbfs,&ihead,0);

	char w_name[0x40], i_id6[7], i_name[0x40];
	StringCopyS(i_id6,sizeof(i_id6),(ccp)&ihead.wii_disc_id);
	StringCopyS(w_name,sizeof(w_name),(ccp)whead->game_title);
	StringCopyS(i_name,sizeof(i_name),(ccp)ihead.game_title);

	ccp w_title = GetTitle(w_id6,w_name);
	ccp i_title = GetTitle(i_id6,i_name);
	ccp n_title = GetTitle(n_id6,w_name);

	TRACE("W-TITLE: %s, %s\n",w_id6,w_title);
	TRACE("I-TITLE: %s, %s\n",i_id6,i_title);
	TRACE("N-TITLE: %s, %s\n",n_id6,n_title);

	// and now the destination filename
	SubstString_t subst_tab[] =
	{
	    { 'j', 0,	0, w_id6 },
	    { 'J', 0,	0, i_id6 },
	    { 'i', 'I',	0, n_id6 },

	    { 'n', 0,	0, w_name },
	    { 'N', 0,	0, i_name },

	    { 'p', 0,	0, w_title },
	    { 'P', 0,	0, i_title },
	    { 't', 'T',	0, n_title },

	    {0,0,0,0}
	};

	char title[PATH_MAX];
	SubstString(title,sizeof(title),subst_tab,set_title,0);
	set_title = title;

	if ( testmode || verbose >= 0 )
	    printf("   - %sSet title to `%s'\n",
			testmode ? "WOULD " : "", set_title );
    }

    if (!testmode
	&& wbfs_rename_disc( wbfs->disc, set_id6, set_title,
				change_wbfs_head, change_iso_head ) )
		return ERROR0(ERR_WBFS,"Renaming of disc failed: %s\n",
				wbfs->sf->f.fname );
    return ERR_OK;
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////                 RenameISOHeader()               ///////////////
///////////////////////////////////////////////////////////////////////////////

int RenameISOHeader ( void * data, ccp fname,
	ccp set_id6, ccp set_title, int verbose, int testmode )
{
    ASSERT(data);

    TRACE("RenameISOHeader(%p,,%.6s,%s,v=%d,tm=%d)\n",
		data, set_id6 ? set_id6 : "-",
		set_title ? set_title : "-", verbose, testmode );

    if ( !set_id6 || strlen(set_id6) < 6 )
	set_id6 = 0; // invalid id6

    if ( !set_title || !*set_title )
	set_title = 0; // invalid title

    if ( !set_id6 && !set_title )
	return 0; // nothing to do

    WDiscHeader_t * whead = (WDiscHeader_t*)data;
    char old_id6[7], new_id6[7];
    memset(old_id6,0,sizeof(old_id6));
    StringCopyS(old_id6,sizeof(old_id6),(ccp)&whead->wii_disc_id);
    memcpy(new_id6,old_id6,sizeof(new_id6));

    if ( testmode || verbose >= 0 )
    {
	if (!fname)
	    fname = "";
	printf(" - %sModify [%s] %s\n",
		testmode ? "WOULD " : "", old_id6, fname );
    }

    if (set_id6)
    {
	memcpy(new_id6,set_id6,6);
	set_id6 = new_id6;
	if ( testmode || verbose >= 0 )
	    printf("   - %sRename ID to `%s'\n", testmode ? "WOULD " : "", set_id6 );
    }

    if (set_title)
    {
	char old_name[0x40];
	StringCopyS(old_name,sizeof(old_name),(ccp)whead->game_title);

	ccp old_title = GetTitle(old_id6,old_name);
	ccp new_title = GetTitle(new_id6,old_name);

	// and now the destination filename
	SubstString_t subst_tab[] =
	{
	    { 'j', 'J',	0, old_id6 },
	    { 'i', 'I',	0, new_id6 },

	    { 'n', 'N',	0, old_name },

	    { 'p', 'P',	0, old_title },
	    { 't', 'T',	0, new_title },

	    {0,0,0,0}
	};

	char title[PATH_MAX];
	SubstString(title,sizeof(title),subst_tab,set_title,0);
	set_title = title;

	if ( testmode || verbose >= 0 )
	    printf("   - %sSet title to `%s'\n",
			testmode ? "WOULD " : "", set_title );
    }

    return wd_rename(data,set_id6,set_title);
}

//
///////////////////////////////////////////////////////////////////////////////
///////////////                       END                       ///////////////
///////////////////////////////////////////////////////////////////////////////

