"""Command line interface."""


import argparse
from fnmatch import fnmatch
from . import io
import tarfile
import logging
logging.basicConfig(level=logging.INFO)



def main(argv=None):
    parser = argparse.ArgumentParser(prog='parton',
                                     description="Command line interface to download parton distribution functions.")
    subparsers = parser.add_subparsers(title='subcommands')
    defaultdir = io.data_dir()
    parser.add_argument("--listdir", default=defaultdir,
                               help="Directory where the index of PDF sets is stored (default: {}).".format(defaultdir))
    parser.add_argument("--pdfdir", default=defaultdir,
                               help="Directory where the PDF sets are stored (default: {}).".format(defaultdir))

    parser_update = subparsers.add_parser('update',
                                          description="Command line script to update the list of PDF sets.",
                                          help="Update the list of parton distribution functions.")
    parser_update.set_defaults(func=update)

    parser_list = subparsers.add_parser('list',
                                          description="Command line script to listthe PDF sets.",
                                          help="Show list of parton distribution functions.")
    parser_list.add_argument('--installed', action='store_true')
    parser_list.set_defaults(func=listpdf)

    parser_install = subparsers.add_parser('install',
                                           description="Command line script to install a PDF set.",
                                           help="Install a PDF set.")
    parser_install.add_argument('name')
    parser_install.add_argument('-y', action='store_true')
    parser_install.set_defaults(func=install)

    args = parser.parse_args(argv)
    try:
        args.func(args)
    except AttributeError:
        parser.print_help()


def update(args):
    io.download_index(args.listdir)


def install(args):
    pdfs_av = io.list_available(args.listdir)
    to_install = [pdf for pdf in pdfs_av if fnmatch(pdf, args.name)]
    if not to_install:
        print("No PDF sets matching the pattern {} found.".format(args.name))
        return
    pdfs_in = set(io.list_installed(args.pdfdir, args.listdir))
    to_install = [pdf for pdf in to_install if pdf not in pdfs_in]
    if not to_install:
        return
    print("The following PDF sets will be installed:")
    print('\n'.join(to_install))
    yes = args.y or input("Proceed? (y/n): ").lower()
    if yes:
        for pdf in to_install:
            try:
                io.download_pdfset(pdf, args.pdfdir)
            except tarfile.TarError:
                logging.error("Unable to extract archive for PDF set {}".format(pdf))


def listpdf(args):
    if args.installed:
        pdfs = io.list_installed(args.pdfdir, args.listdir)
    else:
        pdfs = io.list_available(args.listdir)
    for pdf in pdfs:
        print(pdf)
