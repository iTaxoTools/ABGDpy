/*
	Copyright (C) 2008-2013 G Achaz

	This program is free software; you can redistribute it and/or
	modify it under the terms of the GNU Lesser General Public License
	as published by the Free Software Foundation; either version 2.1
	of the License, or (at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU Lesser General Public License for more details.

	You should have received a copy of the GNU Lesser General Public License
	along with this program; if not, write to the Free Software
	Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

 	for more information, please contact guillaume achaz <achaz@abi.snv.jussieu.fr>/<gachaz@gmail.com>

*/

/******
        file     : abgg.c -- automatic barcod gap discovery
        function : rank values and find a gap in their density - devised to find the limit
	           between population and species in phylogeography (done with/for Nicolas Puillandre)

        created  : April 2008
        modif    : Nov 09 --stable version-- (with a minimum of slope increase)
        modif    : April 10 --stable version-- (with (A) some minimum divergence and (B) at least 1.5 times of slope increase)

        author   : gachaz
*****/

#define _GNU_SOURCE
#include <stdlib.h>
#include <stdio.h>
#include <time.h>
#include <float.h>
#include <math.h>
#include <string.h>
#include <ctype.h>
#include <sys/stat.h>
#include <errno.h>  /* errno */
#include "abgd.h"
#define NBCHARMALLOC 256
static char DEBUG;
static short verbose;
#define SIGN( a ) ( ( (a) > 0 )?1: ( ((a)==0)?0:-1)  )
static int Increase(const void *v1, const void *v2){  	return (int)SIGN( *((double *)v1) - *((double *)v2));  };
#undef SIGN

/*Read one fasta sequence in a file pointer store it in a fastaseq struct
returns 0 if some pbs or some pbs and 1 if everything ok*/
int ReadFastaSequence( FILE *f, struct FastaSeq *laseq)
	{
  	char *name;
  	char *seq;
  	int   n,c;
  	int   nalloc;
	char *nucs="ATGC-+NMRWSYKVHDBNZ";
		nalloc = 128;
	c=fgetc(f);
	if (c!='>')
		{return 0;}
	n=0;
	name= malloc(sizeof(char) * 128);
 	while (1){
 		c=fgetc(f);
 		if (c=='\n' || c=='\r' || c==10 || c==13  ) //do not store weird chars in names
 			break;
 		name[n++]=c;
 		if (n>127)
 			{
 			nalloc += 128;
 			name=realloc(name,sizeof(char) *nalloc);
 			}

 	}

 	name[n]='\0';
	laseq->name=malloc(sizeof(char)*(n+1));

  	strcpy(laseq->name, name);

  	seq = malloc(sizeof(char) * 128);      /* allocate seq in blocks of 128 residues */
  	nalloc = 128;
  	n = 0;

 	 while (1)
    	{
    	c=fgetc(f);
    	if (c==EOF )
    		break;
    	if (c=='>' )
    		{ungetc(c,f);break;} //put back in the stream the next new seq indicator
		if( c!='\n' && c!='\r' && c!='\t' && c!=' ')
		  {
		  if (strchr(nucs,toupper(c))==NULL) html_error(60); /*weird symbol found*/

		  seq[n++]=toupper(c);
		  if (nalloc == n)
	    		{
	      		nalloc += 128;
	      		seq = realloc(seq, sizeof(char) * nalloc);
	    		}
			}
    	}

 	seq[n] = '\0';

	laseq->seq=malloc(sizeof(char)*n+1);
	strcpy(laseq->seq,seq);

  	free(seq);

	 if (c==EOF)
 		return(0);
	 else
		return(1);
}


/*output fasta seq for verification only */
void print_seq(struct FastaSeq *mesSeq,int nseq)
{
int i;
	for (i=0;i<nseq;i++)
	printf("%03d\n%s\n%s\n",i,mesSeq[i].name,mesSeq[i].seq);
}




/*Read a Fasta File and compute the distance Matrix according to method*/
struct DistanceMatrix compute_dis(FILE *f,int method,float ts_tv)
{
struct FastaSeq *mesSeq;

int i=1;;
int nalloc=256;
int nseq=0;
struct DistanceMatrix my_mat;   /* store distance matrix, names and matrix size */


mesSeq=(struct FastaSeq *)malloc (sizeof (struct FastaSeq ) *nalloc);

while (i)
	{

	i=ReadFastaSequence(f, &mesSeq[nseq]);
	nseq++;
	if (nseq==nalloc)
		{
		 nalloc+=256;
		 mesSeq=realloc(mesSeq,sizeof (struct FastaSeq ) * nalloc);
		if (mesSeq==NULL){printf("not enough memory\n");exit(1);}
		}
	}
if (check_names(mesSeq,nseq)==0)
	printf("Two seqs found with same name. Exit\n"),exit(1);

//printf("Going for dist: %d seqs\n",nseq);
my_mat=GetDistMat(nseq,mesSeq, method,ts_tv);


for (i=0;i<nseq;i++)
	{free(mesSeq[i].seq);free(mesSeq[i].name);}
free(mesSeq);
return my_mat;
}



