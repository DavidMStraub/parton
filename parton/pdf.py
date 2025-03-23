from . import io
import os
import re
import yaml
from io import StringIO
import numpy as np
import scipy.interpolate
import scipy.integrate


class MyRectBivariateSpline(scipy.interpolate.RectBivariateSpline):
    """Patch of the `scipy.interpolate.RectBivariateSpline` class extending
    it by the `bounds_error` and `fill_value` options that work
    like for `interp2d`."""

    def __init__(self, x, y, z, *args, bounds_error=False, fill_value=None,
                 **kwargs):
        """Initialize the `MyRectBivariateSpline instance`.

        The additional parameters `bounds_error` and `fill_value` work
        like for `interp2d`."""
        super().__init__(x, y, z, *args, **kwargs)
        self.bounds_error = bounds_error
        self.fill_value = fill_value
        self.x_min, self.x_max = np.amin(x), np.amax(x)
        self.y_min, self.y_max = np.amin(y), np.amax(y)

        # a small margin is added to the min and max values to avoid numerical issues
        self.x_min = self.x_min - abs(self.x_min)/1e10
        self.x_max = self.x_max + abs(self.x_max)/1e10
        self.y_min = self.y_min - abs(self.y_min)/1e10
        self.y_max = self.y_max + abs(self.y_max)/1e10

    def __call__(self, x, y, *args, **kwargs):
        """Call the `MyRectBivariateSpline` instance.

        The shape of the inputs and outputs is the same as for
        `scipy.interpolate.RectBivariateSpline`."""
        # the following code is taken from scipy/interpolate/interpolate.py
        if not kwargs.get("grid", True) and x.shape != y.shape:
            x, y = np.broadcast_arrays(x, y)
        if self.bounds_error or self.fill_value is not None:
            out_of_bounds_x = (x < self.x_min) | (x > self.x_max)
            out_of_bounds_y = (y < self.y_min) | (y > self.y_max)

            any_out_of_bounds_x = np.any(out_of_bounds_x)
            any_out_of_bounds_y = np.any(out_of_bounds_y)

        if self.bounds_error and (any_out_of_bounds_x or any_out_of_bounds_y):
            raise ValueError("Values out of range; x must be in %r, y in %r"
                             % ((self.x_min, self.x_max),
                                (self.y_min, self.y_max)))

        z = super().__call__(x, y, *args, **kwargs)

        if self.fill_value is not None:
            if kwargs.get("grid", True):
                if any_out_of_bounds_x:
                    z[out_of_bounds_x, :] = self.fill_value
                if any_out_of_bounds_y:
                    z[:, out_of_bounds_y] = self.fill_value
            else:
                if any_out_of_bounds_x or any_out_of_bounds_y:
                    z[out_of_bounds_x | out_of_bounds_y] = self.fill_value
        return z


class PDFSet(object):
    """Class representing a PDF set."""

    def __init__(self, name, pdfdir=None):
        """Initialize the PDF set with name `name`.

        Optionally, the directory where the PDF files are located can be
        specified as `pdfdir`."""
        self.name = name
        self.pdfdir = pdfdir or io.data_dir()
        self.read_metadata()

    def read_metadata(self):
        """Read the PDF set's metadata fromm the YAML file.

        This method is called on instantiation and the result is stored in
        the `self.info` attribute."""
        filename = os.path.join(self.pdfdir, self.name, '{}.info'.format(self.name))
        if not os.path.exists(filename):
            raise ValueError("File {} not found".format(filename))
        with open(filename, 'r') as f:
            info = yaml.safe_load(f)
        self.info = info


class PDFMember(object):
    """Class representing a specific member of a PDF set."""

    def __init__(self, pdfset, member=0):
        """Initialize the class.

        The parameter `pdfset` must be an instance of `PDFSet`. The `member`
        parameter must be an integer and defaults to 0."""
        self.pdfset = pdfset
        self.member = member

    def filename(self):
        """Return the absolute path to the PDF grid file."""
        return os.path.join(self.pdfset.pdfdir,
                            self.pdfset.name,
                            '{}_{:04d}.dat'.format(self.pdfset.name, self.member))

    def load(self):
        """Load the PDF grid file.

        Returns the tuple `(meta, grids)`, where `meta` is a dictionary
        with the contents of the YAML metadata block and `grids` is
        a list of strings with the raw contents of the subgrid blocks."""
        filename = self.filename()
        if not os.path.exists(filename):
            raise ValueError("Data file {} not found".format(filename))
        with open(filename, 'r') as f:
            contents = f.read()
        blocks = re.split(r'\n\s*---\s*\n?', contents)
        meta = yaml.safe_load(blocks[0])
        if len(blocks) > 1 and not blocks[-1].strip():
            grids = blocks[1:-1]  # omit first (YAML) and last (empty) block
        else:
            grids = blocks[1:]  # only omit first (YAML) block
        return meta, grids


