// Basado en wl wbfs.c de Kwiirk
// Ricardo Marmolejo García <makiolo@gmail.com>

// Licensed under the terms of the GNU GPL, version 2
// http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt

#include <stdio.h>     /* for printf */
#include <stdlib.h>    /* for exit */
#include <getopt.h>
#include <sys/stat.h>
#include <unistd.h>
#include <time.h>

#include "libwbfs.h"

wbfs_t *wbfs_try_open(char *disc,char *partition, int reset);
wbfs_t *wbfs_try_open_partition(char *fn,int reset);

void spinner(u64 x, u64 max)
{
	static time_t start_time;
	static u32 expected_total;
	u32 d;
	double percent;
	u32 h, m, s;

	if (x == 0) {
		start_time = time(NULL);
		expected_total = 300;
	}

	if (x == max) {
        d = time(NULL) - start_time;
        h = d / 3600;
        m = (d / 60) % 60;
        s = d % 60;
		fprintf(stderr, "FIN;@;%d;@;%02d;@;%02d\n", h, m, s);
		return;
	}

	d = time(NULL) - start_time;

	if (d != 0)
		expected_total = (3 * expected_total + d * max / x) / 4;

	if (expected_total > d)
		d = expected_total - d;
	else
		d = 0;

	h = d / 3600;
	m = (d / 60) % 60;
	s = d % 60;
	percent = 100.0 * x / max;

    fprintf(stdout , "%5.2f;@;%d;@;%02d;@;%02d\n", percent, h, m, s);
    fflush(stdout);
}


int read_wii_file(void*_fp,u32 offset,u32 count,void *iobuf)
{
        FILE*fp =_fp;
        u64 off = offset;
        off<<=2;
		if (fseeko(fp, off, SEEK_SET))
        {
			wbfs_error("Error posicionandome en el fichero al leer");
            return FALSE;
        }
        if (fread(iobuf, count, 1, fp) != 1)
        {
			wbfs_error("Error leyendo disco");
			return FALSE;
        }
        return OK;
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
			return FALSE;
        }
        if (fwrite(iobuf, count*0x8000, 1, fp) != 1)
        {
			wbfs_error("Error escribiendo en el fichero");
			return FALSE;
        }
        return OK;
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


s32 WBFS_DiskSpace(wbfs_t *p , f32 *used, f32 *free)
{
	f32 ssize;
	u32 cnt;

	/* Count used blocks */
	cnt = wbfs_count_usedblocks(p);

	/* Sector size in GB */
	ssize = p->wbfs_sec_sz / GB_SIZE;

	/* Copy values */
	*free = ssize * cnt;
	*used = ssize * (p->n_wbfs_sec - cnt);

	return OK;
}

/////////////////////////////////////////////////////////////////////////////////

// Controladores de cada parametro

int
wiithon_wrapper_ls(wbfs_t *p) {
  int count = wbfs_count_discs(p);

  if(count > 0) {
	int i;
	u8 *b = wbfs_ioalloc(0x100);
	char gameid[7];

	for (i=0; i<count; i++) {
	  if(!wbfs_get_disc_info(p, i, b, 0x100, NULL)) {
		sprintf( gameid, "%c%c%c%c%c%c", b[0], b[1], b[2], b[3], b[4], b[5] );
		f32 size = WBFS_GameSize( p , (u8*)gameid);
		if( size < 0) size = 0.0f;
		fprintf(stdout, "%s;@;%s;@;%f\n", gameid , b + 0x20, size );
	  }
	}

	wbfs_iofree(b);
  }

  return OK;
}

int wiithon_wrapper_df(wbfs_t *p)
{
		f32 usado;
		f32 libre;
        s32 res = WBFS_DiskSpace(p , &usado , &libre);
        if(res == OK)
        {
        	f32 total = usado + libre;
			fprintf(stdout , "%f;@;%f;@;%f\n" , usado ,	libre ,	total);
			return TRUE;
		}
        else
		{
       		return FALSE;
		}
}

static void _spinner(int x,int y){ spinner(x,y);}
int wiithon_wrapper_add(wbfs_t *p,char*argv)
{
        FILE *f = fopen(argv,"r");
        u8 discinfo[7];
        wbfs_disc_t *d;
        if(!f)
        {
			fprintf(stdout,"ISO_NO_EXISTE");
			return FALSE;
		}
        else
        {
			fread(discinfo,6,1,f);
			d = wbfs_open_disc(p,discinfo);
			if(d)
			{
				discinfo[6]=0;
				fprintf(stdout,"YA_ESTA_EN_DISCO\n");
				wbfs_close_disc(d);
				return FALSE;
			}
			else
			{
				return wbfs_add_disc(p,read_wii_file,f,_spinner,ONLY_GAME_PARTITION,0);
			}
        }
}
int wiithon_wrapper_rm(wbfs_t *p, u8 *idgame)
{
    return wbfs_rm_disc(p, idgame);
}
int wiithon_wrapper_extract(wbfs_t *p, u8 *idgame)
{
        wbfs_disc_t *d;
        int ret = 1;
        d = wbfs_open_disc(p,idgame);
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
                fprintf(stderr,"%s no es un IDGAME de la lista ...\n",idgame);
        return ret;
}