//returns the position of c in string l 1 to length(l) return 0 if not
int myIndex(char *l, char c)
{
int i,lo=strlen(l);

for (i=1;i<=lo;i++)
	if (l[i-1]==c)
	return(i);
return(0);
}


/*my own fgets which reallocs sizeof line if needed*/
char *my_get_line(char *ligne,FILE *f_in,int *nbcharmax)
{
char c;
int nbc=0;

	while (1)
		{
		 c=fgetc(f_in);
		 if (feof(f_in))
		 	printf("EOF (1) detected wrong format\n"),exit(1);

		 if (c=='\n'|| c==10 || c=='\r'){
 			ligne[nbc]='\0';

 			break;
 			}
 		ligne[nbc++]=c;
 		if (nbc== *nbcharmax)
 			{
 			*nbcharmax= *(nbcharmax)+NBCHARMALLOC;
 			ligne=realloc(ligne, sizeof(char)*(*nbcharmax));
 			}
 		}


return(ligne);
}




/*do some text editing */
void remplace(char *name,char c,char newc)
{
int i=0;

while (name[i]!='\0')
		{
		if (name[i]==c)
			name[i]=newc;
		i++;
		}

}



/*Read CVS mega matrix which is the default for MEGA 5*/
void readMatrixMegaCVS(FILE *f_in,struct DistanceMatrix *my_mat)
{
int nb=0,a,b,c;
int nbcharmax=NBCHARMALLOC,to_alloc=0;
char *ligne,letter,nombre [12];
long ppos;
//float ff;
//long posit;

	printf("CVS MEGA FILE\n");fflush(stdout);
	ligne=(char *)malloc(sizeof(char)*nbcharmax);
	*ligne='\0';

	while (1)
		{
		ligne=my_get_line(ligne,f_in,&nbcharmax);
		if(strncmp(ligne,"Table,",5)==0 || feof(f_in)) break;
		if (strlen(ligne)>2)
			{nb++;}
		}

	rewind(f_in);
	my_mat->n = nb;
		printf("%ld data<BR>\n",my_mat->n);fflush(stdout);


	my_mat->names = (char **)malloc( (size_t) sizeof(char *)*my_mat->n );
	if( ! my_mat->names )fprintf(stderr, "read_distmat: cannot allocate my_mat.names, bye"), exit(4);

/*	for(a=0;a<my_mat->n; a++){
		my_mat->names[a] = (char *)malloc( (size_t) sizeof(char)*(SIZE_NAME_DIST +1));
		if( ! my_mat->names[a] )
			fprintf(stderr, "read_distmat: cannot allocate my_mat.names[%d], bye",a), exit(4);
	}
*/
	my_mat->dist = (double **)malloc( (size_t) sizeof(double *)*my_mat->n );
	if( ! my_mat->dist)fprintf(stderr, "read_distmat: cannot allocate my_mat.dist, bye"), exit(4);
	for(a=0;a<my_mat->n; a++){
		my_mat->dist[a] = (double *)malloc( (size_t) sizeof(double)*my_mat->n );
		if( ! my_mat->dist[a] )
			fprintf(stderr, "read_distmat: cannot allocate my_mat.dist[%d], bye",a), exit(4);
		}

/*now read */

for (a=0;a<my_mat->n;a++){
		c=0;
		ppos=ftell(f_in);
		to_alloc=0;
		while( (letter=fgetc(f_in)) != ','){ //count length of title
		to_alloc++;
		}
		fseek(f_in,ppos,SEEK_SET);
		my_mat->names[a]=(char *)malloc(sizeof(char)*(to_alloc+1));
		while( (letter=fgetc(f_in)) != ','){
				my_mat->names[a][c] = (char)letter;
				c++;
			}

		my_mat->names[a][c]='\0';
//printf("*****%s\n<BR>",my_mat->names[a]);fflush(stdout);
		for (b=0;b<=a;b++)
			{
			c=0;
			while( (letter=fgetc(f_in)) != ','){
				if (letter=='?'){
				fprintf(stderr,"**Warning distance between %s and %s is unknown,exiting<BR>\n",my_mat->names[a],my_mat->names[b]);exit(1);
				}

				nombre[c]=(char) letter;
				c++;
			}
	    	nombre[c]='\0';

	    	if (c==0)
	    		my_mat->dist[b][a]=my_mat->dist[a][b]=0;
	    	else
			my_mat->dist[b][a]=my_mat->dist[a][b]=strtod(nombre,NULL);

			}

	while (letter != 10  && letter!=13 && letter !='\n'&& !feof(f_in))/* go to end of line*/
		{letter=fgetc(f_in);}
	if (feof(f_in))
		printf("pb reading matrix CVS\n"),exit(1);

	}


free(ligne);

}


