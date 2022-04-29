import argparse
import json
import logging
import os
import sys
import re

from . import __version__
from .ffq import ffq_doi, ffq_gse, ffq_run, ffq_study, ffq_sample, ffq_gsm, ffq_experiment, ffq_encode, ffq_bioproject, ffq_biosample, ffq_links, validate_accession  # noqa

logger = logging.getLogger(__name__)

RUN_TYPES = (
    'SRR',
    'ERR',
    'DRR',
)
PROJECT_TYPES = (
    'SRP',
    'ERP',
    'DRP',
)
EXPERIMENT_TYPES = (
    'SRX',
    'ERX',
    'DRX',
)
SAMPLE_TYPES = ('SRS', 'ERS', 'DRS', 'CRS')
GEO_TYPES = ('GSE', 'GSM')
ENCODE_TYPES = ('ENCSR', 'ENCBS', 'ENCDO')
BIOPROJECT_TYPES = (
    'CRX',
)  # TODO implement CRR and CRP, most dont have public metadata.
BIOSAMPLE_TYPES = ('SAMN', 'SAMD', 'SAMEA', 'SAMEG')
OTHER_TYPES = ('DOI',)
SEARCH_TYPES = RUN_TYPES + PROJECT_TYPES + EXPERIMENT_TYPES + SAMPLE_TYPES + \
    GEO_TYPES + ENCODE_TYPES + BIOPROJECT_TYPES + BIOSAMPLE_TYPES + OTHER_TYPES


