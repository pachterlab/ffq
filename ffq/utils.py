import json
import re
from functools import lru_cache

import requests
from bs4 import BeautifulSoup

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
)

GSE_PARSER = re.compile(r'Series\t\tAccession: (?P<accession>GSE[0-9]+)\t')


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


def search_ena_title(title):
    """Given a title, search the ENA for studies (SRPs) corresponding to the title.

    :param title: study title
    :type title: str

    :return: list of SRPs
    :rtype: list
    """
    # TODO: use cached get. Can't be used currently because dictionaries can
    # not be hashed.
    response = requests.get(
        ENA_SEARCH_URL,
        params={
            'result': 'study',
            'limit': 0,
            'query': f'study_title="{title}"',
            'fields': 'secondary_study_accession',
        }
    )
    response.raise_for_status()
    if not response.text:
        return []
    table = parse_tsv(response.text)
    return [t['secondary_study_accession'] for t in table]


def ncbi_search(db, term):
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
            'retmax': 10  # arbitrary
        }
    )
    response.raise_for_status()
    return response.json()['esearchresult']['idlist']


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
    for linkset in response.json()['linksets']:
        for linksetdb in linkset['linksetdbs']:
            ids.extend(linksetdb['links'])
    return ids


def geo_ids_to_gses(ids):
    """Convert a GEO ID (which is a number) to a GSE (which starts with GSE).

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
    return GSE_PARSER.findall(response.text)


def parse_SRR_range(text):
    """Given an a string of SRR ranges, returns a list of intermediary SRR numbers.

    :param text: an SRR range (example: 'SRR4340020-SRR4340045')
    :type text: str

    :return: a list of SRR numbers
    :rtype: list
    """
    first, last = text.split('-')
    ids = [
        f'SRR{str(i).zfill(len(first) - 3)}'
        for i in range(int(first[3:]),
                       int(last[3:]) + 1)
    ]
    return ids
