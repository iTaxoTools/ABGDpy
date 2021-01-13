
/*

Extension Module for ABGD

Consider using multi-phase extension module initialization instead:
https://www.python.org/dev/peps/pep-0489/

*/

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdlib.h>
#include "abgd.h"
#include "main_abgd.h"

#define SIGN( a ) ( ( (a) > 0 )?1: ( ((a)==0)?0:-1)  )
static int Increase(const void *v1, const void *v2){  	return (int)SIGN( *((double *)v1) - *((double *)v2));  };
#undef SIGN

int abgd_core( int argc, char ** argv){


	char *file;
	char dirfiles[128],
	     file_name[256],
	     ledir[128];

	char *meth=NULL,
	     *newickString=NULL,
	     *newickStringOriginal=NULL,
	     *simplename=NULL;

	char *mask;                      /* used to mask some row/col in the distance matrix -- consider only sub-part of the matrix */

	double *ValArray;               /* array where input data are stored */
	double MaxDist=0.1;             /* default 'a priori' maximum distance within species */
	double *myDist;
	double *vals;                   /* pairwise distances */
	double minSlopeIncrease=1.5;
	double minDist=0.001;

	float ts_tv=2.0; /*defautl value for trans/transv rate for Kimura*/
	long NVal=0;                    /* array size */
	long nval=0;                    /* number of pairwise comparisons */


	long i,j;       /* simple counting tmp variable */

	struct Peak my_abgd;             /* In this Structure, There is the Peak dist and the corresponding rank */
	struct DistanceMatrix distmat;   /* input matrix of distance all vs all */
	struct Composante comp;          /* group partition */
	struct Peak recursive_abgd;     /* structure for storing extra split distance */

	short output_slope=0;            /* to output slopes -- watch out it can be very verbose -- */
	short output_groups=0;           /* output group composition ? */

	short opt_recursion=0;           /* shall we attempt to re-split the primary partition ? */

	short verbose;            /* a bit more verbose */
	short stop_at_once=0;
	char DEBUG;               /* way too much verbose.. only for debugging */

	int myD,imethode=1;
	int *mySpecies,*specInit;
	int nbStepsABGD=10;             /* How many values are inserted in [p,P] */
	int c;
	int flag=1;                     /* if 0, do change in groups, if 1, need another round */
	int a,b;                        /* dummy counters */
	int nc;                         /* number of composantes from the first partition before sub-splitting */
	int round=1;                    /* how many recurssion round */
	int windsize_min=0;             /* the smallest wind_size */
	int windsize_max=0;             /* the smallest wind_size */
	int fmeg=0;
	int withallfiles=0;
	FILE *f, *f2,                     /* flux for reading (f) or output (fout) */
	     *fout;
	int nbbids=20;
	int notreefile=0;/*option for only groups*/

	int ncomp_primary=0;

	*dirfiles='.';
	*(dirfiles+1)='\0';
	ts_tv=2;
	DEBUG=0;
	verbose=0;

	while( (c=getopt(argc, argv, "p:P:n:b:o:d:t:vasmhX:")) != -1 ){

		switch(c){
			case 'a':
				withallfiles=1;//all files are output  default is just graphic files
				break;

			case 'p':
				minDist= atof(optarg);      /* min a priori */
				break;

			case 'P':
				MaxDist=atof(optarg);      /* max a priori P */
				break;

			case 'n':
				nbStepsABGD= atoi(optarg);               /* nbr of a priori dist */
				break;

			case 'd':
				imethode= atoi(optarg);               /* nbr choosing dist method */
				break;
			case 'b':
				nbbids= atoi(optarg);               /* nb bids  */
				break;
			case 'o':								/*dir where results files are written*/
				strcpy(dirfiles,optarg);
				break;

			case 'X':								/*dir where results files are written*/
				minSlopeIncrease=atof(optarg);
				break;

			case 'h':
                 		usage(argv[0]);
				break;

			case 'v':
                 		verbose=1;
				break;
			case 't':
                 		 ts_tv=atof(optarg);		/*trans/trav rate */
				break;

			case 'm':
				fmeg=1;			/*if present format mega CVS*/
			break;

			 case 's':
			 notreefile=1;
			 	break;

			case '?':
			default:
                 		syntax(argv[0]),exit(1);
		}

	}

	if(argc-optind != 1)syntax(argv[0]),exit(1);
	file=argv[optind];


	f=fopen(file,"r");
	if (f==NULL)printf("Cannot locate your file. Please check, bye\n"),exit(1);

		if (verbose) fprintf(stderr," Running abgd in verbose mode...\n");
	simplename = Built_OutfileName( file );
//	printf("%s\n",simplename);

	mySpecies=malloc(sizeof(int)*nbStepsABGD+1);
	specInit=malloc(sizeof(int)*nbStepsABGD+1);

	myDist = Compute_myDist(  minDist,  MaxDist,  nbStepsABGD );


	NVal=0;
	output_slope=0;
	output_groups=0;
	opt_recursion=1;

	/*
		readfile
	*/

	c = fgetc(f);
	rewind(f);

	if ( c == '>')
	{
	if (verbose) fprintf(stderr,"calculating dist matrix\n");
		distmat = compute_dis(f,imethode,ts_tv);
	if (verbose)fprintf(stderr,"calculating dist matrix done\n");
		}
	else
		distmat = read_distmat(f,ts_tv,fmeg);
	if (verbose && c=='>')
	{
	FILE *ftemp;
	ftemp=fopen("distmat.txt","w");
	if (ftemp != NULL)
		{
		fprint_distmat(distmat ,ftemp );
		fclose (ftemp);
		fprintf(stderr,"Matrix dist is written as distmat.txt\n");
		}
	}

	if (withallfiles)
		{
		if (verbose)fprintf(stderr,"\nbuilding newick tree for your data (it can take time when many sequences)\n");
		newickStringOriginal=compute_DistTree(  distmat, dirfiles );
		newickString= malloc( (size_t)  sizeof(char) * strlen(newickStringOriginal)+1);
		if (!newickString )
			printf("pb malloc newick\n"),exit(1);
		strcpy(newickString,newickStringOriginal);//make a copy because going to modify it in next function
//		printf("tree ok\n");
//		print_distmat(distmat);
		}

//print_distmat(distmat);


	switch(imethode){

		case 0:
			meth="K80 Kimura";
			break;

		case 1:
			meth="JC69 Jukes-Cantor";
			break;

		case 2:
			meth="N93 Tamura-Nei" ;
			printf("Please choose another method as Tamura Nei dist method is not fully implemented\n");
			exit(1);
			break;

		case 3:
			meth="SSSI SimpleDistance" ;
			break;

	}

	/*
		1.1 From the matrix, extract distance with the help of mask
	*/
	mask=(char*)malloc( distmat.n*sizeof(char) );
	if(!mask)fprintf(stderr, "main: cannot allocate mask, bye<BR>\n");
	if (verbose)fprintf(stderr,"Writing histogram files\n");
	sprintf(file_name,"%s/%s",dirfiles,simplename);
 	createSVGhisto(file_name,distmat,nbbids);
	if (verbose)fprintf(stderr," histogram Done\nBegining ABGD--->\n");

	for (myD=0;myD<nbStepsABGD;myD++)
	{
	if (verbose)fprintf(stderr,"ABGD step %d \n",myD);

 		MaxDist           = myDist[myD];
		my_abgd.Rank      = -1;
		my_abgd.Dist      = -1;   /* reset results */
		my_abgd.theta_hat =  0;
		flag=1;
		windsize_min=0;
		windsize_max=0;
		NVal=0;
		output_slope=0;
		output_groups=0;

		for(j=0; j<distmat.n; j++)mask[j]=1;
		ValArray = matrix2list( distmat, mask , &NVal);

		if (verbose)fprintf(stderr,"sorting \n");
		qsort((void *) ValArray, (size_t) NVal, (size_t) sizeof(double), Increase );
		if (verbose)fprintf(stderr,"done\n");
	/*
		2. Find the estimated peak of the derivative on windsize values
	*/
		if(windsize_min==0)windsize_min = min_ws( NVal );
		if(windsize_max==0 || windsize_max>NVal-1)windsize_max = NVal-1;

		if (verbose)fprintf(stderr,"look fisrt abgd\n");
		my_abgd = find_abgd( ValArray, NVal, windsize_min, windsize_max, output_slope, MaxDist, minSlopeIncrease  );
		if (verbose)fprintf(stderr,"done\n");

		if(my_abgd.Rank == NVal+0.5){

			printf("Partition %d : found 1 group (prior maximal distance P= %f) **Stop here**\n",  myD+1, MaxDist);
			stop_at_once=1;
			fflush(stdout);

			mySpecies[myD]=1;
			myD++;

			free(ValArray);


			break;
		}

	/*
		3. Extract groups using the limit
	*/
	if (verbose)fprintf(stderr,"extract comp\n");
		comp = extract_composante(  distmat, my_abgd.Dist, mask );



		i=j=comp.n_in_comp[0];
		for(c=1;c<comp.nc;c++){
			i=(comp.n_in_comp[c]<i)?comp.n_in_comp[c]:i;
			j=(comp.n_in_comp[c]>j)?comp.n_in_comp[c]:j;
		}

		specInit[myD]=comp.nc;

		if (withallfiles)
			{

			sprintf(file_name,"%s/%s.partinit.%d.txt",dirfiles,simplename,myD+1);
			fout=fopen(file_name,"w");
			if (fout==NULL)
				printf("problem opening result file %s\n",file_name), exit(1);
			sprintf(file_name,"%s/%s.partinit.%d.tree",dirfiles,simplename,myD+1);
			f2=fopen(file_name,"w");
			print_groups_files_newick( comp ,  distmat ,  fout,newickString  ,f2,0);
			fclose(fout);
			/* reseting newick string to original */
			strcpy(newickString,newickStringOriginal);//make a copy because going to modify it in next function



			}
		else if(notreefile)
			{
			sprintf(file_name,"%s/%s.partinit.%d.txt",dirfiles,simplename,myD+1);
			fout=fopen(file_name,"w");

			if (fout==NULL)
				printf("problem opening result file %s\n",file_name), exit(1);

			print_groups_files(  comp ,  distmat ,  fout,0);
			fclose(fout);
			}

	/*
		Try to resplit each group using recursion startegy on already defined groups
	*/

		ncomp_primary=comp.nc;

	if (verbose)fprintf(stderr,"entering recursion\n");
		while( flag ){

			flag=0;                 /* if no sub-split is done, do not start a new round */
			nc= comp.nc;

				//if (verbose)

				for(a=0; a< nc; a++){


				struct Composante recursive_comp;

				reset_composante( &recursive_comp );                     /* needed for the free in case of no new group */

				bzero( (void *)mask, (size_t)distmat.n*sizeof(char) );   /* built mask used to only consider some cells of the matrix */
				for(b=0;b<comp.n_in_comp[a]; b++)
					mask[ comp.comp[a][b] ] = 1;

				vals = matrix2list( distmat, mask , &nval);                                /* built array of pairwise dist */
				qsort((void *) vals, (size_t) nval, (size_t) sizeof(double), Increase );

				if( nval > 2 ){                                                           /* at least 3 sequences are needed */
					windsize_min = min_ws( nval );
					windsize_max= nval-1;
					recursive_abgd = find_abgd( vals, nval, windsize_min, windsize_max, output_slope, MaxDist ,minSlopeIncrease );

					if(recursive_abgd.Rank != nval+0.5){

						recursive_comp = extract_composante(  distmat, recursive_abgd.Dist, mask );

						if( recursive_comp.nc > 1 ){

							if(verbose){

								printf("Subsequent partition %s\n", (verbose)?"":"(details with -v)" );
								printf("theta_hat  : %g\n", recursive_abgd.theta_hat );
								printf("ABGD dist  : %f\n",  recursive_abgd.Dist);
								printf("ws         : [%d, %d]\n", windsize_min, windsize_max  );
								printf("Group id   : %d (%d nodes)\n",  a, recursive_comp.nn);
								printf("-> groups  : %d\n",  recursive_comp.nc);

							//	printf("Subgroups are:\n");
							//	print_groups( recursive_comp, distmat );
								printf("\n");

							}

							update_composante(  &comp, a, recursive_comp );


							flag=1;

						}

					}
				}
				free( vals );
				free_composante( recursive_comp );
			}
			round++;
		}




		printf("Partition %d : %d / %d groups with / out recursion for P= %f\n",  myD+1, comp.nc,ncomp_primary, MaxDist );
		fflush(stdout);

		i=j=comp.n_in_comp[0];

		for(c=1;c<comp.nc;c++){
			i=(comp.n_in_comp[c]<i)?comp.n_in_comp[c]:i;
			j=(comp.n_in_comp[c]>j)?comp.n_in_comp[c]:j;
		}

		/*
			outputting the partitions
		*/


		if (withallfiles){

			sprintf(file_name,"%s/%s.part.%d.txt",dirfiles,simplename,myD+1);
			fout=fopen(file_name,"w");

			if (fout==NULL)
				printf("problem opening result file %s\n",file_name), exit(1);

			sprintf(file_name,"%s/%s.part.%d.tree",dirfiles,simplename,myD+1);
			f2=fopen(file_name,"w");

			print_groups_files_newick( comp ,  distmat ,  fout,newickString  ,f2,0);

			fclose(fout);

			/*
				reseting newick string to original
			*/
			strcpy(newickString,newickStringOriginal);   /* make a copy because going to modify it in next function */

		}
		else if(notreefile)
		{
		sprintf(file_name,"%s/%s.part.%d.txt",dirfiles,simplename,myD+1);
		fout=fopen(file_name,"w");

		if (fout==NULL)
				printf("problem opening result file %s\n",file_name), exit(1);

		print_groups_files(  comp ,  distmat ,  fout,0);
		fclose(fout);
		}


		mySpecies[myD]=comp.nc;

		if (comp.nc==1) /* found only one part no need to continue */
		{
			myD++;
			break;
		}

		reset_composante( &comp);
		free(ValArray);
	}
//	printf("***************%d et nc=%d %d \n",myD,comp.nc,stop_at_once);
	if ((myD==1 && comp.nc<=1) || (myD==1 && stop_at_once==1))
	   printf("Only one partition found with your data. Nothing to output. You should try to rerun with a lower X (< %f) **Stop here**<BR>\n", minSlopeIncrease);
	else
		{

		sprintf(file_name,"%s/%s.abgd.svg",dirfiles,simplename);
		if(verbose) fprintf(stderr,"writing graphx file\n");
		CreateGraphFiles(mySpecies, specInit,myDist, myD, ledir, meth, file_name);   /* go for a nice piece of draw */
		if(verbose) fprintf(stderr,"writing graphx file done\n");
		printf("---------------------------------\n");
		printf("Results file are :\n");
		printf("Graphic svg file sumarizing this abgd run: %s/%s.abgd.svg\n",dirfiles,simplename);
		printf("Graphic distance histogram svg file : %s/%s.disthist.svg\n",dirfiles,simplename);
		printf("Graphic rank distance svg file : %s/%s.rank.svg\n",dirfiles,simplename);

		if (withallfiles)
			{
			printf("\n%d Text Files are resuming your work:\n",myD*4);
			printf("Description of %d different init/recursives partitions in:\n",myD*2);
			for (c=0;c<myD;c++)
				printf("%s/%s.[partinit/part].%d.txt\n",dirfiles,simplename,c+1);
			printf("Description of %d newick trees in from init/recursives partition:\n",myD*2);
			for (c=0;c<myD;c++)
				printf("%s/%s.[partinit/part].%d.tree\n",dirfiles,simplename,c+1);
			}
		else
		if (notreefile)
					{
			printf("\n%d Text Files are resuming your work:\n",myD*2);
			printf("Description of %d different init/recursives partitions in:\n",myD*2);
			for (c=0;c<myD;c++)
				printf("%s/%s.[partinit/part].%d.txt\n",dirfiles,simplename,c+1);

			}


		printf("---------------------------------\n");
  		}
	free_distmat(  distmat );
	if (stop_at_once==0 )
	free_composante(comp);
		if (withallfiles)
	free(newickString);

	free(mySpecies);

	free(mask);



	return 0;
}

