import logging
import re

from .utils import cached_get, get_xml, parse_tsv

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


def ffq(accession):
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
