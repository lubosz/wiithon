
#define _GNU_SOURCE 1

#include "dclib-utf8.h"
#include <limits.h>

///////////////////////////////////////////////////////////////////////////////
/////   this software is taken from dcLib2 and now publiced under GPL2.   /////
///////////////////////////////////////////////////////////////////////////////

#define u0 DC_UTF8_ILLEGAL
#define u1 DC_UTF8_1CHAR
#define u2 DC_UTF8_2CHAR
#define u3 DC_UTF8_3CHAR
#define u4 DC_UTF8_4CHAR
#define uc DC_UTF8_CONT_ANY

const unsigned short TableUTF8Mode[256] =
{
	u1,u1,u1,u1, u1,u1,u1,u1, u1,u1,u1,u1, u1,u1,u1,u1, // 0000xxxx
	u1,u1,u1,u1, u1,u1,u1,u1, u1,u1,u1,u1, u1,u1,u1,u1, // 0001xxxx
	u1,u1,u1,u1, u1,u1,u1,u1, u1,u1,u1,u1, u1,u1,u1,u1, // 0010xxxx
	u1,u1,u1,u1, u1,u1,u1,u1, u1,u1,u1,u1, u1,u1,u1,u1, // 0011xxxx

	u1,u1,u1,u1, u1,u1,u1,u1, u1,u1,u1,u1, u1,u1,u1,u1, // 0100xxxx
	u1,u1,u1,u1, u1,u1,u1,u1, u1,u1,u1,u1, u1,u1,u1,u1, // 0101xxxx
	u1,u1,u1,u1, u1,u1,u1,u1, u1,u1,u1,u1, u1,u1,u1,u1, // 0110xxxx
	u1,u1,u1,u1, u1,u1,u1,u1, u1,u1,u1,u1, u1,u1,u1,u1, // 0111xxxx

	uc,uc,uc,uc, uc,uc,uc,uc, uc,uc,uc,uc, uc,uc,uc,uc, // 1000xxxx
	uc,uc,uc,uc, uc,uc,uc,uc, uc,uc,uc,uc, uc,uc,uc,uc, // 1001xxxx
	uc,uc,uc,uc, uc,uc,uc,uc, uc,uc,uc,uc, uc,uc,uc,uc, // 1010xxxx
	uc,uc,uc,uc, uc,uc,uc,uc, uc,uc,uc,uc, uc,uc,uc,uc, // 1011xxxx

	u2,u2,u2,u2, u2,u2,u2,u2, u2,u2,u2,u2, u2,u2,u2,u2, // 1100xxxx
	u2,u2,u2,u2, u2,u2,u2,u2, u2,u2,u2,u2, u2,u2,u2,u2, // 1101xxxx
	u3,u3,u3,u3, u3,u3,u3,u3, u3,u3,u3,u3, u3,u3,u3,u3, // 1110xxxx
	u4,u4,u4,u4, u4,u4,u4,u4, u0,u0,u0,u0, u0,u0,u0,u0  // 1111xxxx
};

#undef u0
#undef u1
#undef u2
#undef u3
#undef u4
#undef uc

///////////////////////////////////////////////////////////////////////////////

dcUTF8Mode CheckUTF8Mode ( unsigned char ch )
{
    return (dcUTF8Mode)TableUTF8Mode[ch];
}

#define CheckUTF8Mode(ch) ((dcUTF8Mode)TableUTF8Mode[(unsigned char)(ch)])

///////////////////////////////////////////////////////////////////////////////

int GetUTF8CharLength ( ulong code )
{
    // returns the length of the char 'code'
    //  0 : illegal code

    return code <= DC_UNICODE_MAX_UTF8_1
		? 1
		: code <= DC_UNICODE_MAX_UTF8_2
			? 2
			: code <= DC_UNICODE_MAX_UTF8_3
				? 3
				: code <= DC_UNICODE_MAX_UTF8_4
					? 4
					: 0;
}

///////////////////////////////////////////////////////////////////////////////

