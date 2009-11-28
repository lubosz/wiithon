// Copyright 2009 Kwiirk
// modified by Ricardo Marmolejo García <makiolo@gmail.com>
// copy 1on1 by Pier-Luc Duchaine <pierduch@gmail.com>
// Licensed under the terms of the GNU GPL, version 2
// http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt

#include "libwbfs.h"

#define likely(x)       __builtin_expect(!!(x), 1)
#define unlikely(x)     __builtin_expect(!!(x), 0)

#define ERROR(x) do {wbfs_error(x);goto error;}while(0)
#define ALIGN_LBA(x) (((x)+p->hd_sec_sz-1)&(~(p->hd_sec_sz-1)))
static int force_mode=0;
void wbfs_set_force_mode(int force)
{
		force_mode = force;
}
static u8 size_to_shift(u32 size)
{
		u8 ret = 0;
		while(size)
		{
				ret++;
				size>>=1;
		}
		return ret-1;
}
#define read_le32_unaligned(x) ((x)[0]|((x)[1]<<8)|((x)[2]<<16)|((x)[3]<<24))


wbfs_t*wbfs_open_hd(rw_sector_callback_t read_hdsector,
				rw_sector_callback_t write_hdsector,
				void *callback_data,
				int hd_sector_size, int num_hd_sector __attribute((unused)), int reset)
{
		int i=num_hd_sector,ret;
		u8 *ptr,*tmp_buffer = wbfs_ioalloc(hd_sector_size);
		u8 part_table[16*4];
		ret = read_hdsector(callback_data,0,1,tmp_buffer);
		if(ret)
				return 0;
		//find wbfs partition
		wbfs_memcpy(part_table,tmp_buffer+0x1be,16*4);
		ptr = part_table;
		for(i=0;i<4;i++,ptr+=16)
		{
				u32 part_lba = read_le32_unaligned(ptr+0x8);
				wbfs_head_t *head = (wbfs_head_t *)tmp_buffer;
				ret = read_hdsector(callback_data,part_lba,1,tmp_buffer);
				// verify there is the magic.
				if (head->magic == wbfs_htonl(WBFS_MAGIC))
				{
						wbfs_t*p = wbfs_open_partition(read_hdsector,write_hdsector,
										callback_data,hd_sector_size,0,part_lba,reset);
						return p;
				}
		}
		if(reset)// XXX make a empty hd partition..
		{
		}
		return 0;
}
wbfs_t*wbfs_open_partition(rw_sector_callback_t read_hdsector,
				rw_sector_callback_t write_hdsector,
				void *callback_data,
				int hd_sector_size, int num_hd_sector, u32 part_lba, int reset)
{
		wbfs_t *p = wbfs_malloc(sizeof(wbfs_t));

		wbfs_head_t *head = wbfs_ioalloc(hd_sector_size?hd_sector_size:512);

		//constants, but put here for consistancy
		p->wii_sec_sz = 0x8000;
		p->wii_sec_sz_s = size_to_shift(0x8000);
		p->n_wii_sec = (num_hd_sector/0x8000)*hd_sector_size;
		p->n_wii_sec_per_disc = 143432*2;//support for double layers discs..
		p->head = head;
		p->part_lba = part_lba;
		// init the partition
		if (reset)
		{
				u8 sz_s;
				wbfs_memset(head,0,hd_sector_size);
				head->magic = wbfs_htonl(WBFS_MAGIC);
				head->hd_sec_sz_s = size_to_shift(hd_sector_size);
				head->n_hd_sec = wbfs_htonl(num_hd_sector);
				// choose minimum wblk_sz that fits this partition size
				for(sz_s=6;sz_s<11;sz_s++)
				{
						// ensure that wbfs_sec_sz is big enough to address every blocks using 16 bits
						if(p->n_wii_sec <((1U<<16)*(1<<sz_s)))
								break;
				}
				head->wbfs_sec_sz_s = sz_s+p->wii_sec_sz_s;
		}else
				read_hdsector(callback_data,p->part_lba,1,head);
		if (head->magic != wbfs_htonl(WBFS_MAGIC))
				ERROR("bad magic");
		if(!force_mode && hd_sector_size && head->hd_sec_sz_s !=  size_to_shift(hd_sector_size))
				ERROR("hd sector size doesn't match");
		if(!force_mode && num_hd_sector && head->n_hd_sec != wbfs_htonl(num_hd_sector))
				ERROR("hd num sector doesn't match");
		p->hd_sec_sz = 1<<head->hd_sec_sz_s;
		p->hd_sec_sz_s = head->hd_sec_sz_s;
		p->n_hd_sec = wbfs_ntohl(head->n_hd_sec);

		p->n_wii_sec = (p->n_hd_sec/p->wii_sec_sz)*(p->hd_sec_sz);

		p->wbfs_sec_sz_s = head->wbfs_sec_sz_s;
		p->wbfs_sec_sz = 1<<p->wbfs_sec_sz_s;
		p->n_wbfs_sec = p->n_wii_sec >> (p->wbfs_sec_sz_s - p->wii_sec_sz_s);
		p->n_wbfs_sec_per_disc = p->n_wii_sec_per_disc >> (p->wbfs_sec_sz_s - p->wii_sec_sz_s);
		p->disc_info_sz = ALIGN_LBA(sizeof(wbfs_disc_info_t) + p->n_wbfs_sec_per_disc*2);

		//printf("hd_sector_size %X wii_sector size %X wbfs sector_size %X\n",p->hd_sec_sz,p->wii_sec_sz,p->wbfs_sec_sz);
		p->read_hdsector = read_hdsector;
		p->write_hdsector = write_hdsector;
		p->callback_data = callback_data;

		p->freeblks_lba = (p->wbfs_sec_sz - p->n_wbfs_sec/8)>>p->hd_sec_sz_s;

		if(!reset)
				p->freeblks = 0; // will alloc and read only if needed
		else
		{
				// init with all free blocks
				p->freeblks = wbfs_ioalloc(ALIGN_LBA(p->n_wbfs_sec/8));
				wbfs_memset(p->freeblks,0xff,p->n_wbfs_sec/8);
		}
		p->max_disc = (p->freeblks_lba-1)/(p->disc_info_sz>>p->hd_sec_sz_s);
		if(p->max_disc > p->hd_sec_sz - sizeof(wbfs_head_t))
				p->max_disc = p->hd_sec_sz - sizeof(wbfs_head_t);

		p->tmp_buffer = wbfs_ioalloc(p->hd_sec_sz);
		p->n_disc_open = 0;
		//wbfs_sync(p);
		return p;
error:
		wbfs_free(p);
		wbfs_iofree(head);
		return 0;

}

