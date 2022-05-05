import json
import logging
import re
import time
from urllib.parse import urlparse
import sys

from .utils import (
    geo_ids_to_gses, gsm_id_to_srs, get_doi, get_gse_search_json,
    get_gsm_search_json, get_xml, get_encode_json, get_samples_from_study,
    ncbi_link, ncbi_search, ncbi_fetch_fasta, parse_encode_json,
    search_ena_run_sample, search_ena_run_study, search_ena_title,
    sra_ids_to_srrs, geo_to_suppl, gsm_to_platform, gse_to_gsms, srx_to_srrs,
    get_files_metadata_from_run, parse_url, parse_ncbi_fetch_fasta, ena_fetch,
    parse_bioproject
)

logger = logging.getLogger(__name__)

RUN_PARSER = re.compile(r'(SRR.+)|(ERR.+)|(DRR.+)')
EXPERIMENT_PARSER = re.compile(r'(SRX.+)|(ERX.+)|(DRX.+)')
PROJECT_PARSER = re.compile(r'(SRP.+)|(ERP.+)|(DRP.+)')
SAMPLE_PARSER = re.compile(r'(SRS.+)|(ERS.+)|(DRS.+)')
DOI_PARSER = re.compile('^10.\d{4,9}\/[-._;()\/:A-Z0-9]+')  # noqa


# TODO evenetually create an accession class
# TODO better handling DOI parsing
def validate_accessions(accessions, search_types):
    # 1. extract the prefix 2. determine if prefix is valid or its a DOI
    # {accession: str, prefix: str, valid: bool}

    IDs = []
    for input_accession in accessions:
        # encode needs :3 ?
        # bioproject needs :3 ?
        # biosample needs :4 or : 5 ?
        accession = input_accession.upper()

        valid = False
        prefix = re.findall(r"(\D+).+", accession)[0]

        if prefix in search_types:
            valid = True

        elif DOI_PARSER.match(accession) is not None:
            valid = True
            logger.warning(
                'Searching by DOI may result in missing information.'
            )
            prefix = "DOI"
        else:
            prefix = "UNKNOWN"
        # TODO add error if not valid

        IDs.append({
            "accession": accession,
            "prefix": prefix,
            "valid": valid,
            "error": None
        })

    return IDs


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

    attributes = {}

    for attr in soup.find_all('RUN_ATTRIBUTE'):
        try:
            tag = attr.find('TAG').text
            value = attr.find('VALUE').text
            attributes[tag] = value
        except:  # noqa
            pass
    if attributes:
        try:
            attributes['ENA-SPOT-COUNT'] = int(attributes['ENA-SPOT-COUNT'])
            attributes['ENA-BASE-COUNT'] = int(attributes['ENA-BASE-COUNT'])
        except:  # noqa
            pass
    ftp_files = get_files_metadata_from_run(soup)
    # print(ftp_files)
    # ftp_files = [file for file in ftp_files if accession in file['url']]
    # print(ftp_files)
    # for file in ftp_files:
    #     if accession in file['url']:
    # url, md5, size =file['url'], file['md5'], file['size']
    # # we want url last, so we delete they key and include it later
    # del file['url'], file['md5'], file['size']
    # filetype, fileno = parse_url(file['url'])
    # file['filetype'] = filetype
    # file['filenumber'] = fileno

    alt_links_soup = ncbi_fetch_fasta(accession, 'sra')

    aws_links = parse_ncbi_fetch_fasta(alt_links_soup, 'AWS')
    aws_results = []
    for url in aws_links:
        if accession in url:
            filetype, fileno = parse_url(url)
            aws_results.append({
                'accession': accession,
                "filename": url.split("/")[-1],
                'filetype': filetype,
                'filesize': None,
                'filenumber': fileno,
                'md5': None,
                "urltype": "aws",
                'url': url
            })

    gcp_links = parse_ncbi_fetch_fasta(alt_links_soup, 'GCP')
    gcp_results = []
    for url in gcp_links:
        if accession in url:
            filetype, fileno = parse_url(url)
            gcp_results.append({
                'accession': accession,
                "filename": url.split("/")[-1],
                'filetype': filetype,
                'filesize': None,
                'filenumber': fileno,
                'md5': None,
                "urltype": "gcp",
                'url': url,
            })

    ncbi_links = parse_ncbi_fetch_fasta(alt_links_soup, 'NCBI')
    ncbi_results = []
    for url in ncbi_links:
        if accession in url:
            filetype, fileno = parse_url(url)
            ncbi_results.append({
                'accession': accession,
                "filename": url.split("/")[-1],
                'filetype': filetype,
                'filesize': None,
                'filenumber': fileno,
                'md5': None,
                "urltype": "ncbi",
                'url': url,
            })
    files = {
        'ftp': ftp_files,
        'aws': aws_results,
        'gcp': gcp_results,
        'ncbi': ncbi_results,
    }
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
    sample_attribute = soup.find_all('SAMPLE_ATTRIBUTE')
    try:
        attributes = {
            attr.find('TAG').text: attr.find('VALUE').text
            for attr in sample_attribute
        }
    except:  # noqa
        attributes = ''
    if attributes:
        try:
            attributes['ENA-SPOT-COUNT'] = int(attributes['ENA-SPOT-COUNT'])
            attributes['ENA-BASE-COUNT'] = int(attributes['ENA-BASE-COUNT'])
        except:  # noqa
            pass
    try:

        try:
            experiment = soup.find('ID', text=EXPERIMENT_PARSER).text
        except:  # noqa
            experiment = soup.find('PRIMARY_ID', text=EXPERIMENT_PARSER).text

    except:  # noqa
        experiment = ''
        logger.warning('No experiment found')

    return {
        'accession': accession,
        'title': title,
        'organism': organism,
        'attributes': attributes,
        'experiments': experiment
    }


