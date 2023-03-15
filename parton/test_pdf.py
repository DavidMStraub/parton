import unittest
import tempfile
import os
import shutil
from . import pdf, io
import numpy as np


class TestPDF(unittest.TestCase):
    def test_init(self):
        dir = tempfile.mkdtemp()
        io.download_pdfset('CT10', dir)
        set = pdf.PDFSet('CT10', pdfdir=dir)
        self.assertIsInstance(set.info, dict)
        member = pdf.PDFMember(set, 1)
        self.assertEqual(member.filename(),
                         os.path.join(dir, 'CT10', 'CT10_0001.dat'))
        meta, grids = member.load()
        pdf.PDFGrid.from_block(grids[0])
        shutil.rmtree(dir)

    def test_interpolators(self):
        dir = tempfile.mkdtemp()
        for pdfset in ['CT10', 'NNPDF31_nnlo_as_0118', 'NNPDF30_nnlo_as_0118']:
            io.download_pdfset(pdfset, dir)
            pd = pdf.PDF(pdfset, member=0, pdfdir=dir)

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
        shutil.rmtree(dir)