void wbfs_sync(wbfs_t*p)
{
		// copy back descriptors
		if(p->write_hdsector){
				p->write_hdsector(p->callback_data,p->part_lba+0,1, p->head);

				if(p->freeblks)
						p->write_hdsector(p->callback_data,p->part_lba+p->freeblks_lba,ALIGN_LBA(p->n_wbfs_sec/8)>>p->hd_sec_sz_s, p->freeblks);
		}
}
void wbfs_close(wbfs_t*p)
{
		wbfs_sync(p);

		if(p->n_disc_open)
				ERROR("trying to close wbfs while discs still open");

		wbfs_iofree(p->head);
		wbfs_iofree(p->tmp_buffer);
		if(p->freeblks)
				wbfs_iofree(p->freeblks);

		wbfs_free(p);

error:
		return;
}

wbfs_disc_t *wbfs_open_disc(wbfs_t* p, u8 *discid)
{
		u32 i;
		int disc_info_sz_lba = p->disc_info_sz>>p->hd_sec_sz_s;
		wbfs_disc_t *d = 0;
		for(i=0;i<p->max_disc;i++)
		{
				if (p->head->disc_table[i]){
						p->read_hdsector(p->callback_data,
										p->part_lba+1+i*disc_info_sz_lba,1,p->tmp_buffer);
						if(wbfs_memcmp(discid,p->tmp_buffer,6)==0){
								d = wbfs_malloc(sizeof(*d));
								if(!d)
										ERROR("allocating memory");
								d->p = p;
								d->i = i;
								d->header = wbfs_ioalloc(p->disc_info_sz);
								if(!d->header)
										ERROR("allocating memory");
								p->read_hdsector(p->callback_data,
												p->part_lba+1+i*disc_info_sz_lba,
												disc_info_sz_lba,d->header);
								p->n_disc_open ++;
								//                                for(i=0;i<p->n_wbfs_sec_per_disc;i++)
								//                                        printf("%d,",wbfs_ntohs(d->header->wlba_table[i]));
								return d;
						}
				}
		}
		return 0;
error:
		if(d)
				wbfs_iofree(d);
		return 0;

}
void wbfs_close_disc(wbfs_disc_t*d)
{
		d->p->n_disc_open --;
		wbfs_iofree(d->header);
		wbfs_free(d);
}
// offset is pointing 32bit words to address the whole dvd, although len is in bytes
int wbfs_disc_read(wbfs_disc_t*d,u32 offset, u8 *data, u32 len)
{

		wbfs_t *p = d->p;
		u16 wlba = offset>>(p->wbfs_sec_sz_s-2);
		u32 iwlba_shift = p->wbfs_sec_sz_s - p->hd_sec_sz_s;
		u32 lba_mask = (p->wbfs_sec_sz-1)>>(p->hd_sec_sz_s);
		u32 lba = (offset>>(p->hd_sec_sz_s-2))&lba_mask;
		u32 off = offset&((p->hd_sec_sz>>2)-1);
		u16 iwlba = wbfs_ntohs(d->header->wlba_table[wlba]);
		u32 len_copied;
		int err = 0;
		u8  *ptr = data;
		if(unlikely(iwlba==0))
				return 1;
		if(unlikely(off)){
				off*=4;
				err = p->read_hdsector(p->callback_data,
								p->part_lba + (iwlba<<iwlba_shift) + lba, 1, p->tmp_buffer);
				if(err)
						return err;
				len_copied = p->hd_sec_sz - off;
				if(likely(len < len_copied))
						len_copied = len;
				wbfs_memcpy(ptr, p->tmp_buffer + off, len_copied);
				len -= len_copied;
				ptr += len_copied;
				lba++;
				if(unlikely(lba>lba_mask && len)){
						lba=0;
						iwlba =  wbfs_ntohs(d->header->wlba_table[++wlba]);
						if(unlikely(iwlba==0))
								return 1;
				}
		}
		while(likely(len>=p->hd_sec_sz))
		{
				u32 nlb = len>>(p->hd_sec_sz_s);

				if(unlikely(lba + nlb > p->wbfs_sec_sz)) // dont cross wbfs sectors..
						nlb = p->wbfs_sec_sz-lba;
				err = p->read_hdsector(p->callback_data,
								p->part_lba + (iwlba<<iwlba_shift) + lba, nlb, ptr);
				if(err)
						return err;
				len -= nlb<<p->hd_sec_sz_s;
				ptr += nlb<<p->hd_sec_sz_s;
				lba += nlb;
				if(unlikely(lba>lba_mask && len)){
						lba = 0;
						iwlba =wbfs_ntohs(d->header->wlba_table[++wlba]);
						if(unlikely(iwlba==0))
								return 1;
				}
		}
		if(unlikely(len)){
				err = p->read_hdsector(p->callback_data,
								p->part_lba + (iwlba<<iwlba_shift) + lba, 1, p->tmp_buffer);
				if(err)
						return err;
				wbfs_memcpy(ptr, p->tmp_buffer, len);
		}
		return 0;
}

