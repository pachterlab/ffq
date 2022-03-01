import json
import logging
import re
import time
from urllib.parse import urlparse
import sys

from .utils import (
    cached_get,
    geo_id_to_srps,
    geo_ids_to_gses,
    gsm_id_to_srs,
    get_doi,
    get_gse_search_json,
    get_gsm_search_json,
    get_xml,
    get_encode_json,
    get_samples_from_study,
    ncbi_link,
    ncbi_search,
    ncbi_fetch_fasta,
    ncbi_summary,
    parse_range,
    parse_encode_biosample,
    parse_encode_donor,
    parse_encode_json,
    parse_tsv,
    search_ena_run_sample,
    search_ena_run_study,
    search_ena_study_runs,
    search_ena_title,
    sra_ids_to_srrs,
    geo_to_suppl,
    gsm_to_platform,
    gse_to_gsms,
    srs_to_srx,
    gsm_to_srx,
    srx_to_srrs,
    get_files_metadata_from_run,
    parse_url,
    parse_ncbi_fetch_fasta
)

logger = logging.getLogger(__name__)

RUN_PARSER = re.compile(r'(SRR.+)|(ERR.+)|(DRR.+)')
EXPERIMENT_PARSER = re.compile(r'(SRX.+)|(ERX.+)|(DRX.+)')
PROJECT_PARSER = re.compile(r'(SRP.+)|(ERP.+)|(DRP.+)')
SAMPLE_PARSER = re.compile(r'(SRS.+)|(ERS.+)|(DRS.+)')
DOI_PARSER = re.compile('^10.\d{4,9}\/[-._;()\/:a-z0-9]+')


def validate_accession(accessions, search_types):
    ID_types = [re.findall(r"(\D+).+", accession)[0] for accession in accessions]
    return [(ID_type, accession) if ID_type in search_types else False if DOI_PARSER.match(accession) is None else ("DOI", accession) for accession, ID_type in zip(accessions, ID_types)]
    

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
    files = get_files_metadata_from_run(soup)

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
    experiment = soup.find('ID', text = EXPERIMENT_PARSER).text
    return {
        'accession': accession,
        'title': title,
        'organism': organism,
        'attributes': attributes,
        'experiment': experiment
    }


def parse_experiment_with_run(soup):
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

    experiment = {'accession': accession,
    'title': title,
    'platform': platform,
    'instrument': instrument}

    # Returns all of the runs associated with an experiment
    runs = srx_to_srrs(accession)

    if len(runs) == 1:
        logger.warning(f'There is 1 run for {accession}')

    else:
        logger.warning(f'There are {len(runs)} runs for {accession}')

    runs = {run: ffq_run(run) for run in runs}

    experiment.update({'runs': runs})
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


def ffq_run(accession):
    """Fetch Run information.

    :param accession: run accession
    :type accession: str

    :return: dictionary of run information
    :rtype: dict
    """
    logger.info(f'Parsing run {accession}')
    run = parse_run(get_xml(accession))
    return run


def ffq_study(accession):
    """Fetch Study information.

    :param accession: study accession
    :type accession: str

    :return: dictionary of study information. The dictionary contains a
             'samples' key, which is a dictionary of all the samples in the study, as
             returned by `ffq_sample`.
    :rtype: dict
    """
    logger.info(f'Parsing Study SRP {accession}')
    study = parse_study(get_xml(accession))
    logger.info(f'Getting Sample SRS for {accession}')
    sample_ids = get_samples_from_study(accession)
    logger.warning(f'There are {str(len(sample_ids))} samples for {accession}')
    samples = [ffq_sample(sample_id) for sample_id in sample_ids]
    study.update({'samples': {sample['accession']: sample for sample in samples}})
    return study


def ffq_gse(accession):
    """Fetch GSE information.

    This function finds the GSMs corresponding to the GSE and calls `ffq_gsm`.

    :param accession: GSE accession
    :type accession: str

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
        gse.update({'supplementary_files' : supp})
    else:
        logger.info(f'No supplementary files found for {accession}')        
    gse.pop('geo_id')
    time.sleep(1)
    gsm_ids = gse_to_gsms(accession)
    logger.warning(f'There are {str(len(gsm_ids))} samples for {accession}')
    gsms = [ffq_gsm(gsm_id) for gsm_id in gsm_ids]
    gse.update({'samples': {sample['accession']: sample for sample in gsms}})
    return gse


def ffq_gsm(accession):
    """Fetch GSM information.

    This function finds the SRS corresponding to the GSM and calls `ffq_sample`.

    :param accession: GSM accession
    :type accession: str

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
        gsm.update({'supplementary_files' : supp})
    else:
        logger.info(f'No supplementary files found for {accession}')        

    gsm.update(gsm_to_platform(accession))
    logger.info(f'Getting sample SRS for {accession}')
    srs = gsm_id_to_srs(gsm.pop('geo_id'))
    sample = ffq_sample(srs)
    gsm.update({'sample': {sample['accession']: sample }})
    return gsm


