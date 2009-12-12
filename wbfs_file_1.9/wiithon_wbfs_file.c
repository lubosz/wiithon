// Copyright 2009 Kwiirk
// Licensed under the terms of the GNU GPL, version 2
// http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt

// 10-2009 oggzee: additional commands, split file support

#ifdef WIN32
#include <windows.h>
#include <winioctl.h>
#include <io.h>
#endif

#include <stdio.h>     /* for printf */
#include <stdlib.h>    /* for exit */
#include <getopt.h>
#include <sys/stat.h>
#include <unistd.h>
#include <string.h>
#include <ctype.h>
#include <libgen.h>

//#include "tools.h"
#include "libwbfs.h"
#include "splits.h"

#include "platform.h"

char tool_version[] = "1.9";
char invalid_path[] = "/\\:|<>?*\"'";

wbfs_t *wbfs_try_open(char *disc,char *partition, int reset);
wbfs_t *wbfs_try_open_partition(char *fn,int reset);
int is_device(char *fname);
int read_wiidisc_wbfsdisc(void*fp,u32 offset,u32 count,void*iobuf);

#define GB (1024*1024*1024.)

// copy all partitions
int OPT_sub_dir = 0;
int OPT_part_all = 1;
int OPT_copy_1_1 = 0;
int OPT_overwrite = 0;
int OPT_trim = 0;
char *OPT_filename = 0; // first filename argument
char *OPT_arg3 = NULL;

split_info_t split;

static u32 _be32(const u8 *p)
{
    return (p[0] << 24) | (p[1] << 16) | (p[2] << 8) | p[3];
}

int read_wii_file(void*_fp,u32 offset,u32 count,void*iobuf)
{
    FILE*fp =_fp;
    u64 off = offset;
    off <<= 2;
    size_t ret;
    if (fseeko(fp, off, SEEK_SET))
    {
        printf("error seeking disc %u\n", offset);
        return 1;
    }
    ret = fread(iobuf, count, 1, fp);
    if (ret != 1){
        printf("end of data (%u)\n", offset);
        //printf("error reading disc %u "FMT_llu" %u = %u\n",
        //        offset, off, count, ret);
        //wbfs_error("error reading disc");
        return 1;
    }
    return 0;
}
int write_wii_sector_file(void*_fp,u32 lba,u32 count,void*iobuf)
{
    FILE*fp=_fp;
    u64 off = lba;
    off *=0x8000;
    //printf("w %u %u\n",lba,count);
    if (fseeko(fp, off, SEEK_SET))
    {
        printf("\n\n"FMT_lld" %p\n",off,_fp);
        wbfs_error("error seeking in written disc file");
        return FALSE;
    }
    if (fwrite(iobuf, count*0x8000, 1, fp) != 1){
        wbfs_error("error writing disc file");
        return FALSE;
    }
    return OK;
}


wbfs_t *wbfs_split_create_partition(split_info_t *s, char *fn,int reset)
{
    u32 sector_size = 512;
    // max dual layer:
    u64 size = (u64)143432*2*0x8000ULL + 0x4000000;
    // +0x4000000 because freeblks size is n_wbfs_sec
    // and has to be aligned to 32 (num of bits in an int)
    // using exact file size as max dual layer is not enough for the worst case:
    // doing a 1:1 copy of a dual layer disc, because we need some space for the
    // headers. And the dual layer size is not wbfs sector aligned anyway.
    // So the minimum amount that has to be added is 32 wbfs sectors,
    // which is 32*2MB = 64MB = 0x4000000
    u32 n_sector = size / 512;
    int ret;
    //printf("OPEN_PART %s\n", fn);
    ret = split_create(s, fn, OPT_split_size, size);
    if (ret) return NULL;
    return wbfs_open_partition(
            split_read_sector, split_write_sector, s,
            sector_size, n_sector,0,reset);
}

wbfs_t *wbfs_split_open_partition(split_info_t *s, char *fn,int reset)
{
    u32 sector_size = 512;
    u32 n_sector;
    int ret;
    //printf("OPEN_PART %s\n", fn);
    ret = split_open(s, fn);
    n_sector = s->total_sec;
    if (ret) return NULL;
    return wbfs_open_partition(
            split_read_sector, split_write_sector, s,
            sector_size, n_sector,0,reset);
}

wbfs_t *wbfs_auto_open_partition(char *fn,int reset)
{
    if (is_device(fn)) {
        return wbfs_try_open_partition(fn, reset);
    } else {
        return wbfs_split_open_partition(&split, fn, reset);
    }
}

int get_first_disc_hdr(wbfs_t *p, u8 hdr[0x100])
{
    int count = wbfs_count_discs(p);
    if(count==0) {
        printf("wbfs empty\n");
        return -1;
    }
    u32 size;
    if(wbfs_get_disc_info(p,0,hdr,0x100,&size)) return -1;
    return 0;
}