/*
\t-m    : if present the distance Matrix is supposed to be MEGA CVS (other formats are guessed)\n\
\t-a    : output all partitions and tree files (default only graph files)\n\
\t-s    : output all partitions in 's'imple results txt files\n\
\t-p #  : minimal a priori value (default is 0.001) -Pmin-\n\
\t-P #  : maximal a priori value (default is 0.1) -Pmax-\n\
\t-n #  : number of steps in [Pmin,Pmax] (default is 10)\n\
\t-b #	: number of bids for graphic histogram of distances (default is 20\n\
\t-d #  : distance (0: Kimura-2P, 1: Jukes-Cantor --default--, 2: Tamura-Nei 3:simple distance)\n\
\t-o #  : existent directory where results files are written (default is .)\n\
\t-X #  : mininmum Slope Increase (default is 1.5)\n\
\t-t #  : transition/transversion (for Kimura) default:2\n");
*/

static PyObject *
abgd_main(PyObject *self, PyObject *args)
{
    PyObject *dict;
    PyObject *file;

    // Accept a dictionary-like python object
    if (!PyArg_ParseTuple(args, "O", &dict))
      return NULL;
    if (!PyDict_Check(dict)) {
      PyErr_SetString(PyExc_TypeError, "Not a dictionary");
      return NULL;
    }
    file = PyDict_GetItemString(dict, "file");
    if (file == NULL) {
      PyErr_SetString(PyExc_KeyError, "Key not found: file");
      return NULL;
    }

    PyObject* str = PyUnicode_AsEncodedString(file, "utf-8", "~E~");
    if (str == NULL) return NULL;
    const char *bytes = PyBytes_AS_STRING(str);
    printf("File = %s\n", bytes);

    const char *argv[2];
    argv[0] = "abgd";
    argv[1] = bytes;
    abgd_core(2, argv);

    Py_XDECREF(str);

    //return PyLong_FromLong(sts);
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
abgd_foo(PyObject *self, PyObject *args)
{
    long num, res;

    if (!PyArg_ParseTuple(args, "l", &num))
        return NULL;
    res = num + 42;
    return PyLong_FromLong(res);
}

static PyMethodDef AbgdMethods[] = {
    {"main",  abgd_main, METH_VARARGS,
     "Run ABGD for given parameters."},
    {"foo",  abgd_foo, METH_VARARGS,
     "Add 42."},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

PyDoc_STRVAR(abgd_doc,
"This is a template module just for instruction.");

static struct PyModuleDef abgdmodule = {
    PyModuleDef_HEAD_INIT,
    "abgd",   /* name of module */
    abgd_doc, /* module documentation, may be NULL */
    -1,       /* size of per-interpreter state of the module,
                 or -1 if the module keeps state in global variables. */
    AbgdMethods
};

PyMODINIT_FUNC
PyInit__abgdc(void)
{
    return PyModule_Create(&abgdmodule);
}
