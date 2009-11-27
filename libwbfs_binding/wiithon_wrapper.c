// Basado en el wbfs.c de Kwiirk
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
    
    // casos de excepcion
    if(max <= 0 || x > max || x < 0)
    {
        printf("Error en el contador\n");
        return;
    }
    
	static time_t start_time;
	static u32 d;    
    static int porcentaje_ponderado;
    
	int percent;
    
    int diferencia;
    
    u32 restante;
	u32 h, m, s;

	if (x == 0) {
		start_time = time(NULL);
        d = 300;
        porcentaje_ponderado = 0;
	}

    d = time(NULL) - start_time;
    
    
    percent = (100 * x) / max;

    if(percent > 0)
    {
        /*
         * d = tiempo desde que empezo
         * porcen% --------> d
         * 100-porcen% ----> restante
         */
        
        if( percent > porcentaje_ponderado )
        {
            diferencia = percent - porcentaje_ponderado;
            porcentaje_ponderado+=(diferencia/2);
        }

        if (porcentaje_ponderado != 0)
        {
            restante = (d * (100-porcentaje_ponderado)) / porcentaje_ponderado;
        }
        else
        {
            restante = 300;    
        }
    }
    else
    {
        porcentaje_ponderado = 0;
        restante = 0;    
    }

    h = (restante / 3600);
    m = (restante / 60) % 60;
    s = (restante % 60);
    
    if(x != max)
    {        
        fprintf(stdout , "%d;@;%d;@;%d;@;%d\n", porcentaje_ponderado, h, m, s);
    }
    else
    {
        fprintf(stdout, "FIN;@;%d;@;%d;@;%d\n", h, m, s);
    }
    
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
wiithon_wrapper_ls(wbfs_t *p)
{
    int count = wbfs_count_discs(p);

    if(count > 0)
    {
        int i;
        u8 *b = wbfs_ioalloc(0x100);
        char gameid[7];

        for (i=0; i<count; i++)
        {
            if(!wbfs_get_disc_info(p, i, b, 0x100, NULL))
            {
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

int
wiithon_wrapper_ls_idgame(wbfs_t *p, u8 *idgame)
{
    int count = wbfs_count_discs(p);

    if(count > 0)
    {
        int i;
        u8 *b = wbfs_ioalloc(0x100);
        char gameid[7];

        for (i=0; i<count; i++)
        {
            if(!wbfs_get_disc_info(p, i, b, 0x100, NULL))
            {
                sprintf( gameid, "%c%c%c%c%c%c", b[0], b[1], b[2], b[3], b[4], b[5] );
                if(wbfs_memcmp(gameid, idgame ,6)==0)
                {
                    f32 size = WBFS_GameSize( p , (u8*)gameid);
                    if( size < 0) size = 0.0f;
                    fprintf(stdout, "%s;@;%s;@;%f\n", gameid , b + 0x20, size );
                }
            }
        }
        wbfs_iofree(b);
    }

    return OK;
}

int wiithon_wrapper_check_idgame(wbfs_t *p, u8 *idgame)
{
    return wbfs_integrity_check(p, (u8*)idgame);
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
    int retorno = FALSE;

    FILE *f = fopen(argv,"r");
    u8 discinfo[7];
    wbfs_disc_t *d;
    if(!f)
    {
        fprintf(stdout,"ISO_NO_EXISTE");
        retorno = FALSE;
    }
    else
    {
        if(fread(discinfo,6,1,f) == 1)
        {
            d = wbfs_open_disc(p,discinfo);
            if(d)
            {
                discinfo[6]=0;
                fprintf(stdout,"YA_ESTA_EN_DISCO\n");
                wbfs_close_disc(d);
                retorno = FALSE;
            }
            else
            {
                retorno = wbfs_add_disc(p,read_wii_file,f,_spinner,ONLY_GAME_PARTITION,0);
            }
        }
        else
        {
            wbfs_error("Error leyendo disco.");
            retorno = FALSE;
        }
    }
    return retorno;
}
int wiithon_wrapper_rm(wbfs_t *p, u8 *idgame)
{
    return wbfs_rm_disc(p, idgame);
}
int wiithon_wrapper_extract(wbfs_t *p, u8 *idgame)
{
    wbfs_disc_t *d;
    int retorno = FALSE;
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
        {
            if(buf[i]==' ' || buf[i]=='/' || buf[i]==':')
            {
                buf[i] = '_';
            }
        }
        strncpy(buf+len,".iso",0x100-len);
        FILE *f=fopen(buf,"w");
        if(!f)
        {
            wbfs_fatal("Error al escribir en el ISO de destino");
            retorno = FALSE;
        }
        else
        {
            // write a zero at the end of the iso to ensure the correct size
            // XXX should check if the game is DVD9..
            fseeko(f,(d->p->n_wii_sec_per_disc/2)*0x8000ULL-1ULL,SEEK_SET);
            if(fwrite("",1,1,f) == 1)
            {
                retorno = wbfs_extract_disc(d,write_wii_sector_file,f,_spinner);
                fclose(f);
            }
            else
            {
                wbfs_error("Error escribiendo en el disco. Linea 261");
                retorno = FALSE;
            }
        }
        wbfs_close_disc(d);
    }
    else
    {
        fprintf(stderr,"%s no es un IDGAME de la lista ...\n",idgame);
    }
    return retorno;
}

int wiithon_wrapper_clonar(wbfs_t *p , u8 *discid, char *destino)
{
    int retorno = FALSE;

    wbfs_t *p_dst = wbfs_try_open_partition(destino , 0);
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
        wbfs_close(p_dst);
    }
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
    printf("\t%s -p /dev/sdxY check IDGAME\n" , argv[0]);
    printf("\t%s -p /dev/sdxY ls IDGAME\n" , argv[0]);
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

    while ((opt = getopt(argc, argv, "p:h")) != -1)
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

    if( noFormatear == FALSE )
    {
        printf(" ** Converting %s to FAT32 to WBFS **\n", partition);
        printf(" ** Formating %s to FAT32 **\n", partition);
        char comando1[100] = "umount ";
        strcat (comando1, partition);
        int ret = system(comando1);

        char comando2[100] = "mkdosfs -n WiithonDEV -v -s 8 -F 32 "; // 100: se reserva espacio extra
        strcat (comando2, partition);
        ret = system(comando2);
        if(ret == 0)
        {
            printf(" ** Formated %s as FAT32 **\n" , partition);
            printf(" ** Formating %s to WBFS **\n", partition);
        }
        else
        {
            printf(" ** Don't format. Error %d **\n" , ret);
            noFormatear = TRUE;
        }
    }

    wbfs_t *p = wbfs_try_open_partition( partition, noFormatear );
    if(p != NULL)
    {
        if ( noFormatear == FALSE )
        {
            printf(" ** Formated %s as WBFS **\n" , partition);
            retorno = TRUE;
        }
        else if(numParametros == 0)
        {
            printf("%d\n", numParametros);
            retorno = uso(argv);
        }
        else if ((numParametros == 1) && (strcmp(argv[optind], "ls") == 0))
        {
            retorno = wiithon_wrapper_ls(p);
        }
        else if ((numParametros == 2) && (strcmp(argv[optind], "ls") == 0))
        {
            retorno = wiithon_wrapper_ls_idgame(p, (u8*)argv[4]);
        }
        else if ((numParametros == 2) && (strcmp(argv[optind], "check") == 0))
        {
            retorno = wiithon_wrapper_check_idgame(p, (u8*)argv[4]);
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
            printf("No se ejecuto el comando '%s'\n" , argv[optind]);
        }
        wbfs_close(p);
    }
    else
    {
        printf("Wrapper hecho para wiithon por Ricardo Marmolejo García <makiolo@gmail.com>\n");
        printf("No se ha facilitado ninguna partición WBFS.\n");
        printf("Para más ayuda:\n\t%s -h\n" , argv[0]);
        printf("No obstante, este wrapper esta pensado para ser usado por wiithon, y por tanto no se realizan unas serie de comprobaciones, debido a que se asume que los datos han sido verificados previamente por wiithon.\n");
    }
    exit(retorno);
}
