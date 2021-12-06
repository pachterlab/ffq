import json
import logging
import re
import time
from urllib.parse import urlparse

from .utils import (
    cached_get,
    geo_id_to_srps,
    geo_ids_to_gses,
    gsm_id_to_srx,
    get_doi,
    get_gse_search_json,
    get_gsm_search_json,
    get_xml,
    ncbi_link,
    ncbi_search,
    ncbi_summary,
    parse_run_range,
    parse_tsv,
    search_ena_run_sample,
    search_ena_run_study,
    search_ena_study_runs,
    search_ena_title,
    sra_ids_to_srrs,
    geo_to_suppl,
)

logger = logging.getLogger(__name__)

RUN_PARSER = re.compile(r'(SRR.+)|(ERR.+)|(DRR.+)')
EXPERIMENT_PARSER = re.compile(r'(SRX.+)|(ERX.+)|(DRX.+)')
PROJECT_PARSER = re.compile(r'(SRP.+)|(ERP.+)|(DRP.+)')
SAMPLE_PARSER = re.compile(r'(SRS.+)|(ERS.+)|(DRS.+)')


def parse_run(soup):
    """Given a BeautifulSoup object representing a run, parse out relevant
    information.

    :param soup: a BeautifulSoup object representing a run
    :type soup: bs4.BeautifulSoup

    :return: a dictionary containing run information
    :rtype: dict
    """

    accession = soup.find('PRIMARY_ID', text=RUN_PARSER).text
    experiment = soup.find('PRIMARY_ID', text=EXPERIMENT_PARSER).text \
        if soup.find('PRIMARY_ID', text=EXPERIMENT_PARSER) \
        else soup.find('EXPERIMENT_REF')['accession']
    study_parsed = soup.find('ID', text=PROJECT_PARSER)
    if study_parsed:
        study = study_parsed.text
    else:
        logger.warning(
            'Failed to parse study information from ENA XML. Falling back to '
            'ENA search...'
        )
        study = search_ena_run_study(accession)

    sample_parsed = soup.find('ID', text=SAMPLE_PARSER)
    if sample_parsed:
        sample = sample_parsed.text
    else:
        logger.warning(
            'Failed to parse sample information from ENA XML. Falling back to '
            'ENA search...'
        )
        sample = search_ena_run_sample(accession)
    title = soup.find('TITLE').text
    attributes = {
        attr.find('TAG').text: attr.find('VALUE').text
        for attr in soup.find_all('RUN_ATTRIBUTE')
    }
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

            files.extend(
                [{
                    'url': f'ftp://{url}',
                    'md5': md5,
                    'size': size
                } for url, md5, size in
                 zip(urls.split(';'), md5s.split(';'), sizes.split(';'))]
            )
            break

    # Include BAM (in submitted file)
    for xref in soup.find_all('XREF_LINK'):
        if xref.find('DB').text == 'ENA-SUBMITTED-FILES':
            bam_url = xref.find('ID').text

            table = parse_tsv(cached_get(bam_url))
            assert len(table) == 1

            urls = table[0].get('submitted_ftp', '')
            md5s = table[0].get('submitted_md5', '')
            sizes = table[0].get('submitted_bytes', '')
            formats = table[0].get('submitted_format', '')
            if not urls or not md5s or not sizes or 'BAM' not in formats:
                break
            files.extend(
                [{
                    'url': f'ftp://{url}',
                    'md5': md5,
                    'size': size
                } for url, md5, size in
                 zip(urls.split(';'), md5s.split(';'), sizes.split(';'))]
            )
            break

    return {
        'accession': accession,
        'experiment': experiment,
        'study': study,
        'sample': sample,
        'title': title,
        'attributes': attributes,
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
    accession = soup.find('PRIMARY_ID', text=SAMPLE_PARSER).text
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
    accession = soup.find('PRIMARY_ID', text=EXPERIMENT_PARSER).text
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
    accession = soup.find('PRIMARY_ID', text=PROJECT_PARSER).text
    title = soup.find('STUDY_TITLE').text
    abstract = soup.find('STUDY_ABSTRACT'
                         ).text if soup.find('STUDY_ABSTRACT') else ""

    return {'accession': accession, 'title': title, 'abstract': abstract}


def parse_study_with_run(soup):
    """Given a BeautifulSoup object representing a study, parse out relevant
    information.

    :param soup: a BeautifulSoup object representing a study
    :type soup: bs4.BeautifulSoup

    :return: a dictionary containing study information and run information
    :rtype: dict
    """
    accession = soup.find('PRIMARY_ID', text=PROJECT_PARSER).text
    title = soup.find('STUDY_TITLE').text
    abstract = soup.find('STUDY_ABSTRACT').text

    # Returns all of the runs associated with a study
    runs = []
    run_parsed = soup.find('ID', text=RUN_PARSER)
    if run_parsed:
        run_ranges = run_parsed.text.split(",")
        for run_range in run_ranges:
            if '-' in run_range:
                runs += parse_run_range(run_range)
            else:
                runs.append(run_range)
    else:
        logger.warning(
            'Failed to parse run information from ENA XML. Falling back to '
            'ENA search...'
        )
        # Sometimes the SRP does not contain a list of runs (for whatever reason).
        # A common trend with such projects is that they use ArrayExpress.
        # In the case that no runs could be found from the project XML,
        # fallback to ENA SEARCH.
        runs = search_ena_study_runs(accession)

    return {
        'accession': accession,
        'title': title,
        'abstract': abstract,
        'runlist': runs
    }


def parse_experiment_with_run(soup):
    """Given a BeautifulSoup object representing a experiment, parse out relevant
    information.

    :param soup: a BeautifulSoup object representing a experiment
    :type soup: bs4.BeautifulSoup

    :return: a dictionary containing experiment information and run information
    :rtype: dict
    """
    accession = soup.find('PRIMARY_ID', text=EXPERIMENT_PARSER).text
    title = soup.find('TITLE').text

    # Returns all of the runs associated with a study
    runs = []
    run_parsed = soup.find('ID', text=RUN_PARSER)
    if run_parsed:
        run_ranges = run_parsed.text.split(",")
        for run_range in run_ranges:
            if '-' in run_range:
                runs += parse_run_range(run_range)
            else:
                runs.append(run_range)
    else:
        logger.warning(
            'Failed to parse run information from ENA XML. Falling back to '
            'ENA search...'
        )
        # Sometimes the SRP does not contain a list of runs (for whatever reason).
        # A common trend with such projects is that they use ArrayExpress.
        # In the case that no runs could be found from the project XML,
        # fallback to ENA SEARCH.
        runs = search_ena_study_runs(accession)

    return {
        'accession': accession,
        'title': title,
        'runlist': runs
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
    geo_id = data['esearchresult']['idlist'][-1]
    return {'accession': accession, 'geo_id': geo_id}


def parse_gse_summary(soup):
    """Given a BeautifulSoup object representing a geo study identifier, parse out relevant
    information.

    :param soup: a BeautifulSoup object representing a study
    :type soup: bs4.BeautifulSoup

    :return: a dictionary containing summary of geo study information
    :rtype: dict
    """
    data = json.loads(soup.text)

    geo_id = data['result']['uids'][-1]

    relations = data['result'][f'{geo_id}']['extrelations']
    for value in relations:
        if value['relationtype'] == 'SRA':  # may have many samples?
            sra = value

    if sra:
        srp = sra['targetobject']
        return {'accession': srp}


def ffq_run(accession):
    """Fetch Run information.

    :param accession: run accession
    :type accession: str

    :return: dictionary of run information
    :rtype: dict
    """
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


def ffq_study(accession):
    """Fetch Study information.

    :param accession: study accession
    :type accession: str

    :return: dictionary of study information. The dictionary contains a
             'runs' key, which is a dictionary of all the runs in the study, as
             returned by `ffq_run`.
    :rtype: dict
    """
    logger.info(f'Parsing Study SRP {accession}')
    study = parse_study_with_run(get_xml(accession))

    logger.warning(f'There are {len(study["runlist"])} runs for {accession}')

    runs = {run: ffq_run(run) for run in study.pop('runlist')}

    study.update({'runs': runs})

    return study


def ffq_gse(accession):
    """Fetch GSE information.

    This function finds the SRP corresponding to the GSE and calls `ffq_study`.

    :param accession: GSE accession
    :type accession: str

    :return: dictionary containing GSE information
    :rtype: dict
    """
    logger.info(f'Parsing GEO {accession}')
    gse = parse_gse_search(get_gse_search_json(accession))
    logger.info(f'Finding supplementary files for GEO {accession}')
    time.sleep(1)
    supp = geo_to_suppl(accession, "GSE")
    if len(supp) > 0:
        gse.update({'supplementary_files' : supp})
    else:
        logger.info(f'No supplementary files found for {accession}')        
    logger.info(f'Getting Study SRX for {accession}')
    gse.pop('geo_id')
    logger.info(f'Getting GSM IDs for {accession}')
    time.sleep(1)
    gsm_ids = [ncbi_summary("gds",id)[id]["accession"] for id in ncbi_search("gds", accession) if id.startswith('3') if time.sleep(0.5) is None]

    gsms = [ffq_gsm(gsm_id) for gsm_id in gsm_ids]
    gse.update({'samples': {sample['accession']: sample for sample in gsms}})
    return gse


def ffq_gsm(accession):
    """Fetch GSM information.

    This function finds the SRX corresponding to the GSM and calls `ffq_experiment`.

    :param accession: GSM accession
    :type accession: str

    :return: dictionary containing GSM information
    :rtype: dict
    """
    logger.info(f'Parsing GEO {accession}')
    gsm = get_gsm_search_json(accession)
    logger.info(f'Finding supplementary files for GEO {accession}')
    time.sleep(1)
    supp = geo_to_suppl(accession, "GSM")
    if len(supp) > 0:
        gsm.update({'supplementary_files' : supp})
    else:
        logger.info(f'No supplementary files found for {accession}')        
    logger.info(f'Getting Study SRX for {accession}')

    srxs = gsm_id_to_srx(gsm.pop('geo_id'))
    experiments = [ffq_experiment(srx) for srx in srxs]
    
    gsm.update({'experiments': {experiment['accession']: experiment for experiment in experiments}})
    return gsm


def ffq_experiment(accession):
    """Fetch Experiment information.

    :param accession: experiment accession
    :type accession: str

    :return: dictionary of experiment information. The dictionary contains a
             'runs' key, which is a dictionary of all the runs in the study, as
             returned by `ffq_run`.
    :rtype: dict
    """
    logger.info(f'Parsing Experiment {accession}')
    experiment = parse_experiment_with_run(get_xml(accession))
    if len(experiment["runlist"]) == 1:
        logger.warning(f'There is 1 run for {accession}')

    else:
        logger.warning(f'There are {len(experiment["runlist"])} runs for {accession}')

    runs = {run: ffq_run(run) for run in experiment.pop('runlist')}

    experiment.update({'runs': runs})

    return experiment


def ffq_doi(doi):
    """Fetch DOI information.

    This function first searches CrossRef for the paper title, then uses that
    to find any SRA studies that match the title. If there are, all the runs in
    each study are fetched. If there are not, Pubmed is searched for the DOI,
    which may contain GEO IDs. If there are GEO IDs, `ffq_gse` is called for each.
    If not, the Pubmed entry may include SRA links. If there are, `ffq_run` is
    called for each linked run. These runs are then grouped by SRP.

    :param doi: paper DOI
    :type doi: str

    :return: list of SRA or GEO studies that are linked to this paper. If
             there are SRA studies matching the paper title, the returned
             list is a list of SRA studies. If not, and the paper includes
             a GEO link, it is a list of GEO studies. If not, and the paper
             includes SRA links, it is a list of SRPs.
    :rtype: list
    """
    # Sanitize DOI so that it doesn't include leading http or https
    parsed = urlparse(doi)

    if parsed.scheme:
        doi = parsed.path.strip('/')

    logger.info(f'Searching for DOI \'{doi}\'')
    paper = get_doi(doi)
    title = paper["title"][0]

    logger.info(f'Searching for Study SRP with title \'{title}\'')
    study_accessions = search_ena_title(title)

    if study_accessions:
        logger.info(
            f'Found {len(study_accessions)} studies that match this title: {", ".join(study_accessions)}'
        )
        return [ffq_study(accession) for accession in study_accessions]

    # If not study with the title is found, search Pubmed, which can be linked
    # to a GEO accession.
    logger.warning((
        'No studies found with the given title. '
        f'Searching Pubmed for DOI \'{doi}\''
    ))
    pubmed_ids = ncbi_search('pubmed', doi)

    if not pubmed_ids:
        raise Exception('No Pubmed records match the DOI')
    if len(pubmed_ids) > 1:
        raise Exception(
            f'{len(pubmed_ids)} match the DOI: {", ".join(pubmed_ids)}'
        )

    pubmed_id = pubmed_ids[0]
    logger.info(f'Searching for GEO record linked to Pubmed ID \'{pubmed_id}\'')
    geo_ids = ncbi_link('pubmed', 'gds', pubmed_id)
    if geo_ids:
        # Convert these geo ids to GSE accessions
        gses = geo_ids_to_gses(geo_ids)
        logger.info(f'Found {len(gses)} GEO Accessions: {", ".join(gses)}')
        if len(gses) != len(geo_ids):
            raise Exception((
                'Number of GEO Accessions found does not match the number of GEO '
                f'records: expected {len(geo_ids)} but found {len(gses)}'
            ))
        # Sleep for one second because NCBI has rate-limiting to 3 requests
        # a second
        time.sleep(1)
        return [ffq_gse(accession) for accession in gses]

    # If the pubmed id is not linked to any GEO record, search for SRA records
    logger.warning((
        f'No GEO records are linked to the Pubmed ID \'{pubmed_id}\'. '
        'Searching for SRA record linked to this Pubmed ID.'
    ))
    time.sleep(1)
    sra_ids = ncbi_link('pubmed', 'sra', pubmed_id)
    if sra_ids:
        srrs = sra_ids_to_srrs(sra_ids)
        logger.warning(f"Found {len(srrs)} run accessions.")
        runs = [ffq_run(accession) for accession in srrs]

        # Group runs by project to keep things consistent.
        studies = {}
        for run in runs:
            study = run['study'].copy()  # Prevent recursive dict
            # get the study accession if exists and add the run to the runs
            studies.setdefault(study["accession"],
                               study).setdefault('runs',
                                                 {})[run['accession']] = run

        return [v for k, v in studies.items()]
    else:
        raise Exception(
            f'No SRA records are linked to Pubmed ID \'{pubmed_id}\''
        )