char * NextUTF8Char ( ccp ptr )
{
    // go to next next UTF8 character

    switch (CheckUTF8Mode(*ptr))
    {
	case DC_UTF8_1CHAR:
	    return *ptr ? (char*)ptr+1 : (char*)ptr;

	case DC_UTF8_4CHAR:
	    if ( CheckUTF8Mode(*++ptr) != DC_UTF8_CONT_ANY )
	    break;

	// fall through

	case DC_UTF8_3CHAR:
	case DC_UTF8_CONT_ANY:
	    if ( CheckUTF8Mode(*++ptr) != DC_UTF8_CONT_ANY )
	    break;

	// fall through

	case DC_UTF8_2CHAR:
	    if ( CheckUTF8Mode(*++ptr) != DC_UTF8_CONT_ANY )
	    break;

	// fall through

	default: // DC_UTF8_ILLEGAL
	    return (char*)ptr+1;
    }
    return (char*)ptr;
}

//-----------------------------------------------------------------------------

char * NextUTF8CharE( ccp ptr, ccp end )
{
    // go to next next UTF8 character

    if ( ptr >= end )
	return (char*)end;

    switch (CheckUTF8Mode(*ptr))
    {
	case DC_UTF8_1CHAR:
	    return (char*)ptr+1;

	case DC_UTF8_4CHAR:
	    if ( ++ptr >= end || CheckUTF8Mode(*ptr) != DC_UTF8_CONT_ANY )
	    break;

	// fall through

	case DC_UTF8_3CHAR:
	case DC_UTF8_CONT_ANY:
	    if ( ++ptr >= end || CheckUTF8Mode(*ptr) != DC_UTF8_CONT_ANY )
	    break;

	// fall through

	case DC_UTF8_2CHAR:
	    if ( ++ptr >= end || CheckUTF8Mode(*ptr) != DC_UTF8_CONT_ANY )
	    break;

	// fall through

	default: // DC_UTF8_ILLEGAL
	    return (char*)ptr+1;
    }
    return (char*)ptr;
}

///////////////////////////////////////////////////////////////////////////////

char * PrevUTF8Char ( ccp str )
{
    // go to the previous UTC character

    // kleine Optimierung für den Standardfall
    if ( (uchar)str[-1] < (uint)DC_UNICODE_MAX_UTF8_1 )
	return (char*)str-1;

    ccp ptr = str;
    int n = 0;
    dcUTF8Mode mode = CheckUTF8Mode(*--ptr);
    while ( n < 3 && mode == DC_UTF8_CONT_ANY )
    {
	n++;
	mode = CheckUTF8Mode(*--ptr);
    }

    switch (mode)
    {
	case DC_UTF8_1CHAR:
	    return (char*)( n<1 ? ptr : ptr+1 );

	case DC_UTF8_2CHAR:
	    return (char*)( n<2 ? ptr : ptr+2 );

	case DC_UTF8_3CHAR:
	    return (char*)( n<3 ? ptr : ptr+3 );

	case DC_UTF8_4CHAR:
	    return (char*)( n<4 ? ptr : ptr+4 );

	case DC_UTF8_CONT_ANY:
	    return (char*)str-3;

	default:
	    return (char*)str-1;
    }
}

//-----------------------------------------------------------------------------

char * PrevUTF8CharB ( ccp str, ccp begin )
{
    // go to the previous UTC character

    ccp ptr = str;
    if ( ptr <= begin )
	return (char*)begin;

    // kleine Optimierung für den Standardfall
    if ( (uchar)ptr[-1] < (uint)DC_UNICODE_MAX_UTF8_1 )
	return (char*)ptr-1;

    int n = 0;
    dcUTF8Mode mode = CheckUTF8Mode(*--ptr);
    while ( ptr > begin && n < 3 && mode == DC_UTF8_CONT_ANY )
    {
	n++;
	mode = CheckUTF8Mode(*--ptr);
    }
    switch (mode)
    {
	case DC_UTF8_1CHAR:
	    return (char*)( n<1 ? ptr : ptr+1 );

	case DC_UTF8_2CHAR:
	    return (char*)( n<2 ? ptr : ptr+2 );

	case DC_UTF8_3CHAR:
	    return (char*)( n<3 ? ptr : ptr+3 );

	case DC_UTF8_4CHAR:
	    return (char*)( n<4 ? ptr : ptr+4 );

	case DC_UTF8_CONT_ANY:
	    return (char*)str-3;

	default:
	    return (char*)str-1;
    }
}

