import argparse
import json
import logging
import os
import sys
import re

from . import __version__
from .ffq import ffq_doi, ffq_gse, ffq_run, ffq_study, ffq_sample, ffq_gsm, ffq_experiment, ffq_encode, ffq_ftp, validate_accession

logger = logging.getLogger(__name__)

RUN_TYPES = ('SRR', 'ERR', 'DRR') 
PROJECT_TYPES = ('SRP', 'ERP', 'DRP')  # aka study types 
EXPERIMENT_TYPES = ('SRX',)
SAMPLE_TYPES = ('SRS',)
GEO_TYPES = ('GSE','GSM')
ENCODE_TYPES = ('ENCSR', 'ENCBS', 'ENCDO')
OTHER_TYPES = ('DOI',)
SEARCH_TYPES = RUN_TYPES + PROJECT_TYPES + EXPERIMENT_TYPES + SAMPLE_TYPES + GEO_TYPES + ENCODE_TYPES + OTHER_TYPES


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
            'Can be a SRA / ENA Run Accessions or Study Accessions, '
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
            'The type of term used to query data. Can be one of'
            f'{", ".join(SEARCH_TYPES)} '
            '(default: SRR)'
        ),
        type=str,
        required=False,
        choices=SEARCH_TYPES
        #default='None'
    )

    parser.add_argument(
        '--ftp', help='Skip medatada and return only ftp links for raw data', action='store_true'
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

    # If user provides -t
    if args.t is not None:

    # Check IDs depending on type 
        ######
        # NOTE: include ENCODE ID here, and change ID[0:3] by regex search
        ######
        if args.t in RUN_TYPES + PROJECT_TYPES + EXPERIMENT_TYPES + SAMPLE_TYPES + GEO_TYPES + ENCODE_TYPES:
            for ID in args.IDs:
                ID_type = re.findall(r"(\D+).+", ID)
                if ID_type not in RUN_TYPES + PROJECT_TYPES + EXPERIMENT_TYPES + SAMPLE_TYPES + GEO_TYPES + ENCODE_TYPES:
                    parser.error((
                        f'{ID} failed validation. {args.t}s must start with \'{args.t}\','
                        ' and end with digits.'
                    ))
        elif args.t == 'DOI':
            logger.warning('Searching by DOI may result in missing information.')                    

        #         if ID[0:3] != args.t or not ID[3:].isdigit():
        #             parser.error((
        #                 f'{ID} failed validation. {args.t}s must start with \'{args.t}\','
        #                 ' and end with digits.'
        #             ))
        # elif args.t == 'DOI':
        #     logger.warning('Searching by DOI may result in missing information.')

        if args.ftp:
            results = [ffq_ftp([(args.t, accession)]) for accession in args.IDs]
        
        else:
            try:
                # run ffq depending on type
                if args.t in RUN_TYPES:
                    results = [ffq_run(accession) for accession in args.IDs]
                elif args.t in PROJECT_TYPES:
                    results = [ffq_study(accession) for accession in args.IDs]
                elif args.t in EXPERIMENT_TYPES:
                    results = [ffq_experiment(accession) for accession in args.IDs]
                elif args.t in SAMPLE_TYPES:
                    results = [ffq_sample(accession) for accession in args.IDs]
                elif args.t == 'GSE':
                    results = [ffq_gse(accession) for accession in args.IDs]
                elif args.t == 'GSM':
                    results = [ffq_gsm(accession) for accession in args.IDs]
                elif args.t == 'DOI':
                    results = [study for doi in args.IDs for study in ffq_doi(doi)]

                keyed = {result['accession']: result for result in results}

            except Exception as e:
                if args.verbose:
                    logger.exception(e)
                else:
                    logger.error(e)

    #If user does not provide -t 
    else:
        # Validate and extract types of accessions provided
        type_accessions = validate_accession(args.IDs, RUN_TYPES + PROJECT_TYPES + EXPERIMENT_TYPES + SAMPLE_TYPES + GEO_TYPES + ENCODE_TYPES)

        # If at least one of the accessions is incorrect:  
        if False in type_accessions:
            parser.error(f'{args.IDs[type_accessions.index(False)]} is not a valid ID. IDs can be one of {", ".join(SEARCH_TYPES)}')
            sys.exit(1)

        ############
        # NOTE: Change `type` by another name
        ############
        if args.ftp:
            ffq_ftp(type_accessions)
            sys.exit(1)




        else:
            # run ffq depending on type
            try:
                results = []
                for type, accession in type_accessions:
                    if type in RUN_TYPES:
                        results.append(ffq_run(accession))
                    elif type in PROJECT_TYPES:
                        results.append(ffq_study(accession))
                    elif type in EXPERIMENT_TYPES:
                        results.append(ffq_experiment(accession))
                    elif type in SAMPLE_TYPES:
                        results.append(ffq_sample(accession))
                    elif type == 'GSE':
                        results.append(ffq_gse(accession))
                    elif type == 'GSM':
                        results.append(ffq_gsm(accession))
                    elif type[:3] == 'ENC':
                        results.append(ffq_encode(accession))
                    elif type == 'DOI':
                        logger.warning('Searching by DOI may result in missing information.')
                        results.append(ffq_doi(accession))

                keyed = {result['accession']: result for result in results}

            except Exception as e:
                if args.verbose:
                    logger.exception(e)
                else:
                    logger.error(e)

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