// disc listing
u32 wbfs_count_discs(wbfs_t*p)
{
		u32 i,count=0;
		for(i=0;i<p->max_disc;i++)
				if (p->head->disc_table[i])
						count++;
		return count;

}
u32 wbfs_sector_used(wbfs_t *p,wbfs_disc_info_t *di)
{
		u32 tot_blk=0,j;
		for(j=0;j<p->n_wbfs_sec_per_disc;j++)
				if(wbfs_ntohs(di->wlba_table[j]))
						tot_blk++;
		return tot_blk;

}
u32 wbfs_get_disc_info(wbfs_t*p, u32 index,u8 *header,int header_size,u32 *size)//size in 32 bit
{
		u32 i, count=0;
		int disc_info_sz_lba = p->disc_info_sz>>p->hd_sec_sz_s;
		for(i=0;i<p->max_disc;i++)
				if (p->head->disc_table[i]){
						if(count++==index)
						{
								p->read_hdsector(p->callback_data,
												p->part_lba+1+i*disc_info_sz_lba,1,p->tmp_buffer);
								if(header_size > (int)p->hd_sec_sz)
										header_size = p->hd_sec_sz;
								u32 magic = wbfs_ntohl(*(u32*)(p->tmp_buffer+24));
								if(magic!=0x5D1C9EA3){
										p->head->disc_table[i]=0;
										return 1;
								}
								memcpy(header,p->tmp_buffer,header_size);
								if(size)
								{
										u8 *header = wbfs_ioalloc(p->disc_info_sz);
										p->read_hdsector(p->callback_data,
														p->part_lba+1+i*disc_info_sz_lba,disc_info_sz_lba,header);
										u32 sec_used = wbfs_sector_used(p,(wbfs_disc_info_t *)header);
										wbfs_iofree(header);
										*size = sec_used<<(p->wbfs_sec_sz_s-2);
								}
								return 0;
						}
				}
		return 1;
}

static void load_freeblocks(wbfs_t*p)
{
		if(p->freeblks)
				return;
		// XXX should handle malloc error..
		p->freeblks = wbfs_ioalloc(ALIGN_LBA(p->n_wbfs_sec/8));
		p->read_hdsector(p->callback_data,p->part_lba+p->freeblks_lba,ALIGN_LBA(p->n_wbfs_sec/8)>>p->hd_sec_sz_s, p->freeblks);

}
u32 wbfs_count_usedblocks(wbfs_t*p)
{
		u32 i,j,count=0;
		load_freeblocks(p);
		for(i=0;i<p->n_wbfs_sec/(8*4);i++)
		{
				u32 v = wbfs_ntohl(p->freeblks[i]);
				if(v == ~0U)
						count+=32;
				else if(v!=0)
						for(j=0;j<32;j++)
								if (v & (1<<j))
										count++;
		}
		return count;
}


// write access


static int block_used(u8 *used,u32 i,u32 wblk_sz)
{
		u32 k;
		i*=wblk_sz;
		for(k=0;k<wblk_sz;k++)
				if(i+k<143432*2 && used[i+k])
						return 1;
		return 0;
}