int get_first_disc_id(wbfs_t *p, char *discid)
{
    u8 b[0x100];
    if (get_first_disc_hdr(p, b)) return -1;
    memcpy(discid, b, 6);
    discid[6] = 0;
    return 0;
}



int wbfs_applet_df(wbfs_t *p)
{
    u32 count = wbfs_count_usedblocks(p);
    printf("wbfs total: %.2fG used: %.2fG free: %.2fG\n",
            (float)p->n_wbfs_sec*p->wbfs_sec_sz/GB,
            (float)(p->n_wbfs_sec-count)*p->wbfs_sec_sz/GB,
            (float)(count)*p->wbfs_sec_sz/GB);
    /*printf("bytes tot:"FMT_lld" used:"FMT_lld"  free:"FMT_lld"\n",
            (u64)p->n_wbfs_sec*p->wbfs_sec_sz,
            (u64)(p->n_wbfs_sec-count)*p->wbfs_sec_sz,
            (u64)(count)*p->wbfs_sec_sz);*/
    return p ? 0 : -1;
}

int wbfs_applet_ls(wbfs_t *p)
{
    int count = wbfs_count_discs(p);
    if(count==0)
        printf("wbfs empty\n");
    else{
        int i;
        u32 size;
        u8 *b = wbfs_ioalloc(0x100);
        for (i=0;i<count;i++)
        {
            if(!wbfs_get_disc_info(p,i,b,0x100,&size))
                printf("%.6s : %-40s %.2fG\n", b, b + 0x20, size*4ULL/(GB));
                //printf("("FMT_lld")\n", (u64)size*4ULL);
        }
        wbfs_iofree(b);
    }   
    printf("\n");
    return wbfs_applet_df(p);
}

int wbfs_applet_mkhbc(wbfs_t *p)
{
    int count = wbfs_count_discs(p);
    char filename[7];
    FILE *xml;
    if(count==0)
        printf("wbfs empty\n");
    else{
        int i;
        u32 size;
        u8 *b = wbfs_ioalloc(0x100);
        for (i=0;i<count;i++)
        {
            wbfs_get_disc_info(p,i,b,0x100,&size);
            snprintf(filename,7,"%c%c%c%c%c%c",b[0], b[1], b[2], b[3], b[4], b[5]);
            mkdir(filename, 0777);
            printf("%s\n",filename);
            if (chdir(filename))
                wbfs_fatal("chdir");
            system("cp ../boot.dol .");
            system("cp ../icon.png .");
            xml = fopen("meta.xml","wb");
            fprintf(xml,"<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>\n");
            fprintf(xml,"<app>\n\t<name>%s</name>\n", b+0x20);
            fprintf(xml,"<short_description>%.2fGB on USB HD </short_description>\n",size*4ULL/(GB));
            fprintf(xml,"<long_description>This launches the yal wbfs game loader by Kwiirk for discid %s</long_description>\n",filename);
            fprintf(xml,"</app>");
            fclose(xml);
            if (chdir(".."))
                wbfs_fatal("chdir");
        }
        wbfs_iofree(b);

    }   
    return p ? 0 : -1;
}
int wbfs_applet_init(wbfs_t *p)
{
    // nothing to do actually..
    // job already done by the reset flag of the wbfs_open_partition
    return p!=0;

}

static void _spinner(int x,int y){ spinner(x,y);}

int wbfs_applet_addiso_gethdr(wbfs_t *p,char*argv, u8 *hdr)
{
    //printf("ADD\n");
    FILE *f = fopen(argv,"rb");
    u8 discinfo[0x100];
    u8 discid[8];
    wbfs_disc_t *d;
    if(!f)
        wbfs_error("unable to open disc file");
    else
    {
        fread(discinfo, sizeof(discinfo), 1,f);
        if (hdr) memcpy(hdr, discinfo, sizeof(discinfo));
        memcpy(discid, discinfo, 6);
        discid[6] = 0;
        d = wbfs_open_disc(p,discid);
        fflush(stdout);
        if(d)
        {
            discinfo[6]=0;
            printf("%s already in disc..\n",discid);
            wbfs_close_disc(d);
            return 1;
        } else {
            int part = OPT_part_all ? ALL_PARTITIONS : ONLY_GAME_PARTITION;
            return wbfs_add_disc(p,read_wii_file,f,_spinner,part, OPT_copy_1_1);
        }
    }
    return 1;
}

int wbfs_applet_add_iso(wbfs_t *p,char*argv)
{
    return wbfs_applet_addiso_gethdr(p, argv, NULL);
}

int wbfs_applet_rm(wbfs_t *p,char*argv)
{
    return wbfs_rm_disc(p,(u8*)argv);
}

