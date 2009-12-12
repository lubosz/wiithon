
#ifdef __MINGW32__
#define fseeko fseeko64
#define ftello ftello64
#define mkdir(N,M) mkdir(N)
#else
#define off64_t off_t
#endif

#if defined(_MSC_VER) || defined(__MINGW32__) || defined(__MINGW64__)
#define FMT_llu "%I64u"
#define FMT_lld "%I64d"
#else
#define FMT_llu "%llu"
#define FMT_lld "%lld"
#endif

#ifdef WIN32
int file_truncate(int fd, off64_t length);
#else
#define file_truncate ftruncate
#endif