static u32 alloc_block(wbfs_t*p)
{
		u32 i,j;
		for(i=0;i<p->n_wbfs_sec/(8*4);i++)
		{
				u32 v = wbfs_ntohl(p->freeblks[i]);
				if(v != 0)
				{
						for(j=0;j<32;j++)
								if (v & (1<<j))
								{
										p->freeblks[i] = wbfs_htonl(v & ~(1<<j));
										return (i*32)+j+1;
								}
				}
		}
		return ~0;
}
static void free_block(wbfs_t *p,int bl)
{
		int i = (bl-1)/(32);
		int j = (bl-1)&31;
		u32 v = wbfs_ntohl(p->freeblks[i]);
		p->freeblks[i] = wbfs_htonl(v | 1<<j);
}
u32 wbfs_add_disc(wbfs_t*p,read_wiidisc_callback_t read_src_wii_disc,
				void *callback_data,progress_callback_t spinner,partition_selector_t sel,int copy_1_1)
{
		int i,discn;
		u32 tot,cur;
		u32 wii_sec_per_wbfs_sect = 1<<(p->wbfs_sec_sz_s-p->wii_sec_sz_s);
		wiidisc_t *d = 0;
		u8 *used = 0;
		wbfs_disc_info_t *info = 0;
		u8* copy_buffer = 0;
		used = wbfs_malloc(p->n_wii_sec_per_disc);
		time_t last_time = 0;
		time_t time_now = 0;
		if(!used)
				ERROR("unable to alloc memory");
		if(!copy_1_1)
		{
				d = wd_open_disc(read_src_wii_disc,callback_data);
				if(!d)
						ERROR("unable to open wii disc");
				wd_build_disc_usage(d,sel,used);
				wd_close_disc(d);
				d = 0;
		}


		for(i=0;i<p->max_disc;i++)// find a free slot.
				if(p->head->disc_table[i]==0)
						break;
		if(i==p->max_disc)
				ERROR("no space left on device (table full)");
		p->head->disc_table[i] = 1;
		discn = i;
		load_freeblocks(p);

		// build disc info
		info = wbfs_ioalloc(p->disc_info_sz);
		read_src_wii_disc(callback_data,0,0x100,info->disc_header_copy);

		copy_buffer = wbfs_ioalloc(p->wii_sec_sz);
		if(!copy_buffer)
				ERROR("alloc memory");
		tot=0;
		cur=0;
		if(spinner){
				// count total number to write for spinner
				for(i=0; i<p->n_wbfs_sec_per_disc;i++)
						if(copy_1_1 || block_used(used,i,wii_sec_per_wbfs_sect)) tot += wii_sec_per_wbfs_sect;
				spinner(0,tot);
		}
		for(i=0; i<p->n_wbfs_sec_per_disc;i++){
				u16 bl = 0;
				if(copy_1_1 || block_used(used,i,wii_sec_per_wbfs_sect)) {
						u16 j;

						bl = alloc_block(p);
						if (bl==0xffff)
								ERROR("no space left on device (disc full)");
						for(j=0; j<wii_sec_per_wbfs_sect;j++) {
								u32 offset = (i*(p->wbfs_sec_sz>>2)) + (j*(p->wii_sec_sz>>2));

								read_src_wii_disc(callback_data,offset,p->wii_sec_sz,copy_buffer);

								//fix the partition table
								if(offset == (0x40000>>2))
										wd_fix_partition_table(d, sel, copy_buffer);
								p->write_hdsector(p->callback_data,p->part_lba+bl*(p->wbfs_sec_sz/p->hd_sec_sz)+j*(p->wii_sec_sz/p->hd_sec_sz), p->wii_sec_sz/p->hd_sec_sz,copy_buffer);
								cur++;
						}
						if(spinner) {
								if(last_time == 0)
										time(&last_time);

								time(&time_now);
								/* Update that crap only every 0.5 secs */
								if (difftime(time_now,last_time) > 0.1) {
										spinner(cur,tot);
										last_time = 0;
								}
						}
				}
				info->wlba_table[i] = wbfs_htons(bl);
		}
		// write disc info
		int disc_info_sz_lba = p->disc_info_sz>>p->hd_sec_sz_s;
		p->write_hdsector(p->callback_data,p->part_lba+1+discn*disc_info_sz_lba,disc_info_sz_lba,info);
		wbfs_sync(p);
error:
		if(d)
				wd_close_disc(d);
		if(used)
				wbfs_free(used);
		if(info)
				wbfs_iofree(info);
		if(copy_buffer)
				wbfs_iofree(copy_buffer);
		// init with all free blocks

		return 0;
}

u32 wbfs_rm_disc(wbfs_t*p, u8* discid)
{
		wbfs_disc_t *d = wbfs_open_disc(p,discid);
		int i;
		int discn = 0;
		int disc_info_sz_lba = p->disc_info_sz>>p->hd_sec_sz_s;
		if(!d)
				return FALSE;
		load_freeblocks(p);
		discn = d->i;
		for( i=0; i< p->n_wbfs_sec_per_disc; i++)
		{
				u32 iwlba = wbfs_ntohs(d->header->wlba_table[i]);
				if (iwlba)
						free_block(p,iwlba);
		}
		memset(d->header,0,p->disc_info_sz);
		p->write_hdsector(p->callback_data,p->part_lba+1+discn*disc_info_sz_lba,disc_info_sz_lba,d->header);
		p->head->disc_table[discn] = 0;
		wbfs_close_disc(d);
		wbfs_sync(p);
		return TRUE;
}

