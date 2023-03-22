import unittest
import tempfile
import os
import shutil
import numpy as np
from . import pdf, io
import numpy as np


class TestPDF(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._dir = tempfile.mkdtemp()
        for pdfset in ['CT10', 'NNPDF31_nnlo_as_0118', 'NNPDF30_nnlo_as_0118']:
            io.download_pdfset(pdfset, cls._dir)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._dir)

    def test_init(self):
        set = pdf.PDFSet('CT10', pdfdir=self._dir)
        self.assertIsInstance(set.info, dict)
        member = pdf.PDFMember(set, 1)
        self.assertEqual(member.filename(),
                         os.path.join(self._dir, 'CT10', 'CT10_0001.dat'))
        meta, grids = member.load()
        pdf.PDFGrid.from_block(grids[0])

    def test_interpolators(self):
        dir = tempfile.mkdtemp()
        for pdfset in ['CT10', 'NNPDF31_nnlo_as_0118', 'NNPDF30_nnlo_as_0118']:
            pd = pdf.PDF(pdfset, member=0, pdfdir=self._dir)

            for grid in pd.pdfgrids:
                logx = grid.logx
                logQ2 = grid.logQ2
                xfgrid = grid.xfgrid
                m = len(logx)
                n = len(logQ2)

                for flavor in grid.flavors:
                    grid_values = xfgrid[:, grid.flav_index(flavor)].reshape(m, n)
                    for ix, x in enumerate(np.exp(logx)):
                        for iQ2, Q2 in enumerate(np.exp(logQ2)):
                            if grid_values[ix, iQ2] < 1e-10:
                                continue
                            else:
                                self.assertAlmostEqual(grid.xfxQ2(flavor, x, Q2)/grid_values[ix, iQ2],
                                        1, delta=0.01,
                                        msg=f"Failed for {pdfset} with flavor {flavor}, x={x}, Q2={Q2} (interpolated: {grid.xfxQ2(flavor, x, Q2)}, grid: {grid_values[ix, iQ2]})")

    def test_broadcast(self):
        pd = pdf.PDF('CT10', member=0, pdfdir=self._dir)
        x = np.geomspace(1e-5, 1e-1, 10)
        Q2 = np.geomspace(1, 1e4, 10)
        np.testing.assert_array_equal(
            pd.xfxQ2(1, x, Q2),
            pd.xfxQ2(1, *np.meshgrid(x, Q2, indexing="ij"), grid=False),
        )
        flavor = np.array([0, 3, 1])
        x = np.array([0.1, 0.2, 0.01])
        Q2 = np.array([10, 100, 50])
        np.testing.assert_array_equal(
            np.vectorize(pd.xfxQ2)(flavor, x, Q2),
            pd.xfxQ2(flavor, x, Q2, grid=False),
        )
