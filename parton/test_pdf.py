import unittest
import tempfile
import os
import shutil
from . import pdf, io


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
