from .. import ParallelSampler
from . import pmc
import numpy as np

#needs to be global for MPI to behave
#I think this is still true, at least
global pipeline

def posterior(p):
    # PMC code needs posterior not log posterior
    return pipeline.posterior(p)

class PMCSampler(ParallelSampler):
    parallel_output = False
    sampler_outputs = [("like",float), ("weight",float)]

    def config(self):
        global pipeline
        pipeline = self.pipeline
        self.n_iterations = self.read_ini("iterations", int, default=30)
        self.n_components = self.read_ini("components", int, default=5)
        self.n_samples = self.read_ini("samples_per_iteration", int, 
            default=1000)

        #start values from prior
        start = self.pipeline.start_vector()
        covmat = self.load_covariance_matrix()

        #Sampler object itself.
        quiet = self.pipeline.quiet
        self.sampler = pmc.PopulationMonteCarlo(posterior, self.n_components, 
            start, covmat, quiet=quiet)

        self.interrupted = False
        self.iterations = 0
        self.samples = 0

    def execute(self):
        #Run the MCMC  sampler.
        try:
            results = self.sampler.sample(self.n_samples)
            #returns samples, like, extra, weights
        except KeyboardInterrupt:
            self.interrupted=True
            return
            
        self.iterations += 1
        self.samples += self.n_samples

        for (vector, like, extra, weight) in zip(*results):
            self.output.parameters(vector, extra, (like,weight))

        print "Done %d iterations, %d samples" % (self.iterations, self.samples)


    def is_converged(self):
         # user has pressed Ctrl-C
        if self.interrupted:
            print "Interrupted..."
            return True
        if self.iterations >= self.n_iterations:
            print "Full number of samples generated; sampling complete"
            return True
        return False



    def load_covariance_matrix(self):
        covmat_filename = self.read_ini("covmat", str, "").strip()
        if covmat_filename == "":
            covmat = np.array([p.width()/100.0 for p in self.pipeline.varied_params])
        elif not os.path.exists(covmat_filename):
            raise ValueError(
            "Covariance matrix %s not found" % covmat_filename)
        else:
            covmat = np.loadtxt(covmat_filename)

        if covmat.ndim == 0:
            covmat = covmat.reshape((1, 1))
        elif covmat.ndim == 1:
            covmat = np.diag(covmat ** 2)

        nparams = len(self.pipeline.varied_params)
        if covmat.shape != (nparams, nparams):
            raise ValueError("The covariance matrix was shape (%d x %d), "
                    "but there are %d varied parameters." %
                    (covmat.shape[0], covmat.shape[1], nparams))
        return covmat
