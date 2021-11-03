import json
import re
import time
from functools import lru_cache

import requests
from bs4 import BeautifulSoup
from frozendict import frozendict

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
)

GSE_PARSER = re.compile(r'Series\t\tAccession: (?P<accession>GSE[0-9]+)\t')
SRP_PARSER = re.compile(r'Study acc="(?P<accession>SRP[0-9]+)"')
SRR_PARSER = re.compile(r'Run acc="(?P<accession>SRR[0-9]+)"')


@lru_cache()
def cached_get(*args, **kwargs):
    """Cached version of requests.get.

    :return: text of response
    :rtype: str
    """
    response = requests.get(*args, **kwargs)
    response.raise_for_status()
    return response.text


def get_xml(accession):
    """Given an accession, retrieve the XML from ENA.

    :param accession: an accession
    :type accession: str

    :return: a BeautifulSoup object of the parsed XML
    :rtype: bs4.BeautifulSoup
    """
    return BeautifulSoup(cached_get(f'{ENA_URL}/{accession}/'), 'xml')


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
    geo_id = ncbi_search("gds", accession)[-1]
      
    return {'accession': accession, 'geo_id': geo_id}


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


def gsm_id_to_srx(id):
    """Convert a GEO ID to an SRX.
    :param id: GEO ID
    :type id: str
    :return: SRX accession
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
    return srxs


def geo_ids_to_gses(ids):
    """Convert GEO IDs (which is a number) to a GSEs (which starts with GSE).

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


def parse_run_range(text):
    """Given an a string of run ranges, returns a list of intermediary run numbers.

    :param text: an SRR range (example: 'SRR4340020-SRR4340045') or ERR range (example: 'ERR4340020-ERR4340045')
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
