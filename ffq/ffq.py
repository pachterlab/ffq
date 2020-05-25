import json
import logging
import re
import time
from collections import defaultdict
from urllib.parse import urlparse

from .utils import (
    cached_get,
    geo_ids_to_gses,
    get_doi,
    get_gse_search_json,
    get_gse_summary_json,
    get_xml,
    ncbi_link,
    ncbi_search,
    parse_SRR_range,
    parse_tsv,
    search_ena_title,
)

logger = logging.getLogger(__name__)


def parse_run(soup):
    """Given a BeautifulSoup object representing a run, parse out relevant
    information.

    :param soup: a BeautifulSoup object representing a run
    :type soup: bs4.BeautifulSoup

    :return: a dictionary containing run information
    :rtype: dict
    """
    accession = soup.find('PRIMARY_ID', text=re.compile(r'SRR.+')).text
    experiment = soup.find('PRIMARY_ID', text=re.compile(r'SRX.+')).text
    study = soup.find('ID', text=re.compile(r'SRP.+')).text
    sample = soup.find('ID', text=re.compile(r'SRS.+')).text
    title = soup.find('TITLE').text
    files = []

    # Get FASTQs if available
    for xref in soup.find_all('XREF_LINK'):
        if xref.find('DB').text == 'ENA-FASTQ-FILES':
            fastq_url = xref.find('ID').text

            table = parse_tsv(cached_get(fastq_url))
            assert len(table) == 1

            urls = table[0].get('fastq_ftp', '')
            md5s = table[0].get('fastq_md5', '')
            sizes = table[0].get('fastq_bytes', '')
            # If any of these are empty, that means no FASTQs are
            # available. This usually means the data was submitted as a BAM file.
            if not urls or not md5s or not sizes:
                break

            files = [{
                'url': f'ftp://{url}',
                'md5': md5,
                'size': size
            } for url, md5, size in
                     zip(urls.split(';'), md5s.split(';'), sizes.split(';'))]
            break

    # Fallback to BAM (in submitted file)
    if not files:
        for xref in soup.find_all('XREF_LINK'):
            if xref.find('DB').text == 'ENA-SUBMITTED-FILES':
                bam_url = xref.find('ID').text

                table = parse_tsv(cached_get(bam_url))
                assert len(table) == 1

                urls = table[0].get('submitted_ftp', '')
                md5s = table[0].get('submitted_md5', '')
                sizes = table[0].get('submitted_bytes', '')
                formats = table[0].get('submitted_format', '')
                # If any of these are empty, or there are no BAM files,
                # there's something wrong.
                if not urls or not md5s or not sizes or 'BAM' not in formats:
                    raise Exception(
                        f'Run {accession} does not have any compatible files'
                    )
                files = [
                    {
                        'url': f'ftp://{url}',
                        'md5': md5,
                        'size': size
                    } for url, md5, size in
                    zip(urls.split(';'), md5s.split(';'), sizes.split(';'))
                ]
                break

    return {
        'accession': accession,
        'experiment': experiment,
        'study': study,
        'sample': sample,
        'title': title,
        'files': files
    }


def parse_sample(soup):
    """Given a BeautifulSoup object representing a sample, parse out relevant
    information.

    :param soup: a BeautifulSoup object representing a sample
    :type soup: bs4.BeautifulSoup

    :return: a dictionary containing sample information
    :rtype: dict
    """
    accession = soup.find('PRIMARY_ID', text=re.compile(r'SRS.+')).text
    title = soup.find('TITLE').text
    organism = soup.find('SCIENTIFIC_NAME').text
    attributes = {
        attr.find('TAG').text: attr.find('VALUE').text
        for attr in soup.find_all('SAMPLE_ATTRIBUTE')
    }
    return {
        'accession': accession,
        'title': title,
        'organism': organism,
        'attributes': attributes
    }


def parse_experiment(soup):
    """Given a BeautifulSoup object representing an experiment, parse out relevant
    information.

    :param soup: a BeautifulSoup object representing an experiment
    :type soup: bs4.BeautifulSoup

    :return: a dictionary containing experiment information
    :rtype: dict
    """
    accession = soup.find('PRIMARY_ID', text=re.compile(r'SRX.+')).text
    title = soup.find('TITLE').text
    platform = soup.find('INSTRUMENT_MODEL').find_parent().name
    instrument = soup.find('INSTRUMENT_MODEL').text

    return {
        'accession': accession,
        'title': title,
        'platform': platform,
        'instrument': instrument
    }


def parse_study(soup):
    """Given a BeautifulSoup object representing a study, parse out relevant
    information.

    :param soup: a BeautifulSoup object representing a study
    :type soup: bs4.BeautifulSoup

    :return: a dictionary containing study information
    :rtype: dict
    """
    accession = soup.find('PRIMARY_ID', text=re.compile(r'SRP.+')).text
    title = soup.find('STUDY_TITLE').text
    abstract = soup.find('STUDY_ABSTRACT').text

    return {'accession': accession, 'title': title, 'abstract': abstract}


def parse_study_with_run(soup):
    """Given a BeautifulSoup object representing a study, parse out relevant
    information.

    :param soup: a BeautifulSoup object representing a study
    :type soup: bs4.BeautifulSoup

    :return: a dictionary containing study information and run information
    :rtype: dict
    """
    accession = soup.find('PRIMARY_ID', text=re.compile(r'SRP.+')).text
    title = soup.find('STUDY_TITLE').text
    abstract = soup.find('STUDY_ABSTRACT').text

    # Returns all of the runs associated with a study
    srr = []
    srr_ranges = soup.find('ID', text=re.compile(r'SRR.+')).text.split(",")
    for srr_range in srr_ranges:
        if '-' in srr_range:
            srr += parse_SRR_range(srr_range)
        else:
            srr += srr_range
    return {
        'accession': accession,
        'title': title,
        'abstract': abstract,
        'runlist': srr
    }