u32 wbfs_ren_disc(wbfs_t *p, u8 *discid, char *newname)
{
		wbfs_disc_t *d = wbfs_open_disc(p,discid);
		int disc_info_sz_lba = p->disc_info_sz>>p->hd_sec_sz_s;

		if(d)
		{
				memset(d->header->disc_header_copy+0x20, 0, 0x80);
				strncpy((char *) d->header->disc_header_copy+0x20, (char*)newname, 0x80);

				p->write_hdsector(p->callback_data,p->part_lba+1+d->i*disc_info_sz_lba,disc_info_sz_lba,d->header);
				wbfs_close_disc(d);
				return TRUE;
		}
		else
				return FALSE;
}

u32 wbfs_ren_idgame(wbfs_t *p, u8 *discid, u8 *nuevoid)
{
		wbfs_disc_t *d = wbfs_open_disc(p,discid);
		int disc_info_sz_lba = p->disc_info_sz>>p->hd_sec_sz_s;

		if(d)
		{
				memcpy(d->header->disc_header_copy+0x0, nuevoid, 0x6);
				strncpy((char *) d->header->disc_header_copy+0x0, (char*) nuevoid, 0x6);

				p->write_hdsector(p->callback_data,p->part_lba+1+d->i*disc_info_sz_lba,disc_info_sz_lba,d->header);
				wbfs_close_disc(d);
				return TRUE;
		}
		else
				return FALSE;
}


// trim the file-system to its minimum size
u32 wbfs_trim(wbfs_t*p);

// data extraction
u32 wbfs_extract_disc(wbfs_disc_t*d, rw_sector_callback_t write_dst_wii_sector,void *callback_data,progress_callback_t spinner)
{
		wbfs_t *p = d->p;
		u8* copy_buffer = 0;
		int i;
		int src_wbs_nlb=p->wbfs_sec_sz/p->hd_sec_sz;
		int dst_wbs_nlb=p->wbfs_sec_sz/p->wii_sec_sz;
		copy_buffer = wbfs_ioalloc(p->wbfs_sec_sz);
		if(!copy_buffer)
				ERROR("alloc memory");

		// calcular verdadero MAX
		int max = 0;
		for( i=0; i< p->n_wbfs_sec_per_disc; i++)
		{
				u32 iwlba = wbfs_ntohs(d->header->wlba_table[i]);
				if (iwlba)
				{
						if(i > max)
						{
								max = i;
						}
				}	
		}
		// fin calculo

		for( i=0; i< p->n_wbfs_sec_per_disc; i++)
		{
				u32 iwlba = wbfs_ntohs(d->header->wlba_table[i]);
				if (iwlba)
				{
						p->read_hdsector(p->callback_data, p->part_lba + iwlba*src_wbs_nlb, src_wbs_nlb, copy_buffer);
						write_dst_wii_sector(callback_data, i*dst_wbs_nlb, dst_wbs_nlb, copy_buffer);
				}
				if(spinner)
				{
						spinner(i,max);
				}
		}
		
		if(spinner)
		{
			spinner(p->n_wbfs_sec_per_disc,p->n_wbfs_sec_per_disc);
		}
		
		wbfs_iofree(copy_buffer);
		return TRUE;
error:
		return FALSE;
}
u32 wbfs_extract_file(wbfs_disc_t*d, char *path);

float wbfs_estimate_disc
(
 wbfs_t *p, read_wiidisc_callback_t read_src_wii_disc,
 void *callback_data,
 partition_selector_t sel)
{
		u8 *b;
		int i;
		u32 tot;
		u32 wii_sec_per_wbfs_sect = 1 << (p->wbfs_sec_sz_s-p->wii_sec_sz_s);
		wiidisc_t *d = 0;
		u8 *used = 0;
		wbfs_disc_info_t *info = 0;

		tot = 0;

		used = wbfs_malloc(p->n_wii_sec_per_disc);
		if (!used)
		{
				ERROR("unable to alloc memory");
		}

		d = wd_open_disc(read_src_wii_disc, callback_data);
		if (!d)
		{
				ERROR("unable to open wii disc");
		}

		wd_build_disc_usage(d,sel,used);
		wd_close_disc(d);
		d = 0;

		info = wbfs_ioalloc(p->disc_info_sz);
		b = (u8 *)info;
		read_src_wii_disc(callback_data, 0, 0x100, info->disc_header_copy);

		//fprintf(stderr, "estimating %c%c%c%c%c%c %s...\n",b[0], b[1], b[2], b[3], b[4], b[5], b + 0x20);

		for (i = 0; i < p->n_wbfs_sec_per_disc; i++)
		{
				if (block_used(used, i, wii_sec_per_wbfs_sect))
				{
						tot++;
				}
		}
		//memcpy(header, b, 0x100);

error:
		if (d)
				wd_close_disc(d);

		if (used)
				wbfs_free(used);

		if (info)
				wbfs_iofree(info);

		return tot * (((p->wbfs_sec_sz*1.0) / p->hd_sec_sz) * 512);
}