def parse_experiment_with_run(soup, level):
    """Given a BeautifulSoup object representing an experiment, parse out relevant
    information.

    :param soup: a BeautifulSoup object representing an experiment
    :type soup: bs4.BeautifulSoup

    :param l: positive integer representing how many downstream accession levels should be fetched.
    :type l: int

    :return: a dictionary containing experiment information
    :rtype: dict
    """
    accession = soup.find('PRIMARY_ID', text=EXPERIMENT_PARSER).text
    title = soup.find('TITLE').text
    platform = soup.find('INSTRUMENT_MODEL').find_parent().name
    instrument = soup.find('INSTRUMENT_MODEL').text

    experiment = {
        'accession': accession,
        'title': title,
        'platform': platform,
        'instrument': instrument
    }
    if level is None or level > 1:
        # Returns all of the runs associated with an experiment
        runs = srx_to_srrs(accession)

        if len(runs) == 1:
            logger.warning(f'There is 1 run for {accession}')

        else:
            logger.warning(f'There are {len(runs)} runs for {accession}')

        runs = {run: ffq_run(run) for run in runs}

        experiment.update({'runs': runs})
        return experiment
    else:
        return experiment


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


def parse_gse_search(soup):
    """Given a BeautifulSoup object representing a geo study, parse out relevant
    information.

    :param soup: a BeautifulSoup object representing a study
    :type soup: bs4.BeautifulSoup

    :return: a dictionary containing geo study unique identifier based on a search
    :rtype: dict
    """
    data = json.loads(soup.text)
    if data['esearchresult']['idlist']:
        accession = data['esearchresult']['querytranslation'].split('[')[0]
        geo_id = data['esearchresult']['idlist'][-1]
        return {'accession': accession, 'geo_id': geo_id}
    else:
        logger.error("Provided GSE accession is invalid")
        sys.exit(1)


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


def ffq_run(accession, level=0):  # noqa
    """Fetch Run information.

    :param accession: run accession (SRR, ERR or DRR)
    :type accession: str

    :return: dictionary of run information
    :rtype: dict
    """
    logger.info(f'Parsing run {accession}')
    run = parse_run(get_xml(accession))
    return run


def ffq_study(accession, level=None):
    """Fetch Study information.

    :param accession: study accession (SRP, ERP or DRP)
    :type accession: str

    :param l: positive integer representing how many downstream accession levels should be fetched.
    :type l: int

    :return: dictionary of study information. The dictionary contains a
             'samples' key, which is a dictionary of all the samples in the study, as
             returned by `ffq_sample`.
    :rtype: dict
    """
    logger.info(f'Parsing Study {accession}')
    study = parse_study(get_xml(accession))
    if level is None or level != 1:
        try:
            level -= 1
        except:  # noqa
            pass
        logger.info(f'Getting Sample for {accession}')
        sample_ids = get_samples_from_study(accession)
        logger.warning(
            f'There are {str(len(sample_ids))} samples for {accession}'
        )
        samples = [ffq_sample(sample_id, level) for sample_id in sample_ids]
        study.update({
            'samples': {sample['accession']: sample
                        for sample in samples}
        })
        return study
    else:
        return study


def ffq_gse(accession, level=None):
    """Fetch GSE information.

    This function finds the GSMs corresponding to the GSE and calls `ffq_gsm`.

    :param accession: GSE accession
    :type accession: str

    :param l: positive integer representing how many downstream accession levels should be fetched.
    :type l: int

    :return: dictionary containing GSE information. The dictionary contains a
             'sample' key, which is a dictionary of all the GSMs in the study, as
             returned by `ffq_gsm`.
    :rtype: dict
    """
    logger.info(f'Parsing GEO {accession}')
    gse = parse_gse_search(get_gse_search_json(accession))
    logger.info(f'Finding supplementary files for GEO {accession}')
    time.sleep(1)
    supp = geo_to_suppl(accession, "GSE")
    if len(supp) > 0:
        gse.update({'supplementary_files': supp})
    else:
        logger.info(f'No supplementary files found for {accession}')
    gse.pop('geo_id')
    if level is None or level != 1:
        try:
            level -= 1
        except:  # noqa
            pass
        time.sleep(1)
        gsm_ids = gse_to_gsms(accession)
        logger.warning(f'There are {str(len(gsm_ids))} samples for {accession}')
        gsms = [ffq_gsm(gsm_id, level) for gsm_id in gsm_ids]
        gse.update({
            'geo_samples': {sample['accession']: sample
                            for sample in gsms}
        })
        return gse
    else:
        return gse


