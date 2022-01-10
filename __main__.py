#!/usr/bin/env python
import sys
from helpers.parser import initialize_parser

__version__ = '1.0'
__author__ = 'Sergio Pereira'


def main(argv: list = sys.argv):
    initialize_parser()


if __name__ == "__main__":
    main(sys.argv)
