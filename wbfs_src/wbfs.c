// Copyright 2009 Kwiirk
// Modified by makiolo <makiolo@gmail.com>
// Modified for add Hermes wbfs_integrity_check
// Licensed under the terms of the GNU GPL, version 2
// http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt

#include <stdio.h>     /* for printf */
#include <stdlib.h>    /* for exit */
#include <getopt.h>
#include <sys/stat.h>
#include <unistd.h>

#include "tools.h"
#include "libwbfs.h"

wbfs_t *wbfs_try_open(char *disc,char *partition, int reset);
wbfs_t *wbfs_try_open_partition(char *fn,int reset);

#define GB (1024*1024*1024.)

int read_wii_file(void*_fp,u32 offset,u32 count,void*iobuf)
{
        FILE*fp =_fp;
        u64 off = offset;
        off<<=2;
		if (fseeko(fp, off, SEEK_SET))
        {
			wbfs_error("Error posicionandome en el fichero al leer");
            return 1;
        }
        if (fread(iobuf, count, 1, fp) != 1)
        {
			wbfs_error("Error leyendo disco");
			return 1;
        }
        return 0;
}
int write_wii_sector_file(void*_fp,u32 lba,u32 count,void*iobuf)
{
        FILE*fp=_fp;
        u64 off = lba;
        off *=0x8000;
		if (fseeko(fp, off, SEEK_SET))
        {
			fprintf(stderr,"\n\n%lld %p\n",off,_fp);
			wbfs_error("Error posicionandome en el fichero al escribir");
			return 1;
        }
        if (fwrite(iobuf, count*0x8000, 1, fp) != 1)
        {
			wbfs_error("Error escribiendo en el fichero");
			return 1;
        }
        return 0;
}


f32 WBFS_GameSize(wbfs_t *p , u8 *discid)
{
	wbfs_disc_t *disc = NULL;

	u32 sectors;

	/* No device open */
	if (!p)
		return -1;

	/* Open disc */
	disc = wbfs_open_disc(p, discid);
	if (!disc)
		return -2;

	/* Get game size in sectors */
	sectors = wbfs_sector_used(p, disc->header);

	/* Close disc */
	wbfs_close_disc(disc);

	return (p->wbfs_sec_sz / GB_SIZE) * sectors;
}

int wbfs_applet_ls(wbfs_t *p)
{
        int count = wbfs_count_discs(p);
        if(count==0)
                fprintf(stderr,"Sistemas de ficheros seleccionado vacio\n");
        else{
                int i;
                u32 size;
                u8 *b = wbfs_ioalloc(0x100);
				char gameid[7]; // 6+1
                for (i=0;i<count;i++)
                {
                        if(!wbfs_get_disc_info(p,i,b,0x100,&size))
                        {
							sprintf(gameid, "%c%c%c%c%c%c", b[0], b[1], b[2], b[3], b[4], b[5] );
							f32 size = WBFS_GameSize( p , (u8*)gameid);
							if( size < 0) size = 0.0f;
							fprintf(stderr, "%s;%s;%f\n", gameid , b + 0x20, 0.0f );
						}
                }
                wbfs_iofree(b);
        }   
        return 0;
}

s32 WBFS_DiskSpace(wbfs_t *p , f32 *used, f32 *free)
{
	f32 ssize;
	u32 cnt;

	/* No device open */
	if (!p)
		return -1;

	/* Count used blocks */
	cnt = wbfs_count_usedblocks(p);

	/* Sector size in GB */
	ssize = p->wbfs_sec_sz / GB_SIZE;

	/* Copy values */
	*free = ssize * cnt;
	*used = ssize * (p->n_wbfs_sec - cnt);

	return OK;
}