/*MEGA matrix is a plague because output can be customize a lot..  */
void readMatrixMega(FILE *f_in,struct DistanceMatrix *my_mat)
{

	int a,b,nbc=0,c,n;

	char *ligne,letter,nombre[16];

//	int nbcol=0;;
	int lower=-1;
	int nbcharmax=NBCHARMALLOC;
	int lindex=0;


	ligne=(char *)malloc(sizeof(char)*nbcharmax);

	my_mat->n=0;
	my_mat->names=NULL;
	my_mat->dist=NULL;

	printf("Read Mega Format\n");

	//read the header
	while (1)
		 {
			fscanf(f_in,"%[^\n]\n",ligne);

			char *s = ligne;
			while (*s) {
				*s = toupper((unsigned char) *s);
				s++;
			}

			if (feof(f_in)) printf("pb reading file...\n"),exit(1);

		 	if (strstr(ligne," OF TAXA :") !=NULL)
				my_mat->n=atoi(strchr(ligne,':')+1);

			if (strstr(ligne,"NTAXA=") !=NULL)
				my_mat->n=atoi(strchr(strstr(ligne,"NTAXA="),'=')+1);

			if (strstr(ligne,"DATAFORMAT=")!=NULL)
				{
				if (strstr(ligne,"LOWERLEFT")!=NULL)
					lower=1;
				else
					if (strstr(ligne,"UPPERRIGHT")!=NULL)
						lower=0;
					else
					printf("Unknown data format\n"),exit(1);
				}
			if (*ligne!='!' && strchr(ligne,';'))// we have reach the species desc line
				break;

			}


	printf("%ld data\n",my_mat->n);

	if (my_mat->n ==0) printf("abgd was not able to read your MEGA file: [TAXA] number not in the header\n"),exit(1);


	nbc=0;


//do some memory initialisation
	my_mat->names = (char **)malloc( sizeof(char *)* my_mat->n );
	if( ! my_mat->names )fprintf(stderr, "read_distmat: cannot allocate my_mat->names, bye"), exit(4);

/*	for(a=0;a<my_mat->n; a++){
		my_mat->names[a] = (char *)malloc( sizeof(char)*SIZE_NAME_DIST +1);
		if( ! my_mat->names[a] )
			fprintf(stderr, "read_distmat: cannot allocate my_mat->names[%d], bye",a), exit(4);
	}*/

	my_mat->dist = (double **)malloc( sizeof(double *)* my_mat->n );
	if( ! my_mat->dist )fprintf(stderr, "read_distmat: cannot allocate my_mat->dist, bye"), exit(4);
	for(a=0;a<my_mat->n; a++){
		my_mat->dist[a] = (double *)malloc( sizeof(double)* my_mat->n );
		if( ! my_mat->dist[a] )
			fprintf(stderr, "read_distmat: cannot allocate my_mat->dist[%d], bye",a), exit(4);
		}


	a=0;


//read species name
	while (1)
		{
			lindex=0;
			do
				fscanf(f_in,"%[^\n]\n",ligne);
			while (strlen(ligne)<=1); //skip white lines if needed

			if (strlen(ligne)<=1) break;

 			if (strchr(ligne,'#')!=0)
 					lindex=myIndex(ligne,'#');
 				else
 					{
 					if (strchr(ligne,']'))
 				 		lindex=myIndex(ligne,']');
					else
 						lindex=0;//printf("cant read species \n"),exit(1);
 					}
 			n=strlen(ligne+lindex);
 			my_mat->names[a]= (char *)malloc( sizeof(char)*(n+1));
 			strncpy(my_mat->names[a],ligne+lindex,n);
 			my_mat->names[a][n]='\0';

 									/*names with ( stink */
 			if (strchr(my_mat->names[a],'('))
 				remplace(my_mat->names[a],'(','_');
 			if (strchr(my_mat->names[a],')'))
 				remplace(my_mat->names[a],')','_');


 			a++;

 			if (a==my_mat->n)
 				break;

		}



	do {
		letter=fgetc(f_in);
		if (feof(f_in)) printf("error reading values\n"),exit(1);
		}
	while (letter!=']');	//last line read should be very long but some empty lines occur ....


letter=fgetc(f_in); //be sure we areon  line 1 of matrix
for (a=0;a<my_mat->n;a++){
		c=0;
		while( letter != ']' && !feof(f_in)) //reading after the name.
			letter=fgetc(f_in);

		if (feof(f_in))printf("problem reading your file\n"),exit(1);

		for (b=0;b<=a;b++)
			{
			c=0;
			while( (letter=fgetc(f_in)) == ' ');
			if (feof(f_in) ) break;
			while ( (letter != ' ') && (letter!='\n') && (letter != 10 ) && (letter!=13) && (letter!='[')){
				if (letter==',') letter='.';
				if (letter=='?')
				{
				fprintf(stderr,"**Warning distance between %s and %s is unknown,exiting<BR>\n",my_mat->names[a],my_mat->names[b]);exit(1);
				}


				nombre[c]=(char) letter;
//				printf("%d %c ",letter,letter);
				c++;
				if (c>15) {printf("too much char %d \n",letter);break;}

				letter=fgetc(f_in);
				if (feof(f_in)) break;
				}
	    	nombre[c]='\0';
	    	if (c==0)
	    		my_mat->dist[b][a]=my_mat->dist[a][b]=0;
	    	else
				my_mat->dist[b][a]=my_mat->dist[a][b]=strtod(nombre,NULL);

			}

		while (letter != 10  && letter != ']'  && letter!=13 && letter !='\n'&& !feof(f_in))/* go to end of line*/
			{letter=fgetc(f_in);}
		if (a!=my_mat->n -1 && feof(f_in))
			printf("pb reading matrix CVS\n"),exit(1);

	}

	free(ligne);


}

