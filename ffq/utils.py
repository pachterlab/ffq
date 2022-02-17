import json
import re
import time
from functools import lru_cache
import sys
import numpy as np

import requests
from ftplib import FTP
from bs4 import BeautifulSoup
from frozendict import frozendict
import logging

from .config import (
    CROSSREF_URL,
    ENA_SEARCH_URL,
    ENA_URL,
    GSE_SEARCH_URL,
    GSE_SUMMARY_URL,
    GSE_SEARCH_TERMS,
    GSE_SUMMARY_TERMS,
    NCBI_FETCH_URL,
    NCBI_LINK_URL,
    NCBI_SEARCH_URL,
    NCBI_SUMMARY_URL,
    FTP_GEO_URL,
    FTP_GEO_SAMPLE,
    FTP_GEO_SERIES,
    FTP_GEO_SUPPL,
    ENCODE_BIOSAMPLE_URL,
    ENCODE_JSON
)


RUN_PARSER = re.compile(r'(SRR.+)|(ERR.+)|(DRR.+)')
GSE_PARSER = re.compile(r'Series\t\tAccession: (?P<accession>GSE[0-9]+)\t')
SRP_PARSER = re.compile(r'Study acc="(?P<accession>SRP[0-9]+)"')
SRR_PARSER = re.compile(r'Run acc="(?P<accession>SRR[0-9]+)"')
EXPERIMENT_PARSER = re.compile(r'(SRX.+)|(ERX.+)|(DRX.+)')
SAMPLE_PARSER = re.compile(r'(SRS.+)|(ERS.+)|(DRS.+)')

logger = logging.getLogger(__name__)

@lru_cache()
def cached_get(*args, **kwargs):
    """Cached version of requests.get.

    :return: text of response
    :rtype: str
    """

    response = requests.get(*args, **kwargs)

    try:
        response.raise_for_status()
    except requests.HTTPError as exception:
        logger.error(f'{exception}')
        logger.error ('Provided SRA accession is invalid')
        exit(1)
    text = response.text
    if not text:
        logger.warning(f'No metadata found in {args[0]}')
        sys.exit(1)
    else:
        return response.text


def get_xml(accession):
    """Given an accession, retrieve the XML from ENA.

    :param accession: an accession
    :type accession: str

    :return: a BeautifulSoup object of the parsed XML
    :rtype: bs4.BeautifulSoup
    """

    return BeautifulSoup(cached_get(f'{ENA_URL}/{accession}/'), 'xml')


def get_encode_json(accession):
    return json.loads(cached_get(f'{ENCODE_BIOSAMPLE_URL}/{accession}{ENCODE_JSON}'))

def get_doi(doi):
    """Given a DOI, retrieve metadata from CrossRef.

    :param doi: the DOI, without the leading hostname (no http or https)
    :type doi: str

    :return: response from CrossRef as a dictionary
    :rtype: dict
    """
    return json.loads(cached_get(f'{CROSSREF_URL}/{doi}'))['message']


def get_gse_search_json(accession):
    """Given an accession, retrieve the JSON from GEO SEARCH.

    :param accession: an accession
    :type accession: str

    :return: a BeautifulSoup object of the parsed JSON
    :rtype: bs4.BeautifulSoup
    """
    return BeautifulSoup(
        cached_get(f'{GSE_SEARCH_URL}{accession}{GSE_SEARCH_TERMS}'),
        'html.parser'
    )


def get_gsm_search_json(accession):
    """Given a GSM accession, retrieve the JSON from GEO SEARCH.

    :param accession: a GSM accession
    :type accession: str

    :return: a BeautifulSoup object of the parsed JSON
    :rtype: bs4.BeautifulSoup
    """
    geo = ncbi_search("gds", accession)
    if geo:
        geo_id = geo_id[-1]
        return {'accession': accession, 'geo_id': geo_id}
    else:
        logger.error('Provided GSM accession is invalid')
        sys.exit(1)


