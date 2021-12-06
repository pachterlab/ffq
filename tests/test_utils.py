from unittest import mock, TestCase
from unittest.mock import call

from bs4 import BeautifulSoup

import ffq.utils as utils
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
    FTP_GEO_SUPPL
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

    def test_get_gsm_search_json(self):
        with mock.patch('ffq.utils.ncbi_search') as ncbi_search:
            ncbi_search.return_value = ['geo_id', 'gsm_id']
            result = utils.get_gsm_search_json('accession')
            ncbi_search.assert_called_once_with(
                "gds", "accession")
            self.assertEqual({'accession': 'accession',\
                            'geo_id': 'gsm_id'}, result)
            #self.assertTrue(isinstance(result, BeautifulSoup))

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

    def test_search_ena_study_runs(self):
        with mock.patch('ffq.utils.cached_get') as cached_get:
            cached_get.return_value = 'run_accession\nSRR13436369\nSRR13436370\nSRR13436371\n'
            self.assertEqual(['SRR13436369', 'SRR13436370', 'SRR13436371'],
                             utils.search_ena_study_runs('study'))
            cached_get.assert_called_once_with(
                ENA_SEARCH_URL,
                params={
                    'query': 'secondary_study_accession="study"',
                    'result': 'read_run',
                    'fields': 'run_accession',
                    'limit': 0,
                }
            )

    def test_search_ena_run_study(self):
        with mock.patch('ffq.utils.cached_get') as cached_get:
            cached_get.return_value = 'run_accession\tsecondary_study_accession\nSRR13436369\tSRP301759\n'
            self.assertEqual('SRP301759', utils.search_ena_run_study('run'))
            cached_get.assert_called_once_with(
                ENA_SEARCH_URL,
                params={
                    'query': 'run_accession="run"',
                    'result': 'read_run',
                    'fields': 'secondary_study_accession',
                    'limit': 0,
                }
            )

    def test_search_ena_run_sample(self):
        with mock.patch('ffq.utils.cached_get') as cached_get:
            cached_get.return_value = (
                'run_accession\tsample_accession\tsecondary_sample_accession\n'
                'SRR13436369\tSAMN17315475\tSRS8031399\n'
            )
            self.assertEqual('SRS8031399', utils.search_ena_run_sample('run'))
            cached_get.assert_called_once_with(
                ENA_SEARCH_URL,
                params={
                    'query': 'run_accession="run"',
                    'result': 'read_run',
                    'fields': 'secondary_sample_accession',
                    'limit': 0,
                }
            )

    def test_search_ena_title(self):
        with mock.patch('ffq.utils.cached_get') as cached_get:
            cached_get.return_value = 'study_accession\tsecondary_study_accession\nPRJNA579178\tSRP226764\n'
            self.assertEqual(['SRP226764'], utils.search_ena_title('title'))
            cached_get.assert_called_once_with(
                ENA_SEARCH_URL,
                params={
                    'result': 'study',
                    'limit': 0,
                    'query': 'study_title="title"',
                    'fields': 'secondary_study_accession',
                }
            )

    def test_ncbi_summary(self):
        with mock.patch('ffq.utils.requests.get') as get:
            get.return_value.json.return_value = {
                'result': {
                    'uids': ['id1', 'id2'],
                    'id1': 'summary1',
                    'id2': 'summary2'
                }
            }
            self.assertEqual({
                'id1': 'summary1',
                'id2': 'summary2',
            }, utils.ncbi_summary('db', 'id'))
            get.assert_called_once_with(
                NCBI_SUMMARY_URL,
                params={
                    'db': 'db',
                    'id': 'id',
                    'retmode': 'json',
                    'retmax': 10000,
                }
            )

    def test_ncbi_search(self):
        with mock.patch('ffq.utils.requests.get') as get:
            get.return_value.json.return_value = {
                'esearchresult': {
                    'idlist': ['id1', 'id2']
                }
            }
            self.assertEqual(['id1', 'id2'], utils.ncbi_search('db', 'term'))
            get.assert_called_once_with(
                NCBI_SEARCH_URL,
                params={
                    'db': 'db',
                    'term': 'term',
                    'retmode': 'json',
                    'retmax': 100000
                }
            )

    def test_ncbi_link(self):
        with mock.patch('ffq.utils.requests.get') as get:
            get.return_value.json.return_value = {
                'linksets': [{
                    'linksetdbs': [{
                        'links': ['id1', 'id2']
                    }]
                }]
            }
            self.assertEqual(['id1', 'id2'],
                             utils.ncbi_link('origin', 'destination', 'id'))
            get.assert_called_once_with(
                NCBI_LINK_URL,
                params={
                    'dbfrom': 'origin',
                    'db': 'destination',
                    'id': 'id',
                    'retmode': 'json',
                }
            )

    def test_geo_id_to_srps(self):
        with mock.patch('ffq.utils.ncbi_summary') as ncbi_summary:
            ncbi_summary.return_value = {
                'id': {
                    'extrelations': [{
                        'relationtype': 'SRA',
                        'targetobject': 'SRP1'
                    }]
                }
            }
            self.assertEqual(['SRP1'], utils.geo_id_to_srps('id'))
            ncbi_summary.assert_called_once_with('gds', 'id')

    def test_gsm_id_to_srx(self):
        with mock.patch('ffq.utils.ncbi_summary') as ncbi_summary:
            ncbi_summary.return_value = {
                'id': {
                    'extrelations': [{
                        'relationtype': 'SRA',
                        'targetobject': 'SRX1'
                    }]
                }
            }
            self.assertEqual(['SRX1'], utils.geo_id_to_srps('id'))
            ncbi_summary.assert_called_once_with('gds', 'id')

    def test_geo_id_to_srps_bioproject(self):
        with mock.patch('ffq.utils.ncbi_summary') as ncbi_summary,\
            mock.patch('ffq.utils.ncbi_search') as ncbi_search,\
            mock.patch('ffq.utils.ncbi_link') as ncbi_link:
            ncbi_summary.side_effect = [{
                'id': {
                    'bioproject': 'PRJNA1'
                }
            }, {
                'SRA1': 'Study acc="SRP1"',
                'SRA2': 'Study acc="SRP1"'
            }]
            ncbi_search.return_value = ['BIOPROJECT1']
            ncbi_link.return_value = ['SRA1', 'SRA2']
            self.assertEqual(['SRP1'], utils.geo_id_to_srps('id'))
            self.assertEqual(2, ncbi_summary.call_count)
            ncbi_summary.assert_has_calls([
                call('gds', 'id'), call('sra', 'SRA1,SRA2')
            ])
            ncbi_search.assert_called_once_with('bioproject', 'PRJNA1[PRJA]')
            ncbi_link.assert_called_once_with(
                'bioproject', 'sra', 'BIOPROJECT1'
            )

    def test_geo_ids_to_gses(self):
        with mock.patch('ffq.utils.requests.get') as get:
            get.return_value.text = 'Series\t\tAccession: GSE1\tSeries\t\tAccession: GSE2\t'
            self.assertEqual(['GSE1', 'GSE2'],
                             utils.geo_ids_to_gses(['id1', 'id2']))
            get.assert_called_once_with(
                NCBI_FETCH_URL, params={
                    'db': 'gds',
                    'id': 'id1,id2',
                }
            )

    def test_sra_ids_to_srrs(self):
        with mock.patch('ffq.utils.requests.get') as get:
            get.return_value.text = 'Run acc="SRR1" Run acc="SRR2"'
            self.assertEqual(['SRR1', 'SRR2'],
                             utils.sra_ids_to_srrs(['id1', 'id2']))
            get.assert_called_once_with(
                NCBI_SUMMARY_URL, params={
                    'db': 'sra',
                    'id': 'id1,id2',
                }
            )

    def test_parse_run_range(self):
        text = 'SRR10-SRR13'
        self.assertEqual(['SRR10', 'SRR11', 'SRR12', 'SRR13'],
                         utils.parse_run_range(text))

    def test_parse_run_range_leading_zero(self):
        text = 'SRR01-SRR05'
        self.assertEqual(['SRR01', 'SRR02', 'SRR03', 'SRR04', 'SRR05'],
                         utils.parse_run_range(text))

    def test_geo_to_suppl(self):
        self.assertEqual([[{'filename': 'GSM12345.CEL.gz',
                            'size': '2964920',
                            'url': 'ftp.ncbi.nlm.nih.gov/geo/samples/GSM12nnn/GSM12345/suppl/GSM12345.CEL.gz'}]],
                            utils.gsm_to_suppl("GSM12345", "GSM))
                        