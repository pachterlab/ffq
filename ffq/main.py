import argparse
import json
import logging
import os
import sys

from . import __version__
from .ffq import ffq_doi, ffq_gse, ffq_srp, ffq_srr, ffq_erp, ffq_err

logger = logging.getLogger(__name__)

RUN_TYPES = ('SRR', 'ERR')
PROJECT_TYPES = ('SRP', 'ERP')
GEO_TYPES = ('GSE',)
OTHER_TYPES = ('DOI',)
SEARCH_TYPES = RUN_TYPES + PROJECT_TYPES + GEO_TYPES + OTHER_TYPES


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

    parser.add_argument(
        'IDs',
        help=(
            'Can be a SRA Run Accessions, SRA Study Accessions, '
            'GEO Study Accessions, DOIs or paper titles.'
        ),
        nargs='+'
    )
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
        help=(
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
    if args.t in RUN_TYPES + PROJECT_TYPES + GEO_TYPES:
        for ID in args.IDs:
            if ID[0:3] != args.t or not ID[3:].isdigit():
                parser.error((
                    f'{ID} failed validation. {args.t}s must start with \'{args.t}\','
                    ' and end with digits.'
                ))
    elif args.t == 'DOI':
        logger.warning('Searching by DOI may result in missing information.')

    try:
        # run ffq depending on type
        if args.t == 'SRR':
            results = [ffq_srr(accession) for accession in args.IDs]
        elif args.t == 'SRP':
            results = [ffq_srp(accession) for accession in args.IDs]
        elif args.t == 'ERR':
            results = [ffq_err(accession) for accession in args.IDs]
        elif args.t == 'ERP':
            results = [ffq_erp(accession) for accession in args.IDs]
        elif args.t == 'GSE':
            results = [ffq_gse(accession) for accession in args.IDs]
        elif args.t == 'DOI':
            results = [study for doi in args.IDs for study in ffq_doi(doi)]

        keyed = {result['accession']: result for result in results}

        if args.o:
            if args.split:
                # Split each result into its own JSON.
                for result in results:
                    os.makedirs(args.o, exist_ok=True)
                    with open(os.path.join(args.o,
                                           f'{result["accession"]}.json'),
                              'w') as f:
                        json.dump(result, f, indent=4)
            else:
                # Otherwise, write a single JSON with result accession as keys.
                if os.path.dirname(
                        args.o
                ) != '':  # handles case where file is in current dir
                    os.makedirs(os.path.dirname(args.o), exist_ok=True)
                with open(args.o, 'w') as f:
                    json.dump(keyed, f, indent=4)
        else:
            print(json.dumps(keyed, indent=4))
    except Exception as e:
        if args.verbose:
            logger.exception(e)
        else:
            logger.error(e)
