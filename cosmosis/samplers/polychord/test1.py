import ctypes
dll=ctypes.cdll.LoadLibrary("./polychord_interface.so")
polychord = dll.polychord_cosmosis_interface_

loglike_type = ctypes.CFUNCTYPE(
    ctypes.c_double,  #likelihood
    ctypes.c_int, #nparam
    ctypes.c_int, #nderived
    ctypes.POINTER(ctypes.c_double),  #parameters
    ctypes.POINTER(ctypes.c_double),  #derived parameters
)

output_type = ctypes.CFUNCTYPE(
    None,
    ctypes.c_int, #count
    ctypes.c_double,  #weight
    ctypes.c_double,  #post
    ctypes.c_int, #length of the rest of the parameters
    ctypes.POINTER(ctypes.c_double),    
)

def output_printer(count, weight, post, n, params):
    print "POST ", count, weight, post, '  '.join(str(params[i]) for i in xrange(n))

output_printer = output_type(output_printer)

def loglike(n,m,x, y):
    x0 = x[0]
    x1 = x[1]
    L = -0.5*(x0-0.5)**2/0.1**2 -0.5*(x1-0.5)**2/0.1**2
    return L

loglike = loglike_type(loglike)

polychord.argtypes = [
    ctypes.c_int,
    ctypes.c_char_p,
    ctypes.c_int,
    ctypes.c_char_p,
    output_type,
    loglike_type,
]
polychord.restype = ctypes.c_int




names = ["x", "y"]
names = ''.join(name.ljust(128) for name in names)
status = polychord(2, names, 0, "", output_printer, loglike)
print "status = ", status
