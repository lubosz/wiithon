// modified by Ricardo Marmolejo García <makiolo@gmail.com>

#ifndef LIBWBFS_OS_H
#define LIBWBFS_OS_H

// this file abstract the os integration
// libwbfs_glue.h for segher tools env.

// standard u8, u32 and co types, + fatal
//#include "tools.h"
#include <stdio.h>


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


// añadido por makiolo
#define OK 0
#define TRUE 0

#define FALSE 1

// constantes cogidas del libwbfs del usbloader GX
#define KB_SIZE		1024.0
#define MB_SIZE		1048576.0
#define GB_SIZE		1073741824.0

#define wbfs_fatal(x) fatal(x)
#define wbfs_error(x) fatal(x)

#include <stdlib.h>
#define wbfs_malloc(x) malloc(x)
#define wbfs_free(x) free(x)

// alloc memory space suitable for disk io
#define wbfs_ioalloc(x) malloc(x)
#define wbfs_iofree(x) free(x)

 #include <arpa/inet.h>

// endianess tools
#define wbfs_ntohl(x) ntohl(x)
#define wbfs_ntohs(x) ntohs(x)
#define wbfs_htonl(x) htonl(x)
#define wbfs_htons(x) htons(x)

#include <string.h>
#define wbfs_memcmp(x,y,z) memcmp(x,y,z)
#define wbfs_memcpy(x,y,z) memcpy(x,y,z)
#define wbfs_memset(x,y,z) memset(x,y,z)

#endif
