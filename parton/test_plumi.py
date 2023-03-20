import unittest
import tempfile
import shutil
from . import pdf, io
import numpy as np
import scipy.interpolate


def interpolator_slow(pl, p1, p2):
    def f1(x):
        return pl.pdf.xfxQ2(p1, x, pl.Q2) / x
    def f2(x):
        return pl.pdf.xfxQ2(p2, x, pl.Q2) / x
    @np.vectorize
    def y(t):
        def _int(x):
            return f1(x) * f2(t / x) / x
        return scipy.integrate.quad(lambda x: _int(x), t, 1)[0]
    _x = np.logspace(np.log10(pl.x_min), 0, num=int(pl.N/10))
    _y = y(_x)
    return scipy.interpolate.interp1d(np.log(_x), _y, kind='cubic', bounds_error=True)


class TestPartonLumi(unittest.TestCase):
    def test_plumi(self):
        dir = tempfile.mkdtemp()
        for pdfset in ['CT10', 'NNPDF31_nnlo_as_0118', 'NNPDF30_nnlo_as_0118']:
            io.download_pdfset(pdfset, dir)
            pd = pdf.PDF(pdfset, member=0, pdfdir=dir)
            pl = pdf.PLumi(pd, Q2=1000**2)

            for f in (0, 1, 4):
                int_slow = interpolator_slow(pl, f, -f)
                for t in (0.01, 0.05, 0.25):
                    L = pl.L(f, -f, t)
                    L_slow = int_slow(np.log(t))
                    self.assertAlmostEqual(L / L_slow, 1, delta=0.01,
                                        msg="Failed for {}".format((pdfset, f, t)))
        shutil.rmtree(dir)