int do_extract(wbfs_disc_t *d, char *destname)
{
    int ret = 1;
    if(!d) return -1;
    FILE *f = fopen(destname,"rb");
    if (f) {
        fclose(f);
        if (OPT_overwrite) {
            //printf("\nNote: file already exists: %s (overwriting)\n", destname);
        } else {
            //printf("\nError: file already exists: %s\n", destname);
            return FALSE;
        }
    }

    f = fopen(destname,"wb");
    if(!f)
        wbfs_fatal("unable to open dest file");
    else{
        //printf("writing to %s\n",destname);

        // check if the game is DVD9..
        // XXX is it needed?
        /*
           u32 comp_blk;
           u32 last_blk;
           comp_blk = wbfs_sector_used2(d->p, d->header, &last_blk);
           u64 real_size = (u64)(last_blk+1) * (u64)d->p->wbfs_sec_sz;
           u64 dual_size = (d->p->n_wii_sec_per_disc)*0x8000ULL;
           */
        u64 single_size = (d->p->n_wii_sec_per_disc/2)*0x8000ULL;
        u64 size = single_size;
        //if (real_size > single_size) size = dual_size;

        //printf("allocating file\n");
        // write a zero at the end of the iso to ensure the correct size
        //fseeko(f,size-1ULL,SEEK_SET);
        //fwrite("",1,1,f);
        if (!OPT_trim) {
            file_truncate(fileno(f), size);
        }

        ret = wbfs_extract_disc(d,write_wii_sector_file,f,_spinner);
        fclose(f);
        //printf("\n");
    }
    return ret;
}

void get_gameid_title(char *buf, u8 *hdr, int re_space)
{
    int i,len;
    /* get the name of the title to find out the name of the iso */
    strncpy(buf, (char*)hdr, 6);
    strcpy(buf+6, "_");
    strncpy(buf+7, (char*)hdr+0x20, 64);
    buf[7+64] = 0;
    len = strlen(buf);
    // replace silly chars with '_'
    for (i = 0; i < len; i++) {
        if(strchr(invalid_path, buf[i]) || iscntrl(buf[i])) {
            buf[i] = '_';
        }
        if (re_space && buf[i] == ' ') {
            buf[i] = '_';
        }
    }
}

void get_hdr_titlename(u8 *hdr, char *fname, char *path)
{
    int len;
    char *buf;
    // add path
    strcpy(fname, path);
    len = strlen(fname);
    if (len && fname[len-1] != '/' && fname[len-1] != '\\') {
        strcat(fname, "/");
    }
    len = strlen(fname);
    buf = fname + len;
    get_gameid_title(buf, hdr, 1);
}

void get_disc_titlename(wbfs_disc_t *d, char *fname, char *path)
{
    get_hdr_titlename(d->header->disc_header_copy, fname, path);
}

void get_disc_isoname(wbfs_disc_t *d, char *fname, char *path)
{
    get_disc_titlename(d, fname, path);
    strcat(fname, ".iso");
}

void mk_title_txt(char *fname_wbfs, u8 *hdr)
{
    char fname[1024];
    char path[1024];
    char dname[1024];
    char id[8], title[64+1];
    FILE *f;

    // dirname() might modify, so we need a tmp copy
    strcpy(dname, fname_wbfs);
    strcpy(path, dirname(dname));
    get_hdr_titlename(hdr, fname, path);
    strcat(fname, ".txt");

    memcpy(id, hdr, 6);
    id[6] = 0;
    memcpy(title, hdr+0x20, 64);
    title[64] = 0;
    f = fopen(fname, "wb");
    if (!f) return;
    fprintf(f, "%.6s = %.64s\n", id, title);
    fclose(f);
    //printf("Info file: %s\n", fname);
}

int wbfs_applet_extract_iso(wbfs_t *p, char*argv, char *path)
{
    int ret = 1;
    wbfs_disc_t *d = wbfs_open_disc(p,(u8*)argv);
    if(d)
    {
        char isoname[1024];
        get_disc_isoname(d, isoname, path);
        ret = do_extract(d, isoname);
        wbfs_close_disc(d);
    }
    else
        printf("%s not in disc..\n",argv);
    return ret;
}

int wbfs_applet_extractiso0(wbfs_t *p,char*argv)
{
    return wbfs_applet_extract_iso(p, argv, "");
}