///////////////////////////////////////////////////////////////////////////////

ulong GetUTF8Char ( ccp str )
{
    // fast scan of a UTF8 char -> ignore errors in continuation bytes

    const ulong result = (uchar)*str;
    switch (CheckUTF8Mode(result))
    {
	case DC_UTF8_1CHAR:
	    return result;

	case DC_UTF8_2CHAR:
	    return ( result & 0x1f ) <<  6
	     | ( str[1] & 0x3f );

	case DC_UTF8_3CHAR:
	    return ( result & 0x0f ) << 12
	     | ( str[1] & 0x3f ) <<  6
	     | ( str[2] & 0x3f );

	case DC_UTF8_4CHAR:
	    return ( result & 0x07 ) << 18
	     | ( str[1] & 0x3f ) << 12
	     | ( str[2] & 0x3f ) <<  6
	     | ( str[3] & 0x3f );

	case DC_UTF8_CONT_ANY:
	    return ( result & 0x3f ) << 12
	     | ( str[1] & 0x3f ) <<  6
	     | ( str[2] & 0x3f );

	default: // DC_UTF8_ILLEGAL
	    return result & 0x7f | LONG_MIN;
    }
}

///////////////////////////////////////////////////////////////////////////////

ulong ScanUTF8Char ( ccp * p_str )
{
    // scan a UTF8 char. Set bit LONG_MAX if an error seen.
    // *str is set to next next char if on no error.

    int n_cont;
    ccp ptr = *p_str;
    ulong result = (uchar)*ptr++;
    switch (CheckUTF8Mode(result))
    {
	case DC_UTF8_1CHAR:
	    if (result)
		(*p_str)++;
	    return result;

	case DC_UTF8_2CHAR:
	    result &= 0x1f;
	    n_cont = 1;
	    break;

	case DC_UTF8_3CHAR:
	    result &= 0x0f;
	    n_cont = 2;
	    break;

	case DC_UTF8_4CHAR:
	    result &= 0x07;
	    n_cont = 3;
	    break;

	case DC_UTF8_CONT_ANY:
	    if ( CheckUTF8Mode((uchar)*ptr) && CheckUTF8Mode((uchar)*++ptr) )
		ptr++;
	    *p_str = ptr;
	    return LONG_MIN;

	default: // DC_UTF8_ILLEGAL
	    (*p_str)++;
	    return result & 0x7f | LONG_MIN;
    }

    while ( n_cont-- > 0 )
    {
	if ( CheckUTF8Mode(*ptr) == DC_UTF8_CONT_ANY )
	    result = result << 6 | *ptr++ & 0x3f;
	else
	{
	    result |= LONG_MIN;
	    break;
	}
    }

    *p_str = ptr;
    return result;
}

//-----------------------------------------------------------------------------

ulong ScanUTF8CharE ( ccp * p_str, ccp end )
{
    // scan a UTF8 char. Set bit LONG_MAX if an error seen
    // *str is set to next next char if on no error.

    ccp ptr = *p_str;
    if ( ptr >= end )
	return LONG_MIN;

    int n_cont;
    ulong result = (uchar)*ptr++;
    switch (CheckUTF8Mode(result))
    {
	case DC_UTF8_1CHAR:
	    (*p_str)++;
	    return result;

	case DC_UTF8_2CHAR:
	    if ( ptr >= end )
		return LONG_MIN;
	    result &= 0x1f;
	    n_cont = 1;
	    break;

	case DC_UTF8_3CHAR:
	    if ( ptr+1 >= end )
		return LONG_MIN;
	    result &= 0x0f;
	    n_cont = 2;
	    break;

	case DC_UTF8_4CHAR:
	    if ( ptr+2 >= end )
		return LONG_MIN;
	    result &= 0x07;
	    n_cont = 3;
	    break;

	case DC_UTF8_CONT_ANY:
	    if (     ptr < end && CheckUTF8Mode((uchar)*ptr)
	    && ++ptr < end && CheckUTF8Mode((uchar)*ptr) )
		ptr++;
	    *p_str = ptr;
	    return LONG_MIN;

	default: // DC_UTF8_ILLEGAL
	    (*p_str)++;
	    return result & 0x7f | LONG_MIN;
    }

    while ( n_cont-- > 0 )
    {
	if ( CheckUTF8Mode(*ptr) == DC_UTF8_CONT_ANY )
	    result = result << 6 | *ptr++ & 0x3f;
	else
	{
	    result |= LONG_MIN;
	    break;
	}
    }

    *p_str = ptr;
    return result;
}

