import argparse
import json
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

    parser.add_argument('SRRs', help='SRA Run Accessions (SRRs)', nargs='+')
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
    logging.getLogger('chardet.charsetprober').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

    logger.debug('Printing verbose output')
    logger.debug(args)

    # Check SRRs
    for SRR in args.SRRs:
        if SRR[0:3] != "SRR" or len(SRR) != 10 or not SRR[3:].isdigit():
            parser.error((
                f'{SRR} failed validation. SRRs must be 10 characters long, '
                'start with \'SRR\', and end with seven digits.'
            ))

    runs = ffq(args.SRRs)
    for run in runs:
        with open(f'{run["accession"]}.json', 'w') as f:
            json.dump(run, f, indent=4)