/*
	Takes a distance file as an input (phylip format)
	Return a struc with a distance matrix
*/

struct DistanceMatrix read_distmat(FILE *f_in,float ts_tv,int fmeg){

	int a=0,b,c;
	int letter;
	char first_c;
	int kk=0;
	long ppos=0;
	int toalloc=0;
	struct DistanceMatrix my_mat;

	my_mat.ratio_ts_tv= ts_tv;
	first_c=fgetc(f_in);

	if (first_c=='#') a=1;

	rewind (f_in);
	if (fmeg==1)
		readMatrixMegaCVS(f_in,&my_mat);
	else
		if(a==1)
 	    	readMatrixMega(f_in,&my_mat);
 		 else {
 		 	printf("Phylip distance file\n");
			my_mat.n=0;
			my_mat.names=NULL;
			my_mat.dist=NULL;

			fscanf( f_in, "%ld", &my_mat.n);
 //fprintf(stderr,"->%d seqs to read\n",my_mat.n);
			while( (letter=fgetc(f_in)) != '\n' && !feof(f_in)) kk++;

			if (feof(f_in))printf("Pb with file\n"),exit(1);

			if (kk>10){
			printf("There might be a problem with your Phylip distance file\n");
			printf("If you have a MEGA file stop this by hitting ctrL C and check the help\n");
			}



			my_mat.names = (char **)malloc( (size_t) sizeof(char *)*my_mat.n );
			if( ! my_mat.names )fprintf(stderr, "read_distmat: cannot allocate my_mat.names, bye"), exit(4);



			my_mat.dist = (double **)malloc( (size_t) sizeof(double *)*my_mat.n );
			if( ! my_mat.dist )fprintf(stderr, "read_distmat: cannot allocate my_mat.dist, bye"), exit(4);
			for(a=0;a<my_mat.n; a++){
				my_mat.dist[a] = (double *)malloc( (size_t) sizeof(double)*my_mat.n );
				if( ! my_mat.dist[a] )
					fprintf(stderr, "read_distmat: cannot allocate my_mat.dist[%d], bye",a), exit(4);
			}


	//	fprintf(stderr,"reading names\n");
			for(a=0;a<my_mat.n; a++){

				c=0;
				toalloc=0;
				ppos=ftell(f_in);
				while( ((letter=fgetc(f_in)) != ' ')&& (letter !='\t')){

					if(c < SIZE_NAME_DIST-1){

						toalloc++;
					}

				}
			my_mat.names[a] = (char *)malloc( (size_t) sizeof(char)*	(toalloc+1));
			fseek(f_in,ppos,SEEK_SET);
			while( ((letter=fgetc(f_in)) != ' ')&& (letter !='\t') ) {

					if(c < SIZE_NAME_DIST-1){

						my_mat.names[a][c] = (char)letter;
						c++;
					}

				}
				my_mat.names[a][c]=0;
				//fprintf(stderr,"%s\n",my_mat.names[a]);


				for(b=0;b<my_mat.n; b++)
					{
					fscanf( f_in, "%lf", ( my_mat.dist[a] + b) );
					//if ( (my_mat.dist[a] + b <0 ||  my_mat.dist[a] + b >1 )
					//fprintf(stderr,"check your matrix , distances should be beetween 0 and 1\n"),exit(1);
					}


				while( ( (letter=fgetc(f_in)) != '\n') && (letter !='\t'));
			}

			fclose(f_in);



			}
//		printf("%ld data read\n",my_mat.n);
			return my_mat;

}







