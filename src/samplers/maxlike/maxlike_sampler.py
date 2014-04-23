from sampler import Sampler
import numpy as np


MAXLIKE_INI_SECTION = "maxlike"


class MaxlikeSampler(Sampler):

    def config(self):
        self.tolerance = self.ini.getfloat(MAXLIKE_INI_SECTION,
                                           "tolerance", 1e-3)
        self.maxiter = self.ini.getint(MAXLIKE_INI_SECTION,
                                       "maxiter", 1000)

        self.converged = False

    def execute(self):
        import scipy.optimize

        def likefn(p_in):
            #Check the normalization
            if np.any(p_in<0) or np.any(p_in>1):
                return np.inf
            p = self.pipeline.denormalize_vector(p_in)
            like, extra = self.pipeline.likelihood(p)
            return -like

        start_vector = np.array([param.normalize(param.start)
                                 for param in self.pipeline.varied_params])

        opt_norm = scipy.optimize.fmin(likefn,
                                       start_vector,
                                       xtol=self.tolerance,
                                       disp=False,
                                       maxiter=self.maxiter)

        opt = self.pipeline.denormalize_vector(opt_norm)
        print opt

        self.converged = True

    def is_converged(self):
        return self.converged
