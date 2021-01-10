
SRC= abgdCore.c \
     bionjcabgd.c
	
OBJ= $(SRC:.c=.o)

CC= gcc

CFLAGS= -O2

all: abgd 

%.o: %.c
	$(CC) $(CFLAGS) $(INCLUDE_DIRS) -c -o $@ $<;


abgd:	$(OBJ) main_abgd.c
	$(CC) $(CFLAGS)  -o $@  $(OBJ) main_abgd.c -lm


clean:
	\rm -f abgd abgdWeb.cgi *.o

