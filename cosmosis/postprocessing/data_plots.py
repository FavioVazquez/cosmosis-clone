from cosmosis.postprocessing import lazy_pylab as pylab
import os
import numpy as np

class DataPlot(object):
	filename=""
	def __init__(self, data_dir):
		self.data_dir=data_dir

	def filepath(self, filename):
		class_name = self.__class__.__name__[8:]
		return os.path.join(self.data_dir, class_name, filename)		

	def plot(self, **kwargs):
		print "Unknown plot."
		pass

class DataPlotPlanck(DataPlot):
	filename='COM_PowerSpect_CMB_R1.10.fits'
	def plot(self):
		try:
			import pyfits
		except ImportError:
			try:
				import astropy.io.fits
				pyfits=astropy.io.fits
			except ImportError:
				raise ImportError("Need either pyfits or astropy for overlaid Planck plots")
		filename=self.filepath(self.filename)
		high_ell_data = pyfits.getdata(filename, 2)

		# Load the low-ell data and plot with error bars
		# At low ell there is just an error in the y direction
		# as each mode corresponds to a single ell
		low_ell_data = pyfits.getdata(filename, 1)
		ell = low_ell_data['ell']
		d_ell = low_ell_data['d_ell']
		err = [low_ell_data['errdown'], low_ell_data['errup']]
		pylab.errorbar(ell, d_ell, err, fmt='k.', capsize=0)

		#Load the high-data and plot
		#At high ell we need an ell error bar as well to indicate
		#the ell-range each point corresponds to
		high_ell_data = pyfits.getdata(filename, 2)
		ell = high_ell_data['ell']
		d_ell = high_ell_data['d_ell']
		xerr = [ell-high_ell_data['lmin'], high_ell_data['lmax']-ell]
		yerr = high_ell_data['err']
		pylab.errorbar(ell, d_ell, yerr, xerr, fmt='k.', capsize=0)

class DataPlotHeymans(DataPlot):
	def __init__(self, data_dir):
		super(DataPlotHeymans, self).__init__(data_dir)
		# In this case it's worth loading all the data in advance
		# because there are multiple bins

		#PMC format file, see 
		#http://www.cfhtlens.org/astronomers/cosmological-data-products#six_bin_tomography
		path = self.filepath(self.filename)
		data = np.loadtxt(path)
		nbin = len(data)//2
		self.nbin=nbin
		self.theta_plus = data[:nbin, 0]
		self.theta_minus = data[:nbin, 0]
		self.xiplus = data[:nbin, 1:]
		self.xminus = data[nbin:, 1:]

		#Covariance file - ordering just reads along the 
		#order of the xipm file.  But we only need the diagonal
		covariance_filepath = self.filepath("covariance.dat")
		covmat = np.loadtxt(covariance_filepath)
		sigma = covmat.diagonal()**0.5
		sigma_xi = np.array(np.split(sigma, 2*self.nbin))
		self.sigma_xiplus = sigma_xi[:self.nbin]
		self.sigma_ximinus = sigma_xi[self.nbin:]

	def index(self, bin1, bin2):
		return self.nbin*(bin1-1) + (bin1-1) - bin1*(bin1-1)/2 + bin2-bin1

class DataPlotHeymansFull(DataPlotHeymans):
	filename = "cfhtlens_xipm_6bin.dat"
	def plot(self, bin1, bin2, plus):
		theta = self.theta_plus
		assert bin2 >= bin1, "Bin ordering incorrect in Heymans data plot"
		col = self.index(bin1, bin2)
		y = self.xiplus if plus else self.ximinus
		y = y[:, col]
		sigma = self.sigma_xiplus if plus else self.sigma_ximinus
		sigma = sigma[:,col]
		pylab.errorbar(theta, y, sigma, fmt='.')



# 1,1 1,2 1,3 1,4 1,5 1,6
#     2,2 2,3 2,4 2,5 2,6
#         3,3 3,4 3,5 3,6
#             4,4 4,5 4,6
#                 5,5 5,6
#                     6,6
#start of n'th row = sum(i=1,n excl) b-i
#s_n=(n-1)*b - n*(n-1)/2


if __name__ == '__main__':
	p=DataPlotHeymansFull(".")
	for bin1 in xrange(1,7):
		for bin2 in xrange(bin1, 7):
			pylab.subplot(6,6,(bin1-1)+(bin2-1)*6)
			p.plot(bin1, bin2, True)
			pylab.xscale('log')
			pylab.yscale('log')
	pylab.show()