import itertools
import numpy as np

from .. import ParallelSampler


GRID_INI_SECTION = "grid"


def task(p):
    return grid_pipeline.posterior(p)


class GridSampler(ParallelSampler):
    parallel_output = False

    def config(self):
        global grid_pipeline
        grid_pipeline = self.pipeline

        self.converged = False
        self.nsample = self.ini.getint(GRID_INI_SECTION,
                                       "nsample_dimension", 1)

    def execute(self):
        self.output.comment("Running with %d samples per dimension"%self.nsample)
        only_params=self.ini.get(GRID_INI_SECTION, "only_grid", "")

        if only_params == "":
            only_params=None
            number_params = len(self.pipeline.varied_params)
        else:
            #parse the list of sampled parameters
            only_params = [x.strip() for x in only_params.split()]
            #check that the parameters specified to sample over
            #actually exist
            varied_param_names = [str(x) for x in self.pipeline.varied_params]
            fixed_param_names = [str(x) for x in self.pipeline.fixed_params]
            #check that these parameters actually exist
            #to avoid user confusion, and count the number of parameters
            number_params = 0            
            for param in only_params:
                if param in fixed_param_names:
                    print "WARNING: You asked to grid-sample over %s but it is a fixed parameter so will be fixed"
                elif param not in varied_param_names:
                    raise ValueError("You asked to grid-sample over an unknown parameter, %s"%param)
                else:
                    number_params+=1

        number_samples_expected = self.nsample**number_params
        print
        print "For this grid we will be running: "
        print " %d ^ %d = %d samples" % (self.nsample, number_params, number_samples_expected)
        print 
        if number_samples_expected>1e7:
            print "Okay, you asked for more than 10 million likelihoods"
            print "That's far too many - something is wrong here.  Probably"
            print "you are trying to grid over too many dimensions."
            print 
            print "You can restrict the parameters to be gridded"
            print "By fixing parameters in the values file, or "
            print "by setting, in the ini file, e.g.:"
            print "[grid]"
            print "only_params=cosmological_parameters--omega_m cosmological_parameters--h0"
            print
            raise ValueError("Too many grid points requested - see message above")

        if number_samples_expected>20000:
            print "This seems like quite a lot of samples."
            print "Maybe an MCMC like emcee or multinest would be better?"
            print
            print "Or you can restrict the parameters to be sampled over"
            print "By fixing parameters in the values file, or "
            print "by setting, in the ini file, e.g.:"
            print "[grid]"
            print "only_params=cosmological_parameters--omega_m,cosmological_parameters--h0"
            print

        samples = list(itertools.product(*[np.linspace(*param.limits,
                                                       num=self.nsample)
                                            if ((only_params is None) or 
                                                str(param) in only_params)
                                            else [param.start]
                                           for param
                                           in self.pipeline.varied_params
                                           ]))

        if self.pool:
            results = self.pool.map(task, samples)
        else:
            results = map(task, samples)

        for sample, (prob, extra) in itertools.izip(samples, results):
            self.output.parameters(sample, extra)
        self.converged = True

    def is_converged(self):
        return self.converged
