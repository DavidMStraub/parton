[![Build Status](https://travis-ci.org/DavidMStraub/parton.svg?branch=master)](https://travis-ci.org/DavidMStraub/parton) [![Coverage Status](https://coveralls.io/repos/github/DavidMStraub/parton/badge.svg?branch=master)](https://coveralls.io/github/DavidMStraub/parton?branch=master)

# parton &ndash; a Python package for parton distributions and parton luminosities

parton is a Python package providing parton distribution functions and parton luminosities. It uses the PDF data files provided by the [LHAPDF](https://lhapdf.hepforge.org/) project. Its API is  partially compatible to LHAPDF's Python API, even though only a subset of its features are implemented.

parton is written in pure Python, i.e. it runs on Linux, Mac OS, and Windows.

## Installation

To install the package without administrator privileges, run
```
python3 -m pip install parton --user
```

## Command-line interface

parton provides a command-line interface that mimicks (and is partially compatible to) LHAPDF's `lhapdf` command. In particular, it can be used to install PDF grid files. It is accessed by running the package as a script,
```
python3 -m parton
```
For instance, to install a specific PDF set, run
```
python3 -m parton update
python3 -m parton install 'CT10'
```
If you already have a directory with PDF sets (e.g. from LHAPDF), that can be used as well.

## Python usage

The API for numerically evaluating PDFs is modeled after LHAPDF's Python API:
```python
from parton import mkPDF
pdf = mkPDF('CT10', 0)
# up quark PDF at x=0.1, Q=1000 GeV
pdf.xfxQ(2, 0.1, 1000)
```
If the PDF sets are in a non-default location (on Linux, the default location is `~/.local/share/parton/`), this directory can be changed through `mkPDF`'s `pdfdir` argument.

Parton luminosities are accessed similarly through the `PLumi` class, but the factorization scale has to be fixed on instantiation,
```python
from parton import PLumi
# pdf has been defined above
plumi = PLumi(pdf, Q2=1000)
# u-ubar parton luminosity at shat/s=0.1
plumi.L(2, -2, 0.1)
```

## License

parton is released under the MIT license.

## Contributors

parton was originally written by David M. Straub (@DavidMStraub)

Other contributors:

- Peter Stangl (@peterstangl)

## Citation info

parton cannot be cited at present. Please do not forget to also acknowledge the [LHAPDF](https://lhapdf.hepforge.org/) project.
