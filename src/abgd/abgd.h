#ifndef ABGDWEB_H

#define ABGDWEB_H

#define DATE "April 11 2013"


/*if more than MAXSEQ4NEWICK then the newick string will not be computed (but all partitions will be computed) */
#define MAXSEQ4NEWICK 700
#define SIZE_NAME_DIST 100   /* do not store characters after SIZE_NAME_DIST */
#define WEB_ADMIN "sophie.brouillet@mnhn.fr"
struct Peak {

	double Dist;
	double Rank;
	double theta_hat;
};




struct DistanceMatrix {

	long n;            /* number of sequence */
	char **names;      /* store names, at most SIZE_NAME_DIST char */
	double **dist;     /* a 2-d matrix of distance [0, \inf] */
	double ratio_ts_tv;		/*transition/transversion rate*/

};


struct Composante {

	int nc;           /* numnber of composantes */
	int nn;           /* number of nodes / sequences */
	int nm;           /* number of masked/excluded nodes (with -1 in node_compid) */

	int *node_compid;   /* the comp_id of each node -- this starts by generating this array */

	int *n_in_comp;     /* number of nodes in each composante */
	int **comp;         /* a list of node id in each composante */

};

struct FastaSeq {
char *name;
char *seq;
};

#define MINI(a,b) ((a<=b)?a:b) 

struct DistanceMatrix GetDistMat (int nseq, struct FastaSeq *mesSeqs, int method,float ts_tv);
struct Peak find_abgd( double *Array, long N, long windsize_min, long windsize_max, short output_slope, double MaxDist ,double SlopeIncrease );
struct Peak FindFirstPeak( double *Array, long N, int winsiz, short output_slope, double *Pi, double MaxDist,double SlopeIncrease  );
double *matrix2list( struct DistanceMatrix  distmat, char *mask, long *Nval );
void setcomp( int node, int compid, int * node_compid, struct DistanceMatrix matrix, double max_dist, char *mask);
struct Composante compute_node_compid(  struct DistanceMatrix matrix, double max_dist, char *mask );
struct Composante extract_composante(  struct DistanceMatrix matrix, double max_dist, char *mask );

void distanceTN93 (struct FastaSeq *,int l,struct  DistanceMatrix  mymat);
void distanceK80 (struct FastaSeq *,int l,struct  DistanceMatrix  mymat);
void distanceJC69 (struct FastaSeq *,int l,struct  DistanceMatrix  mymat);

int comparaison(const void *v1, const void *v2);


void html_error(int nb);
int check_compat(char *s1,char *s2,int l);
int check_names(struct FastaSeq *mesSeq, int nbseq);
int mainBionj(struct DistanceMatrix distMat ,char *file_out);
long min_ws( long nval );
void reset_composante( struct Composante * c );
void print_groups( struct Composante my_comp , struct DistanceMatrix distmat  );
void update_composante(  struct Composante *main_comp, int id, struct Composante sub_comp );

void free_composante(  struct Composante c  );
void print_groups_files( struct Composante my_comp , struct DistanceMatrix distmat  ,FILE *f,int);
void print_groups_files_newick( struct Composante my_comp , struct DistanceMatrix distmat  ,FILE *f,char *lastring, FILE *f2,int);
void print_groups_newick( struct Composante my_comp , struct DistanceMatrix distmat  ,char *lastring, FILE *f2);
void free_distmat(  struct DistanceMatrix mat );
void print_distmat(  struct DistanceMatrix distmat  );
int callabgd (	double minDist,
				double MaxDist,
				int nbStepsABGD,
				int imethode,
				int nbbids,
				char *dirfiles,
				double minSlopeIncrease,
				float ts_tv,
				int fmeg,
				char * file);

#endif
