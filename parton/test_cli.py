import unittest
import sys
import tempfile
import os
import shutil
from . import cli, io


# path of the Python interpreter
PYTHON = sys.executable


class TestCLI(unittest.TestCase):
    def test_cli(self):
        dir = tempfile.mkdtemp()
        cli.main(['--listdir', dir, 'update'])
        listfile = os.path.join(dir, 'pdfsets.index')
        self.assertTrue(os.path.exists(listfile))
        self.assertIn(' CT10 ', open(listfile).read())
        cli.main(['--listdir', dir, '--pdfdir', dir, 'install', 'CT10', '-y'])
        self.assertTrue(os.path.exists(os.path.join(dir, 'CT10')))
        inst = io.list_installed(dir, dir)
        self.assertListEqual(inst, ['CT10'])
        shutil.rmtree(dir)
