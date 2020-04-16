import argparse
import logging
import sys

from . import __version__
from .ffq import ffq

logger = logging.getLogger(__name__)


def main():
    """Command-line entrypoint.
    """
    # Main parser
    parser = argparse.ArgumentParser(description='ffq {}'.format(__version__))
    parser._actions[0].help = parser._actions[0].help.capitalize()

    parser.add_argument('srrs', help='SRA Run Accessions (SRRs)', nargs='+')
    parser.add_argument(
        '--verbose', help='Print debugging information', action='store_true'
    )
    # Show help when no arguments are given
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    logging.basicConfig(
        format='[%(asctime)s] %(levelname)7s %(message)s',
        level=logging.DEBUG if args.verbose else logging.INFO,
    )

    logger.debug('Printing verbose output')
    logger.debug(args)
    ffq(args)
