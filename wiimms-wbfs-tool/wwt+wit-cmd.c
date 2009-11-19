
///////////////////////////////////////////////////////////////////////////////
//   This file is included by wwt.c and wit.c and contains common commands.  //
///////////////////////////////////////////////////////////////////////////////

enumError cmd_error()
{
    if (!n_param)
    {
	const bool print_header = !(used_options&OB_NO_HEADER);

	if (print_header)
	{
	    print_title(stdout);
	    printf(" List of error codes\n\n");
	}
	int i;

	// calc max_wd
	int max_wd = 0;
	for ( i=0; i<ERR__N; i++ )
	{
	    const int len = strlen(GetErrorName(i));
	    if ( max_wd < len )
		max_wd = len;
	}

	// print table
	for ( i=0; i<ERR__N; i++ )
	    printf("%3d : %-*s : %s\n",i,max_wd,GetErrorName(i),GetErrorText(i));

	if (print_header)
	    printf("\n");
	return ERR_OK;
    }

    int stat;
    long num = ERR__N;
    if ( n_param != 1 )
	stat = ERR_SYNTAX;
    else
    {
	char * end;
	num = strtoul(first_param->arg,&end,10);
	stat = *end ? ERR_SYNTAX : num < 0 || num >= ERR__N ? ERR_SEMANTIC : ERR_OK;
    }

    if (long_count)
	printf("%s\n",GetErrorText(num));
    else
	printf("%s\n",GetErrorName(num));
    return stat;
}

//
///////////////////////////////////////////////////////////////////////////////

enumError cmd_exclude()
{
    ParamList_t * param;
    for ( param = first_param; param; param = param->next )
	AtFileHelper(param->arg,true,AddExcludeID);

    SetupExcludeDB();
    DumpIDDB(&exclude_db,stdout);
    return ERR_OK;
}

//
///////////////////////////////////////////////////////////////////////////////

enumError cmd_titles()
{
    ParamList_t * param;
    for ( param = first_param; param; param = param->next )
	AtFileHelper(param->arg,true,AddTitleFile);

    InitializeTDB();
    DumpIDDB(&title_db,stdout);
    return ERR_OK;
}

//
///////////////////////////////////////////////////////////////////////////////