int wbfs_applet_extract_wbfs(wbfs_t *p, char*arg, char *path)
{
    int ret = 1;
    wbfs_disc_t *d = wbfs_open_disc(p,(u8*)arg);
    if(!d) {
        //printf("%s not in disc..\n",arg);
        return FALSE;
    }

    u8 b[0x100];
    wbfs_disc_read(d, 0, b, 0x100);
    u32 magic = _be32(b+24);
    if(magic!=0x5D1C9EA3){
        //printf("SKIP: Not a wii disc - bad magic (%08x)\n\n", magic);
        goto err;
    }

    char destname[1024];
    if (strlen(arg)!=6) {
        //printf("invalid DISCID: '%s'\n", arg);
        goto err;
    }
    strcpy(destname, path);
    int len = strlen(path);
    if (len && path[len-1] != '/' && path[len-1] != '\\') {
        strcat(destname, "/");
    }
    if (OPT_sub_dir) {
        char *c = destname + strlen(destname);
        get_gameid_title(c, b, 0);
        mkdir(destname, 0777);
        strcat(c, "/");
    }
    strcat(destname, arg);
    strcat(destname, ".wbfs");
    
    //printf("Writing '%s' to: '%s'\n", arg, destname);
    mk_title_txt(destname, b);
    fflush(stdout);

    split_info_t dest_split;
    wbfs_t *dest_p = wbfs_split_create_partition(&dest_split, destname, 1);
    fflush(stdout);
    if (!dest_p) goto err;

    int part = OPT_part_all ? ALL_PARTITIONS : ONLY_GAME_PARTITION;
    ret = wbfs_add_disc(dest_p, read_wiidisc_wbfsdisc, d, _spinner, part, 0);
    fflush(stdout);
    
    wbfs_close_disc(d);
    wbfs_trim(dest_p);
    wbfs_close(dest_p);
    split_close(&dest_split);
    fflush(stdout);
    
    return ret;

err:
    if (d) wbfs_close_disc(d);
    return FALSE;
}

int wbfs_applet_extract_wbfs_all(wbfs_t *p, char *path)
{
    int count = wbfs_count_discs(p);
    if(count==0) {
        //printf("wbfs empty\n");
        return FALSE;
    }
    wbfs_applet_ls(p);
    //printf("\nExtracting ALL games to: '%s'\n", path);

    int i, r, ret = 0;
    u32 size;
    u8 b[0x100];
    char discid[8];
    for (i=0;i<count;i++) {
        if(!wbfs_get_disc_info(p,i,b,0x100,&size)) {
            printf("\n%d / %d : ", i+1, count);
            printf("%.6s : %-40s %.2fG\n", b, b + 0x20, size*4ULL/(GB));
            //printf("("FMT_lld")\n", (u64)size*4ULL);
            // check magic
            u32 magic = _be32(b+24);
            if (magic != 0x5D1C9EA3){
                printf("SKIP: Not a wii disc - bad magic (%08x)\n\n", magic);
                continue;
            }
            memcpy(discid, b, 6);
            discid[6] = 0;
            r = wbfs_applet_extract_wbfs(p, discid, path);
            if (r) {
                printf("\nERROR: extract (%.6s) = %d\n\n", discid, r);
                ret = -1;
            }
        }
    }
    //printf("Done.\n");
    return ret;
}

int wbfs_applet_add_wbfs(wbfs_t *p, char *fname)
{
    //printf("Adding %s to WBFS\n", fname);

    split_info_t src_split;
    wbfs_t *src_p = wbfs_split_open_partition(&src_split, fname, 0);
    fflush(stdout);
    if (!src_p) return -1;

    char discid[8];
    if (get_first_disc_id(src_p, discid)) {
        printf("error finding ID in %s\n", fname);
        wbfs_close(src_p);
        split_close(&src_split);
        return -1;
    }
    //printf("ID: %s\n", discid);

    wbfs_disc_t *d;
    // check if disc present on targer
    d = wbfs_open_disc(p, (u8*)discid);
    fflush(stdout);
    if (d)
    {
        printf("%s already in disc..\n", discid);
        wbfs_close_disc(d);
        wbfs_close(src_p);
        split_close(&src_split);
        return -1;
    }
    //printf("not present\n");

    // open disc in source
    d = wbfs_open_disc(src_p, (u8*)discid);
    if (!d)    {
        printf("Error getting %s from %s\n", discid, fname);
        wbfs_close(src_p);
        split_close(&src_split);
        return -1;
    }

    fflush(stdout);
    int part = OPT_part_all ? ALL_PARTITIONS : ONLY_GAME_PARTITION;
    int ret = wbfs_add_disc(p, read_wiidisc_wbfsdisc, d, _spinner, part, 0);
    fflush(stdout);
    
    wbfs_close_disc(d);
    wbfs_close(src_p);
    split_close(&src_split);
    fflush(stdout);

    return ret;
}

int wbfs_applet_make_info(wbfs_t *p)
{
    char *name_wbfs = OPT_filename;
    if (is_device(name_wbfs)) name_wbfs = "";
    int count = wbfs_count_discs(p);
    if(count==0)
        printf("wbfs empty\n");
    else{
        int i;
        u32 size;
        u8 *b = wbfs_ioalloc(0x100);
        for (i=0;i<count;i++)
        {
            if(!wbfs_get_disc_info(p,i,b,0x100,&size))
                printf("%.6s : %-40s %.2fG\n", b, b + 0x20, size*4ULL/(GB));
                //printf("("FMT_lld")\n", (u64)size*4ULL);
            mk_title_txt(name_wbfs, b);
        }
        wbfs_iofree(b);
    }   
    printf("\n");
    return wbfs_applet_df(p);
}

