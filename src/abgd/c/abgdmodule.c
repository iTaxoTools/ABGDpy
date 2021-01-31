
/*

Extension Module for ABGD

Consider using multi-phase extension module initialization instead:
https://www.python.org/dev/peps/pep-0489/

*/

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdlib.h>
#include <stdio.h>
#include "abgd.h"
#include "main_abgd.h"

#define SIGN( a ) ( ( (a) > 0 )?1: ( ((a)==0)?0:-1)  )
static int Increase(const void *v1, const void *v2){  	return (int)SIGN( *((double *)v1) - *((double *)v2));  };
#undef SIGN

// Set var = dict[str], do nothing if key does not exist.
// On failure, sets error indicator and returns -1.
// Return 0 on success.
// Beware: parsing strings allocates memory!
int parseItem(PyObject *dict, const char *str, const char t, void *var) {

	PyObject *item;
	PyObject *value;
	switch(t){
		case 'b':
			item = PyDict_GetItemString(dict, str);
			if (item == NULL) return 0;
			*(int *)var = PyObject_IsTrue(item);
			if (*(int *)var == -1) {
				PyErr_Format(PyExc_TypeError, "parseItem: Expected boolean value for key '%s'", str);
				return -1;
			}
			break;
		case 'i':
			item = PyDict_GetItemString(dict, str);
			if (item == NULL) return 0;
			*(int *)var = (int) PyLong_AsLong(item);
			if (PyErr_Occurred()) {
				PyErr_Format(PyExc_TypeError, "parseItem: Expected integer value for key '%s'", str);
				return -1;
			}
			break;
		case 'd':
			item = PyDict_GetItemString(dict, str);
			if (item == NULL) return 0;
			*(double *)var = (double) PyFloat_AsDouble(item);
			if (PyErr_Occurred()) {
				PyErr_Format(PyExc_TypeError, "parseItem: Expected double value for key '%s'", str);
				return -1;
			}
			break;
		case 'f':
			item = PyDict_GetItemString(dict, str);
			if (item == NULL) return 0;
			*(float *)var = (float) PyFloat_AsDouble(item);
			if (PyErr_Occurred()) {
				PyErr_Format(PyExc_TypeError, "parseItem: Expected float value for key '%s'", str);
				return -1;
			}
			break;
		case 's':
			item = PyDict_GetItemString(dict, str);
			if (item == NULL) return 0;
			value = PyUnicode_AsEncodedString(item, "utf-8", "~E~");
			if (value == NULL) {
				PyErr_Format(PyExc_TypeError, "parseItem: Expected string value for key '%s'", str);
				return -1;
			}
			const char *bytes = PyBytes_AS_STRING(value);
			*(const char **)var = malloc(strlen (bytes) + 1);
			strcpy(*(const char **)var, bytes);
			Py_XDECREF(value);
			break;
		default:
			PyErr_Format(PyExc_TypeError, "parseItem: Unexpected type: %c", t);
			return -1;
		}
	return 0;
}

