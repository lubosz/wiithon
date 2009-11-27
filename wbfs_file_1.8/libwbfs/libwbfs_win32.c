#if defined(WIN32) || defined(__CYGWIN__)

#include <windows.h>
#include <winioctl.h>
#include <setupapi.h>
#include <io.h>

#include <stdio.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <string.h>
#include <fcntl.h>
#include <ctype.h>

#if defined(__CYGWIN__)
#define _get_osfhandle get_osfhandle
typedef long long off64_t;
#endif

#include "libwbfs.h"

void print_error(char *devname)
{
	LPVOID lpMsgBuf;
	DWORD err = GetLastError();
	FormatMessage( 
			FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM,
			NULL, err,
			MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT), // Default language
			(LPTSTR) &lpMsgBuf, 0, NULL );
	printf("%s", devname);
	printf("Error: (%d) %s", (int)err, (char*)lpMsgBuf);
}

int file_truncate(int fd, off64_t length)
{
	int ret;
	HANDLE fh;
	fh = (HANDLE)_get_osfhandle(fd);
	if (fh == INVALID_HANDLE_VALUE) {
		print_error("_get_osfhandle");
		return -1;
	}
	//printf("fd: %d fh: %d\n", fd, fh);
	DWORD dw;
	// enable sparse files on windows
	BOOL bRet = DeviceIoControl(fh, FSCTL_SET_SPARSE, NULL, 0, NULL, 0, &dw, NULL);
	if (!bRet) {
		printf("file not sparse (%d)\n", (int)GetLastError());
	}
	LARGE_INTEGER noff;
	//printf("off: %I64d\n", length);
	ret = SetFilePointerEx(fh, (LARGE_INTEGER)length, &noff, FILE_BEGIN);
	if (ret == 0) {
		print_error("SetFilePointerEx");
		return -1;
	}
	//printf("noff: %I64d\n", noff);
	ret = SetEndOfFile(fh);
	if (ret == 0) {
		print_error("SetEndOfFile");
		return -1;
	}
	return 0;
}

int is_device(char *fname)
{
	if (strncmp(fname, "\\\\.\\", 4) == 0) return 1;
	if (strncmp(fname, "\\\\?\\", 4) == 0) return 1;
	if (strlen(fname) == 2 && fname[1] == ':' && isalpha(fname[0])) return 1;
	return 0;
}

static int read_sector(void *_handle, u32 lba, u32 count, void *buf)
{
	HANDLE *handle = (HANDLE *)_handle;
	LARGE_INTEGER large;
	DWORD read;
	u64 offset = lba;
	
	offset *= 512ULL;
	large.QuadPart = offset;

	
	if (SetFilePointerEx(handle, large, NULL, FILE_BEGIN) == FALSE)
	{
		fprintf(stderr, "\n\n%lld %d %p\n", offset, count, _handle);
		wbfs_error("error seeking in hd sector (read)");
		return 1;
	}
	
	read = 0;
	if (ReadFile(handle, buf, count * 512ULL, &read, NULL) == FALSE)
	{
		wbfs_error("error reading hd sector");
		return 1;
	}
	
	return 0;
}

static int write_sector(void *_handle, u32 lba, u32 count, void *buf)
{
	HANDLE *handle = (HANDLE *)_handle;
	LARGE_INTEGER large;
	DWORD written;
	u64 offset = lba;

	offset *= 512ULL;
	large.QuadPart = offset;

	if (SetFilePointerEx(handle, large, NULL, FILE_BEGIN) == FALSE)
	{
		wbfs_error("error seeking in hd sector (write)");
		return 1;
	}

	written = 0;
	if (WriteFile(handle, buf, count * 512ULL, &written, NULL) == FALSE)
	{
		wbfs_error("error writing hd sector");
		return 1;
	}
	
	return 0;
  
}

static void close_handle(void *handle)
{
	CloseHandle((HANDLE *)handle);
}

static int get_capacity(char *fileName, u32 *sector_size, u32 *sector_count)
{
	DISK_GEOMETRY dg;
	PARTITION_INFORMATION pi;

	DWORD bytes;
	HANDLE *handle = CreateFile(fileName, GENERIC_READ | GENERIC_WRITE, 0, NULL, OPEN_EXISTING, FILE_FLAG_NO_BUFFERING, NULL);

	if (handle == INVALID_HANDLE_VALUE)
	{
		print_error(fileName);
		wbfs_error("could not open drive");
		return 0;
	}
	
	if (DeviceIoControl(handle, IOCTL_DISK_GET_DRIVE_GEOMETRY, NULL, 0, &dg, sizeof(DISK_GEOMETRY), &bytes, NULL) == FALSE)
	{
		print_error(fileName);
		CloseHandle(handle);
		wbfs_error("could not get drive geometry");
		return 0;
	}

	*sector_size = dg.BytesPerSector;

	if (DeviceIoControl(handle, IOCTL_DISK_GET_PARTITION_INFO, NULL, 0, &pi, sizeof(PARTITION_INFORMATION), &bytes, NULL) == FALSE)
	{
		print_error(fileName);
		CloseHandle(handle);
		wbfs_error("could not get partition info");
		return 0;
	}

	*sector_count = (u32)(pi.PartitionLength.QuadPart / dg.BytesPerSector);
	
	CloseHandle(handle);
	return 1;
}

/*
wbfs_t *wbfs_try_open_hd(char *driveName, int reset)
{
	wbfs_error("no direct harddrive support");
	return 0;
}
*/

wbfs_t *wbfs_try_open_partition(char *partitionName, int reset)
{
	HANDLE *handle;
	wbfs_t * ret;

	char drivePath[8] = "\\\\?\\Z:";
	char *devName;
	
	u32 sector_size, sector_count;
	
	if (!is_device(partitionName))
	{
		wbfs_error("bad drive name");
		return NULL;
	}
	if (strlen(partitionName) == 2) {
		drivePath[4] = partitionName[0];
		devName = drivePath;
	} else {
		devName = partitionName;
	}

	//printf("Opening Device: '%s'\n", devName);
	
	if (!get_capacity(devName, &sector_size, &sector_count))
	{
		return NULL;
	}

	//printf("Capacity: %d %d\n", sector_size, sector_count);
	
	handle = CreateFile(devName, GENERIC_READ | GENERIC_WRITE, 0, NULL, OPEN_EXISTING, FILE_FLAG_NO_BUFFERING, NULL);
	
	if (handle == INVALID_HANDLE_VALUE)
	{
		print_error(devName);
		return NULL;
	}

	ret= wbfs_open_partition(read_sector, write_sector, handle, sector_size, sector_count, 0, reset);
	if (!ret) CloseHandle(handle);
	else ret->close_hd = close_handle;

	return ret;
}

/*
wbfs_t *wbfs_try_open(char *disc, char *partition, int reset)
{
	wbfs_t *p = 0;
	
	if (partition)
	{
		p = wbfs_try_open_partition(partition,reset);
	}
	
	if (!p && !reset && disc)
	{
		p = 0;
	}
	else if(!p && !reset)
	{
		p = 0;
	}

	return p;
}
*/

#endif