int wbfs_applet_id_title(wbfs_t *p)
{
    u8 hdr[0x100];
    if (get_first_disc_hdr(p, hdr)) {
        return -1;
    }
    char id_title[100]; // required: 6+1+64+1
    get_gameid_title(id_title, hdr, 0);
    printf("%s\n", id_title);
    return 0;
}

int wbfs_applet_extract_file(wbfs_t *p, char*argv, char *arg2)
{
    wbfs_disc_t *d;
    void *data = NULL;
    int size = 0;
    d = wbfs_open_disc(p,(u8*)argv);
    if(!d)
    {
        printf("Disc not found: %s\n", argv);
        return -1;
    }
    size = wbfs_extract_file(d, arg2, &data);
    wbfs_close_disc(d);
    if (!data || size <= 0) {
        printf("File: %s not found in disc %s\n",arg2, argv);
        return -1;
    }
    FILE *f;
    char *outfile = OPT_arg3;
    if (!outfile) outfile = arg2;
    if (!*outfile) outfile = "fst.dat";
    f = fopen(outfile, "wb");
    if (!f) {
        perror("fopen");
        return -1; 
    }
    if (fwrite(data, size, 1, f) != 1) {
        perror("write");
        return -1; 
    }
    fclose(f);
    printf("extracted: (%.6s) '%s' -> '%s'\n", argv, arg2, outfile);
    return 0;
}

typedef struct {
    u8 filetype;
    char name_offset[3];
    u32 fileoffset;
    u32 filelen;
} __attribute__((packed)) FST_ENTRY;


char *fstfilename2(FST_ENTRY *fst, u32 index)
{
    u32 count = _be32((u8*)&fst[0].filelen);
    u32 stringoffset;
    if (index < count)
    {
        //stringoffset = *(u32 *)&(fst[index]) % (256*256*256);
        stringoffset = _be32((u8*)&(fst[index])) % (256*256*256);
        return (char *)((u32)fst + count*12 + stringoffset);
    } else
    {
        return NULL;
    }
}

void fst_list(void *afst)
{
    //FST_ENTRY *fst = (FST_ENTRY *)*(u32 *)0x80000038;
    FST_ENTRY *fst = (FST_ENTRY *)afst;
    u32 count = _be32((u8*)&fst[0].filelen);
    u32 i;
    printf("fst files: %d\n", count);
    for (i=1;i<count;i++) {        
        //printf("%d %p %p\n", i, fst, fstfilename2(fst, i));
        printf("%d %s\n", i, fstfilename2(fst, i));
        fflush(stdout);
    }
}


int wbfs_applet_ls_file(wbfs_t *p,char*argv)
{
    wbfs_disc_t *d;
    int size = 0;
    void *fst;
    d = wbfs_open_disc(p,(u8*)argv);
    if (!d) {
        printf("%s not in disc..\n",argv);
        return -1;
    }
    size = wbfs_extract_file(d, "", &fst);
    wbfs_close_disc(d);
    if (!fst || size <= 0) {
        printf("%s not in disc..\n", argv);
        return -1;
    }
    printf("fst found: %d\n", size);
    fst_list(fst);
    free(fst);
    return 0;
}

int wbfs_applet_create(char *dest_name, char*argv)
{
    u8 hdr[0x100];
    wbfs_t *p = wbfs_split_create_partition(&split, dest_name, 1);
    int ret = -1;
    if (!p) return -1;
    memset(hdr, 0, sizeof(hdr));
    ret = wbfs_applet_addiso_gethdr(p,argv, hdr);
    if (ret == 0 && hdr[0] != 0) {
        // success
        mk_title_txt(dest_name, hdr);
    }
    wbfs_trim(p);
    wbfs_close(p);
    split_close(&split);
    return ret;
}

/*
int wbfs_applet_create0(char *dest_name, char*argv)
{
    //char buf[1024];
    //strncpy(buf,argv,1019);
    //strcpy(buf+strlen(buf),".wbfs");
    FILE *f=fopen(dest_name,"wb");
    if(!f)
        wbfs_fatal("unable to open dest file");
    else{
        // reserve space for the maximum size.
        fseeko(f,143432*2*0x8000ULL-1ULL,SEEK_SET);
        fwrite("",1,1,f);
        fclose(f);
        wbfs_t *p = wbfs_try_open_partition(dest_name,1);
        if(p){
            wbfs_applet_add(p,argv);
            wbfs_trim(p);
            ftruncate(fileno((FILE*)p->callback_data),p->n_hd_sec*512ULL);
            wbfs_close(p);
        }
    }
    return 0;
}
*/

