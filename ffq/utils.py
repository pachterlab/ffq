from functools import lru_cache

import requests
from bs4 import BeautifulSoup

from .config import (
    ENA_URL,
    GSE_SEARCH_URL,
    GSE_SUMMARY_URL,
    GSE_SEARCH_TERMS,
    GSE_SUMMARY_TERMS
)


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

def get_gse_search_json(accession):
    """Given an accession, retrieve the JSON from GEO SEARCH.

    :param accession: an accession
    :type accession: str

    :return: a BeautifulSoup object of the parsed JSON
    :rtype: bs4.BeautifulSoup
    """
    return BeautifulSoup(cached_get(f'{GSE_SEARCH_URL}{accession}{GSE_SEARCH_TERMS}'), 'html.parser')

def get_gse_summary_json(accession):
    """Given an accession, retrieve the JSON from GEO SUMMARY.

    :param accession: an accession
    :type accession: str

    :return: a BeautifulSoup object of the parsed JSON
    :rtype: bs4.BeautifulSoup
    """
    return BeautifulSoup(cached_get(f'{GSE_SUMMARY_URL}{accession}{GSE_SUMMARY_TERMS}'), 'html.parser')


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

def parse_SRR_range(text):
    """Given an a string of SRR ranges, returns a list of intermediary SRR numbers.

    :param text: an SRR range (example: 'SRR4340020-SRR4340045')
    :type text: str

    :return: a list of SRR numbers
    :rtype: list
    """
    data = [int(i[3:]) for i in text.split("-")]
    ids = [f'SRR{i}' for i in range(data[0], data[1]+1)] 
    return ids
