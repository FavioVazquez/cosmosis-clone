MPI=0
include ${COSMOSIS_SRC_DIR}/config/compilers.mk
FCFLAGS=$(FFLAGS)

ifeq ($MPI,1)
error Argh MPI
FCOMP=$(MPIFC)
else
FCOMP=$(FC)
export 
endif

# Where polychord is stored
POLYCHORD_DIR = ./PolyChord/src

# Where likelihoods are stored
LIKELIHOOD_DIR = ./likelihoods

# Where likelihood examples are stored
EXAMPLE_LIKELIHOOD_DIR = $(LIKELIHOOD_DIR)/examples

# Where binaries are stored
BIN_DIR = ./bin

# Add these libraries to the program
LIBCHORD += -L$(POLYCHORD_DIR) -lchord
LIBLIKE += -L$(LIKELIHOOD_DIR) -L$(EXAMPLE_LIKELIHOOD_DIR)
EXT_LIBS += -lstdc++


INC += -I$(POLYCHORD_DIR) 

# likelihood libraries, this is created by changing X to libX.a
EXAMPLE_LIKELIHOODS = $(patsubst %,lib%.a,$(EXAMPLES))
PROGRAM_LIKELIHOODS = $(patsubst %,lib%.a,$(PROGRAMS))


# Export all of the necessary variables  
export DEBUG COMPILER_TYPE FCFLAGS MPI AR FC CC CCFLAGS EXAMPLE_LIKELIHOODS IPO EXT_LIBS MPIFC


# "make" builds all
all: polychord_interface.so

polychord_interface.so: libchord.a polychord_interface.F90
	$(FC) -shared -o polychord_interface.so $(FCFLAGS) $(INC) polychord_interface.F90 $(LIBCHORD) 

# Rule for building polychord library
libchord.a:
	cd $(POLYCHORD_DIR) && make libchord.a



clean:
	rm -f *.o *.mod *.MOD
	cd $(POLYCHORD_DIR) && make clean
