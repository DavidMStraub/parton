import urllib.request
import os
import logging
import appdirs
import tarfile
logging.basicConfig(level=logging.INFO)


def data_dir():
    """Return the default data directory."""
    datadir = appdirs.user_data_dir('parton')
    if not os.path.exists(datadir):
        os.makedirs(datadir)
    return datadir


URL_INDEX = 'https://lhapdfsets.web.cern.ch/current/pdfsets.index'
URL_PDF = 'https://lhapdfsets.web.cern.ch/current/{}.tar.gz'


def download_file(url, filename):
    logging.info("Downloading {} to {}...".format(url, filename))
    urllib.request.urlretrieve(url, filename=filename)
    logging.info("Done.")


def download_index(listdir):
    filename = os.path.join(listdir, 'pdfsets.index')
    download_file(URL_INDEX, filename)
    with open(filename, 'r') as f:
        contents = f.read()
        if '<html>' in contents:
            raise Exception("There was a problem downloading the file {}".format(URL_INDEX))
            os.remove(filename)



def download_pdfset(name, pdfdir):
    filename = os.path.join(pdfdir, '{}.tar.gz'.format(name))
    download_file(URL_PDF.format(name), filename)
    logging.info("Extracting {} ...".format(filename))
    tar = tarfile.open(filename, "r:gz")
    tar.extractall(pdfdir)
    tar.close()
    logging.info("Done. Deleting {}.".format(filename))
    os.remove(filename)


def list_available(listdir):
    filename = os.path.join(listdir, 'pdfsets.index')
    with open(filename, 'r') as f:
        lines = f.readlines()
    return [line.split(' ')[1] for line in lines]


def list_installed(pdfdir, listdir):
    all = list_available(listdir)
    return [pdf for pdf in all
            if os.path.exists(os.path.join(pdfdir, pdf))]