// wbfsGUI v14.1 Pier-Luc Duchaine <pierduch@gmail.com>
unsigned int wbfs_copy_disc(wbfs_disc_t*d_src, wbfs_t*p_dst, progress_callback_t spinner)
{
		int retorno = FALSE;

		wbfs_t *p_src = d_src->p;
		unsigned char* copy_buffer = 0;
		unsigned char* dst_copy_buffer = 0;
		int i;

		unsigned int src_wbs_nlb=p_src->wbfs_sec_sz/p_src->hd_sec_sz;
		unsigned int dst_wbs_nlb=p_dst->wbfs_sec_sz/p_dst->hd_sec_sz;
		
		wbfs_disc_info_t *info = NULL;

		if( src_wbs_nlb%dst_wbs_nlb != 0 && dst_wbs_nlb%src_wbs_nlb != 0)
		{
				ERROR("Difference between source and dest");
		}

		int n_src_in_dst = 1;
		int n_dst_in_src = 1;

		if( src_wbs_nlb > dst_wbs_nlb )
		{
				n_dst_in_src = src_wbs_nlb / dst_wbs_nlb;
		}
		else
		{
				n_src_in_dst = dst_wbs_nlb / src_wbs_nlb;
		}

		copy_buffer = (unsigned char*)wbfs_ioalloc(p_src->wbfs_sec_sz);
		if(!copy_buffer)
		{
				ERROR("alloc memory");
		}

		for(i=0;i<p_dst->max_disc;i++)// find a free slot.
				if(p_dst->head->disc_table[i]==0)
						break;
		if(i==p_dst->max_disc)
		{
				ERROR("no space left on device (table full)");
		}
		p_dst->head->disc_table[i] = 1;
		int discn = i;
		load_freeblocks(p_dst);

		info = (wbfs_disc_info_t*)wbfs_ioalloc(p_dst->disc_info_sz);
		memset(info, 0, p_dst->disc_info_sz);

		memcpy(info->disc_header_copy, d_src->header->disc_header_copy, 0x100);

		if( src_wbs_nlb == dst_wbs_nlb)
		{
				for( i=0; i< p_src->n_wbfs_sec_per_disc; i++)
				{
						unsigned int iwlba = wbfs_ntohs(d_src->header->wlba_table[i]);
						unsigned short bl = 0;
						if (iwlba)
						{
								bl = alloc_block(p_dst);
								if (bl==0xffff)
								{
										ERROR("no space left on device (disc full)");
								}

								p_src->read_hdsector( p_src->callback_data, p_src->part_lba + iwlba*src_wbs_nlb, src_wbs_nlb, copy_buffer);
								p_dst->write_hdsector(p_dst->callback_data, p_dst->part_lba +    bl*dst_wbs_nlb, dst_wbs_nlb, copy_buffer);
						}

						info->wlba_table[i] = wbfs_htons(bl);

						if(spinner)
								spinner(i,p_src->n_wbfs_sec_per_disc);
				}
		}
		else if (n_src_in_dst == 1)
		{
				int buf_dst_step = p_dst->wbfs_sec_sz;

				for( i=0; i< p_src->n_wbfs_sec_per_disc; i++)
				{
						unsigned int iwlba = wbfs_ntohs(d_src->header->wlba_table[i]);
						unsigned short bl = 0;
						if (iwlba)
						{
								p_src->read_hdsector( p_src->callback_data, p_src->part_lba + iwlba*src_wbs_nlb, src_wbs_nlb, copy_buffer);

								int l = 0;
								for( l = 0; l < n_dst_in_src; ++l)
								{
										bl = alloc_block(p_dst);
										if (bl==0xffff)
												ERROR("no space left on device (disc full)");

										p_dst->write_hdsector(p_dst->callback_data, p_dst->part_lba + bl*dst_wbs_nlb, dst_wbs_nlb, copy_buffer + l * buf_dst_step);

										info->wlba_table[i*n_dst_in_src+l] = wbfs_htons(bl);
								}
						}

						if(spinner)
								spinner(i,p_src->n_wbfs_sec_per_disc);
				}
		}
		else if (n_dst_in_src == 1)
		{
				dst_copy_buffer = (unsigned char*)wbfs_ioalloc(p_dst->wbfs_sec_sz);

				if(!dst_copy_buffer)
						ERROR("alloc memory");

				int buf_src_step = p_src->wbfs_sec_sz;
				int need_to_write = FALSE;

				for( i=0; i< p_src->n_wbfs_sec_per_disc; i++)
				{
						if(need_to_write==TRUE && i%n_src_in_dst == 0)
						{
								unsigned short bl = 0;

								bl = alloc_block(p_dst);
								if (bl==0xffff)
										ERROR("no space left on device (disc full)");

								p_dst->write_hdsector(p_dst->callback_data, p_dst->part_lba +    bl*dst_wbs_nlb, dst_wbs_nlb, dst_copy_buffer);
								info->wlba_table[(i/n_src_in_dst)-1] = wbfs_htons(bl);

								memset(dst_copy_buffer, 0, p_dst->wbfs_sec_sz);
								need_to_write = FALSE;
						}

						unsigned int iwlba = wbfs_ntohs(d_src->header->wlba_table[i]);
						if (iwlba)
						{
								p_src->read_hdsector( p_src->callback_data, p_src->part_lba + iwlba*src_wbs_nlb, src_wbs_nlb, dst_copy_buffer + (i%n_src_in_dst) * buf_src_step);
								need_to_write = TRUE;
						}

						if(spinner)
								spinner(i,p_src->n_wbfs_sec_per_disc);
				}

				if(need_to_write==TRUE)
				{
						unsigned short bl = 0;

						bl = alloc_block(p_dst);
						if (bl==0xffff)
						{
								printf("%d\n",bl);
								ERROR("no space left on device (disc full)");
						}

						p_dst->write_hdsector(p_dst->callback_data, p_dst->part_lba +    bl*dst_wbs_nlb, dst_wbs_nlb, dst_copy_buffer);
						info->wlba_table[(i/n_src_in_dst)-1] = wbfs_htons(bl);

						memset(dst_copy_buffer, 0, p_dst->wbfs_sec_sz);
						need_to_write = FALSE;
				}
		}

		if(spinner)
				spinner(p_src->n_wbfs_sec_per_disc,p_src->n_wbfs_sec_per_disc);

		// write disc info
		int disc_info_sz_lba = p_dst->disc_info_sz>>p_dst->hd_sec_sz_s;
		p_dst->write_hdsector(p_dst->callback_data, p_dst->part_lba+1+discn*disc_info_sz_lba,disc_info_sz_lba,info);
		wbfs_sync(p_dst);

		retorno = TRUE;

error:
		if(info)
				wbfs_iofree(info);
		if(copy_buffer)
				wbfs_iofree(copy_buffer);
		if(dst_copy_buffer)
				wbfs_iofree(dst_copy_buffer);


		// init with all free blocks

		return retorno;
}


