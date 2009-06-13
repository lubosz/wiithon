// Modified by makiolo <makiolo@gmail.com>

#ifdef __linux__
#include <stdio.h>
#include <sys/ioctl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <linux/fs.h>
#include <fcntl.h>
#include <unistd.h>

#include "libwbfs.h"

static int wbfs_fread_sector(void *_fp,u32 lba,u32 count,void*buf)
{
        FILE*fp =_fp;                                 
        u64 off = lba;
        off*=512ULL;
		if (fseeko(fp, off, SEEK_SET))
        {
            fprintf(stderr,"\n\n%lld %d %p\n",off,count,_fp);
			//wbfs_error("Error al posicionarse en la particion del disco");
            return FALSE;
        }
        if (fread(buf, count*512ULL, 1, fp) != 1){
                //wbfs_error("Error leyendo disco");
                return FALSE;
        }
        return OK;
  
}
static int wbfs_fwrite_sector(void *_fp,u32 lba,u32 count,void*buf)
{
        FILE*fp =_fp;
        u64 off = lba;
        off*=512ULL;
	if (fseeko(fp, off, SEEK_SET))
        {
			wbfs_error("Error al posicionarse en la particion del disco");
            return FALSE;
        }
        if (fwrite(buf, count*512ULL, 1, fp) != 1){
                wbfs_error("Error escribiendo disco");
                return FALSE;
        }
        return OK;
  
}
static int get_capacity(char *file,u32 *sector_size,u32 *n_sector)
{
        int fd = open(file,O_RDONLY);
        int ret;
        if(fd<0){
                return 0;
        }
        ret = ioctl(fd,BLKSSZGET,sector_size);
        if(ret<0)
        {
                FILE *f;
                close(fd);
                f = fopen(file,"r");
                fseeko(f,0,SEEK_END);
                *n_sector = ftello(f)/512;
                *sector_size = 512;
                fclose(f);
                return 1;
        }
        ret = ioctl(fd,BLKGETSIZE,n_sector);
        close(fd);
        if(*sector_size>512)
                *n_sector*=*sector_size/512;
        if(*sector_size<512)
                *n_sector/=512/ *sector_size;
        return 1;
}
wbfs_t *wbfs_try_open_hd(char *fn,int reset)
{
        u32 sector_size, n_sector;
        if(!get_capacity(fn,&sector_size,&n_sector))
                return NULL;
        FILE *f = fopen(fn,"r+");
        if (!f)
                return NULL;
        return wbfs_open_hd(wbfs_fread_sector,wbfs_fwrite_sector,f,
                            sector_size ,n_sector,reset);
}
wbfs_t *wbfs_try_open_partition(char *fn,int reset)
{
        u32 sector_size, n_sector;
        if(!get_capacity(fn,&sector_size,&n_sector))
                return NULL;
        FILE *f = fopen(fn,"r+");
        if (!f)
                return NULL;
        return wbfs_open_partition(wbfs_fread_sector,wbfs_fwrite_sector,f,
                                   sector_size ,n_sector,0,reset);
}
wbfs_t *wbfs_try_open(char *disc,char *partition, int reset)
{
        wbfs_t *p = 0;
        if(partition)
                p = wbfs_try_open_partition(partition,reset);
        if (!p && !reset && disc)
                p = wbfs_try_open_hd(disc,0);
        else if(!p && !reset){
                char buffer[32];
                int i;
                int n;
                for (i='b';i<'z';i++)
                {
                    for (n=1;n<5;n++)
                    {
                        snprintf(buffer,32,"/dev/sd%c%d",i ,n);
                        p = wbfs_try_open_hd(buffer,0);
                        if(p)
                        {
                                fprintf(stderr,"Autodetectada %s ...\n",buffer);
                                return p;
                        }
                        snprintf(buffer,32,"/dev/hd%c%d",i , n);
                        p = wbfs_try_open_hd(buffer,0);
                        if(p)
                        {
                                fprintf(stderr,"Autodetectada %s ...\n",buffer);
                                return p;
                        }                     
                    }
                }
                wbfs_error("No se ha encontrado ninguna particion WBFS (verifica los permisos))");
        }
        return p;
}

#endif