int conv_to_wbfs(char *filename, char *dest_dir)
{
    //printf("Converting %s to WBFS\n", filename);
    char newname[1024], *c;
    u8 hdr[0x100];
    char discid[8];

    FILE *f = fopen(filename,"rb");
    if(!f) {
        //printf("unable to open iso file '%s'", filename);
        return FALSE;
    }
    //fread(discid,6,1,f);
    fread(hdr, sizeof(hdr), 1,f);
    fclose(f);
    strncpy(discid, (char*)hdr, 6);
    discid[6] = 0;
    if (*dest_dir == 0) {
        // empty dest_dir, use same dir as source
        strcpy(newname, filename);
        c = strrchr(newname, '/');
        if (!c) c = strrchr(newname, '\\');
        if (c) c++; else c = newname;
        *c = 0;
    } else {
        strcpy(newname, dest_dir);
        strcat(newname, "/");
    }
    c = newname + strlen(newname);
    if (OPT_sub_dir) {
        // get_gameid_title
        get_gameid_title(c, hdr, 0);
        mkdir(newname, 0777);
        strcat(c, "/");
        c += strlen(c);
    }
    sprintf(c, "%.6s.wbfs", discid);
    printf("Writing: %s\n", newname);
    wbfs_applet_create(newname, filename);
    return OK;
}

int conv_to_iso(char *filename, char *dest_dir)
{
    char discid[8];

    //printf("Converting %s to ISO\n", filename);

    wbfs_t *p = wbfs_auto_open_partition(filename, 0);
    if(!p) {
        //printf("error opening %s\n", filename);
        return FALSE;
    }
    if (get_first_disc_id(p, discid))
    {
        //printf("error finding ID in %s\n", filename);
        return FALSE;
    }
    char path[1024], *c;
    if (*dest_dir == 0) {
        strcpy(path, filename);
        c = strrchr(path, '/');
        if (!c) c = strrchr(path, '\\');
        if (c) c++; else c = path;
        *c = 0;
        dest_dir = path;
    }
    wbfs_applet_extract_iso(p, discid, dest_dir);
    return OK;
}

int convert(char *filename, char *dest_dir)
{
    // only filename specified
    char *dot;
    dot = strrchr(filename, '.');
    if (!dot) return -2;
    if (strcasecmp(dot, ".iso") == 0) {
        if (conv_to_wbfs(filename, dest_dir)) return -1;
    } else if (strcasecmp(dot, ".wbfs") == 0) {
        if (conv_to_iso(filename, dest_dir)) return -1;
    } else {
        return -2;
    }
    return 0;
}

int wbfs_applet_debug_info(wbfs_t *p)
{
#define PRINT_X(X) printf("%-20s: %-7d 0x%x\n", #X, (u32)p->X, (u32)p->X)
    //wbfs_head_t *head;
    //PRINT_X(head->magic);
    // parameters copied in the partition for easy dumping, and bug reports
    PRINT_X(head->n_hd_sec);           // total number of hd_sec in this partition
    PRINT_X(head->hd_sec_sz_s);       // sector size in this partition
    PRINT_X(head->wbfs_sec_sz_s);     // size of a wbfs sec

    /* hdsectors, the size of the sector provided by the hosting hard drive */
    PRINT_X(hd_sec_sz);
    PRINT_X(hd_sec_sz_s); // the power of two of the last number
    PRINT_X(n_hd_sec);     // the number of hd sector in the wbfs partition

    /* standard wii sector (0x8000 bytes) */
    PRINT_X(wii_sec_sz); 
    PRINT_X(wii_sec_sz_s);
    PRINT_X(n_wii_sec);
    PRINT_X(n_wii_sec_per_disc);

    /* The size of a wbfs sector */
    PRINT_X(wbfs_sec_sz);
    PRINT_X(wbfs_sec_sz_s); 
    PRINT_X(n_wbfs_sec);   // this must fit in 16 bit!
    PRINT_X(n_wbfs_sec_per_disc);   // size of the lookup table

    PRINT_X(part_lba);
    PRINT_X(max_disc);
    PRINT_X(freeblks_lba);
    //u32 *freeblks;
    PRINT_X(disc_info_sz);

    PRINT_X(n_disc_open);
    return 0;
}