void fatal(const char *s, ...)
{
		perror(s);
		exit(FALSE);
}

// Extract disk CISO
unsigned int wbfs_extract_disc_ciso(wbfs_disc_t*d, rw_sector_callback_t write_dst_wii_sector,void *callback_data,progress_callback_t spinner)
{
	wbfs_t *p = d->p;
	unsigned char* copy_buffer = 0;
	unsigned int i;
	unsigned int src_wbs_nlb=p->wbfs_sec_sz/p->hd_sec_sz;
	unsigned int dst_wbs_nlb=p->wbfs_sec_sz/p->wii_sec_sz;
	unsigned int offset=0;

	copy_buffer = (unsigned char*)wbfs_ioalloc(p->wbfs_sec_sz);
	if(!copy_buffer)
		ERROR("alloc memory");

	memset(copy_buffer,0,p->wbfs_sec_sz);
	copy_buffer[0]='C';
	copy_buffer[1]='I';
	copy_buffer[2]='S';
	copy_buffer[3]='O';

	i=dst_wbs_nlb<<15;

	copy_buffer[4]=i & 0xFF;
	copy_buffer[5]=(i>>8) & 0xFF;
	copy_buffer[6]=(i>>16) & 0xFF;
	copy_buffer[7]=(i>>24) & 0xFF;

	for( i=0; i< p->n_wbfs_sec_per_disc; i++)
	{
		if (wbfs_ntohs(d->header->wlba_table[i])) copy_buffer[i+8]=1;
		else copy_buffer[i+8]=0;
	}

	write_dst_wii_sector(callback_data, 0, 1, copy_buffer);

	offset=1;
	for( i=0; i< p->n_wbfs_sec_per_disc; i++)
	{
		unsigned int iwlba = wbfs_ntohs(d->header->wlba_table[i]);
		if (iwlba)
		{   
			if(spinner)
				spinner(i,p->n_wbfs_sec_per_disc);
			p->read_hdsector(p->callback_data, p->part_lba + iwlba*src_wbs_nlb, src_wbs_nlb, copy_buffer);
			write_dst_wii_sector(callback_data, offset, dst_wbs_nlb, copy_buffer);

			offset+=dst_wbs_nlb;
		}
	}

	wbfs_iofree(copy_buffer);
	return 0;
error:
	return 1;
}