def ffq_gsm(accession, level=None):
    """Fetch GSM information.

    This function finds the SRS corresponding to the GSM and calls `ffq_sample`.

    :param accession: GSM accession
    :type accession: str

    :param l: positive integer representing how many downstream accession levels should be fetched.
    :type l: int

    :return: dictionary containing GSM information. The dictionary contains a
             'sample' key, which is a dictionary of the sample asssociated to the GSM, as
             returned by `ffq_sample`.
    :rtype: dict
    """
    logger.info(f'Parsing GSM {accession}')
    gsm = get_gsm_search_json(accession)
    logger.info(f'Finding supplementary files for GSM {accession}')
    time.sleep(1)
    supp = geo_to_suppl(accession, "GSM")
    if supp:
        gsm.update({'supplementary_files': supp})
    else:
        logger.info(f'No supplementary files found for {accession}')

    gsm.update(gsm_to_platform(accession))
    if level is None or level != 1:
        try:
            level -= 1
        except:  # noqa
            pass
        logger.info(f'Getting sample for {accession}')
        srs = gsm_id_to_srs(gsm.pop('geo_id'))
        if srs:
            sample = ffq_sample(srs, level)
            gsm.update({'samples': {sample['accession']: sample}})
        else:
            return gsm
        return gsm
    else:
        return gsm


def ffq_experiment(accession, level=None):
    """Fetch Experiment information.

    :param accession: experiment accession (SRX, ERX or DRX)
    :type accession: str

    :param l: positive integer representing how many downstream accession levels should be fetched.
    :type l: int

    :return: dictionary of experiment information. The dictionary contains a
             'runs' key, which is a dictionary of all the runs in the study, as
             returned by `ffq_run`.
    :rtype: dict
    """
    logger.info(f'Parsing Experiment {accession}')
    experiment = parse_experiment_with_run(get_xml(accession), level)
    return experiment


def ffq_sample(accession, level=None):
    """Fetch Sample information.

    :param accession: sample accession (SRS, ERS or DRS)
    :type accession: str

    :param l: positive integer representing how many downstream accession levels should be fetched.
    :type l: int

    :return: dictionary of sample information. The dictionary contains a
             'runs' key, which is a dictionary of all the runs in the study, as
             returned by `ffq_run`.
    :rtype: dict
    """
    logger.info(f'Parsing sample {accession}')
    sample = parse_sample(get_xml(accession))
    if level is None or level != 1:
        try:
            level -= 1
        except:  # noqa
            pass
        logger.info(f'Getting Experiment for {accession}')
        exp_id = sample['experiments']
        if exp_id:
            if ',' in exp_id:
                exp_ids = exp_id.split(',')
                experiments = [
                    ffq_experiment(exp_id, level) for exp_id in exp_ids
                ]
                sample.update({
                    'experiments': [{
                        experiment['accession']: experiment
                    } for experiment in experiments]
                })
                return sample
            else:
                experiment = ffq_experiment(exp_id, level)
                sample.update({
                    'experiments': {
                        experiment['accession']: experiment
                    }
                })
        else:
            logger.warning(f'No Experiment found for {accession}')
        return sample
    else:
        return sample


def ffq_encode(accession, level=0):
    """Fetch ENCODE ids information. This
    function receives an ENCSR, ENCBS or ENCD
    ENCODE id and fetches the associated metadata

    :param accession: an ENCODE id (ENCSR, ENCBS or ENCD)
    :type accession: str

    :return: dictionary of ENCODE id metadata.
    :rtype: dict
    """
    logger.info(f'Parsing {accession}')
    encode = parse_encode_json(accession, get_encode_json(accession))
    return encode


def ffq_bioproject(accession, level=0):  # noqa
    """Fetch bioproject ids information. This
    function receives a CXR accession
    and fetches the associated metadata

    :param accession: a bioproject CXR id
    :type accession: str

    :return: dictionary of bioproject metadata.
    :rtype: dict
    """
    return parse_bioproject(ena_fetch(accession, 'bioproject'))


def ffq_biosample(accession, level=None):
    """Fetch biosample ids information. This
    function receives a SAMN accession
    and fetches the associated metadata

    :param accession: a biosample SAMN id
    :type accession: str

    :return: dictionary of biosample metadata.
    :rtype: dict
    """
    soup = ena_fetch(accession, 'biosample')
    sample = soup.find('id', text=SAMPLE_PARSER).text
    try:
        level = level - 1
    except:  # noqa
        pass
    sample_data = ffq_sample(sample, level)
    return {'accession': accession, 'samples': sample_data}


def ffq_doi(doi, level=0):  # noqa
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
        return [ffq_study(accession, None) for accession in study_accessions]

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
        # Sleep for 1sec because NCBI has rate-limiting to 3 requests/sec
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
