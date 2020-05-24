import argparse
import json
import logging
import os
import sys

from . import __version__
from .ffq import ffq_srr, ffq_gse

logger = logging.getLogger(__name__)


SEARCH_TYPES = ('SRR', 'GSE', 'XXX')

def main():
    """Command-line entrypoint.
    """
    # Main parser
    parser = argparse.ArgumentParser(
        description=(
            f'ffq {__version__}: Fetch run information from '
            'the European Nucleotide Archive (ENA).'
        )
    )
    parser._actions[0].help = parser._actions[0].help.capitalize()

    parser.add_argument('IDs', help='Can be a SRA Run Accessions, GEO Study, or XXX', nargs='+')
    parser.add_argument(
        '-o',
        metavar='OUT',
        help=(
            'Path to JSON file to write run information. If `--split` is '
            'used, path to directory in which to place JSON files. '
            '(default: standard out)'
        ),
        type=str,
        required=False,
    )

    parser.add_argument(
        '-t',
        metavar='TYPE',
        help = (
            'The type of term used to query data. Can be one of '
            f'{", ".join(SEARCH_TYPES)} '
            '(default: SRR)'
        ),
        type=str,
        required=False,
        choices=SEARCH_TYPES,
        default='SRR'
    )

    parser.add_argument(
        '--split', help='Split runs into their own files.', action='store_true'
    )
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

    # Check the -o is provided if --split is set
    if args.split and not args.o:
        parser.error('`-o` must be provided when using `--split`')

    # Check IDs depending on type
    if args.t == 'SRR':
        for ID in args.IDs:
            if ID[0:3] != "SRR" or len(ID) != 10 or not ID[3:].isdigit():
                parser.error((
                    f'{ID} failed validation. SRRs must be 10 characters long, '
                    'start with \'SRR\', and end with seven digits.'
                ))
    elif args.t == 'GSE':
        for ID in args.IDs:
            if ID[0:3] != "GSE" or not ID[3:].isdigit():
                parser.error((
                    f'{ID} failed validation. GSEs must start with \'GSE\','
                    ' and end with digits.'
                ))

    # run ffq depending on type
    if args.t == 'SRR':
        runs = [ffq_srr(accession) for accession in args.IDs]
    elif args.t == 'GSE':
        runs = [ffq_gse(accession) for accession in args.IDs]

   
    keyed = {run['accession']: run for run in runs}

    if args.o:
        if args.split:
            # Split each run into its own JSON.
            for run in runs:
                os.makedirs(args.o, exist_ok=True)
                with open(os.path.join(args.o, f'{run["accession"]}.json'),
                          'w') as f:
                    json.dump(run, f, indent=4)
        else:
            # Otherwise, write a single JSON with run accession as keys.
            if os.path.dirname(args.o) != '': # handles case where file is in current dir
                os.makedirs(os.path.dirname(args.o), exist_ok=True) 
            with open(args.o, 'w') as f:
                json.dump(keyed, f, indent=4)
    else:
        print(json.dumps(keyed, indent=4))
