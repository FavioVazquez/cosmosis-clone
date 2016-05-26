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
MPIFCOMP=$(MPIFC)


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
LIBCHORD_MPI += -L$(POLYCHORD_DIR) -lchord_mpi
LIBLIKE += -L$(LIKELIHOOD_DIR) -L$(EXAMPLE_LIKELIHOOD_DIR)
EXT_LIBS += -lstdc++


INC += -I$(POLYCHORD_DIR) 

# likelihood libraries, this is created by changing X to libX.a
EXAMPLE_LIKELIHOODS = $(patsubst %,lib%.a,$(EXAMPLES))
PROGRAM_LIKELIHOODS = $(patsubst %,lib%.a,$(PROGRAMS))


# Export all of the necessary variables  
export DEBUG COMPILER_TYPE FCFLAGS MPI AR FC CC CCFLAGS EXAMPLE_LIKELIHOODS IPO EXT_LIBS MPIFC MPIFCOMP


# "make" builds all
all: polychord_interface.so polychord_interface_mpi.so

polychord_interface.so: $(POLYCHORD_DIR)/libchord.a polychord_interface.F90
	$(FC) -shared -o polychord_interface.so $(FCFLAGS) $(INC) polychord_interface.F90 $(LIBCHORD) 

polychord_interface_mpi.so: $(POLYCHORD_DIR)/libchord_mpi.a polychord_interface.F90
	$(MPIFC) -shared -o polychord_interface_mpi.so $(FCFLAGS) -DMPI $(INC) polychord_interface.F90 $(LIBCHORD_MPI) 


# Rule for building polychord library
$(POLYCHORD_DIR)/libchord.a:
	cd $(POLYCHORD_DIR) && make libchord.a

$(POLYCHORD_DIR)/libchord_mpi.a:
	cd $(POLYCHORD_DIR) && make libchord_mpi.a

.PHONY: $(POLYCHORD_DIR)/libchord.a $(POLYCHORD_DIR)/libchord_mpi.a

clean:
	rm -f *.o *.mod *.MOD
	cd $(POLYCHORD_DIR) && make clean