def ffq_experiment(accession):
    """Fetch Experiment information.

    :param accession: experiment accession (SRX)
    :type accession: str

    :return: dictionary of experiment information. The dictionary contains a
             'runs' key, which is a dictionary of all the runs in the study, as
             returned by `ffq_run`.
    :rtype: dict
    """
    logger.info(f'Parsing Experiment {accession}')
    experiment = parse_experiment_with_run(get_xml(accession))
    return experiment


def ffq_sample(accession):

    """Fetch Sample information.

    :param accession: sample accession (SRS)
    :type accession: str

    :return: dictionary of sample information. The dictionary contains a
             'runs' key, which is a dictionary of all the runs in the study, as
             returned by `ffq_run`.
    :rtype: dict
    """
    logger.info(f'Parsing sample {accession}')
    sample = parse_sample(get_xml(accession))
    logger.info(f'Getting Experiment SRX for {accession}')
    experiment = ffq_experiment(sample['experiment'])
    sample.update({'experiment': {experiment['accession']: experiment}})
    return sample


def ffq_encode(accession):
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


def ffq_links(type_accessions, server):
    """Prints download links for raw data
    from provided server (FTP, AWS, or GCP)
    to the terminal

    :param type_accession: tuple of accession type and accession id
    :type type_accessions: (str, str)
    
    :param server: server of desired links
    "type server: str

    :return: None
    :rtype: None
    """
    origin_SRP = False
    origin_GSE = False
    for id_type, accession in type_accessions:
        if id_type == "GSE":
            print("accession\tfiletype\tfilenumber\tlink")
            accession = gse_to_gsms(accession) 
            id_type = "GSM"
            origin_GSE = True

        else:
            pass 
        if id_type == "GSM":

            if isinstance(accession, str):
                accession = [accession]
            counter = 0
            for gsm in accession:
                srx = gsm_to_srx(gsm)
                srrs = srx_to_srrs(srx)
                for srr in srrs:
                    if server == 'ftp':
                        for file in get_files_metadata_from_run(get_xml(srr)):
                            url = file['url']
                            if origin_GSE:
                                print(gsm, end = '\t')                  
                                filetype, fileno = parse_url(url)      
                                print(f'\t{filetype}\t{fileno}\t{url}')
                            else:
                                print(url, end = ' ')
                    else:
                        urls = parse_ncbi_fetch_fasta(ncbi_fetch_fasta(srr, 'sra'), server)
                        for url in urls:
                            if origin_GSE:
                                print(gsm, end = '\t')                  
                                filetype, fileno = parse_url(url)      
                                print(f'\t{filetype}\t{fileno}\t{url}')
                            else:
                                print(url, end = " ")

        if id_type == "SRP":
            # print(accession)
            # print("-" * len(accession))
            # print('\n')
            accession = get_samples_from_study(accession)
            id_type = 'SRS'
            origin_SRP = True

        if id_type == "SRS":
            counter = 0
            if isinstance(accession, str):
                accession = [accession]
            for srs in accession:
                accession = srs_to_srx(srs)
                id_type = "SRX"
        if id_type == "SRX":
            srrs = srx_to_srrs(accession)
            for srr in srrs:
                if server == 'ftp':
                    for file in get_files_metadata_from_run(get_xml(srr)):
                        url = file['url']
                        if origin_SRP:
                            print(srr, end = '\t')                  
                            filetype, fileno = parse_url(url)      
                            print(f'\t{filetype}\t{fileno}\t{url}')
                        else:
                            print(url, end = ' ')
                else:
                    urls = parse_ncbi_fetch_fasta(ncbi_fetch_fasta(srr, 'sra'), server)
                    for url in urls:
                        if origin_SRP:
                            print(srr, end = '\t')                  
                            filetype, fileno = parse_url(url)      
                            print(f'\t{filetype}\t{fileno}\t{url}')
                        else:
                            print(url, end = " ")
        if id_type == "SRR":
            if server == 'ftp':
                for file in get_files_metadata_from_run(get_xml(accession)):
                    print(file['url'], end = " ")
            else:
                urls = parse_ncbi_fetch_fasta(ncbi_fetch_fasta(accession, 'sra'), server)
                for url in urls:
                    print(url, end = " ")


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