///////////////////////////////////////////////////////////////////////////////

ulong ScanUTF8CharInc ( ccp * p_str )
{
    // scan a UTF8 char. Set bit LONG_MAX if an error seen
    // *str is set to next next char => it is incremetned always!

    int n_cont;
    ccp ptr = *p_str;
    ulong result = (uchar)*ptr++;
    switch (CheckUTF8Mode(result))
    {
	case DC_UTF8_1CHAR:
	    (*p_str)++;
	    return result;

	case DC_UTF8_2CHAR:
	    result &= 0x1f;
	    n_cont = 1;
	    break;

	case DC_UTF8_3CHAR:
	    result &= 0x0f;
	    n_cont = 2;
	    break;

	case DC_UTF8_4CHAR:
	    result &= 0x07;
	    n_cont = 3;
	    break;

	case DC_UTF8_CONT_ANY:
	    if ( CheckUTF8Mode((uchar)*ptr) && CheckUTF8Mode((uchar)*++ptr) )
		ptr++;
	    *p_str = ptr;
	    return LONG_MIN;

	default: // DC_UTF8_ILLEGAL
	    (*p_str)++;
	    return result & 0x7f | LONG_MIN;
    }

    while ( n_cont-- > 0 )
    {
	if ( CheckUTF8Mode(*ptr) == DC_UTF8_CONT_ANY )
	    result = result << 6 | *ptr++ & 0x3f;
	else
	{
	    result |= LONG_MIN;
	    break;
	}
    }

    *p_str = ptr;
    return result;
}

//-----------------------------------------------------------------------------

ulong ScanUTF8CharIncE ( ccp * p_str, ccp end )
{
    // scan a UTF8 char. Set bit LONG_MAX if an error seen
    // *str is set to next next char => it is incremetned always!

    ccp ptr = *p_str;
    if ( ptr >= end )
    {
	(*p_str)++;
	return LONG_MIN;
    }

    int n_cont = 0;
    ulong result = (uchar)*ptr++;
    switch (CheckUTF8Mode(result))
    {
	case DC_UTF8_1CHAR:
	    (*p_str)++;
	    return result;

	case DC_UTF8_2CHAR:
	    result &= 0x1f;
	    n_cont = 1;
	    break;

	case DC_UTF8_3CHAR:
	    result &= 0x0f;
	    n_cont = 2;
	    break;

	case DC_UTF8_4CHAR:
	    result &= 0x07;
	    n_cont = 3;
	    break;

	case DC_UTF8_CONT_ANY:
	    if (     ptr < end && CheckUTF8Mode((uchar)*ptr)
		&& ++ptr < end && CheckUTF8Mode((uchar)*ptr) )
		    ptr++;
	    *p_str = ptr;
	    return LONG_MIN;

	default: // DC_UTF8_ILLEGAL
	    (*p_str)++;
	    return result & 0x7f | LONG_MIN;
    }

    while ( n_cont-- > 0 )
    {
	if ( ptr < end && CheckUTF8Mode(*ptr) == DC_UTF8_CONT_ANY )
	    result = result << 6 | *ptr++ & 0x3f;
	else
	{
	    result |= LONG_MIN;
	    break;
	}
    }

    *p_str = ptr;
    return result;
}

//////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////

