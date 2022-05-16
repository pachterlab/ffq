from unittest import mock, TestCase
from unittest.mock import call

from bs4 import BeautifulSoup
import json

import ffq.utils as utils
from ffq.config import (
    CROSSREF_URL, ENA_SEARCH_URL, ENA_URL, GSE_SEARCH_URL, GSE_SUMMARY_URL,
    GSE_SEARCH_TERMS, GSE_SUMMARY_TERMS, NCBI_FETCH_URL, NCBI_LINK_URL,
    NCBI_SEARCH_URL, NCBI_SUMMARY_URL
)
from tests.mixins import TestMixin


class TestUtils(TestMixin, TestCase):

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
            ncbi_search.assert_called_once_with("gds", "accession")
            self.assertEqual({
                'accession': 'accession',
                'geo_id': 'gsm_id'
            }, result)
            # self.assertTrue(isinstance(result, BeautifulSoup))

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

    def test_get_samples_from_study(self):
        self.assertEqual([
            'SRS4698189', 'SRS4698190', 'SRS4698191', 'SRS4698192',
            'SRS4698193', 'SRS4698194', 'SRS4698195', 'SRS4698196', 'SRS4698197'
        ], utils.get_samples_from_study("SRP194123"))

    def test_parse_encode_biosample(self):
        with open(self.biosample_path, 'r') as f:
            biosample = json.loads(f.read())
        self.assertEqual({
            "accession": "ENCBS941ZTJ",
            "dbxrefs": ["GEO:SAMN19597695"],
            "description": "",
            "genetic_modifications": [],
            "treatments": [],
            "sex": "unknown",
            "life_stage": "unknown",
            "age": "unknown",
            "age_units": "",
            "organism": {
                "schema_version": "6",
                "scientific_name": "Mus musculus",
                "name": "mouse",
                "status": "released",
                "taxon_id": "10090",
                "@id": "/organisms/mouse/",
                "@type": ["Organism", "Item"],
                "uuid": "3413218c-3d86-498b-a0a2-9a406638e786"
            },
            "biosample_ontology": {
                "classification": "",
                "term_name": "",
                "organ_slims": "",
                "cell_slims": "",
                "system_slims": "",
                "developmental_slims": "",
                "treatments": [],
                "genetic_modifications": []
            }
        }, utils.parse_encode_biosample(biosample))

    def test_parse_encode_donor(self):
        with open(self.donor_path, 'r') as f:
            donor = json.loads(f.read())
        self.assertEqual({
            "accession": "ENCDO072AAA",
            "dbxrefs": ["GEO:SAMN04284198"],
            "organism": {
                "schema_version": "6",
                "scientific_name": "Mus musculus",
                "name": "mouse",
                "status": "released",
                "taxon_id": "10090",
                "@id": "/organisms/mouse/",
                "@type": ["Organism", "Item"],
                "uuid": "3413218c-3d86-498b-a0a2-9a406638e786"
            },
            "sex": "",
            "life_stage": "",
            "age": "",
            "age_units": "",
            "health_status": "",
            "ethnicity": ""
        }, utils.parse_encode_donor(donor))

    def test_parse_encode_json(self):
        with open(self.encode_experiment_path, 'r') as f:
            experiment = json.loads(f.read())
        with open(self.encode_experiment_output_path, 'r') as f:
            output = json.loads(f.read())
        self.assertEqual(
            output, utils.parse_encode_json('ENCSR998WNE', experiment)
        )

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

    def test_parse_range_srr(self):
        text = 'SRR10-SRR13'
        self.assertEqual(['SRR10', 'SRR11', 'SRR12', 'SRR13'],
                         utils.parse_range(text))

    def test_parse_range_arbitrary(self):
        text = 'XXXX10-XXXX13'
        self.assertEqual(['XXXX10', 'XXXX11', 'XXXX12', 'XXXX13'],
                         utils.parse_range(text))

    def test_parse_range_leading_zero(self):
        text = 'SRR01-SRR05'
        self.assertEqual(['SRR01', 'SRR02', 'SRR03', 'SRR04', 'SRR05'],
                         utils.parse_range(text))

    def test_geo_to_suppl(self):
        self.assertEqual([{
            "accession":
                "GSM12345",
            'filename':
                'GSM12345.CEL.gz',
            "filetype":
                None,
            'filesize':
                2964920,
            "filenumber":
                1,
            "md5":
                None,
            "urltype":
                "ftp",
            'url':
                'ftp://ftp.ncbi.nlm.nih.gov/geo/samples/GSM12nnn/GSM12345/suppl/GSM12345.CEL.gz'
        }], utils.geo_to_suppl("GSM12345", "GSM"))
        self.assertEqual([{
            "accession":
                "GSE102592",
            'filename':
                'filelist.txt',
            "filetype":
                None,
            'filesize':
                697,
            "filenumber":
                1,
            "md5":
                None,
            "urltype":
                "ftp",
            'url':
                'ftp://ftp.ncbi.nlm.nih.gov/geo/series/GSE102nnn/GSE102592/suppl/filelist.txt'
        }, {
            "accession":
                "GSE102592",
            'filename':
                'GSE102592_RAW.tar',
            "filetype":
                None,
            'filesize':
                176916480,
            "filenumber":
                2,
            "md5":
                None,
            "urltype":
                "ftp",
            'url':
                'ftp://ftp.ncbi.nlm.nih.gov/geo/series/GSE102nnn/GSE102592/suppl/GSE102592_RAW.tar'
        }], utils.geo_to_suppl("GSE102592", "GSE"))

    def test_gsm_to_platform(self):
        accession = 'GSM2928379'
        self.assertEqual({
            'platform': {
                'accession': 'GPL21290',
                'title': 'Illumina HiSeq 3000 (Homo sapiens)'
            }
        }, utils.gsm_to_platform(accession))

    def test_gse_to_gsms(self):
        with mock.patch('ffq.utils.get_gse_search_json') as get_gse_search_json, \
            mock.patch('ffq.utils.ncbi_summary') as ncbi_summary:
            get_gse_search_json.return_value = BeautifulSoup(
                """{"header":{"type":"esearch","version":"0.3"},"esearchresult":{
                    "count":"16","retmax":"1","retstart":"0","idlist":["200128889"],
                    "translationset":[],"translationstack":[{"term":"GSE128889[GEO Accession]",
                    "field":"GEO Accession","count":"16","explode":"N"},"GROUP"],
                    "querytranslation":"GSE128889[GEO Accession]"}}\n""",
                'html.parser'
            )

            ncbi_summary.return_value = {
                '200128889': {
                    'accession':
                        'GSE128889',
                    'bioproject':
                        'PRJNA532348',
                    'entrytype':
                        'GSE',
                    'samples': [{
                        'accession': 'GSM3717979'
                    }, {
                        'accession': 'GSM3717982',
                        'title': 'BulkRNA-seq_murine_p12_CD142_Rep3'
                    }, {
                        'accession': 'GSM3717978'
                    }, {
                        'accession': 'GSM3717981',
                        'title': 'BulkRNA-seq_murine_p12_CD142_Rep2'
                    }]
                }
            }
            self.assertEqual([
                'GSM3717978', 'GSM3717979', 'GSM3717981', 'GSM3717982'
            ], utils.gse_to_gsms("accession"))

    def test_gsm_to_srx(self):
        with mock.patch('ffq.utils.get_gsm_search_json') as get_gsm_search_json, \
            mock.patch('ffq.utils.ncbi_summary') as ncbi_summary:
            get_gsm_search_json.return_value = {
                'accession': "GSM3717978",
                'geo_id': "303717978"
            }
            ncbi_summary.return_value = {
                '303717978': {
                    'accession':
                        'GSM3717978',
                    'bioproject':
                        '',
                    'entrytype':
                        'GSM',
                    'extrelations': [{
                        'relationtype':
                            'SRA',
                        'targetftplink':
                            'ftp://ftp-trace.ncbi.nlm.nih.gov/sra/sra-instant/reads/ByExp/sra/SRX/SRX569/SRX5692097/',
                        'targetobject':
                            'SRX5692097'
                    }]
                }
            }
            self.assertEqual("SRX5692097", utils.gsm_to_srx("accession"))

    def test_srs_to_srx(self):
        self.assertEqual("SRX5692096", utils.srs_to_srx("SRS4631628"))

    def test_srx_to_srrs(self):
        self.assertEqual([
            'SRR8984431', 'SRR8984432', 'SRR8984433', 'SRR8984434'
        ], utils.srx_to_srrs("SRX5763720"))

    def test_get_files_metadata_from_run(self):
        # TODO adjust links accordingly
        with open(self.run_path, 'r') as f:
            soup = BeautifulSoup(f.read(), 'xml')
        self.assertEqual([{
            "accession":
                "SRR8426358",
            "filename":
                "SRR8426358_1.fastq.gz",
            'filetype':
                "fastq",
            'filesize':
                5507959060,
            'filenumber':
                1,
            'md5':
                'be7e88cf6f6fd90f1b1170f1cb367123',
            "urltype":
                "ftp",
            'url':
                'ftp://ftp.sra.ebi.ac.uk/vol1/fastq/SRR842/008/SRR8426358/SRR8426358_1.fastq.gz'
        }, {
            "accession":
                "SRR8426358",
            "filename":
                "SRR8426358_2.fastq.gz",
            'filetype':
                "fastq",
            'filesize':
                7194107512,
            'filenumber':
                2,
            'md5':
                '2124da22644d876c4caa92ffd9e2402e',
            "urltype":
                "ftp",
            'url':
                'ftp://ftp.sra.ebi.ac.uk/vol1/fastq/SRR842/008/SRR8426358/SRR8426358_2.fastq.gz'
        }], utils.get_files_metadata_from_run(soup))

    def test_get_files_metadata_from_run_bam(self):
        with open(self.run2_path, 'r') as f:
            soup = BeautifulSoup(f.read(), 'xml')
        self.assertEqual([{
            "accession":
                "SRR6835844",
            "filename":
                "10X_P4_0.bam",
            'filetype':
                "bam",
            'filesize':
                17093057664,
            'filenumber':
                1,
            'md5':
                '5355fe6a07155026085ce46631268ab1',
            "urltype":
                "ftp",
            'url':
                'ftp://ftp.sra.ebi.ac.uk/vol1/SRA653/SRA653146/bam/10X_P4_0.bam'
        }], utils.get_files_metadata_from_run(soup))

    def test_parse_url(self):
        self.assertEqual(
            ('fastq', 1),
            utils.parse_url(
                'ftp://ftp.sra.ebi.ac.uk/vol1/fastq/SRR842/008/SRR8426358/SRR8426358_1.fastq.gz'
            )
        )

    
    def test_parse_ncbi_fetch_fasta(self):
        with open(self.alt_links, 'r') as f:
            soup = BeautifulSoup(f.read(), 'xml')        
        self.assertEqual(
            ['https://sra-pub-src-1.s3.amazonaws.com/SRR6835844/10X_P4_0.bam.1', 
             'https://sra-pub-run-odp.s3.amazonaws.com/sra/SRR6835844/SRR6835844'], utils.parse_ncbi_fetch_fasta(soup, 'AWS')
        )


    def test_parse_bioproject(self):
        with open(self.bioproject_path, 'r') as f:
            soup = BeautifulSoup(f.read(), 'xml')
        self.assertEqual(
            {
                'accession': 'PRJNA118013',
                'title': 'affy_cinetique_lyon_rose: Flower/Petal initiation and development in roses',
                'description': 'affy_cinetique_lyon_rose. The objective is to identify genes involved in ' 
                'petal development and senescence. R. chinensis cv Old Blush (OB) was used for the following '
                'reasons: it is a diploid Chinese rose that participated in the generation of modern roses '
                '(recurrent flowering, scent, etc.). The objective here is to identify genes whose expression '
                'is associated with different flower development stages, from floral meristem to senescing '
                'flower. These genes are putative candidates involved in floral initiation, development and '
                'senescence. All samples were collected at the same time early in the afternoon. Meristems and '
                'early flower development stages were dissected under a microscope. Total RNA was extracted from '
                'harvested tissues using the Plant RNA kit (Macherey Nagel), and then used to hybridize '
                'Rosa-Affymetrix microarrays. Keywords: time course Overall design: 12 arrays - rose 6 developmental '
                'stages, 2 replicates each.',
                'dbxref': 'GSE18342',
                'organism': 'Rosa chinensis',
                'target_material': 'eTranscriptome'
            }, utils.parse_bioproject(soup))

    def test_findkey(self):
        with open(self.srr_keyed) as f:
            keyed = json.load(f)
        found = []
        self.assertEqual(
            [
                {
                    'accession': 'SRR5398235',
                    'filename': 'A.merged.bam',
                    'filetype': 'bam',
                    'filesize': 21692817709,
                    'filenumber': 1,
                    'md5': '3d3d2020752b9af657cf22b725a94207',
                    'urltype': 'ftp',
                    'url': 'ftp://ftp.sra.ebi.ac.uk/vol1/SRA550/SRA550660/bam/A.merged.bam'
                }
            ], utils.findkey(keyed, 'ftp', found))