/*************************************************/
int myCompare(const void *v1, const void *v2)
{
const float *fv1 = (float *)v1;
const float *fv2 = (float *)v2;
//printf("%f %f\n",*fv1,*fv2);
if (*fv1< *fv2)
	return(-1);
else
	return (1);
}
/*************************************************/
void CreateHeadersvg(FILE *svgout,int largeur,int hauteur)
{
fprintf(svgout,"<?xml version=\"1.0\" standalone=\"no\"?>\n");
fprintf(svgout,"<!DOCTYPE svg PUBLIC \"-//W3C//DTD SVG 1.1//EN\"\n") ;
fprintf(svgout,"\"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd\">\n");
fprintf(svgout,"<svg xmlns=\"http://www.w3.org/2000/svg\"\n");
fprintf(svgout,"width=\"%d\" height=\"%d\" >\n",largeur,hauteur);
fprintf(svgout,"<g>\n"); // g for grouping all the graphic otherwise each square is an object
}


/*************************************************/
/*plot 2 files distance hist and rank dist*/
void createSVGhisto(char *file,struct DistanceMatrix dist_mat,int nbbids)
{
int i,j,k;
int *histo;
float maxi=0;
char chaine [12];

	int largeur=720;
	int hauteur=520;
	int marge=40;
	int bordure=60;
	int sizelegend=45;
	int x1,y1,y2,x2,xt;

	float pas;
	FILE *svgout;

	double intervalle,echellex,echelley;
	char filename[256];
	float *histocum;
	char  *colors[3]={"#FFFFFF","#D82424","#EBE448"};
	int nbcomp=((dist_mat.n * (dist_mat.n -1)))/2.0;



	sprintf(filename,"%s.disthist.svg",file);

	svgout=fopen(filename,"w");
	CreateHeadersvg(svgout,largeur+sizelegend, hauteur+sizelegend);

	histo=malloc(sizeof(int)*nbbids+1);
	if (histo==NULL)
	fprintf(stderr,"pb malloc histo(1)\n"),exit(1);

	histocum=malloc(sizeof(float)*nbcomp+1);
	if (histo==NULL)
	fprintf(stderr,"pb malloc histo(2)\n"),exit(1);

	for (i=0;i<nbbids;i++)histo[i]=0;

	k=0;
	for (i=0;i<dist_mat.n-1;i++)
		{
		for (j=i+1;j<dist_mat.n;j++)
			{
			if (maxi<dist_mat.dist[i][j])
				maxi=dist_mat.dist[i][j];
			histocum[k++] = (float) dist_mat.dist[i][j];

			}
	}
	printf("sorting distances\n");
	qsort(histocum, nbcomp,sizeof(float),myCompare);
	printf("sorting distances done\n");

	intervalle=maxi/(float)nbbids;
	k=0;
	for (i=0;i<dist_mat.n-1;i++)
		for (j=i+1;j<dist_mat.n;j++)
			{
			k=dist_mat.dist[i][j]/intervalle;
			histo[k]++;
			}


	maxi=0;

for (i=0;i<nbbids;i++)
	{
	if (maxi<histo[i])
		maxi=histo[i];

	}
	fflush(stdout);
	largeur=largeur -bordure;
	hauteur=hauteur -bordure;



	echellex=(float)largeur/nbbids;
	echelley=(float)hauteur/maxi;


	fprintf(svgout,"<line x1=\"%d\" y1=\"%d\"  x2=\"%d\" y2=\"%d\" style=\" stroke: black;\"/>\n",marge,marge,marge,hauteur+marge	 );
	fprintf(svgout,"<line x1=\"%d\" y1=\"%d\"  x2=\"%d\" y2=\"%d\" style=\" stroke: black;\"/>\n", marge ,hauteur+marge ,largeur+marge,hauteur+marge);

	pas=maxi/10.0;

	for(i=0;i<10;i++)
		{
			y1=hauteur+marge - ((i+1)*echelley*pas) ;
			fprintf(svgout,"<line x1=\"%d\" y1=\"%d\"  x2=\"%d\" y2=\"%d\" style=\" stroke: black;\"/>\n",marge-3, y1,marge,y1 );
			fprintf(svgout,"<text x=\"%d\" y=\"%d\" style=\"font-family: monospace; font-size: 10px;\">%d</text>\n",
			5,y1,(int)((i+1)*pas));
			}


	fprintf(svgout,"<text x=\"5\" y=\"15\" style=\"font-family: monospace; font-size: 10px;\">nbr</text>\n");


//plotting squares and values and ticks on x axis; write the image map using the exact same values
	for (i=0;i<nbbids;i++)
		{
		//plot the value
		x1=marge+ ((i)*echellex);
		y1=hauteur+marge-(histo[i]*echelley);
		y2=(histo[i]*echelley) ;
		fprintf(svgout,"<rect x=\"%d\" y=\"%d\" width=\"%d\" height=\"%d\"  fill= \"#EBE448\"  style=\" stroke: black;\" />\n", x1, y1, (int)echellex,y2);

		if ((nbbids<=20) || (nbbids>20 && i%2==0)) // because too much people on x axis if too much bids
	   		{
	   		sprintf(chaine,"%.2f",i*intervalle);
			fprintf(svgout,"<line x1=\"%d\" y1=\"%d\"  x2=\"%d\" y2=\"%d\" style=\" stroke: black;\"/>\n",x1,marge+hauteur, x1,marge+hauteur+5);
 			fprintf(svgout,"<text x=\"%d\" y=\"%d\" transform=\"rotate(90,%d,%d)\" style=\"font-family: monospace; font-size: 10px;\">%s</text>\n",
					x1,marge+hauteur+5,x1,marge+hauteur+5,chaine);
	  		}

		}

	fprintf(svgout,"<text x=\"%d\" y=\"%d\" style=\"font-family: monospace; font-size: 10px;\">Dist. value</text>\n",largeur+25,marge+hauteur+10);
	fprintf(svgout,"</g>\n");
	fprintf(svgout,"</svg>\n");
	fclose(svgout);

printf("first plot done\n");


	//now draw the rank hist
	sprintf(filename,"%s.rank.svg",file);
	svgout=fopen(filename,"w");
	CreateHeadersvg(svgout,largeur+sizelegend+marge, hauteur+sizelegend+marge);

	fflush(stdout);
	maxi=histocum[nbcomp-1];
	echelley=(float)hauteur/maxi;


	fprintf(svgout,"<line x1=\"%d\" y1=\"%d\"  x2=\"%d\" y2=\"%d\" style=\" stroke: black;\"/>\n",marge,marge,marge,hauteur+marge	 );
	fprintf(svgout,"<line x1=\"%d\" y1=\"%d\"  x2=\"%d\" y2=\"%d\" style=\" stroke: black;\"/>\n", marge ,hauteur+marge ,largeur+marge,hauteur+marge);


	pas=hauteur/10;
	for(i=0;i<10;i++)
		{

			y1=hauteur+marge - ((i+1)*pas) ;
			fprintf(svgout,"<line x1=\"%d\" y1=\"%d\"  x2=\"%d\" y2=\"%d\" style=\" stroke: black;\"/>\n",marge-3, y1,marge,y1);
			sprintf(chaine,"%.2f",(float)(i+1)*(maxi/10));
			fprintf(svgout,"<text x=\"%d\" y=\"%d\" style=\"font-family: monospace; font-size: 10px;\">%s</text>\n",marge-(8*(int)strlen(chaine)), y1 ,chaine);

			}


	//drawing x axis
	echellex=(float)largeur/(float)nbcomp;
	for (i=0;i<10;i++)
			{
			k=(i+1)*((float)largeur/10.0);
			xt=marge+ k;

			sprintf(chaine,"%d",(i+1)*(nbcomp/10));
 	 		fprintf(svgout,"<line x1=\"%d\" y1=\"%d\"  x2=\"%d\" y2=\"%d\" style=\" stroke: black;\"/>\n" ,	xt,marge+hauteur, xt,marge+hauteur+5);
			fprintf(svgout,"<text x=\"%d\" y=\"%d\" transform=\"rotate(90,%d,%d)\" style=\"font-family: monospace; font-size: 10px;\">%s</text>\n",
				xt,marge+hauteur+5,xt,marge+hauteur+5,chaine);
			}
		fprintf(svgout,"<text x=\"%d\" y=\"%d\" style=\"font-family: monospace; font-size: 10px;\">Rank</text>\n",largeur+marge+5,marge+hauteur-10);
		fprintf(svgout,"<text x=\"%d\" y=\"%d\" style=\"font-family: monospace; font-size: 10px;\">Dist. value</text>\n",5,15);

	fprintf(svgout,"<polyline style=\"stroke: %s; stroke-width:1;fill: none;\"  points=\"",colors[1]);
	x2=y2=0;
	for (i=0;i<nbcomp-1;i++)
		{
			x1=marge+ ((i)*echellex);
			y1=hauteur -(histocum[i]*echelley) +marge;
			if (i==0 || x1!=x2 || y1!=y2)
				fprintf(svgout,"%d %d,",x1,y1); //draw new coords only
			x2=x1;
			y2=y1;

			}
	x1=marge+ ((i)*echellex);
	y1=hauteur -(histocum[i]*echelley) +marge;
	fprintf(svgout,"%d %d\"/>",x1,y1);

	fprintf(svgout,"</g>\n");
	fprintf(svgout,"</svg>\n");
	fclose(svgout);

	free(histo);

printf("second plot done\n");
}