int wbfs_applet_df(wbfs_t *p)
{
		f32 usado;
		f32 libre;
        s32 res = WBFS_DiskSpace(p , &usado , &libre);
        if(res == OK)
        {
        	f32 total = usado + libre;
			fprintf(stdout , "%f;%f;%f\n" , usado ,	libre ,	total);
			return TRUE;
		}
        else
		{
       		return FALSE;
		}
        
        
        
}

int wbfs_applet_mkhbc(wbfs_t *p)
{
        int count = wbfs_count_discs(p);
        char filename[7];
        FILE *xml;
        if(count==0)
                fprintf(stderr,"Sistemas de ficheros WBFS vacio.\n");
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
                        xml = fopen("meta.xml","w");
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
        return p!=0;
}
int wbfs_applet_init(wbfs_t *p)
{
        // nothing to do actually..
        // job already done by the reset flag of the wbfs_open_partition
        return p!=0;
        
}

int wbfs_applet_check(wbfs_t *p , char * idgame)
{
	if( wbfs_integrity_check(p , (u8*)idgame) == TRUE)
	{
		exit(TRUE);
	}
	else
	{
		exit(FALSE);
	}
	
}

static void _spinner(int x,int y){ spinner(x,y);}
int wbfs_applet_add(wbfs_t *p,char*argv)
{
        FILE *f = fopen(argv,"r");
        u8 discinfo[7];
        wbfs_disc_t *d;
        if(!f)
        {
			fprintf(stderr,"No se puede abrir la ISO, tal vez no exista. Pruebe a indicar la ruta completa entre comillas");
			return FALSE;
		}
        else
        {
			fread(discinfo,6,1,f);
			d = wbfs_open_disc(p,discinfo);
			if(d)
			{
				discinfo[6]=0;
				fprintf(stderr,"%s ya está en el disco ...\n",discinfo);
				wbfs_close_disc(d);
				return TRUE;
			}
			else
			{
				return wbfs_add_disc(p,read_wii_file,f,_spinner,ONLY_GAME_PARTITION,0);
			}
        }
}
int wbfs_applet_rm(wbfs_t *p,char*argv)
{
	if( wbfs_rm_disc(p,(u8*)argv) == 1)
	{
		//fprintf(stderr,"%s no existe. Elija un IDGAME de la lista ...\n",argv);
		exit(FALSE);
	}
	else
	{
		//fprintf(stderr,"%s ha sido borrado.\n",argv);	
		exit(TRUE);
	}
		
}
int wbfs_applet_extract(wbfs_t *p,char*argv)
{
        wbfs_disc_t *d;
        int ret = 1;
        d = wbfs_open_disc(p,(u8*)argv);
        if(d)
        {
                char buf[0x100];
                int i,len;
                /* get the name of the title to find out the name of the iso */
                strncpy(buf,(char*)d->header->disc_header_copy+0x20,0x100);
                len = strlen(buf);
                // replace silly chars by '_'
                for( i = 0; i < len; i++)
                        if(buf[i]==' ' || buf[i]=='/' || buf[i]==':')
                                buf[i] = '_';
                strncpy(buf+len,".iso",0x100-len);
                FILE *f=fopen(buf,"w");
                if(!f)
                        wbfs_fatal("Error al escribir en el ISO de destino");
                else{
                        fprintf(stderr,"Escribiendo %s\n",buf);

                        // write a zero at the end of the iso to ensure the correct size
                        // XXX should check if the game is DVD9..
                        fseeko(f,(d->p->n_wii_sec_per_disc/2)*0x8000ULL-1ULL,SEEK_SET);
                        fwrite("",1,1,f);

                        ret = wbfs_extract_disc(d,write_wii_sector_file,f,_spinner);
                        fclose(f);
                }
                wbfs_close_disc(d);
                
        }
        else
                fprintf(stderr,"%s no es un IDGAME de la lista ...\n",argv);
        return ret;
}
int wbfs_applet_create(char*argv)
{
		/*
        char buf[1024];
        strncpy(buf,argv,1019);
        strcpy(buf+strlen(buf),".wbfs");
        FILE *f=fopen(buf,"w");
        if(!f)
                wbfs_fatal("unable to open dest file");
        else{
                // reserve space for the maximum size.
                fseeko(f,143432*2*0x8000ULL-1ULL,SEEK_SET);
                fwrite("",1,1,f);
                fclose(f);
                wbfs_t *p = wbfs_try_open_partition(buf,1);
                if(p){
                        wbfs_applet_add(p,argv);
                        wbfs_trim(p);
                        ftruncate(fileno(p->callback_data),p->n_hd_sec*512ULL);
                        wbfs_close(p);
                }
        }
        */
        wbfs_fatal("sin implementar");
        return 1;
}