class PDFGrid(object):
    """Class representing an individual subgrid of a PDF in 'lhagrid1' format.
    """
    def __init__(self, x, Q, xfgrid, flavors):
        """Initialize the grid from arrays of `x`, `Q` spanning a grid,
        xfx values on the grid, and a list of flavours.

        Note that it is usually more convenient to initialize the class
        using the `from_block` class method."""
        self.x = x
        self.Q = Q
        self.logx = np.log(self.x)
        self.logQ2 = np.log(self.Q**2)
        self.xfgrid = xfgrid
        self.flavors = flavors
        self._interpolators = {}

    @classmethod
    def from_block(cls, block):
        """Class method. Return an instance of the class given the raw contents
        of a 'lhagrid1' subgrid block as a string."""
        lines = block.splitlines()
        x = np.loadtxt(StringIO(lines[0]))
        Q = np.loadtxt(StringIO(lines[1]))
        flavors = np.loadtxt(StringIO(lines[2]), dtype=int)
        xfgrid = np.loadtxt(StringIO('\n'.join(lines[3:])))
        return cls(x, Q, xfgrid, flavors)

    def flav_index(self, flavor):
        """Return the position in the list of flavors corresponding to flavor
        `flavor`. 0 is interpreted as 21 (gluon)."""
        if flavor == 0:
            # 0 is an alias for 21 (gluon)!
            return self.flav_index(21)
        if not np.isin(flavor, self.flavors):
            raise ValueError("Flavor {} not contained in flavors {}".format(flavor, self.flavors))
        i, = np.where(self.flavors == flavor)
        return i

    def interpolator(self, flavor):
        """Return an instance of the `MyRectBivariateSpline` interpolator
        for flavor `flavor`.

        Returns a cached instance after the first call."""
        if flavor not in self._interpolators:
            m = len(self.x)
            n = len(self.Q)
            i = self.flav_index(flavor)
            self._interpolators[flavor] = MyRectBivariateSpline(self.logx, self.logQ2, self.xfgrid[:, i].reshape(m, n), bounds_error=False, fill_value=np.nan)
        return self._interpolators[flavor]

    def xfxQ2(self, flavor, x, Q2, grid=True):
        """Return x*f(x) for flavor `flavor`, momentum fraction `x` and
        squared factorization scale in units of GeV^2, `Q2`."""
        flavors = np.unique(flavor)
        if grid and len(flavors) > 1:
            raise RuntimeError("No logical way to make a grid for multiple flavors")
        elif grid:
            return self.interpolator(flavors[0])(np.log(x), np.log(Q2), grid=grid)
        # this could be further optimized to not evaluate every point for every flavor
        flavor, x, Q2 = np.broadcast_arrays(flavor, x, Q2)
        out = self.interpolator(flavors[0])(np.log(x), np.log(Q2), grid=False)
        for f in flavors[1:]:
            mask = flavor == f
            out[mask] = self.interpolator(f)(np.log(x), np.log(Q2), grid=False)[mask]
        return out


class PDF(object):
    """Class representing a PDF that gives access to the numerical values."""

    def __init__(self, name, member=0, pdfdir=None):
        """Initialize the class by speciying the PDF set's `name`, the index
        of the `member` PDF, and, optionally, the directory `pdfdir` where the
        PDF grid files are stored."""
        self.name = name
        self.member = member
        self.pdfset = PDFSet(name, pdfdir=pdfdir)
        self.pdfmember = PDFMember(self.pdfset, member=member)
        meta, grids = self.pdfmember.load()
        self.pdfgrids = [PDFGrid.from_block(grid) for grid in grids]

    def xfxQ(self, flavor, x, Q, grid=True):
        """Return x*f(x) by specifying flavor, `x`, and factorization scale
        `Q` in GeV."""
        return self.xfxQ2(flavor, x, Q**2, grid=grid)

    def xfxQ2(self, flavor, x, Q2, grid=True):
        """Return x*f(x) by specifying flavor, `x`, and factorization scale
        squared `Q2` in GeV^2."""
        if grid == True:
            res = np.full((np.size(x), np.size(Q2)), np.nan)
        else:
            flavor, x, Q2 = map(np.asarray, (flavor, x, Q2))
            res = np.full(np.broadcast_shapes(flavor.shape, x.shape, Q2.shape), np.nan)
        for i, pdfgrid in enumerate(self.pdfgrids):
            _res = pdfgrid.xfxQ2(flavor, x, Q2, grid=grid)
            res[np.isnan(res)] = _res[np.isnan(res)]
            if not np.any(np.isnan(res)):
                break
        if np.size(res) == 1:
            res = float(res)
        return res


class PLumi(object):
    """Class representation a parton luminosity."""

    def __init__(self, pdf, Q2):
        """Initialize the class by specifying a `PDF` instance and a value
        for the factorization scale squared `Q2` in GeV^2."""
        self.pdf = pdf
        self.Q2 = Q2
        self.N = 1000
        self.x_min = np.min([np.min(v.x) for v in pdf.pdfgrids])
        self._interpolators = {}

    def _interpolator(self, p1, p2):
        def f1(x):
            return self.pdf.xfxQ2(p1, x, self.Q2).ravel() / x
        def f2(x):
            return self.pdf.xfxQ2(p2, x, self.Q2).ravel() / x
        _x = np.logspace(np.log10(self.x_min), 0, num=self.N)
        _f1 = f1(_x)
        _f2 = f2(_x)
        _y = np.convolve(_f1, _f2, 'full')[-self.N:] / self.N * (-np.log(self.x_min))
        return scipy.interpolate.interp1d(np.log(_x), _y, kind='cubic', bounds_error=False, fill_value=np.nan)

    def interpolator(self, p1, p2):
        """Return an instance of the `scipy.interpolate.interp1d` interpolator
        for flavors `p1` and `p2`.

        Returns a cached instance after the first call."""
        if (p1, p2) not in self._interpolators:
            self._interpolators[(p1, p2)] = self._interpolator(p1, p2)
        return self._interpolators[(p1, p2)]

    def L(self, p1, p2, t):
        """Return the parton luminosity for flavors `p1` and `p2` and
        the ratio `t` of partonic and hadronic center-of-mass energy
        squared."""
        return self.interpolator(p1, p2)(np.log(t))


# alias to mimic LHAPDF API
mkPDF = PDF
