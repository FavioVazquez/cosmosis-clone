from .. import ParallelSampler, Sampler
import numpy as np
import bumps.pdfwrapper
import bumps.fitters
import bumps.names


def minus_log_probability(p):
    global pipeline
    post, derived = pipeline.posterior(p)
    print post, p
    return -post

class BumpsSampler(Sampler):
    parallel_output = False
    sampler_outputs = [("post", float)]

    def config(self):
        global pipeline
        pipeline = self.pipeline
        self.converged=False

    def execute(self):
        labels = [str(s) for s in self.pipeline.varied_params]
        start = self.pipeline.start_vector()
        model = bumps.pdfwrapper.VectorPDF(minus_log_probability, start, labels=labels)
        parameters = model.parameters()
        for label,param in zip(labels, self.pipeline.varied_params):
            parameters[label].range(param.limits[0], param.limits[1])
        problem = bumps.names.FitProblem(model)
        solver = bumps.fitters.DreamFit(problem)
        results = solver.solve()
        solver.save("bumps.dat")
        self.converged=True

    def is_converged(self):
        return self.complete