/*Create the main result file: plat the different number of groups found for the value considered*/
void CreateGraphFiles(int *myPart,int *partInit,double *maxDist, int NbPart,char *dirfiles,char *meth,char *lefich)
	{

	int largeur=720;         /* size of the whole graphic image */
	int hauteur=520;         /* size of the whole graphic image */

	int marge=40;            /* place to write legend and other stuff */
	int bordure=60;          /* place to write legend and other stuff */
	int sizelegend=45;       /* place to write legend and other stuff */

	int maxSpecies=0;
	int x1,y1,xl,xt;

	int i,j,k,nbTicks,diff,whichtick;
	double *vech;
	int minPow,maxPow;
	FILE *svgout;

	int grossomodo;
	double echelley,echellex;
	char v[12];
	char  *colors[3]={"#FFFFFF","#D82424","#EBE448"};


	/*usefull for drawing a nice log scale*/
	minPow=(int)floor(log10(maxDist[0]));
	if (maxDist[0]==0) printf("Very unexpected error (1)\n"),exit(1);
	maxPow=(int)floor(log10(maxDist[NbPart-1]));
	if (maxDist[NbPart-1]==0) printf("Very unexpected error(2) \n"),exit(1);
	diff=abs(minPow)-abs(maxPow);
	nbTicks=10*(diff+1);
	vech=malloc (sizeof (double) * nbTicks);
	for (i=0,k=minPow;i<=diff;i++,k++)
		for (j=0;j<10;j++)
			vech[j+(i*10)]	=pow(10,k)*j;	//values of the log scale

	svgout=fopen (lefich,"w");
	if (svgout==NULL)
		printf("pb ouverture fichier\n"),exit(1);
	CreateHeadersvg(svgout,largeur+sizelegend,hauteur+sizelegend+10);

	for (i=0;i<NbPart;i++)
		{
		if (myPart[i]>maxSpecies)
			maxSpecies=myPart[i]; //find the number max of species in one partition
		}

	grossomodo=maxSpecies/10;  	//try to have a scale with numbers ending by 0s...
	maxSpecies=grossomodo*10 +10;

	largeur=largeur -bordure;
	hauteur=hauteur -bordure;

	//compute scales on each axes
	echelley=(float)hauteur/(float)maxSpecies;
	echellex=(float)largeur/(log10(maxDist[NbPart-1]/maxDist[0]));
	fprintf(svgout,"<line x1=\"%d\" y1=\"%d\"  x2=\"%d\" y2=\"%d\" style=\" stroke: black;\"/>\n",	 marge,marge,marge,hauteur+marge);
	fprintf(svgout,"<text x=\"5\" y=\"12\" style=\"font-family: monospace; font-size: 10px;\">nb. groups</text>\n");
	fprintf(svgout,"<line x1=\"%d\" y1=\"%d\"  x2=\"%d\" y2=\"%d\" style=\" stroke: black;\"/>\n",	marge ,hauteur+marge ,largeur+marge,hauteur+marge) ;
	fprintf(svgout,"<text x=\"%d\" y=\"%d\" style=\"font-family: monospace; font-size: 10px;\">prior intraspecific divergence (P)</text>\n",largeur-120,2*sizelegend+hauteur);


	xl=largeur/NbPart;

	/*drawing y axis ticks and values*/
	whichtick=pow(10,(int)(log10(maxSpecies)-1));

	for(i=0,j=0;i<=maxSpecies;j++)
			{
			y1=hauteur+marge -(i*echelley) ;

			fprintf(svgout,"<line x1=\"%d\" y1=\"%d\"  x2=\"%d\" y2=\"%d\" style=\" stroke: black;\"/>\n",	marge-3, y1,marge,y1) ;
			if ((maxSpecies/whichtick)<30 || ((maxSpecies/whichtick)>=30 && j%2==0))
				fprintf(svgout,"<text x=\"%d\" y=\"%d\" style=\"font-family: monospace; font-size: 10px;\">%d</text>\n",17,y1-5,i);
			i=i+whichtick;
			}

	/*drawing x axis ticks*/
	for (i=0;i<nbTicks;i++)
	{

	if (vech[i]>=maxDist[0] && vech[i]<=maxDist[NbPart-1])
		{
		xt=marge+ (log10(vech[i]/maxDist[0])*echellex);
		fprintf(svgout,"<line x1=\"%d\" y1=\"%d\"  x2=\"%d\" y2=\"%d\" style=\" stroke: black;\"/>\n",	xt,marge+hauteur, xt,marge+hauteur+3) ;

		}
	}
	fprintf(svgout,"<rect x=\"%d\" y=\"%d\" width=\"5\" height=\"5\" fill= \"%s\" />\n",
							largeur -20, 20, colors[1]);
	fprintf(svgout,"<text x=\"%d\" y=\"%d\" style=\"font-family: monospace; font-size: 10px;\">Recursive Partition</text>\n",largeur-20+8,25);
	fprintf(svgout,"<rect x=\"%d\" y=\"%d\" width=\"5\" height=\"5\" fill= \"%s\" />\n",
							largeur-20, 40, colors[2]);
	fprintf(svgout,"<text x=\"%d\" y=\"%d\" style=\"font-family: monospace; font-size: 10px;\">Initial Partition</text>\n",largeur-20+8,45);


	/*plotting results and the P corresponding on x scale*/
	for (i=0;i<NbPart;i++)
	{
		x1=marge+ (log10(maxDist[i]/maxDist[0])*echellex); //(x1,y1,x2,y2) are coords of the little square

		y1=hauteur  -(myPart[i]*echelley) +marge;

		fprintf(svgout,"<rect x=\"%d\" y=\"%d\" width=\"5\" height=\"5\" fill= \"%s\" />\n",
							 x1, y1, colors[1]);
		sprintf(v,"%.4f",maxDist[i]);
		fprintf(svgout,"<line x1=\"%d\" y1=\"%d\"  x2=\"%d\" y2=\"%d\" style=\" stroke: black;\"/>\n",	x1,marge+hauteur, x1,marge+hauteur+5) ;
		fprintf(svgout,"<text x=\"%d\" y=\"%d\" transform=\"rotate(90,%d,%d)\" style=\"font-family: monospace; font-size: 10px;\">%s</text>\n",
					x1-5,marge+hauteur+5,
					x1-5,marge+hauteur+5,v);

		y1=hauteur  -(partInit[i]*echelley) +marge;
		fprintf(svgout,"<rect x=\"%d\" y=\"%d\" width=\"5\" height=\"5\" fill= \"%s\" />\n",
							 x1, y1, colors[2]);
	}

		fprintf(svgout,"</g>\n");
	fprintf(svgout,"</svg>\n");
fclose(svgout);
}




