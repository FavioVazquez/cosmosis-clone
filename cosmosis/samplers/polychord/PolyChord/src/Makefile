# Object files:
# find all files ending in 90, and change .f90 and .F90 to .o, 
OBJECTS = $(patsubst %.F90,%.o,$(patsubst %.f90,%.o,$(wildcard *90)))
# include the dependencies
include makefile.dep
include makefile_mpi.dep

MPI_OBJECTS = $(patsubst %.o,mpi/%.o, $(OBJECTS))

# The polychord library depends on the objects
# we should make all the objects and the archive them with AR
libchord.a: $(OBJECTS)
	$(AR) rc $@ $^

libchord_mpi.a: $(MPI_OBJECTS)
	$(AR) rc $@ $^

mpi/%.o: %.f90
	$(MPIFCOMP) $(FCFLAGS) -DMPI -o $@ -c $< $(EXT_LIBS)

mpi/%.o: %.F90
	$(MPIFCOMP) $(FCFLAGS) -DMPI -o $@ -c $< $(EXT_LIBS)


# General rule for building object file (.o)  from fortran files (.f90)
%.o: %.f90
	$(FCOMP) $(FCFLAGS) -c $< $(EXT_LIBS)  

# General rule for building object file (.o)  from fortran files (.F90)
%.o: %.F90
	$(FCOMP) $(FCFLAGS) -c $< $(EXT_LIBS)  


# Utility targets
.PHONY: clean

clean:
	rm -f *.o *.mod *.MOD mpi/*.o  *.a