struct wbfs_applets{
    char *opt;
    int (*func)(wbfs_t *p);
    int (*func_arg)(wbfs_t *p, char *argv);
    int (*func_arg2)(wbfs_t *p, char *arg1, char *arg2);
    char *arg_name;
    int dest; // is first arg a src or dest
} wbfs_applets[] = {
#define APPLET_0(d,x)   { #x,wbfs_applet_##x,NULL,NULL, "", d}
#define APPLET_1(d,x,A) { #x,NULL,wbfs_applet_##x,NULL, A, d}
#define APPLET_2(d,x,A) { #x,NULL,NULL,wbfs_applet_##x, A, d}
    APPLET_0(0, ls),
    APPLET_0(0, df),
    APPLET_0(0, make_info),
    APPLET_0(0, id_title),
    APPLET_0(1, init),
    APPLET_1(1, add_iso,          "<SRC:filename.iso>"),
    APPLET_1(1, add_wbfs,         "<SRC:filename.wbfs>"),
    APPLET_1(1, rm,               "<GAMEID>"),
    APPLET_2(0, extract_iso,      "<GAMEID> <DST:dir>"),
    APPLET_2(0, extract_wbfs,     "<GAMEID> <DST:dir>"),
    APPLET_1(0, extract_wbfs_all, "<DST:dir>"),
    APPLET_1(0, ls_file,          "<GAMEID>"),
    APPLET_2(0, extract_file,     "<GAMEID> <file> [<DST:file>]"),
    //APPLET_0(0, mkhbc),
    APPLET_0(0, debug_info),
};
static int num_applets = sizeof(wbfs_applets)/sizeof(wbfs_applets[0]);

void usage_basic(char **argv)
{
    char *tool = strrchr(argv[0], '/');
    if (!tool) tool = strrchr(argv[0], '\\');
    if (tool) tool++; else tool = argv[0];
    //printf("Usage: %s [-d disk|-p partition]\n", argv[0]);
    printf("%s %s by oggzee, based on wbfs by kwiirk\n\n", tool, tool_version);
    printf("Usage: %s [OPTIONS] <DRIVE or FILENAME> [COMMAND [ARGS]]:\n", tool);
    printf("\n");
    printf("  Given just a filename it will convert from iso to wbfs or vice versa:\n");
    printf("\n");
    printf("    %s filename.iso\n", tool);
    printf("    Will convert filename.iso to GAMEID.wbfs\n");
    printf("    And create an info file GAMEID_TITLE.txt\n");
    printf("\n");
    printf("    %s filename.wbfs\n", tool);
    printf("    Will convert filename.wbfs to GAMEID_TITLE.iso\n");
    printf("\n");
}

void usage(char **argv)
{
    int i;
    usage_basic(argv);
    printf("  COMMANDS:\n");
    printf("        <filename.iso>   convert  <DST:dir>\n");
    printf("        <filename.wbfs>  convert  <DST:dir>\n");
    printf("    <DST:filename.wbfs>  create   <SRC:filename.iso>\n");
    for (i=0;i<num_applets;i++) {
        printf("    %sdrive or file>  %-16s %s\n",
                wbfs_applets[i].dest ? "<DST:" : "    <",
                wbfs_applets[i].opt,
                wbfs_applets[i].arg_name);
    }
    printf("\n");
    printf("  OPTIONS: (it's recommended to just use the defaults)\n");
    printf("    -s SIZE  :  Set split size ["FMT_lld"] ", DEF_SPLIT_SIZE);
    printf("(%d sectors)\n", (u32)(DEF_SPLIT_SIZE/512));
    printf("                Must be a multiple of 512 (sector size)\n");
    printf("    -d       :  Create a GAMEID_TITLE directory and place\n");
    printf("                the created .wbfs file there\n");
    printf("    -a       :  Copy ALL partitions from ISO [default]\n");
    printf("    -g       :  Copy only game partition from ISO\n");
    printf("    -1       :  Copy 1:1 from ISO\n");
    printf("    -2       :  Use split size: 2GB-32kb ("FMT_lld")\n", SPLIT_SIZE_2);
    printf("    -4       :  Use split size: 4GB-32kb ("FMT_lld")\n", SPLIT_SIZE_4);
    printf("    -0       :  Don't split (split size: "FMT_lld")\n", SPLIT_SIZE_0);
    printf("    -f       :  Force wbfs mode even if the wbfs file or partition\n");
    printf("                integrity check is invalid (non matching number of\n");
    printf("                sectors or other parameters)\n");
    printf("    -t       :  trim extracted iso size\n");
    //printf("    -w       :  Overwrite\n");
    printf("    -h       :  Help\n");
    exit(EXIT_FAILURE);
}