double * Compute_myDist( double minDist, double MaxDist, int nbStepsABGD ){

	double *myDist;
	double myScale,myInit;
	int ii;

	myDist = (double *) malloc( (size_t) sizeof(double) * nbStepsABGD );

	myDist[0]=minDist;

	myScale=log10( MaxDist/myDist[0] ) / (float)( nbStepsABGD-1.0 );

	myInit=log10( myDist[0] );

 	for (ii=1;ii< nbStepsABGD-1	;ii++)	{
 		myDist[ii]=pow(10,myInit+(myScale*ii));
 		}
 	myDist[ii]=MaxDist;


	return myDist;

}

char *Built_OutfileName( char *file ){

	char * bout;
	int ii;

	char *simplename;

	bout = ( strrchr(file,'/') == NULL )? file : strrchr(file,'/')+1;        /* either the begining or after the last '/' */

	ii = ( strchr(bout,'.')==NULL )? strlen(bout) : strchr(bout,'.')-bout ;  /* # of char before the first '.' */


	simplename=malloc(sizeof(char)*ii+1);

	strncpy(simplename,bout,ii);

	simplename[ii]='\0';

	return simplename;
}

char * compute_DistTree( struct DistanceMatrix  distmat, char *dirfiles ){


	int ii=0;
	FILE *fnex;
	char fileNex[128];
	int c;
	char *newickStringOriginal;

	sprintf(fileNex,"%s/.newick.tempo.%d",dirfiles,getpid());
	mainBionj(distmat ,fileNex);

	fnex=fopen(fileNex,"r");
	if(!fnex)fprintf(stderr, "compute_DistTree: cannot read in file %s, bye\n", fileNex),exit(1);

	while(fgetc(fnex)!=EOF)
		ii++;

	newickStringOriginal   = (char *)malloc( (size_t)  sizeof(char)*ii+1);

	if(!newickStringOriginal )
		fprintf(stderr, "compute_DistTree: cannot allocate newickStringOriginal or newickString, bye\n"),exit(1);

	rewind (fnex);
	ii=0;
	while(1){
		c=fgetc(fnex);
		if (c==EOF)
			break;
		if ( isascii(c) )
			*( newickStringOriginal + ii++ ) = c;
	}

	*(newickStringOriginal +ii)='\0';
		fclose(fnex);
unlink(fileNex);
return(newickStringOriginal);



}

/********************

	  Help and Usage

*********************/

void syntax(char *arg0){
	fprintf(stderr, "syntax is '%s [-h] [options] distance_matrix or fasta file'\n", arg0);
}

void usage(char *arg0)
{
 	fprintf(stderr,"/*\n\tAutomatic Barcod Gap Discovery\n*/\n");
 	syntax(arg0);
 	fprintf(stderr, "\tfile is EITHER a distance matrix in phylip format OR aligned sequences in fasta format\n"
			);

 	fprintf(stderr,
 	"Options are:\n\
	\t-h    : this help\n\
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

	exit(1);
}
