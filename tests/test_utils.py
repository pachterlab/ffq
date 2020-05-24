from unittest import mock, TestCase

from bs4 import BeautifulSoup

import ffq.utils as utils
from ffq.config import (
    CROSSREF_URL, ENA_URL, ENA_SEARCH_URL, GSE_SEARCH_URL, GSE_SEARCH_TERMS, GSE_SUMMARY_URL,
    GSE_SUMMARY_TERMS
)


class TestUtils(TestCase):

    def test_cached_get(self):
        with mock.patch('ffq.utils.requests') as requests:
            self.assertEqual(requests.get().text, utils.cached_get())

    def test_get_xml(self):
        with mock.patch('ffq.utils.cached_get') as cached_get:
            cached_get.return_value = """
            <TAGS>
                <VALUE1>value1</VALUE1>
                <VALUE2>value2</VALUE2>
            </TAGS>
            """
            result = utils.get_xml('accession')
            cached_get.assert_called_once_with(f'{ENA_URL}/accession/')
            self.assertTrue(isinstance(result, BeautifulSoup))

    def test_get_gse_search_json(self):
        with mock.patch('ffq.utils.cached_get') as cached_get:
            cached_get.return_value = """
            {
                {key1:value1},
                {key2:value2}
            }
            """
            result = utils.get_gse_search_json('accession')
            cached_get.assert_called_once_with(
                f'{GSE_SEARCH_URL}accession{GSE_SEARCH_TERMS}'
            )
            self.assertTrue(isinstance(result, BeautifulSoup))

    def test_get_gse_summary_json(self):
        with mock.patch('ffq.utils.cached_get') as cached_get:
            cached_get.return_value = """
            {
                {key1:value1},
                {key2:value2}
            }
            """
            result = utils.get_gse_summary_json('accession')
            cached_get.assert_called_once_with(
                f'{GSE_SUMMARY_URL}accession{GSE_SUMMARY_TERMS}'
            )
            self.assertTrue(isinstance(result, BeautifulSoup))

    def test_parse_tsv(self):
        s = 'header1\theader2\theader3\nvalue1\tvalue2\tvalue3'
        self.assertEqual([{
            'header1': 'value1',
            'header2': 'value2',
            'header3': 'value3'
        }], utils.parse_tsv(s))

    def test_get_doi(self):
        with mock.patch('ffq.utils.cached_get') as cached_get:
            cached_get.return_value = """{
                "message": {"key": "value"}
            }"""
            result = utils.get_doi('doi')
            cached_get.assert_called_once_with(f'{CROSSREF_URL}/doi')
            self.assertEqual({'key': 'value'}, result)

    def test_search_ena_title(self):
        with mock.patch('ffq.utils.requests.get') as get:
            get.return_value.text = 'study_accession\tsecondary_study_accession\nPRJNA579178\tSRP226764\n'
            self.assertEqual(['SRP226764'], utils.search_ena_title('title'))
            get.assert_called_once_with(
                ENA_SEARCH_URL,
                params={
                    'result': 'study',
                    'limit': 0,
                    'query': f'study_title="title"',
                    'fields': 'secondary_study_accession',
                }
            )
            
    def test_SRR_range(self):
        text = 'SRR10-SRR13'
        self.assertEqual(['SRR10', 'SRR11', 'SRR12', 'SRR13'],
                         utils.parse_SRR_range(text))