static PyObject *
abgd_main(PyObject *self, PyObject *args) {

	PyObject *dict;
	PyObject *item;
	const char *separator_str = NULL;
	char separator;

	const char *file = NULL;
	const char *dirfiles = NULL;
	const char *dirfiles_default = ".";
	char file_name[256],
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
	double *bcod;
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

	short verbose;									/* a bit more verbose */
	short stop_at_once=0;
	char DEBUG;											/* way too much verbose.. only for debugging */

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
	int nbreal;
	struct tm      *tm;
	int ncomp_primary=0;
	// char buffer2[80];
	const char *timeSig = NULL;
	const char *timeSig_default = "?";
	int withspart=1;
	Spart *myspar,*myspar2;
	int **nb_subsets;
	struct stat st;
	struct stat     statbuf;
	FILE *fres=stdout;
	char dataFilename[256];
	// char buffer[80];
   	struct stat stfile = {0};
char *bout;


	// Fetch time from arguments instead
	// stat(argv[0], &statbuf);
  //   tm = localtime(&statbuf.st_mtime);
	//
 	// strftime(buffer,80,"%x - %I:%M%p", tm); // 11/19/20 - 05:34PM
	// strftime(buffer2,80,"%FT%T", tm); // 11/19/20 - 05:34PM

	// *dirfiles='.';
	// *(dirfiles+1)='\0';
	ts_tv=2;
	DEBUG=0;
	verbose=0;


	if (parseItem(PyModule_GetDict(self), "separator", 's', &separator_str)) return NULL;
	if (!separator_str) {
		PyErr_SetString(PyExc_TypeError, "abgd_main: Module global not found: 'separator'");
		return NULL;
	}
	separator = separator_str[0];
	printf("> separator = %c\n", separator);

	// Accept a dictionary-like python object
	if (!PyArg_ParseTuple(args, "O", &dict))
		return NULL;
	if (!PyDict_Check(dict)) {
		PyErr_SetString(PyExc_TypeError, "abgd_main: Argument must be a dictionary");
		return NULL;
	}

	if (parseItem(dict, "file", 's', &file)) return NULL;
	printf("> file = %s\n", file);

	if (!file) {
		PyErr_SetString(PyExc_KeyError, "abgd_main: Mandatory key: 'file'");
		return NULL;
	}

	f=fopen(file,"r");
	if (f==NULL) {
		PyErr_Format(PyExc_FileNotFoundError, "abgd_main: Input file not found: '%s'", file);
		return NULL;
	}
	simplename = Built_OutfileName( file );
	//	printf("%s\n",simplename);

	if (parseItem(dict, "out", 's', &dirfiles)) return NULL;
	if (!dirfiles) dirfiles = dirfiles_default;
	printf("> dirfiles = %s\n", dirfiles);

	if (parseItem(dict, "time", 's', &timeSig)) return NULL;
	if (!timeSig) timeSig = timeSig_default;
	printf("> timeSig = %s\n", timeSig);

	if (parseItem(dict, "method", 'i', &imethode)) return NULL;
	printf("> imethode = %i\n", imethode);

	if (parseItem(dict, "bids", 'i', &nbbids)) return NULL;
	printf("> nbbids = %i\n", nbbids);

	if (parseItem(dict, "steps", 'i', &nbStepsABGD)) return NULL;
	printf("> nbStepsABGD = %i\n", nbStepsABGD);

	if (parseItem(dict, "min", 'd', &minDist)) return NULL;
	printf("> minDist = %f\n", minDist);

	if (parseItem(dict, "max", 'd', &MaxDist)) return NULL;
	printf("> MaxDist = %f\n", MaxDist);

	if (parseItem(dict, "slope", 'd', &minSlopeIncrease)) return NULL;
	printf("> minSlopeIncrease = %f\n", minSlopeIncrease);

	if (parseItem(dict, "rate", 'f', &ts_tv)) return NULL;
	printf("> ts_tv = %f\n", ts_tv);

	if (parseItem(dict, "mega", 'b', &fmeg)) return NULL;
	printf("> fmeg = %i\n", fmeg);

	if (parseItem(dict, "all", 'b', &withallfiles)) return NULL;
	printf("> withallfiles = %i\n", withallfiles);

	if (parseItem(dict, "spart", 'b', &withspart)) return NULL;
	printf("> withspart = %i\n", withspart);

	if (parseItem(dict, "verbose", 'b', &verbose)) return NULL;
	printf("> verbose = %i\n", verbose);

	if (parseItem(dict, "simple", 'b', &notreefile)) return NULL;
	printf("> notreefile = %i\n", notreefile);

	//check that dirfiles ends by a '/' otherwise may have some pb

	if (strrchr(file,separator))
		sprintf(dataFilename,"%s",strrchr(file,separator)+1);
	else
		sprintf(dataFilename,"%s",file);
	if (strrchr(dataFilename,'.'))
		{bout=strrchr(dataFilename,'.'); (*bout) ='\0';}
//check if output dir file exist an create


if (stat(dirfiles, &stfile) == -1)
    mkdir(dirfiles, 0700);

	f=fopen(file,"r");
	if (f==NULL)printf("Cannot locate your file. Please check, bye\n"),exit(1);

		if (verbose) fprintf(stderr," Running abgd in verbose mode...\n");
	simplename = Built_OutfileName( file );
//	printf("%s\n",simplename);

	sprintf(file_name,"%s%c%s.log.txt",dirfiles,separator,simplename);
	freopen (file_name,"w",stdout);
	printf("### logfile = %s\n", file_name);

	mySpecies=malloc(sizeof(int)*nbStepsABGD+1);
	specInit=malloc(sizeof(int)*nbStepsABGD+1);

	myDist = Compute_myDist(  minDist,  MaxDist,  nbStepsABGD );
	bcod=malloc(sizeof(double*)*nbStepsABGD);

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

	printf("ok\n");

		myspar=malloc(sizeof(Spart)*distmat.n);
		myspar2=malloc(sizeof(Spart)*distmat.n);
		nb_subsets=malloc(sizeof(int *) *nbStepsABGD);

		for (i=0;i<nbStepsABGD;i++)
			nb_subsets[i]=malloc(sizeof(int)*2);
		for (i=0;i<distmat.n;i++)
		{
			myspar[i].name=malloc(sizeof(char)*strlen( distmat.names[i])+1);
			strcpy_spart(myspar[i].name,distmat.names[i]);
			myspar2[i].name=malloc(sizeof(char)*strlen( distmat.names[i])+1);
			strcpy_spart(myspar2[i].name,distmat.names[i]);
			myspar[i].specie=malloc(sizeof(int)*nbStepsABGD);
			myspar2[i].specie=malloc(sizeof(int)*nbStepsABGD);
		}

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
	sprintf(file_name,"%s%c%s",dirfiles,separator,simplename);
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

		bcod[myD]=my_abgd.Dist;

		if (withallfiles)
			{

			sprintf(file_name,"%s%c%s.partinit.%d.txt",dirfiles,separator,simplename,myD+1);
			fout=fopen(file_name,"w");
			if (fout==NULL)
				printf("problem opening result file %s\n",file_name), exit(1);
			sprintf(file_name,"%s%c%s.partinit.%d.tree",dirfiles,separator,simplename,myD+1);
			f2=fopen(file_name,"w");
			print_groups_files_newick( comp ,  distmat ,  fout,newickString  ,f2,0,stdout,"");

			fclose(fout);
			/* reseting newick string to original */
			strcpy(newickString,newickStringOriginal);//make a copy because going to modify it in next function

			}
		else if(notreefile)
			{
			sprintf(file_name,"%s%c%s.partinit.%d.txt",dirfiles,separator,simplename,myD+1);
			fout=fopen(file_name,"w");

			if (fout==NULL)
				printf("problem opening result file %s\n",file_name), exit(1);

			print_groups_files(  comp ,  distmat ,  fout,0);
			fclose(fout);
			}

		if (withspart) mem_spart_files(comp,myspar,myD,nb_subsets,0,distmat.n,fres);

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

				// bzero( (void *)mask, (size_t)distmat.n*sizeof(char) );   /* built mask used to only consider some cells of the matrix */
				memset((void *)mask, 0, (size_t)distmat.n*sizeof(char));	/* Replaces the above */
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



		//bcod[myD]=recursive_abgd.Dist;
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

			sprintf(file_name,"%s%c%s.part.%d.txt",dirfiles,separator,simplename,myD+1);
			fout=fopen(file_name,"w");

			if (fout==NULL)
				printf("problem opening result file %s\n",file_name), exit(1);

			sprintf(file_name,"%s%c%s.part.%d.tree",dirfiles,separator,simplename,myD+1);
			f2=fopen(file_name,"w");

			print_groups_files_newick( comp ,  distmat ,  fout,newickString  ,f2,0,stdout,"");


			fclose(fout);

			/*
				reseting newick string to original
			*/
			strcpy(newickString,newickStringOriginal);   /* make a copy because going to modify it in next function */

		}
		else if(notreefile)
		{
		sprintf(file_name,"%s%c%s.part.%d.txt",dirfiles,separator,simplename,myD+1);
		fout=fopen(file_name,"w");

		if (fout==NULL)
				printf("problem opening result file %s\n",file_name), exit(1);

		print_groups_files(  comp ,  distmat ,  fout,0);

		fclose(fout);
		}

		if (withspart) mem_spart_files(comp,myspar2,myD,nb_subsets,1,distmat.n,fres);


		mySpecies[myD]=comp.nc;

		if (comp.nc==1) /* found only one part no need to continue */
		{
			myD++;
			break;
		}

		reset_composante( &comp);
		free(ValArray);
	}
 //printf("***************%d et nc=%d %d \n",myD,comp.nc,stop_at_once);
	if ((myD==1 && comp.nc<=1) || (myD==1 && stop_at_once==1))
	   printf("Only one partition found with your data. Nothing to output. You should try to rerun with a lower X (< %f) **Stop here**<BR>\n", minSlopeIncrease);
	else
		{

		sprintf(file_name,"%s%c%s.abgd.svg",dirfiles,separator,simplename);
		if(verbose) fprintf(stderr,"writing graphx file\n");
		CreateGraphFiles(mySpecies, specInit,myDist, myD, ledir, meth, file_name);   /* go for a nice piece of draw */
		if(verbose) fprintf(stderr,"writing graphx file done\n");
		printf("---------------------------------\n");
		printf("Results file are :\n");
		printf("Graphic svg file sumarizing this abgd run: %s%c%s.abgd.svg\n",dirfiles,separator,simplename);
		printf("Graphic distance histogram svg file : %s%c%s.disthist.svg\n",dirfiles,separator,simplename);
		printf("Graphic rank distance svg file : %s%c%s.rank.svg\n",dirfiles,separator,simplename);

		if (withallfiles)
			{
			printf("\n%d Text Files are resuming your work:\n",myD*4);
			printf("Description of %d different init/recursives partitions in:\n",myD*2);
			for (c=0;c<myD;c++)
				printf("%s%c%s.[partinit/part].%d.txt\n",dirfiles,separator,simplename,c+1);
			printf("Description of %d newick trees in from init/recursives partition:\n",myD*2);
			for (c=0;c<myD;c++)
				printf("%s%c%s.[partinit/part].%d.tree\n",dirfiles,separator,simplename,c+1);
			}
		else
		if (notreefile)
					{
			printf("\n%d Text Files are resuming your work:\n",myD*2);
			printf("Description of %d different init/recursives partitions in:\n",myD*2);
			for (c=0;c<myD;c++)
				printf("%s%c%s.[partinit/part].%d.txt\n",dirfiles,separator,simplename,c+1);

			}

		if (withspart)
			{
			nbreal=((myD-1) < nbStepsABGD)? myD-1 : nbStepsABGD;
			printf("Spart files (%d real steps)\n",nbreal);
			CreateSpartFile(myspar,myspar2,dirfiles,nbreal,dataFilename,nb_subsets,distmat.n,timeSig,fres,separator,meth,minSlopeIncrease,bcod);
			}

		printf("---------------------------------\n");
  		}

	free_distmat(  distmat );
	if (stop_at_once==0 )
	free_composante(comp);
		if (withallfiles)
			free(newickString);

	free(bcod);
	free(mySpecies);
	free(mask);
	free(specInit);

	for (i=0;i<nbStepsABGD;i++)
			free(nb_subsets[i]);
	free(nb_subsets);

	for (i=0;i<distmat.n;i++)
		{
			free(myspar[i].name);
			free(myspar2[i].name);

			free(myspar[i].specie);
			free(myspar2[i].specie);

		}

	free (myspar);
	free (myspar2);

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

static PyObject *
abgd_foo2(PyObject *self, PyObject *args)
{
  const char *dir;

  if (!PyArg_ParseTuple(args, "s", &dir))
      return NULL;
	printf("foo dir = %s\n", dir);

	char file_name[128];
	sprintf(file_name,"%s/foo.bar", dir);
	printf("foo file_name = %s\n", file_name);

	FILE *file;
	file=fopen(file_name,"w");
	if (file != NULL)
	{
	fprintf(stderr,"Matrix dist is written as distmat.txt\n");
	fprintf(file,"BARBARA\n");
	fclose (file);
	}
  return PyLong_FromLong(1);
}

static PyMethodDef AbgdMethods[] = {
  {"main",  abgd_main, METH_VARARGS,
   "Run ABGD for given parameters."},
  {"foo",  abgd_foo, METH_VARARGS,
   "Add 42."},
  {"foo2",  abgd_foo2, METH_VARARGS,
   "Write temp file."},
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
PyInit_abgdc(void)
{
	PyObject *m = NULL;
  m = PyModule_Create(&abgdmodule);
	if (m != NULL) {
		if (PyModule_AddStringConstant(m, "separator", "/")) {
			Py_XDECREF(m);
			m = NULL;
		}
	}
	return m;
}
