
This is a module that wraps ABGD for use with Python.

Original ABGD:	https://bioinfo.mnhn.fr/abi/public/abgd/

Source code:	https://bioinfo.mnhn.fr/abi/public/abgd/last.tgz


## Usage example

```
import abgdc
abgdc.main({'file':'test.fas','all':True})
```

## Arguments

The following keys are checked in the provided dictionary: (TBA)

- file:		accepted formats: fasta alignment, phylip distance file, MEGA distance file (see below)
- out:		existent directory where results files are written
- method:	distance (0: Kimura-2P, 1: Jukes-Cantor --default--, 3: simple distance)
- bids:		number of bids for graphic histogram of distances (default is 20)
- steps:	number of steps in [Pmin,Pmax] (default is 10)
- min:		minimal a priori value (default is 0.001) -Pmin-
- max:		maximal a priori value (default is 0.1) -Pmax-lt is 20)
- slope:	mininmum Slope Increase (default is 1.5)
- rate:		transition/transversion (for Kimura 3-P distance) default:2.0
- mega:		if True, the distance Matrix is supposed to be MEGA CVS (other formats are guessed)
- all:		output all partitions and tree files (default only graph files)
- verbose:	verbose mode (outputs a lot of values)
- simple:		option for only groups
- logfile:	redirect and save stdout/stderr to file
- spart:		create spart files

## Warning

This module often uses exit() to abort in case of error, shutting down the whole Python process that called it.
It is also possible that allocated memory is not freed in such cases. For this reason,
it is recommended to run _abgdc.main() on its own subprocess.
To verify that no errors occured, check that the process exitcode is 0.

## Changes

The original ABGD code was also slightly altered for the cross-platform wrapper to compile. Here follows a *noncomprehensive* list of changes:

- Create `main_abgd.h`: header file exposing `main_abgd.c` functions, used by `abgdmodule.c/abgd_main`
- Remove header includes: `strings.h` `unistd.h` `dirent.h`: linux-only libraries
- Disable function: `abgdCore.c/print_groups_newick`: used non-standard `strcasestr`, function not called anywhere
- Edit function: `main_abgd.c/readMatrixMega`: used non-standard `strcasestr`: replaced with `toupper` and `strstr`
- Remove function: `main_abgd.c/main`: functionality copied to `abgdmodule.c/abgd_main` with the following changes:
-- Replace `bzero` with `memset`
-- Accept a Python dictionary object as a single argument
-- Change variable `dirfiles` into a `const char`
-- Replace some `exit(1)` occurences with Python exceptions
-- No longer prefix output files with input basename
-- Add option for stdout/stderr redirection to a file


## Original README file

```
ABGD command line: Brief Install and How to Description



******Install
you can install in 4 steps by typing the 4 following commands in a terminal
1) cd <dir where abgd.tgz is located>
2) tar -xvzf abgd.tgz
3) cd Abgd
4) make
You should have a working abgd script in your Abgd directory.

******Run:
If you are in a hurry and want as soon as possible to see abgd working, just type

./abgd <file_name>


<file_name> must be one of these files:
-fasta alignment
-phylip distance file
-MEGA distance file (see MEGA information below)

./abgd -h
will give you this help

		-m	  : if present the distance Matrix is supposed to be MEGA CVS (other formats are guessed)
		-a	  : output all partitions and tree files (default only graph files)
		-v	  : verbose mode (outputs a lot of values)
		-p #  : minimal a priori value (default is 0.001) -Pmin-
		-P #  : maximal a priori value (default is 0.1) -Pmax-
		-n #  : number of steps in [Pmin,Pmax] (default is 10)
		-b #  : number of bids for graphic histogram of distances (default is 20)
		-d #  : distance (0: Kimura-2P, 1: Jukes-Cantor --default--)
		-o #  : existent directory where results files are written --(default is .)
		-s #  : mininmum Slope Increase (default is 1.5)
		-t #  : transition/transversion (for Kimura 3-P distance) default:2

As the -a option can produce a good number of results file, we recommand that you use the -o option with it to specify an output directory.
To reduce the number of files:if you want, for example, output only one partition you should specify n=1 and Pmin=Pmax in the command line


******Results:
Each run of abgd will produce 3 SVG files.
SVG files can be opened with any browser or edited with a free sofware as Inkscape (inkscape.org)
The main result file is named as your data file but the extension is substitued by ".abgd.svg"
Two additional graphic files showing the distances distribution are also created
The first one is ended by ".disthist.svg" and shows the histogram of distance (you can choose the number of bids with -b option)
The second one is ended by ".rank.svg" and is a plot of the distance from the smallest to the highest rank.


If you choose the -a option, you will get much more files:
For each step, a list of all groups with sequences names and a newick tree representation (each species will be followed by the name of the abgd group) are written.
This list is written once for the initial partition and second for the recursive partiton
They end by ".partinit.#.txt" (or ".part.#.txt") and ".partinit.#.tree" or (".part.#.tree"), # beeing the number of the examined step
The names of these files are outputted at the program completion.
Contrary to the web site there is no limitation in the sequence number when building the tree.



If you want the maximum of information to be displayed run abgd with -v

******Information

This software is delivered with  BIONJ C source code very slightly modified to construct the newick tree.

You can get more information on BIONJ here:
BIONJ: an improved version of the NJ algorithm based on a simple model of sequence data."
Gascuel O. Molecular Biology and Evolution. 1997 14:685-695



-------------------MEGA information---------------
Two MEGA distance files are read:

*********
CVS file (default MEGA 5)  formated as follows:
[name 1],,
[name 2],##,,
...
[name n],##,##,... ##,,

You must specify a -m option on command line with this type of file

**********
default MEGA 4, formated as below
#mega
!Format DataType=Distance DataFormat=LowerLeft NTaxa=100
!other informations
	line
	line...

;
[1] #name 1
[2] #name 2
...
[n] #name n

[1 2.... n]
[1]
[2] ##
[3] ## ##
...
[n] ## ## .....##

This mega format is assumed  as soon as the "#mega" keyword is present on 1st line
Some variations are tolerated in this latter format, but if you get an error you should try to stick to the one above.
```