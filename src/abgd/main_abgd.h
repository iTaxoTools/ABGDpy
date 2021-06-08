/*
	Header file for main_abgd.c, used by abgdmodule.c.
*/

int ReadFastaSequence( FILE *f, struct FastaSeq *laseq);
void print_seq(struct FastaSeq *mesSeq,int nseq);
struct DistanceMatrix compute_dis(FILE *f,int method,float ts_tv);
int myIndex(char *l, char c);
char *my_get_line(char *ligne,FILE *f_in,int *nbcharmax);
void remplace(char *name,char c,char newc);
void readMatrixMegaCVS(FILE *f_in,struct DistanceMatrix *my_mat);
void readMatrixMega(FILE *f_in,struct DistanceMatrix *my_mat);
struct DistanceMatrix read_distmat(FILE *f_in,float ts_tv,int fmeg);
int myCompare(const void *v1, const void *v2);
void CreateHeadersvg(FILE *svgout,int largeur,int hauteur);
void createSVGhisto(char *file,struct DistanceMatrix dist_mat,int nbbids);
void CreateGraphFiles(int *myPart,int *partInit,double *maxDist, int NbPart,char *dirfiles,char *meth,char *lefich);
double * Compute_myDist( double minDist, double MaxDist, int nbStepsABGD );
char *Built_OutfileName( char *file );
char * compute_DistTree( struct DistanceMatrix  distmat, char *dirfiles );
void syntax(char *arg0);
void usage(char *arg0);