def get_gse_summary_json(accession):
    """Given an accession, retrieve the JSON from GEO SUMMARY.

    :param accession: an accession
    :type accession: str

    :return: a BeautifulSoup object of the parsed JSON
    :rtype: bs4.BeautifulSoup
    """
    return BeautifulSoup(
        cached_get(f'{GSE_SUMMARY_URL}{accession}{GSE_SUMMARY_TERMS}'),
        'html.parser'
    )


def get_samples_from_study(accession):

    """Given an SRP accession for a study, get list of
    associated samples.

    :param accession: an SRP id representing a study
    :type accession: str

    :return: a list of associated experiment ids (SRSs)
    :rtype: list
    """
    soup = get_xml(accession)
    samples_parsed = soup.find("ID", text = SAMPLE_PARSER)
    samples = []
    if samples_parsed:
        samples_ranges = samples_parsed.text.split(',')
        for sample_range in samples_ranges:
            if '-' in sample_range:
                samples += parse_range(sample_range) 
            else:
                samples.append(sample_range)
    else:
            # The original code fell to ENA search if runs were not found. I don't know if this is
            # necessary, so make a warning to detect it in case it is.      
        logger.warning('No samples found for study. Modify code to search through ENA') 
        return

    return samples

def parse_encode_biosample(data, accession = ''):
    keys_biosample = ['accession', 'dbxrefs', 'description', 'genetic_modifications', 'treatments', 'sex', 'life_stage', 'age', 'age_units', 'organism', 'genetic_modifications' ]
    biosample = {key: data.get(key, '') for key in keys_biosample}

    keys_biosample_ontology = ['classification', 'term_name', 'organ_slims', 'cell_slims', 'system_slims', 'developmental_slims', 'system_slims', 'treatments', 'genetic_modifications']
    biosample_ontology = {key: data.get(key, '') for key in keys_biosample_ontology}
    biosample.update({'biosample_ontology': biosample_ontology})
    return biosample


def parse_encode_donor(data, accession = ''):
    keys_donor = ['accession', 'dbxrefs', 'organism', 'sex', 'life_stage', 'age', 'age_units', 'health_status', 'ethnicity']
    donor = {key: data.get(key, '') for key in keys_donor}
    return donor


def parse_encode_json(accession, data):
    
    """Parse a python dictionary containing
    ENCODE metadata into a parsed dictionary 
    with select metadata to be returned by 
    `ffq_ENCODE`

    :param data: python dictionary containing ENCODE metadata
    :type s: dict

    :return: dictionary with parsed ENCODE metadata
    :rtype: dict
    """

    encode = {}
    if accession[:5] == "ENCSR":
        keys_assay = ['accession', 'description', 'dbxrefs']
        encode.update({key: data.get(key, '') for key in keys_assay})
        replicates_data_list = []

        for replicate in data['replicates']:
            keys_replicate = ['biological_replicate_number', 'technical_replicate_number']
            replicate_data = {key: replicate.get(key, '') for key in keys_replicate}

            library = replicate['library']
            keys_library = ['accession', 'dbxrefs']
            library_data = {key: library.get(key, '') for key in keys_library}


            biosample = parse_encode_biosample(library['biosample'])
            donor = parse_encode_donor(library['biosample']['donor'])
    
            biosample.update({'donor' : donor})
            library_data.update({'biosample': biosample})
            replicate_data.update({'library' : library_data})
            replicates_data_list.append(replicate_data)

        encode.update({'replicates': replicate for replicate in replicates_data_list})

        files_data = []
        keys_files = ['accession', 'description', 'dbxrefs', 'file_format', 'file_size', 'output_type', 'cloud_metadata']
        for file in data['files']:
            files_data.append({key: (file[key] if key in file.keys() else "") for key in keys_files})

        encode.update({'files' : {file['accession'] : file for file in files_data}})

        return encode

    if accession[:5] == 'ENCBS':
        encode = parse_encode_biosample(data, accession)

    if accession[:5] == "ENCDO":
        encode = parse_encode_donor(data, accession)

    return encode



def parse_tsv(s):
    """Parse TSV-formatted string into a list of dictionaries.

    :param s: TSV-formatted string
    :type s: str

    :return: list of dictionaries, with each dictionary containing keys from
             the header (first line of string)
    :rtype: list
    """
    lines = s.strip().splitlines()
    header = lines.pop(0).split('\t')

    rows = []
    for line in lines:
        values = line.split('\t')
        rows.append({key: value for key, value in zip(header, values)})
    return rows