ulong GetUTF8AnsiChar ( ccp str )
{
    // scan an UTF8 char. On error scan an ANSI char!

    const uchar * ptr = (const uchar *)str;
    ulong result = *ptr++;
    switch (CheckUTF8Mode(result))
    {
	case DC_UTF8_2CHAR:
	    if ( CheckUTF8Mode(*ptr) == DC_UTF8_CONT_ANY )
	    {
		return ( result & 0x1f ) << 6 | *ptr & 0x3f;
	    }
	    return result;

	case DC_UTF8_3CHAR:
	    if (   CheckUTF8Mode(ptr[0]) == DC_UTF8_CONT_ANY
		&& CheckUTF8Mode(ptr[1]) == DC_UTF8_CONT_ANY )
	    {
		return (( result & 0x0f ) << 6
		    | ptr[0] & 0x3f ) << 6
		    | ptr[1] & 0x3f;
	    }
	    return result;

	case DC_UTF8_4CHAR:
	    if (   CheckUTF8Mode(ptr[0]) == DC_UTF8_CONT_ANY
		&& CheckUTF8Mode(ptr[1]) == DC_UTF8_CONT_ANY
		&& CheckUTF8Mode(ptr[2]) == DC_UTF8_CONT_ANY )
	    {
		return ((( result & 0x07 ) << 6
		     | ptr[0] & 0x3f ) << 6
		     | ptr[1] & 0x3f ) << 6
		     | ptr[2] & 0x3f;
	    }
	    return result;

	default:
	    return result;
    }
}

///////////////////////////////////////////////////////////////////////////////

ulong ScanUTF8AnsiChar ( ccp * p_str )
{
    // scan an UTF8 char. On error scan an ANSI char!

    const uchar * ptr = (const uchar *)*p_str;
    ulong result = *ptr++;
    switch (CheckUTF8Mode(result))
    {
	case DC_UTF8_2CHAR:
	    if ( CheckUTF8Mode(*ptr) == DC_UTF8_CONT_ANY )
	    {
	    result = ( result & 0x1f ) << 6 | *ptr++ & 0x3f;
	    }
	    break;

	case DC_UTF8_3CHAR:
	    if (   CheckUTF8Mode(ptr[0]) == DC_UTF8_CONT_ANY
		&& CheckUTF8Mode(ptr[1]) == DC_UTF8_CONT_ANY )
	    {
		result = (( result & 0x0f ) << 6
		    | ptr[0] & 0x3f ) << 6
		    | ptr[1] & 0x3f;
		ptr += 2;
	    }
	    break;

	case DC_UTF8_4CHAR:
	    if (   CheckUTF8Mode(ptr[0]) == DC_UTF8_CONT_ANY
		&& CheckUTF8Mode(ptr[1]) == DC_UTF8_CONT_ANY
		&& CheckUTF8Mode(ptr[2]) == DC_UTF8_CONT_ANY )
	    {
		result = ((( result & 0x07 ) << 6
		    | ptr[0] & 0x3f ) << 6
		    | ptr[1] & 0x3f ) << 6
		    | ptr[2] & 0x3f;
		ptr += 3;
	    }
	    break;

	default:
	    break;
    }
    *p_str = (ccp)ptr;
    return result;
}

//-----------------------------------------------------------------------------

ulong ScanUTF8AnsiCharE ( ccp * p_str, ccp end )
{
    // scan an UTF8 char. On error scan an ANSI char!

    const uchar * ptr = (const uchar *)*p_str;
    if ( (ccp)ptr >= end )
    {
	(*p_str)++;
	return LONG_MIN;
    }
    ulong result = *ptr++;
    switch (CheckUTF8Mode(result))
    {
	case DC_UTF8_2CHAR:
	    if (   (ccp)ptr < end
		&& CheckUTF8Mode(*ptr) == DC_UTF8_CONT_ANY )
	    {
		result = ( result & 0x1f ) << 6 | *ptr++ & 0x3f;
	    }
	    break;

	case DC_UTF8_3CHAR:
	    if (   (ccp)ptr+1 < end
		&& CheckUTF8Mode(ptr[0]) == DC_UTF8_CONT_ANY
		&& CheckUTF8Mode(ptr[1]) == DC_UTF8_CONT_ANY )
	    {
		result = (( result & 0x0f ) << 6
		    | ptr[0] & 0x3f ) << 6
		    | ptr[1] & 0x3f;
		ptr += 2;
	    }
	    break;

	case DC_UTF8_4CHAR:
	    if (   (ccp)ptr+2 < end
		&& CheckUTF8Mode(ptr[0]) == DC_UTF8_CONT_ANY
		&& CheckUTF8Mode(ptr[1]) == DC_UTF8_CONT_ANY
		&& CheckUTF8Mode(ptr[2]) == DC_UTF8_CONT_ANY )
	    {
		result = ((( result & 0x07 ) << 6
		    | ptr[0] & 0x3f ) << 6
		    | ptr[1] & 0x3f ) << 6
		    | ptr[2] & 0x3f;
		ptr += 3;
	    }
	    break;

	default:
	    break;
    }
    *p_str = (ccp)ptr;
    return result;
}

