import json
import re
import time
from functools import lru_cache
import sys

import requests
from ftplib import FTP
from bs4 import BeautifulSoup
from frozendict import frozendict
import logging

from .config import (
    CROSSREF_URL, ENA_SEARCH_URL, ENA_URL, ENA_FETCH, GSE_SEARCH_URL,
    GSE_SUMMARY_URL, GSE_SEARCH_TERMS, GSE_SUMMARY_TERMS, NCBI_FETCH_URL,
    NCBI_LINK_URL, NCBI_SEARCH_URL, NCBI_SUMMARY_URL, FTP_GEO_URL,
    FTP_GEO_SAMPLE, FTP_GEO_SERIES, FTP_GEO_SUPPL, ENCODE_BIOSAMPLE_URL,
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
        if exception.getcode() == 429:
            logger.error(
                '429 Client Error: Too Many Requests. Please try again later'
            )
            exit(1)
        else:
            logger.error(f'{exception}')
            logger.error('Provided accession is invalid')
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
    return json.loads(
        cached_get(f'{ENCODE_BIOSAMPLE_URL}/{accession}{ENCODE_JSON}')
    )


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
        geo_id = geo[-1]
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
    samples_parsed = soup.find("ID", text=SAMPLE_PARSER)
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
        logger.warning(
            'No samples found for study. Modify code to search through ENA'
        )
        return

    return samples


def parse_encode_biosample(data):
    """Parse a python dictionary containing
    ENCODE's biosample metadata into a dictionary
    with select biosample metadata

    :param data: python dictionary containing ENCODE' biosample metadata
    :type s: dict

    :return: dictionary with parsed ENCODE's biosample metadata
    :rtype: dict
    """
    keys_biosample = [
        'accession', 'dbxrefs', 'description', 'genetic_modifications',
        'treatments', 'sex', 'life_stage', 'age', 'age_units', 'organism',
        'genetic_modifications'
    ]
    biosample = {key: data.get(key, '') for key in keys_biosample}

    keys_biosample_ontology = [
        'classification', 'term_name', 'organ_slims', 'cell_slims',
        'system_slims', 'developmental_slims', 'system_slims', 'treatments',
        'genetic_modifications'
    ]
    biosample_ontology = {
        key: data.get(key, '')
        for key in keys_biosample_ontology
    }
    biosample.update({'biosample_ontology': biosample_ontology})
    return biosample


def parse_encode_donor(data):
    """Parse a python dictionary containing
    ENCODE's donor metadata into a dictionary
    with select donor metadata

    :param data: python dictionary containing ENCODE' donor metadata
    :type s: dict

    :return: dictionary with parsed ENCODE's donor metadata
    :rtype: dict
    """
    keys_donor = [
        'accession', 'dbxrefs', 'organism', 'sex', 'life_stage', 'age',
        'age_units', 'health_status', 'ethnicity'
    ]
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
            keys_replicate = [
                'biological_replicate_number', 'technical_replicate_number'
            ]
            replicate_data = {
                key: replicate.get(key, '')
                for key in keys_replicate
            }

            library = replicate['library']
            keys_library = ['accession', 'dbxrefs']
            library_data = {key: library.get(key, '') for key in keys_library}

            biosample = parse_encode_biosample(library['biosample'])
            donor = parse_encode_donor(library['biosample']['donor'])

            biosample.update({'donor': donor})
            library_data.update({'biosample': biosample})
            replicate_data.update({'library': library_data})
            replicates_data_list.append(replicate_data)

        encode.update({
            'replicates': replicate
            for replicate in replicates_data_list
        })

        files_data = []
        keys_files = [
            'accession', 'description', 'dbxrefs', 'file_format', 'file_size',
            'output_type', 'cloud_metadata'
        ]
        for file in data['files']:
            files_data.append({
                key: (file[key] if key in file.keys() else "")
                for key in keys_files
            })

        encode.update({
            'files': {file['accession']: file
                      for file in files_data}
        })

        return encode

    if accession[:5] == 'ENCBS':
        encode = parse_encode_biosample(data)

    if accession[:5] == "ENCDO":
        encode = parse_encode_donor(data)

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


def ncbi_fetch_fasta(accession, db):
    """ Fetch fastq files information from the
    specified NCBI entrez database for the specified
    accession

    :param accession: database id
    :type: str

    :param db: ENTREZ database
    :type: str

    :return: BeautifulSoup object with fastq files information
    :rtype: bs4.BeautifulSoup
    """
    response = requests.get(
        NCBI_FETCH_URL,
        params={
            'db': db,
            'id': accession,
            'rettype': 'fasta',
            'retmode': 'xml'  # max allowed
        }
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as exception:
        logger.error(f'{exception}')
        logger.error('Provided accession is invalid')
        exit(1)
    text = response.text
    if not text:
        logger.warning(f'No metadata found for {accession}')
        sys.exit(1)
    else:
        return BeautifulSoup(response.content, 'xml')


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
            if value['relationtype'] == 'SRA':  # may have many samples?
                srxs.append(value['targetobject'])
    if srxs:
        for srx in srxs:
            try:
                soup = get_xml(srx)
                sample = soup.find(
                    re.compile(r'PRIMARY_ID|ID'), text=SAMPLE_PARSER
                ).text
            except:  # noqa
                logger.warning('No sample found')
                return
    else:
        logger.warning((
            "No sample found. Either the provided GSM accession is "
            "invalid or raw data was not provided for this record"
        ))
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

    :param text: an accession range (example: 'SRR4340020-SRR4340045', 'SRS345678-SRS34590, 'ERR4340020-ERR4340045')
    :type text: str

    :return: a list of range of accession numbers
    :rtype: list
    """

    first, last = text.split('-')
    base = re.match(r'^.*?(?=[0-9])', first).group(0)

    ids = [
        f'{base}{str(i).zfill(len(first) - len(base))}'
        for i in range(int(first[len(base):]),
                       int(last[len(base):]) + 1)
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
    try:
        files = ftp.mlsd(path)
    except:  # noqa
        return []
    try:
        supp = []
        idx = 0
        for entry in files:
            if entry[1].get("type") == "file":
                idx += 1
                supp.append({
                    "accession": accession,
                    'filename':
                        entry[0],  # TODO maybe add to other link objects?
                    'filetype': None,  # TODO, get
                    'filesize': int(entry[1].get('size')),
                    'filenumber': idx,
                    'md5': None,
                    "urltype": "ftp",
                    'url': f"ftp://{FTP_GEO_URL}{path}{entry[0]}",
                })
    except:  # noqa
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
    platform_id = ncbi_search("gds", accession)[0]
    if platform_id.startswith('1'):
        platform_summary = ncbi_summary("gds", platform_id)[platform_id]
        platform = {
            k: v
            for k, v in platform_summary.items()
            if k in ["accession", "title"]
        }
        return {'platform': platform}
    else:
        return {}


def gse_to_gsms(accession):
    """Given a GSE accession
    returns all associated GSM ids.
    :param accession: GSE id
    :type id: str
    :return: a list of GSM ids
    :rtype: list
    """
    data = json.loads(get_gse_search_json(accession).text)
    if data['esearchresult']['idlist']:
        gse_id = data['esearchresult']['idlist'][-1]
        gse = ncbi_summary("gds", gse_id)
        gsms = [sample['accession'] for sample in gse[gse_id]['samples']]
        gsms.sort()
        return gsms
    else:
        logger.error("Provided GSE accession is invalid")
        sys.exit(1)


def gsm_to_srx(accession):
    """Given a GSM accession
    returns all associated SRX ids.
    :param accession: GSM id
    :type id: str
    :return: a list of SRX ids
    :rtype: list
    """
    id = get_gsm_search_json(accession)['geo_id']
    summary_extrelations = ncbi_summary("gds", id)[id]['extrelations']
    if summary_extrelations:
        return summary_extrelations[0]['targetobject']
    else:
        return None


def srp_to_srx(accession):
    soup = get_xml(accession)
    experiments_parsed = soup.find("ID", text=EXPERIMENT_PARSER)
    experiments = []
    if experiments_parsed:
        experiments_ranges = experiments_parsed.text.split(',')
        for experiments_range in experiments_ranges:
            if '-' in experiments_range:
                experiments += parse_range(experiments_range)
            else:
                experiments.append(experiments_range)
    else:
        # The original code fell to ENA search if runs were not found. I don't know if this is
        # necessary, so make a warning to detect it in case it is.
        logger.warning(
            'No experiments found for study. Modify code to search through ENA'
        )
        return
    return experiments


def srs_to_srx(accession):
    """Given an SRS accession
    returns all associated SRX ids.
    :param accession: SRS id
    :type id: str
    :return: a list of SRX ids
    :rtype: list
    """
    soup = get_xml(accession)
    return soup.find('ID', text=EXPERIMENT_PARSER).text


def srx_to_srrs(accession):
    """Given an SRX accession
    returns all associated SRR ids.
    :param accession: SRX id
    :type id: str
    :return: a list of SRR ids
    :rtype: list
    """
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


def get_files_metadata_from_run(soup):
    """Given a BeautifulSoup object with
    SRR run metadata, returns list of
    dictionaries with metadata of associated files
    :param soup: a BeautifulSoup object with SRR metadata
    :type id: bs4.BeautifulSoup
    :return: a list files metadata dictionaries
    :rtype: list
    """
    accession = soup.find('PRIMARY_ID', text=RUN_PARSER).text
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
                    "accession": accession,
                    "filename": url.split("/")[-1],
                    'filetype': parse_url(url)[0],
                    'filesize': int(size),
                    'filenumber': parse_url(url)[1],
                    'md5': md5,
                    "urltype": "ftp",
                    'url': f'ftp://{url}',
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
            # print(urls)
            files.extend(
                [{
                    "accession": accession,
                    "filename": url.split("/")[-1],
                    'filetype': parse_url(url)[0],
                    'filesize': int(size),
                    'filenumber': parse_url(url)[1],
                    'md5': md5,
                    "urltype": "ftp",
                    'url': f'ftp://{url}',
                } for url, md5, size in
                 zip(urls.split(';'), md5s.split(';'), sizes.split(';'))]
            )
            break
    return files


def parse_url(url):
    """ Given a raw data link, returns
    the file type and file number of the
    associated file

    :param url: raw data download link
    :type url: str

    :return: file type (bam, fastq or SRA) and
    file number (either 1 or 2 for reads 1 and 2 of
    fastqs, or 1 for bam, unique fastqs, and SRA files)
    :rtype: str, str
    """
    url = url.lower()
    fileno = None
    if "bam" in url:
        filetype = "bam"
    elif "fastq" in url:
        filetype = 'fastq'
    else:
        filetype = 'sra'

    if filetype == 'bam':
        fileno = 1
    elif filetype == 'fastq':
        if '_r1' in url or '_1' in url:
            fileno = 1
        elif '_r2' in url or '_2' in url:
            fileno = 2
        elif '_i1' in url:
            fileno = 3
        else:
            fileno = 1
    if filetype == 'sra':
        fileno = 1
    return (filetype, fileno)


def parse_ncbi_fetch_fasta(soup, server):
    """ Given the output of `ncbi_fetch_fasta` and
    the server of interest, returns fastq or bam urls
    hosted in the specified server

    :param soup: BeautifulSoup object (output of `ncbi_fetch_fasta`
    with fastq information
    :type: bs4.BeautifulSoup object

    :param server: host server of urls to be returned (AWS, GCP or NCBI)
    :type: str

    :rparam: list of urls
    :rtype: list
    """
    links = []
    for alternative in soup.find_all('Alternatives'):
        if alternative.get('org') == server:
            links.append(alternative.get('url'))
    if 'bam' in links[0] or len(links) > 2:
        links.pop()
    return links


def ena_fetch(accession, db):
    """ Fetch information from the specified
    ENA database for the specified accession

    :param accession: database id
    :type: str

    :param db: ENA database
    :type: str

    :return: BeautifulSoup object with accession information
    :rtype: bs4.BeautifulSoup
    """
    return BeautifulSoup(
        cached_get(f'{ENA_FETCH}?db={db}&id={accession}', 'xml'), 'lxml'
    )


def parse_bioproject(soup):
    """ Parse the output of `ena_fetch` for the bioproject
    database by extracting relevant metadata

    :param soup: BeautifulSoup object (output of `ena_fetch` with db = bioproject)
    :type: bs4.BeautifulSoup object

    :rparam: dictionary with metadata
    :rtype: dict
    """
    # Exception for: the followin bioproject ID is not public
    if 'is not public in BioProject' in soup.text:
        logger.error('The provided ID is not public in BioProject. Exiting')
        sys.exit(0)
    target = soup.find('target')
    if target:
        target_material = target.get('material')
    else:
        target_material = ''
    return {
        'accession': soup.find('archiveid').get('accession'),
        'title': soup.find('title').text,
        'description': soup.find("description").text,
        'dbxref': soup.find('id').text,
        'organism': soup.find('organismname').text,
        'target_material': target_material
    }


def findkey(obj, key, objs=[]):
    if key in obj:
        return obj[key]
    for _, v in obj.items():
        if isinstance(v, dict):
            item = findkey(v, key, objs)
            if item is not None:
                objs += item
    return None