def search_ena_study_runs(accession):
    """Given a study accession (SRP), submit a search request to ENA for all
    linked run accessions (SRR).

    :param accession: study accession
    :type accession: str

    :return: list of SRPs
    :rtype: list
    """
    text = cached_get(
        ENA_SEARCH_URL,
        params=frozendict({
            'query': f'secondary_study_accession="{accession}"',
            'result': 'read_run',
            'fields': 'run_accession',
            'limit': 0,
        })
    )
    if not text:
        return []
    table = parse_tsv(text)
    return [t['run_accession'] for t in table]


def search_ena_run_study(accession):
    """Given a run accession (SRR), submit a search request to ENA for its
    corresponding study accession (SRP).

    :param accession: run accession
    :type accession: str

    :return: study accession
    :rtype: str
    """
    text = cached_get(
        ENA_SEARCH_URL,
        params=frozendict({
            'query': f'run_accession="{accession}"',
            'result': 'read_run',
            'fields': 'secondary_study_accession',
            'limit': 0,
        })
    )
    if not text:
        return []
    table = parse_tsv(text)
    # Make sure only one study was returned
    accessions = set(t['secondary_study_accession'] for t in table)
    if len(accessions) != 1:
        raise Exception(
            f'Run {accession} is associated with {len(accessions)} studies, '
            'but one was expected.'
        )
    return list(accessions)[0]


def search_ena_run_sample(accession):
    """Given a run accession (SRR), submit a search request to ENA for its
    corresponding sample accession (SRS).

    :param accession: run accession
    :type accession: str

    :return: sample accession
    :rtype: str
    """
    text = cached_get(
        ENA_SEARCH_URL,
        params=frozendict({
            'query': f'run_accession="{accession}"',
            'result': 'read_run',
            'fields': 'secondary_sample_accession',
            'limit': 0,
        })
    )
    if not text:
        return []
    table = parse_tsv(text)
    # Make sure only one study was returned
    accessions = set(t['secondary_sample_accession'] for t in table)
    if len(accessions) != 1:
        raise Exception(
            f'Run {accession} is associated with {len(accessions)} samples, '
            'but one was expected.'
        )
    return list(accessions)[0]


def search_ena_title(title):
    """Given a title, search the ENA for studies (SRPs) corresponding to the title.

    :param title: study title
    :type title: str

    :return: list of SRPs
    :rtype: list
    """
    text = cached_get(
        ENA_SEARCH_URL,
        params=frozendict({
            'result': 'study',
            'limit': 0,
            'query': f'study_title="{title}"',
            'fields': 'secondary_study_accession',
        })
    )
    if not text:
        return []
    table = parse_tsv(text)

    # If there is no secondary_study_accession, need to use bioproject.
    srps = [
        t['secondary_study_accession']
        for t in table
        if 'secondary_study_accession' in t and t['secondary_study_accession']
    ]
    bioprojects = [
        t['study_accession']
        for t in table
        if 'secondary_study_accession' not in t
    ]

    if bioprojects:
        bioproject_ids = ncbi_search(
            'bioproject',
            ' or '.join(f'{bioproject}[PRJA]' for bioproject in bioprojects)
        )
        sra_ids = ncbi_link('bioproject', 'sra', ','.join(bioproject_ids))

        # Fetch summaries of these SRA ids
        time.sleep(1)
        sras = ncbi_summary('sra', ','.join(sra_ids))
        srps.extend(SRP_PARSER.findall(str(sras)))

    return list(set(srps))


def ncbi_summary(db, id):
    """Fetch a summary from the specified NCBI entrez database for the specified term.
    Documentation: https://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.ESummary

    :param db: an entrez database
    :type db: str
    :param id: database id, can be comma-delimited list of ids
    :type id: str

    :return: dictionary of id-summary pairs
    :rtype: dict
    """
    # TODO: use cached get. Can't be used currently because dictionaries can
    # not be hashed.
    response = requests.get(
        NCBI_SUMMARY_URL,
        params={
            'db': db,
            'id': id,
            'retmode': 'json',
            'retmax': 10000  # maximum allowed
        }
    )
    response.raise_for_status()
    return {
        id: summary
        for id, summary in response.json()['result'].items()
        if id != 'uids'
    }


