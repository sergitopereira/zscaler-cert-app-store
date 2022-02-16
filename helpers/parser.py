import argparse
from app_store import UpdateCertStore


def initialize_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--all',
                        help='Add Zscaler root certificate to all installed applications',
                        action='store_true'
                        )
    parser.add_argument('-p', '--python',
                        help='Add Zscaler root certificate to pip and requests.Note that python2 is not supported',
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
    parser.add_argument('-c', '--curl',
                        help='Add Zscaler root certificate to curl',
                        action='store_true'
                        )
    parser.add_argument('-w', '--wget',
                        help='Add Zscaler root certificate to wget',
                        action='store_true'
                        )

    parser.add_argument('-n', '--npm',
                        help='Add Zscaler root certificate to NPM',
                        action='store_true'
                        )
    parser.add_argument('-l', '--libressl',
                        help='Add Zscaler root certificate to libressl. This needs to be executed as root',
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
    a = UpdateCertStore()
    if args.version:
        print('Plugin version version 1.5')
    if args.python:
        a.app_python()
    if args.git:
        a.app_git()
    if args.download:
        a.GetZscalerRoot()
    if args.ruby:
        a.app_ruby()
    if args.curl:
        a.app_curl()
    if args.wget:
        a.app_wget()
    if args.npm:
        a.app_npm()
    if args.libressl:
        a.app_libreSSL()
    if args.all:
        for app, value in a.installed_apps.items():
            if value['installed']:
                if 'python' in app:
                    a.app_python()
                if 'git' in app:
                    a.app_git()
                if 'ruby' in app:
                    a.app_ruby()
                if 'wget' in app:
                    a.app_wget()
                if 'curl' in app:
                    a.app_curl()
                if 'npm' in app:
                    a.app_npm()
    a.print_results()