def parse_gse_search(soup):
    """Given a BeautifulSoup object representing a geo study, parse out relevant
    information.

    :param soup: a BeautifulSoup object representing a study
    :type soup: bs4.BeautifulSoup

    :return: a dictionary containing geo study unique identifier based on a search
    :rtype: dict
    """
    data = json.loads(soup.text)

    accession = data['esearchresult']['querytranslation'].split('[')[0]
    gse_id = data['esearchresult']['idlist'][-1]
    return {'accession': accession, 'gse_id': gse_id}


def parse_gse_summary(soup):
    """Given a BeautifulSoup object representing a geo study identifier, parse out relevant
    information.

    :param soup: a BeautifulSoup object representing a study
    :type soup: bs4.BeautifulSoup

    :return: a dictionary containing summary of geo study information
    :rtype: dict
    """
    data = json.loads(soup.text)

    gse_id = data['result']['uids'][-1]

    relations = data['result'][f'{gse_id}']['extrelations']
    for value in relations:
        if value['relationtype'] == 'SRA':  # may have many samples?
            sra = value

    srp = sra['targetobject']

    return {'accession': srp}


def ffq_srr(accession):
    logger.info(f'Parsing run {accession}')
    run = parse_run(get_xml(accession))
    logger.debug(f'Parsing sample {run["sample"]}')
    sample = parse_sample(get_xml(run['sample']))
    logger.debug(f'Parsing experiment {run["experiment"]}')
    experiment = parse_experiment(get_xml(run['experiment']))
    logger.debug(f'Parsing study {run["study"]}')
    study = parse_study(get_xml(run['study']))

    run.update({'sample': sample, 'experiment': experiment, 'study': study})
    return run


def ffq_srp(accession):
    logger.info(f'Parsing Study SRP {accession}')
    study = parse_study_with_run(get_xml(accession))

    logger.warning(f'There are {len(study["runlist"])} runs for {accession}')

    runs = {run: ffq_srr(run) for run in study.pop('runlist')}

    # Remove study information from runs because that is redundant.
    for run in runs.values():
        del run['study']

    study.update({'runs': runs})

    return study


def ffq_gse(accession):
    logger.info(f'Parsing GEO {accession}')
    gse = parse_gse_search(get_gse_search_json(accession))

    logger.info(f'Getting Study SRP for {accession}')
    study = parse_gse_summary(get_gse_summary_json(gse['gse_id']))

    logger.info(f'Parsing Study SRP {study["accession"]}')
    run_info = parse_study_with_run(get_xml(study["accession"]))

    runlist = run_info.pop('runlist')
    study.update(run_info)

    logger.warning(f'There are {len(runlist)} runs for {accession}')

    runs = defaultdict()
    for run in runlist:
        logger.info(f'Parsing run {run}')
        runs[run] = parse_run(get_xml(run))

    gse.update({'study': study, 'runs': runs})

    return gse


# def ffq_title(title):
#     logger.info(f'Searching for Study SRP with title \'{title}\'')
#     study_accessions = search_ena_title(title)
#
#     if not study_accessions:
#         raise Exception('No studies found for the given title')
#     logger.info(
#         f'Found {len(study_accessions)} studies that match this title: {", ".join(study_accessions)}'
#     )
#
#     return [ffq_srp(accession) for accession in study_accessions]


def ffq_doi(doi):
    # Sanitize DOI so that it doesn't include leading http or https
    parsed = urlparse(doi)

    if parsed.scheme:
        doi = parsed.path.strip('/')

    logger.info(f'Searching for DOI \'{doi}\'')
    paper = get_doi(doi)
    title = paper["title"][0]
    logger.info(f'Found paper with title \'{title}\'')

    logger.info(f'Searching for Study SRP with title \'{title}\'')
    study_accessions = search_ena_title(title)

    # If not study with the title is found, search Pubmed, which can be linked
    # to a GEO accession.
    if not study_accessions:
        logger.warning((
            'No studies found with the given title. '
            f'Searching Pubmed for DOI \'{doi}\''
        ))
        pmids = ncbi_search('pubmed', doi)

        if not pmids:
            raise Exception('No Pubmed records match the DOI')
        if len(pmids) > 1:
            raise Exception(f'{len(pmids)} match the DOI: {", ".join(pmids)}')

        pmid = pmids[0]
        logger.info(f'Found Pubmed ID \'{pmid}\'')
        logger.info(f'Searching for GEO record linked to this Pubmed ID.')
        geoids = ncbi_link('pubmed', 'gds', pmid)
        if not geoids:
            raise Exception(
                f'No GEO records are linked to the Pubmed ID \'{pmid}\''
            )
        logger.info(f'Found {len(geoids)} GEO records: {", ".join(geoids)}')

        # Convert these geo ids to GSE accessions
        logger.info('Finding GEO Accessions for these GEO records')
        gses = geo_ids_to_gses(geoids)
        if len(gses) != len(geoids):
            raise Exception((
                'Number of GEO Accessions found does not match the number of GEO '
                f'records: expected {len(geoids)} but found {len(gses)}'
            ))
        logger.info(f'Found GEO Accessions: {", ".join(gses)}')

        # Sleep for one second because NCBI has rate-limiting to 3 requests
        # a second
        time.sleep(1)
        return [ffq_gse(accession) for accession in gses]

    logger.info(
        f'Found {len(study_accessions)} studies that match this title: {", ".join(study_accessions)}'
    )

    return [ffq_srp(accession) for accession in study_accessions]
