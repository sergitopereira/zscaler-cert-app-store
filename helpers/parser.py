import argparse
from app_store import UpdateCertStore

def initialize_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--python',
                        help='Add Zscaler root certificate to python',
                        action='store_true')
    parser.add_argument('-d', '--download',
                        help='Download Zscaler root certificate from keychain',
                        action='store_true')
    parser.add_argument('-g', '--git',
                        help='Add Zscaler root certificate to git',
                        action='store_true')
    parser.add_argument('-r', '--ruby',
                        help='Add Zscaler root certificate to Ruby',
                        action='store_true'
                        )
    parser.add_argument('-v', '--version',
                        help='Script version',
                        action='store_true')

    args = parser.parse_args()
    plugin_selection(args)


def plugin_selection(args):
    """
    Selects the plugin to be used based on the parser
    :param args: parer arguments
    :return:
    """
    print(args)
    a = UpdateCertStore()
    print("ok")
    if args.version:
        print('Plugin version version 1.0')
    if args.python:
        a.app_python()
        return
    if args.git:
        a.app_git()
        return
    if args.download:
        a.GetZscalerRoot()
        return
    if args.ruby:
        print("sergio")
        a.app_ruby()
        return