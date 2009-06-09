// Copyright 2007,2008  Segher Boessenkool  <segher@kernel.crashing.org>
// Modified by makiolo <makiolo@gmail.com>
// Licensed under the terms of the GNU GPL, version 2
// http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt

#ifndef _TOOLS_H
#define _TOOLS_H

/*+----------------------------------------------------------------------------------------------+*/
typedef unsigned char u8;									///< 8bit unsigned integer
typedef unsigned short u16;								///< 16bit unsigned integer
typedef unsigned int u32;									///< 32bit unsigned integer
typedef unsigned long long u64;						///< 64bit unsigned integer
/*+----------------------------------------------------------------------------------------------+*/
typedef signed char s8;										///< 8bit signed integer
typedef signed short s16;									///< 16bit signed integer
typedef signed int s32;										///< 32bit signed integer
typedef signed long long s64;							///< 64bit signed integer
/*+----------------------------------------------------------------------------------------------+*/
typedef volatile unsigned char vu8;				///< 8bit unsigned volatile integer
typedef volatile unsigned short vu16;			///< 16bit unsigned volatile integer
typedef volatile unsigned int vu32;				///< 32bit unsigned volatile integer
typedef volatile unsigned long long vu64;	///< 64bit unsigned volatile integer
/*+----------------------------------------------------------------------------------------------+*/
typedef volatile signed char vs8;					///< 8bit signed volatile integer
typedef volatile signed short vs16;				///< 16bit signed volatile integer
typedef volatile signed int vs32;					///< 32bit signed volatile integer
typedef volatile signed long long vs64;		///< 64bit signed volatile integer
/*+----------------------------------------------------------------------------------------------+*/
// fixed point math typedefs
typedef s16 sfp16;                              ///< 1:7:8 fixed point
typedef s32 sfp32;                              ///< 1:19:8 fixed point
typedef u16 ufp16;                              ///< 8:8 fixed point
typedef u32 ufp32;                              ///< 24:8 fixed point
/*+----------------------------------------------------------------------------------------------+*/
typedef float f32;
typedef double f64;
/*+----------------------------------------------------------------------------------------------+*/
typedef volatile float vf32;
typedef volatile double vf64;
/*+----------------------------------------------------------------------------------------------+*/


u16 be16(const u8 *p);
u32 be32(const u8 *p);
u64 be64(const u8 *p);
u64 be34(const u8 *p);

void wbe16(u8 *p, u16 x);
void wbe32(u8 *p, u32 x);
void wbe64(u8 *p, u64 x);

//#define round_down(x,n) ((x) & -(n))
#define round_up(x,n) (-(-(x) & -(n)))

// bignum
int bn_compare(u8 *a, u8 *b, u32 n);
void bn_sub_modulus(u8 *a, u8 *N, u32 n);
void bn_add(u8 *d, u8 *a, u8 *b, u8 *N, u32 n);
void bn_mul(u8 *d, u8 *a, u8 *b, u8 *N, u32 n);
void bn_inv(u8 *d, u8 *a, u8 *N, u32 n);	// only for prime N
void bn_exp(u8 *d, u8 *a, u8 *N, u32 n, u8 *e, u32 en);

// crypto
void md5(u8 *data, u32 len, u8 *hash);
void sha(u8 *data, u32 len, u8 *hash);
void get_key(const char *name, u8 *key, u32 len);
void aes_cbc_dec(u8 *key, u8 *iv, u8 *in, u32 len, u8 *out);
void aes_cbc_enc(u8 *key, u8 *iv, u8 *in, u32 len, u8 *out);
void decrypt_title_key(u8 *tik, u8 *title_key);
int check_cert_chain(u8 *data, u32 data_len, u8 *cert, u32 cert_len);
int check_ec(u8 *ng, u8 *ap, u8 *sig, u8 *sig_hash);
void generate_ecdsa(u8 *R, u8 *S, u8 *k, u8 *hash);
int check_ecdsa(u8 *Q, u8 *R, u8 *S, u8 *hash);
void ec_priv_to_pub(u8 *k, u8 *Q);

// compression
void do_yaz0(u8 *in, u32 in_size, u8 *out, u32 out_size);

// error handling
void fatal(const char *s, ...);

// output formatting
void print_bytes(u8 *x, u32 n);
void hexdump(u8 *x, u32 n);
void dump_tmd(u8 *tmd);
void spinner(u64 x, u64 max);

#endif
