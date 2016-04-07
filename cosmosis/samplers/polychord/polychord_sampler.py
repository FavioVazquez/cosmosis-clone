from .. import ParallelSampler
import ctypes
import os
import cosmosis
import numpy as np
import sys

logpost_type = ctypes.CFUNCTYPE(
    ctypes.c_double,  #likelihood
    ctypes.c_int, #nparam
    ctypes.c_int, #nderived
    ctypes.POINTER(ctypes.c_double),  #parameters
    ctypes.POINTER(ctypes.c_double),  #derived parameters
)

output_type = ctypes.CFUNCTYPE(
    None,
    ctypes.c_int, #sample index
    ctypes.c_double,  #weight
    ctypes.c_double,  #post
    ctypes.c_int, #length of the rest of the parameters
    ctypes.POINTER(ctypes.c_double),    
)

def flatten_strings(names,n):
    return ''.join(name.ljust(n) for name in names)

class PolychordSampler(ParallelSampler):
    parallel_output = False
    sampler_outputs = [("post", float), ("weight", float)]
    def config(self):
        print "pool", self.pool
        if self.pool:
            libname = "polychord_interface_mpi.so"
        else:
            libname = "polychord_interface.so"

        dirname = os.path.split(__file__)[0]
        libname = os.path.join(dirname, libname)
            
        try:
            dll = ctypes.cdll.LoadLibrary(libname)
        except Exception as error:
            sys.stderr.write("Multinest could not be loaded.\n")
            sys.stderr.write("This may mean an MPI compiler was not found to compile it,\n")
            sys.stderr.write("or that some other error occurred.  More info below.\n")
            sys.stderr.write(str(error)+'\n')
            sys.exit(1)


        self.converged=False

        self.ndim = len(self.pipeline.varied_params)
        self.nderiv = len(self.pipeline.extra_saves)
        self.last_nsample = -1

        polychord = dll.polychord_cosmosis_interface_
        polychord.argtypes = [
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            output_type,
            logpost_type,
        ]
        polychord.restype = ctypes.c_int
        self.polychord = polychord

        if self.output:
            def output_logger(c, weight, post, n, params):
                params = np.array([params[i] for i in xrange(n)])
                self.last_nsample = c
                self.output_params(params, post, weight)
        else:
            def output_logger(weight, post, n, params):
                pass
        self.wrapped_output_logger = output_type(output_logger)

        def posterior(nparam, nderived, params, derived):
            #Check lengths are what we expect
            assert nparam==self.ndim
            assert nderived==self.nderiv

            #pull out values from cube
            cube_vector = np.array([params[i] for i in xrange(nparam)])
            vector = self.pipeline.denormalize_vector(cube_vector)

            try:
                post, extra = self.pipeline.posterior(vector)
                print vector, post
            except KeyboardInterrupt:
                raise sys.exit(1)

            for i in xrange(nderived):
                derived[i] = extra[i]

            return post
        self.wrapped_posterior = logpost_type(posterior)

    def worker(self):
        self.sample()

    def execute(self):
        self.log_z = 0.0
        self.log_z_err = 0.0

        nparam = self.ndim
        nderived = self.nderiv
        names = flatten_strings([str(p) for p in self.pipeline.varied_params], 128)
        derived_names = flatten_strings(['--'.join(p) for p in self.pipeline.extra_saves], 128)
        output_sub = self.wrapped_output_logger
        logpost_func = self.wrapped_posterior

        status = self.polychord(nparam, names, nderived, derived_names, output_sub, logpost_func)
        print "Polychord status = ", status
        self.converged = True

        self.output.final("log_z", self.log_z)
        self.output.final("log_z_error", self.log_z_err)
        self.output.final("nsample", self.last_nsample)


    def output_params(self, params, post, weight):
        varied_params = params[:self.ndim]
        extra = params[self.ndim:]
        self.output.parameters(varied_params, extra, post, weight)
        self.output.flush()

    def is_converged(self):
        return self.converged