unsigned int wbfs_add_ciso_disc(wbfs_t*p,read_wiidisc_callback_t read_src_wii_disc,
								void *callback_data,progress_callback_t spinner,partition_selector_t sel,int copy_1_1)
{
	int i,discn;
	unsigned int wii_sec_per_wbfs_sect = 1<<(p->wbfs_sec_sz_s-p->wii_sec_sz_s);
	unsigned char *used = 0;
	wbfs_disc_info_t *info = 0;
	unsigned char* copy_buffer = 0;
	used = (unsigned char*)wbfs_malloc(p->n_wii_sec_per_disc);

	if(!used)
		ERROR("unable to alloc memory");

	for(i=0;i<p->max_disc;i++)// find a free slot.
		if(p->head->disc_table[i]==0)
			break;

	if(i==p->max_disc)
		ERROR("no space left on device (table full)");

	p->head->disc_table[i] = 1;
	discn = i;
	load_freeblocks(p);

	copy_buffer = (unsigned char*)wbfs_ioalloc(p->wii_sec_sz);
	if(!copy_buffer)
		ERROR("alloc memory");

	int reading_offset = 0;
	read_src_wii_disc(callback_data, reading_offset, 0x8000, copy_buffer);
	reading_offset += 0x8000;

	//int block_size = (copy_buffer[7]<<24) + (copy_buffer[6]<<16) + (copy_buffer[5]<<8) + copy_buffer[4];

	for( i=8; i< 0x8000; i++)
	{
		if (copy_buffer[i]);
	}

	// build disc info
	info = (wbfs_disc_info_t*)wbfs_ioalloc(p->disc_info_sz);
	read_src_wii_disc(callback_data,reading_offset,0x100,info->disc_header_copy);

	for(i=0; i<p->n_wbfs_sec_per_disc;i++){
		unsigned short bl = 0;
		if(copy_1_1 || block_used(used,i,wii_sec_per_wbfs_sect)) {
			unsigned short j;

			bl = alloc_block(p);
			if (bl==0xffff)
				ERROR("no space left on device (disc full)");
			for(j=0; j<wii_sec_per_wbfs_sect;j++) {
				unsigned int offset = (i*(p->wbfs_sec_sz>>2)) + (j*(p->wii_sec_sz>>2));

				read_src_wii_disc(callback_data,offset,p->wii_sec_sz,copy_buffer);

				p->write_hdsector(p->callback_data,p->part_lba+bl*(p->wbfs_sec_sz/p->hd_sec_sz)+j*(p->wii_sec_sz/p->hd_sec_sz),
					p->wii_sec_sz/p->hd_sec_sz,copy_buffer);
			}
		}
				if(spinner)
					spinner(i,p->n_wbfs_sec_per_disc);

		info->wlba_table[i] = wbfs_htons(bl);
	}
	// write disc info
	int disc_info_sz_lba = p->disc_info_sz>>p->hd_sec_sz_s;
	p->write_hdsector(p->callback_data,p->part_lba+1+discn*disc_info_sz_lba,disc_info_sz_lba,info);
	wbfs_sync(p);
error:
	if(used)
		wbfs_free(used);
	if(info)
		wbfs_iofree(info);
	if(copy_buffer)
		wbfs_iofree(copy_buffer);
	// init with all free blocks

	return 0;
}

wbfs_disc_t *wbfs_open_index_disc(wbfs_t* p, u32 i)
{
	int disc_info_sz_lba = p->disc_info_sz>>p->hd_sec_sz_s;
	wbfs_disc_t *d = 0;

	if (p->head->disc_table[i])
	{
		p->read_hdsector(p->callback_data,
		p->part_lba+1+i*disc_info_sz_lba,1,p->tmp_buffer);

		d = wbfs_malloc(sizeof(*d));
		if(d)
		{
			d->p = p;
			d->i = i;
			d->header = wbfs_ioalloc(p->disc_info_sz);
			if(d->header)
			{
				p->read_hdsector(p->callback_data,
				p->part_lba+1+i*disc_info_sz_lba,
				disc_info_sz_lba,d->header);
				p->n_disc_open ++;
				return d;
			}
			else
			{
				if(d) wbfs_iofree(d);
				return NULL;       
			}
		}
		else
		{
			if(d) wbfs_iofree(d);
			return NULL;       
		}
	}
	else
	{
		return NULL;	
	}
}


u32 wbfs_integrity_check(wbfs_t* p , u8* discid)
{	
	u32 i2,n,m;
	u32 disc_info_sz_lba = p->disc_info_sz >> p->hd_sec_sz_s;
	u32 discn;

	char id1[7];
	char id2[7];

	load_freeblocks(p);

	wbfs_disc_t *d = wbfs_open_disc(p , discid);
	if(!d)
	{
		return FALSE;	
	}
	else
	{
		memcpy(id1,p->tmp_buffer,6);
		id1[6]='\0';

		u32 correcto = TRUE;
		i2 = 0;
		
		while( (correcto == TRUE) && i2<p->max_disc)
		{
			wbfs_disc_t * d2 = wbfs_open_index_disc(p, i2);
			if (d2 != NULL && d != d2)
			{
				memcpy(id2,p->tmp_buffer,6);
				id2[6]='\0';
				if( strcmp(id1 , id2) != 0 )
				{
					n = 0;
					while ( (correcto == TRUE) && n<p->n_wbfs_sec_per_disc )
					{
						u32 iwlba = wbfs_ntohs(d->header->wlba_table[n]);
						if (iwlba)
						{
							m = 0;
							while( (correcto == TRUE) && m<p->n_wbfs_sec_per_disc )
							{
								u32 iwlba2 = wbfs_ntohs(d2->header->wlba_table[m]);
								if(iwlba)
								{
									if(iwlba==iwlba2)
									{
										correcto = FALSE;
									}
								}
							m++;
							}
						}
					n++;
					}
				}
				wbfs_close_disc(d2);
			}
			i2++;
		}
		wbfs_close_disc(d);
		return correcto;			
	}
}

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