def main():
    """Command-line entrypoint.
    """
    # Main parser
    parser = argparse.ArgumentParser(
        description=((
            f'ffq {__version__}: A command line tool to find sequencing data '
            'from SRA / GEO / ENCODE / ENA / EBI-EMBL / DDBJ / Biosample.'
        ))
    )
    parser._actions[0].help = parser._actions[0].help.capitalize()

    parser.add_argument(
        'IDs',
        help=(
            'One or multiple SRA / GEO / ENCODE / ENA / EBI-EMBL / DDBJ / Biosample accessions, '
            'DOIs, or paper titles'
        ),
        nargs='+'
    )
    parser.add_argument(
        '-o',
        metavar='OUT',
        help=('Path to write metadata (default: standard out)'),
        type=str,
        required=False,
    )

    parser.add_argument(
        '-t',
        metavar='TYPE',
        help=argparse.SUPPRESS,
        type=str,
        required=False,
        choices=SEARCH_TYPES
    )

    parser.add_argument(
        '-l',
        metavar='LEVEL',
        help='Max depth to fetch data within accession tree',
        type=int
    )

    parser.add_argument('--ftp', help='Return FTP links', action='store_true')

    parser.add_argument(
        '--aws',
        help=  # noqa
        'Return AWS links',
        action='store_true'
    )

    parser.add_argument(
        '--gcp',
        help=  # noqa
        'Return GCP links',
        action='store_true'
    )

    parser.add_argument(
        '--ncbi',
        help=  # noqa
        'Return NCBI links',
        action='store_true'
    )
    parser.add_argument(
        '--split',
        help=  # noqa
        'Split output into separate files by accession  (`-o` is a directory)',
        action='store_true'
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

    if args.l:
        if args.l <= 0:  # noqa
            parser.error('level `-l` must be equal or greater than 1')
    args.IDs = [id.upper() for id in args.IDs]
    # If user provides -t
    if args.t is not None:
        # Check IDs depending on type
        if args.t in RUN_TYPES + PROJECT_TYPES + EXPERIMENT_TYPES + SAMPLE_TYPES + \
        GEO_TYPES + BIOPROJECT_TYPES + BIOSAMPLE_TYPES + ENCODE_TYPES:
            for ID in args.IDs:
                IDs = re.findall(r"(\D+).+", ID)

                if len(IDs) == 0:
                    parser.error((
                        f'{ID} failed validation. {args.t}s must start with \'{args.t}\','
                        ' and end with digits.'
                    ))
                else:
                    ID_type = IDs[0]
                    if ID_type not in RUN_TYPES + PROJECT_TYPES + EXPERIMENT_TYPES + SAMPLE_TYPES + \
                        GEO_TYPES + BIOPROJECT_TYPES + BIOSAMPLE_TYPES + ENCODE_TYPES:
                        parser.error((
                            f'{ID} failed validation. {args.t}s must start with \'{args.t}\','
                            ' and end with digits.'
                        ))
        elif args.t == 'DOI':
            logger.warning(
                'Searching by DOI may result in missing information.'
            )

        if args.ftp:
            keyed = [
                ffq_links([(args.t, accession)], 'ftp')
                for accession in args.IDs
            ]

        elif args.aws:
            keyed = [
                ffq_links([(args.t, accession)], 'AWS')
                for accession in args.IDs
            ]

        elif args.gcp:
            keyed = [
                ffq_links([(args.t, accession)], 'GCP')
                for accession in args.IDs
            ]

        elif args.ncbi:
            keyed = [
                ffq_links([(args.t, accession)], 'NCBI')
                for accession in args.IDs
            ]

        else:
            try:
                # run ffq depending on type
                if args.t in RUN_TYPES:
                    results = [ffq_run(accession) for accession in args.IDs]
                elif args.t in PROJECT_TYPES:
                    results = [
                        ffq_study(accession, args.l) for accession in args.IDs
                    ]
                elif args.t in EXPERIMENT_TYPES:
                    results = [
                        ffq_experiment(accession, args.l)
                        for accession in args.IDs
                    ]
                elif args.t in SAMPLE_TYPES:
                    results = [
                        ffq_sample(accession, args.l) for accession in args.IDs
                    ]
                elif args.t == 'GSE':
                    results = [
                        ffq_gse(accession, args.l) for accession in args.IDs
                    ]
                elif args.t == 'GSM':
                    results = [
                        ffq_gsm(accession, args.l) for accession in args.IDs
                    ]
                elif args.t == 'DOI':
                    results = [
                        study for doi in args.IDs for study in ffq_doi(doi)
                    ]

                keyed = {result['accession']: result for result in results}

            except Exception as e:
                if args.verbose:
                    logger.exception(e)
                else:
                    logger.error(e)

    # If user does not provide -t
    else:
        # Validate and extract types of accessions provided
        type_accessions = validate_accession(
            args.IDs,
            RUN_TYPES + PROJECT_TYPES + EXPERIMENT_TYPES + SAMPLE_TYPES +
            GEO_TYPES + ENCODE_TYPES + BIOPROJECT_TYPES + BIOSAMPLE_TYPES
        )
        # If at least one of the accessions is incorrect:
        if False in type_accessions:
            parser.error(
                f'{args.IDs[type_accessions.index(False)]} is not a valid ID. IDs can be one of {", ".join(SEARCH_TYPES)}'  # noqa
            )
            sys.exit(1)

        ############
        # NOTE: Change `type` by another name
        ############
        if args.ftp:
            keyed = ffq_links(type_accessions, 'ftp')

        elif args.aws:
            keyed = ffq_links(type_accessions, 'AWS')

        elif args.gcp:
            keyed = ffq_links(type_accessions, 'GCP')

        elif args.ncbi:
            keyed = ffq_links(type_accessions, 'NCBI')

        else:
            # run ffq depending on type
            try:

                results = []
                for id_type, accession in type_accessions:
                    if id_type in RUN_TYPES:
                        results.append(ffq_run(accession))
                    elif id_type in PROJECT_TYPES:
                        results.append(ffq_study(accession, args.l))
                    elif id_type in EXPERIMENT_TYPES:
                        results.append(ffq_experiment(accession, args.l))
                    elif id_type in SAMPLE_TYPES:
                        results.append(ffq_sample(accession, args.l))
                    elif id_type == 'GSE':
                        results.append(ffq_gse(accession, args.l))
                    elif id_type == 'GSM':
                        results.append(ffq_gsm(accession, args.l))
                    elif id_type[:3] == 'ENC':
                        results.append(ffq_encode(accession))
                    elif id_type[:3] in BIOPROJECT_TYPES:
                        results.append(ffq_bioproject(accession))
                    elif id_type[:4
                                 ] in BIOSAMPLE_TYPES or id_type[:5
                                                                 ] in BIOSAMPLE_TYPES:
                        results.append(ffq_biosample(accession, args.l))
                    elif id_type == 'DOI':
                        logger.warning(
                            'Searching by DOI may result in missing information.'
                        )
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
                with open(os.path.join(args.o, f'{result["accession"]}.json'),
                          'w') as f:
                    json.dump(result, f, indent=4)
        else:
            # Otherwise, write a single JSON with result accession as keys.
            if os.path.dirname(
                    args.o) != '':  # handles case where file is in current dir
                os.makedirs(os.path.dirname(args.o), exist_ok=True)
            with open(args.o, 'w') as f:
                json.dump(keyed, f, indent=4)
    else:
        print(json.dumps(keyed, indent=4))
