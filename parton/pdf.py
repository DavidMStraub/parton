from . import io
import os
import yaml
from io import StringIO
import numpy as np
import scipy.interpolate


class MyRectBivariateSpline(scipy.interpolate.RectBivariateSpline):
    """Patch of the `scipy.interpolate.RectBivariateSpline` class extending
    it by the `bounds_error` option that works like for `interpnd`."""

    def __init__(self, x, y, z, *args, bounds_error=False, **kwargs):
        super().__init__(x, y, z, *args, **kwargs)
        self.xmin = x[0]
        self.xmax = x[-1]
        self.ymin = y[0]
        self.ymax = y[-1]
        self.bounds_error = bounds_error

    def _check_bounds_error(self, x, y):
        if not self.bounds_error:
            return True
        if not self.xmin <= x <= self.xmax:
            raise ValueError("Value x={} is out of bounds.".format(x))
        if not self.ymin <= y <= self.ymax:
            raise ValueError("Value x={} is out of bounds.".format(x))
        return True

    def __call__(self, x, y, *args, **kwargs):
        self._check_bounds_error(x, y)
        return super().__call__(x, y, *args, **kwargs)


class PDFSet(object):
    """Class representing a PDF set."""

    def __init__(self, name, pdfdir=None):
        self.name = name
        self.pdfdir = pdfdir or io.data_dir()
        self.read_metadata()

    def read_metadata(self):
        filename = os.path.join(self.pdfdir, self.name, '{}.info'.format(self.name))
        if not os.path.exists(filename):
            raise ValueError("File {} not found".format(filename))
        with open(filename, 'r') as f:
            info = yaml.load(f)
        self.info = info


class PDFMember(object):
    """Class representing a PDF set."""

    def __init__(self, pdfset, member=0):
        self.pdfset = pdfset
        self.member = member

    def filename(self):
        return os.path.join(self.pdfset.pdfdir,
                            self.pdfset.name,
                            '{}_{:04d}.dat'.format(self.pdfset.name, self.member))

    def load(self):
        filename = self.filename()
        if not os.path.exists(filename):
            raise ValueError("Data file {} not found".format(filename))
        with open(filename, 'r') as f:
            contents = f.read()
        blocks = contents.split('\n---\n')
        meta = yaml.load(blocks[0])
        grids = blocks[1:-1]  # omit 1st (YAML) and last (empty) block
        return meta, grids


class PDFGrid(object):
    def __init__(self, x, Q, xfgrid, flavors):
        self.x = x
        self.Q = Q
        self.logx = np.log(self.x)
        self.logQ2 = np.log(self.Q**2)
        self.xfgrid = xfgrid
        self.flavors = flavors
        self._interpolators = {}

    @classmethod
    def from_block(cls, block):
        lines = block.splitlines()
        x = np.loadtxt(StringIO(lines[0]))
        Q = np.loadtxt(StringIO(lines[1]))
        flavors = np.loadtxt(StringIO(lines[2]), dtype=int)
        xfgrid = np.loadtxt(StringIO('\n'.join(lines[3:])))
        return cls(x, Q, xfgrid, flavors)

    def flav_index(self, flavor):
        if flavor == 0:
            # 0 is an alias for 21 (gluon)!
            return self.flav_index(21)
        if not np.isin(flavor, self.flavors):
            raise ValueError("Flavor {} not contained in flavors {}".format(flavor, self.flavors))
        i, = np.where(self.flavors == flavor)
        return i

    def interpolator(self, flavor):
        if flavor not in self._interpolators:
            m = len(self.x)
            n = len(self.Q)
            i = self.flav_index(flavor)
            self._interpolators[flavor] = MyRectBivariateSpline(self.logx, self.logQ2, self.xfgrid[:, i].reshape(m, n), bounds_error=True)
        return self._interpolators[flavor]

    def xfxQ2(self, flavor, x, Q2):
        return float(self.interpolator(flavor)(np.log(x), np.log(Q2)))


class PDF(object):
    def __init__(self, name, member=0, pdfdir=None):
        self.name = name
        self.member = member
        self.pdfset = PDFSet(name, pdfdir=pdfdir)
        self.pdfmember = PDFMember(self.pdfset, member=member)
        meta, grids = self.pdfmember.load()
        self.pdfgrids = [PDFGrid.from_block(grid) for grid in grids]

    def xfxQ(self, flavor, x, Q):
        return self.xfxQ2(flavor, x, Q**2)

    def xfxQ2(self, flavor, x, Q2):
        for pdfgrid in self.pdfgrids:
            try:
                return pdfgrid.xfxQ2(flavor, x, Q2)
            except ValueError:
                continue
        raise ValueError("Value is out of bounds on all subgrids.")


# alias to mimic LHAPDF API
mkPDF = PDF