def ncbi_search(db, term):
    # Note (AGM): consolidate with get_gsm_search_json and get_gse_search_json  
    """Search the specified NCBI entrez database for the specified term.
    Documentation: https://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.ESearch

    :param db: an entrez database
    :type db: str
    :param term: search term
    :type term: str

    :return: list of ids that match the search
    :rtype: list
    """
    # TODO: use cached get. Can't be used currently because dictionaries can
    # not be hashed.
    response = requests.get(
        NCBI_SEARCH_URL,
        params={
            'db': db,
            'term': term,
            'retmode': 'json',
            'retmax': 100000  # max allowed
        }
    )
    response.raise_for_status()
    return sorted(response.json().get('esearchresult', {}).get('idlist', []))


def ncbi_link(origin, destination, id):
    """Translate an ID from one NCBI entrez database to another.
    Documentation: https://www.ncbi.nlm.nih.gov/books/NBK25499/#chapter4.ELink

    :param origin: the entrez database that the id belongs to
    :type origin: str
    :param destination: the entrez database to translate the id to
    :type destination: str
    :param id: entrez database ID
    :type id: str

    :return: list of ids that match the search
    :rtype: list
    """ 
    # TODO: use cached get. Can't be used currently because dictionaries can
    # not be hashed.  
    response = requests.get(
        NCBI_LINK_URL,
        params={
            'dbfrom': origin,
            'db': destination,
            'id': id,
            'retmode': 'json',
        }
    )
    response.raise_for_status()
    ids = []
    for linkset in response.json().get('linksets', []):
        if linkset:
            for linksetdb in linkset.get('linksetdbs', {}):
                ids.extend(linksetdb.get('links', []))
    return sorted(list(set(ids)))


def geo_id_to_srps(id):
    """Convert a GEO ID to an SRP.

    :param id: GEO ID
    :type id: str

    :return: SRP accession
    :rtype: str
    """
    summaries = ncbi_summary('gds', id)
    data = summaries[id]

    # Check if there is a directly linked SRP
    srps = []
    if 'extrelations' in data:
        for value in data['extrelations']:
            if value['relationtype'] == 'SRA':  # may have manys samples?
                srps.append(value['targetobject'])
        return srps

    # No SRA relation was found, but all GSEs have linked bioproject, so
    # search for that instead.
    bioproject_ids = ncbi_search('bioproject', f'{data["bioproject"]}[PRJA]')
    assert len(bioproject_ids) == 1
    bioproject_id = bioproject_ids[0]

    # Search for SRA ids linked to this bioproject.
    sra_ids = ncbi_link('bioproject', 'sra', bioproject_id)

    # Fetch summaries of these SRA ids
    time.sleep(1)
    sras = ncbi_summary('sra', ','.join(sra_ids))
    srps = list(set(SRP_PARSER.findall(str(sras))))
    return srps


def gsm_id_to_srs(id):
    """Convert a GEO ID to an SRS.
    :param id: GEO ID
    :type id: str
    :return: SRS accession
    :rtype: str
    """
    summaries = ncbi_summary('gds', id)
    data = summaries[id]

    # Check if there is a directly linked SRX 
    srxs = []
    if 'extrelations' in data:
        for value in data['extrelations']:
            if value['relationtype'] == 'SRA':  # may have manys samples?  
                srxs.append(value['targetobject'])
    if srxs:
        for srx in srxs:
            soup = get_xml(srx)
            sample = soup.find('ID', text = SAMPLE_PARSER).text
    else:
        logger.warning(f'No SRS sample found. Please check if the provided GSM accession is valid')
        exit(1)
    return sample
 