///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////

int ScanUTF8Length ( ccp str, ccp end )
{
    int count = 0;
    ccp ptr = str;
    if (end)
    {
	while ( ptr < end )
	{
	    const char ch = *ptr++;
	    switch (CheckUTF8Mode(ch))
	    {
		case DC_UTF8_2CHAR:
		    if ( CheckUTF8Mode(*ptr) == DC_UTF8_CONT_ANY )
			ptr++;
		    break;

		case DC_UTF8_3CHAR:
		    if (   CheckUTF8Mode(ptr[0]) == DC_UTF8_CONT_ANY
			&& CheckUTF8Mode(ptr[1]) == DC_UTF8_CONT_ANY )
			    ptr += 2;
		    break;

		case DC_UTF8_4CHAR:
		    if (   CheckUTF8Mode(ptr[0]) == DC_UTF8_CONT_ANY
			&& CheckUTF8Mode(ptr[1]) == DC_UTF8_CONT_ANY
			&& CheckUTF8Mode(ptr[2]) == DC_UTF8_CONT_ANY )
			    ptr += 3;
		    break;

		default:
		    break;
	    }
	    count++;
	}
    }
    else
    {
	for (;;)
	{
	    const char ch = *ptr++;
	    if (!ch)
		break;
	    switch (CheckUTF8Mode(ch))
	    {
		case DC_UTF8_2CHAR:
		    if ( CheckUTF8Mode(*ptr) == DC_UTF8_CONT_ANY )
			ptr++;
		    break;

		case DC_UTF8_3CHAR:
		    if (   CheckUTF8Mode(ptr[0]) == DC_UTF8_CONT_ANY
			&& CheckUTF8Mode(ptr[1]) == DC_UTF8_CONT_ANY )
			    ptr += 2;
		    break;

		case DC_UTF8_4CHAR:
		    if (   CheckUTF8Mode(ptr[0]) == DC_UTF8_CONT_ANY
			&& CheckUTF8Mode(ptr[1]) == DC_UTF8_CONT_ANY
			&& CheckUTF8Mode(ptr[2]) == DC_UTF8_CONT_ANY )
			    ptr += 3;
		    break;

		default:
		    break;
	    }
	    count++;
	}
    }
    return count;
}

///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////

char * PrintUTF8Char ( char * buf, ulong code )
{
    code &= DC_UNICODE_CODE_MASK;

    if ( code <= DC_UNICODE_MAX_UTF8_1 )
    {
	*buf++ = code;
    }
    else if ( code <= DC_UNICODE_MAX_UTF8_2 )
    {
	*buf++ = code >> 6        | 0xc0;
	*buf++ = code      & 0x3f | 0x80;
    }
    else if ( code <= DC_UNICODE_MAX_UTF8_3 )
    {
	*buf++ = code >> 12        | 0xe0;
	*buf++ = code >>  6 & 0x3f | 0x80;
	*buf++ = code       & 0x3f | 0x80;
    }
    else
    {
	*buf++ = code >> 18 & 0x07 | 0xf0;
	*buf++ = code >> 12 & 0x3f | 0x80;
	*buf++ = code >>  6 & 0x3f | 0x80;
	*buf++ = code       & 0x3f | 0x80;
    }
    return buf;
}

///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////