void wbfs_applet_rename(wbfs_t *p , int argc , char * idgame , char * nuevoNombre)
{
	//Espera 6 parametros de wiithon, lo dejo fuera del interface de wbfs
	if(argc==6)
	{
		if (wbfs_ren_disc(p, (u8*)idgame, (u8*)nuevoNombre) == TRUE)
		{
			printf ("Cambiado nombre a %s\n" , nuevoNombre);
		}
		else
		{
			printf ("ERROR: Cambiado nombre a %s\n" , nuevoNombre);	
		}
	}
	else
	{
		wbfs_error("ERROR: Renombra a través de wiithon");	
	}
}

struct wbfs_applets{
        char *opt;
        int (*func_arg)(wbfs_t *p, char *argv);
        int (*func)(wbfs_t *p);
} wbfs_applets[] = {
#define APPLET(x) { #x,wbfs_applet_##x,NULL}
#define APPLET_NOARG(x) { #x,NULL,wbfs_applet_##x}
        APPLET_NOARG(ls),
        APPLET_NOARG(df),
        APPLET_NOARG(mkhbc),
        APPLET_NOARG(init),
        APPLET(add),
        APPLET(rm),
        APPLET(extract),
        //APPLET_NOARG(check),
        APPLET(check),
};
static int num_applets = sizeof(wbfs_applets)/sizeof(wbfs_applets[0]);
void usage(char **argv)
{
        int i;
        fprintf(stderr, "Uso: %s [-d disco|-p particion]\n",
                argv[0]);
        for (i=0;i<num_applets;i++)
                fprintf(stderr, "\t %s %s\n",wbfs_applets[i].opt,wbfs_applets[i].func_arg?"(fichero|id)":"");
        exit(EXIT_FAILURE);
}
int
main(int argc, char *argv[])
{
	int retorno = EXIT_SUCCESS;
        int  opt;
        int i;
        char *partition=0,*disc =0;
        while ((opt = getopt(argc, argv, "p:d:hf")) != -1) {
                switch (opt) {
                case 'p':
                        partition = optarg;
                        break;
                case 'd':
                        disc = optarg;
                        break;
                case 'f':
                        wbfs_set_force_mode(1);
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
              
        if (strcmp(argv[optind],"create")==0)
        {
                if(optind + 1 >= argc)
                        usage(argv);
                else
                        return wbfs_applet_create(argv[optind+1]);
                
        }

        for (i=0;i<num_applets;i++)
        {
                struct wbfs_applets *ap = &wbfs_applets[i];
                if (strcmp(argv[optind],ap->opt)==0)
                {
                        wbfs_t *p = wbfs_try_open(disc , partition, ap->func== wbfs_applet_init);
                        if(!p) break;
                                                                        
						if(ap->func_arg)
						{
								if(optind + 1 >= argc)
										usage(argv);
								else
										retorno = ap->func_arg(p, argv[optind+1]);
						}else
								ap->func(p);
						wbfs_close(p);
						break;
                }
        }

		if (strcmp(argv[optind], "rename") == 0)
		{
			wbfs_t *p = wbfs_try_open(disc , partition, 0);
			if(p) wbfs_applet_rename(p, argc , argv[4] , argv[5]);
		}

        exit(retorno);
}