int main(int argc, char *argv[])
{
    int opt;
    int i;
    int ret = -1;
    //char *partition=0,*disc =0;
    char *filename = 0;
    char *dest_name = "";

    // disable stdout buffering
    setvbuf(stdout, NULL, _IONBF, 0); 

    if (argc == 1) {
        usage_basic(argv);
        printf("  Use -h for help on commands and options\n");
        exit(EXIT_FAILURE);
    }

    while ((opt = getopt(argc, argv, "s:hag0124dftw")) != -1) {
        switch (opt) {
            /*case 'p':
              partition = optarg;
              break;
              case 'd':
              disc = optarg;
              break;*/
            case 's':
                {
                    long long size;
                    if (sscanf(optarg, ""FMT_lld"", &size) != 1) {
                        printf("Invalid split size value!\n");
                        goto err;
                    }
                    if (size <= 0 || size % 512) {
                        printf("Invalid split size!\n");
                        goto err;
                    }
                    if (size % (32*1024)) {
                        printf("WARNING: split size not 32kb aligned!\n");
                    }
                    OPT_split_size = size;
                    printf("Split size: "FMT_lld" (%d sectors)\n",
                            OPT_split_size, (u32)(OPT_split_size/512));
                }
                break;
            case 'd':
                printf("Using OPTION -d : Create a GAMEID_TITLE directory\n");
                OPT_sub_dir = 1;
                break;
            case 'a':
                printf("Using OPTION -a : install all partitions\n");
                OPT_part_all = 1;
                break;
            case 'g':
                printf("Using OPTION -g : install only game partitions\n");
                OPT_part_all = 0;
                break;
            case '1':
                printf("Using OPTION -1 : make a 1:1 copy\n");
                OPT_copy_1_1 = 1;
                OPT_part_all = 1;
                break;
            case '0':
                OPT_split_size = SPLIT_SIZE_0;
                printf("Using OPTION -0 : no splits.\n");
                printf("Split size: "FMT_lld" (%d sectors)\n",
                        OPT_split_size, (u32)(OPT_split_size/512));
                break;
            case '2':
                OPT_split_size = SPLIT_SIZE_2;
                printf("Using OPTION -2 : ");
                printf("Split size: "FMT_lld" (%d sectors)\n",
                        OPT_split_size, (u32)(OPT_split_size/512));
                break;
            case '4':
                OPT_split_size = SPLIT_SIZE_4;
                printf("Using OPTION -4 : ");
                printf("Split size: "FMT_lld" (%d sectors)\n",
                        OPT_split_size, (u32)(OPT_split_size/512));
                break;
            case 'f':
                printf("Using OPTION -f : force wbfs even if wbfs integrity is invalid\n");
                wbfs_set_force_mode(1);
                break;
            case 't':
                printf("Using OPTION -t : trim extracted iso size\n");
                OPT_trim = 1;
                break;
            case 'w':
                //printf("Using OPTION -w : overwrite target iso\n");
                OPT_overwrite = 1;
                break;
            case 'h':
            default: /* '?' */
                usage(argv);
        }
    }
    if (optind >= argc) {
        usage(argv);
        exit(EXIT_FAILURE);
    }

    OPT_filename = filename = argv[optind];
    optind++;

    if (optind == argc)
    {
        // only filename specified
        dest_name = "";
        goto L_convert;
    }

    if (optind >= argc) {
        goto usage;
    }


    if (strcmp(argv[optind], "create")==0)
    {
        if(optind + 1 >= argc) goto usage;
        dest_name = argv[optind+1];
        return wbfs_applet_create(filename, dest_name);
    }

    if (strcmp(argv[optind], "convert")==0)
    {
        if(optind + 1 >= argc) goto usage;
        dest_name = argv[optind+1];
        L_convert:
        ret = convert(filename, dest_name);
        if (ret == -2) goto usage;
        if (ret == -1) goto err;
        goto exit;
    }

    for (i=0;i<num_applets;i++)
    {
        struct wbfs_applets *ap = &wbfs_applets[i];
        if (strcmp(argv[optind],ap->opt)==0)
        {
            //wbfs_t *p = wbfs_try_open_partition(filename,
            //                          ap->func== wbfs_applet_init);
            wbfs_t *p = wbfs_auto_open_partition(filename,
                    ap->func== wbfs_applet_init);
            if(!p) {
                printf("Error opening WBFS '%s'\n", filename);
                return 1;
            }
            if(ap->func)
            {
                ret = ap->func(p);
            }
            else if(ap->func_arg)
            {
                if(optind + 1 >= argc)
                    usage(argv);
                else
                    ret = ap->func_arg(p, argv[optind+1]);
            }
            else if(ap->func_arg2)
            {
                if(optind + 2 >= argc)
                    usage(argv);
                else {
                    if (optind + 3 < argc)
                        OPT_arg3 = argv[optind+3];
                    else
                        OPT_arg3 = NULL;
                    ret = ap->func_arg2(p, argv[optind+1], argv[optind+2]);
                }
            }
            wbfs_close(p);
            break;
        }
    }
    if (i==num_applets) {
        printf("Error: unknown command: %s\n\n", argv[optind]);
        goto usage;
    }
    if (ret) goto err;

exit:
    exit(EXIT_SUCCESS);
usage:
    usage(argv);
err:
    exit(EXIT_FAILURE);
}