int wiithon_wrapper_clonar(wbfs_t *p , u8 *discid, char *destino)
{
    int retorno = FALSE;

    wbfs_t *p_dst = wbfs_try_open(NULL, destino , 0);
    if(p_dst)
    {
        wbfs_disc_t *d_src = wbfs_open_disc(p_dst,discid);
        if(d_src)
        {
            fprintf(stderr, "%s ya esta en disco...\n", discid);
            wbfs_close_disc(d_src);
        }
        else
        {
            d_src = wbfs_open_disc(p,discid);
            if(d_src)
            {
                retorno = wbfs_copy_disc(d_src , p_dst , _spinner);
                wbfs_close_disc(d_src);
            }
        }
    }
    wbfs_close(p_dst);
    return retorno;
}

int wiithon_wrapper_rename(wbfs_t *p , u8 *idgame , char *nuevoNombre)
{
    return wbfs_ren_disc(p, idgame, nuevoNombre);
}

int wiithon_wrapper_rename_idgame(wbfs_t *p , u8 *idgame , u8 *nuevoIDGAME)
{
    return wbfs_ren_idgame(p, idgame, nuevoIDGAME);
}

int uso(char *argv[])
{
    printf("\t%s -p /dev/sdxY formatear\n" , argv[0]);
    printf("\t%s -p /dev/sdxY ls\n" , argv[0]);
    printf("\t%s -p /dev/sdxY df\n" , argv[0]);
    printf("\t%s -p /dev/sdxY add fichero.iso\n" , argv[0]);
    printf("\t%s -p /dev/sdxY rm IDGAME\n" , argv[0]);
    printf("\t%s -p /dev/sdxY extract IDGAME\n" , argv[0]);
    printf("\t%s -p /dev/sdxY clonar IDGAME /dev/destinoXY\n" , argv[0]);
    printf("\t%s -p /dev/sdxY rename IDGAME NuevoNombre\n" , argv[0]);
    printf("\t%s -p /dev/sdxY rename_idgame IDGAME NUEVO_IDGAME\n", argv[0]);
    return FALSE;
}

int main(int argc, char *argv[])
{
	int retorno = FALSE;
    int opt;
    int numParametros;
    int noFormatear;
    char *partition = NULL;

    while ((opt = getopt(argc, argv, "p:d:hf:f")) != -1)
    {
            switch (opt)
            {
                case 'p':
                    partition = optarg;
                    break;
                case 'h':
                default:
                    uso(argv);
                    exit(0);
            }
    }

    // Le resto 1 de la propia aplicación
    // Le resto los 2 parametros del device (-p /dev/sda1)
    numParametros = argc - 1 - 2;

    noFormatear = ((numParametros == 1) && (strcmp(argv[optind], "formatear") == 0)) ? FALSE : TRUE;

    wbfs_t *p = wbfs_try_open(NULL, partition, noFormatear );
    if(p)
    {
        if ( noFormatear == FALSE )
        {
            printf("Se ha formateado %s\n" , partition);
        }
        else if(numParametros == 0)
        {
            retorno = uso(argv);
        }
        else if ((numParametros == 1) && (strcmp(argv[optind], "ls") == 0))
        {
            retorno = wiithon_wrapper_ls(p);
        }
        else if ((numParametros == 1) && (strcmp(argv[optind], "df") == 0))
        {
            retorno = wiithon_wrapper_df(p);
        }
        else if ((numParametros == 2) && (strcmp(argv[optind], "add") == 0))
        {
            retorno = wiithon_wrapper_add(p, argv[4]);
        }
        else if ((numParametros == 2) && (strcmp(argv[optind], "rm") == 0))
        {
            retorno = wiithon_wrapper_rm(p, (u8*)argv[4]);
        }
        else if ((numParametros == 2) && (strcmp(argv[optind], "extract") == 0))
        {
            retorno = wiithon_wrapper_extract(p, (u8*)argv[4]);
        }
        else if ((numParametros == 3) && (strcmp(argv[optind], "clonar") == 0))
        {
            retorno = wiithon_wrapper_clonar(p,  (u8*)argv[4] , argv[5]);
        }
        else if ((numParametros == 3) && (strcmp(argv[optind], "rename") == 0))
        {
            retorno = wiithon_wrapper_rename(p , (u8*)argv[4] , argv[5]);
        }
        else if ((numParametros == 3) && (strcmp(argv[optind], "rename_idgame") == 0))
        {
            retorno = wiithon_wrapper_rename_idgame(p , (u8*)argv[4] , (u8*)argv[5]);
        }
        else
        {
            retorno = uso(argv);
        }
        wbfs_close(p);
    }
    else
    {
        printf("Wrapper hecho para wiithon por Ricardo Marmolejo García <makiolo@gmail.com>");
        printf("No se ha facilitado ninguna partición WBFS.\n");
        p = wbfs_try_open(0,0,0); //Autodetecta partición WBFS mediante libwbfs
        wbfs_close(p);
        printf("Para más ayuda:\n\t%s -h\n" , argv[0]);
        printf("No obstante, este wrapper esta pensado para ser usado desde wiithon, y por tanto no se realizan unas serie de comprobaciones, debido a que se asume que los datos han sido verificados previamente por wiithon.\n");
    }
    exit(retorno);
}