def geo_ids_to_gses(ids):
    """Convert GEO IDs (which is a number) to GSE (which start with GSE).

    :param id: list of GEO IDs
    :type id: list

    :return: list of GSE accessions
    :rtype: list
    """
    # TODO: use cached get. Can't be used currently because dictionaries can
    # not be hashed.
    response = requests.get(
        NCBI_FETCH_URL, params={
            'db': 'gds',
            'id': ','.join(ids)
        }
    )
    response.raise_for_status()
    return sorted(list(set(GSE_PARSER.findall(response.text))))



def sra_ids_to_srrs(ids):
    """Convert SRA IDs (which is a number) to SRRs.

    :param id: list of SRA IDs
    :type id: list

    :return: list of SRR accessions
    :rtype: list
    """
    # TODO: use cached get. Can't be used currently because dictionaries can
    # not be hashed.
    response = requests.get(
        NCBI_SUMMARY_URL, params={
            'db': 'sra',
            'id': ','.join(ids)
        }
    )
    response.raise_for_status()
    return sorted(list(set(SRR_PARSER.findall(response.text))))


def parse_range(text):
    """Given an a string of any accession ranges, returns a list of intermediary accession numbers.

    :param text: an SRA range (example: 'SRR4340020-SRR4340045', 'SRS345678-SRS34590, 'ERR4340020-ERR4340045')
    :type text: str

    :return: a list of range of accession numbers
    :rtype: list
    """


    first, last = text.split('-')
    base = re.match(r'^.*?(?=[0-9])', first).group(0)

    ids = [
        f'{base}{str(i).zfill(len(first) - 3)}'
        for i in range(int(first[3:]),
                       int(last[3:]) + 1)
    ]
    return ids


def geo_to_suppl(accession, GEO):
    """Retrieve supplemental files
    associated with a GEO ID.
    :param accession: GEO ID
    :type id: str
    :param GEO: Type of GEO entry, either GSM or GSE
    :type id: str
    :return: a list of dictionaries with supplemental file information
    :rtype: list
    """
    if GEO == "GSM":
        link = FTP_GEO_SAMPLE
    elif GEO == "GSE":
        link = FTP_GEO_SERIES
    ftp = FTP(FTP_GEO_URL)
    ftp.login()
    path = f'{link}{accession[:-3]}nnn/{accession}{FTP_GEO_SUPPL}'
    files = ftp.mlsd(path)
    try:
        supp = [
                 {
               'filename' : entry[0],
                   'url' : f"{FTP_GEO_URL}{path}{entry[0]}",
                'size' : entry[1].get('size')
             }
         for entry in files if entry[1].get('type') == 'file']
        
    except:
        return []

    return supp

def gsm_to_platform(accession):
    """Retrieve platform metadata
    associated with a GSM ID.
    :param accession: GSM ID
    :type id: str
    :return: a dictionary with platform accession and title
    :rtype: dict
    """
    platform_id = ncbi_search("gds",accession)[0]
    if platform_id.startswith('1'):
        platform_summary = ncbi_summary("gds", platform_id)[platform_id]
        platform = {k:v for k,v in platform_summary.items() if k in ["accession", "title"]}
        return {'platform' : platform}
    else:
        return {}

def gse_to_gsms(accession):
    gse_id = json.loads(get_gse_search_json(accession).text)['esearchresult']['idlist'][-1]
    gse = ncbi_summary("gds",gse_id)
    gsms = [sample['accession'] for sample in gse[gse_id]['samples']]
    gsms.sort()
    return gsms


def gsm_to_srx(accession):
    id = get_gsm_search_json(accession)['geo_id']
    srx = ncbi_summary("gds", id)[id]['extrelations'][0]['targetobject']
    return srx


def srs_to_srx(accession):
    soup = get_xml(accession)
    return soup.find('ID', text = EXPERIMENT_PARSER).text


def srx_to_srrs(accession):
    soup = get_xml(accession)
    runs = []
    run_parsed = soup.find('ID', text=RUN_PARSER)
    if run_parsed:
        run_ranges = run_parsed.text.split(",")
        for run_range in run_ranges:
            if '-' in run_range:
                runs += parse_range(run_range)
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
    return runs


def get_ftp_links_from_run(soup):
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
    return files

