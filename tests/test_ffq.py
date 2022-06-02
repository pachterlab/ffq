from unittest import mock, TestCase
from unittest.mock import call
from bs4 import BeautifulSoup

import ffq.ffq as ffq
from tests.mixins import TestMixin


class TestFfq(TestMixin, TestCase):

    def test_validate_accessions(self):
        SEARCH_TYPES = (
            'SRR', 'ERR', 'DRR', 'SRP', 'ERP', 'DRP', 'SRX', 'GSE', 'GSM', 'DOI'
        )
        self.assertEqual(
            [
                {
                    'accession': 'SRR244234',
                    'prefix': 'SRR',
                    'valid': True,
                    'error': None
                },
                {
                    'accession': 'SRT44322',
                    'prefix': 'UNKNOWN',
                    'valid': False,
                    'error': None
                },
                {
                    'accession': '10.1016/J.CELL.2018.06.052',
                    'prefix': 'DOI',
                    'valid': True,
                    'error': None
                },
                {
                    'accession': 'ASA10.1016/J.CELL.2018.06.052',
                    'prefix': 'UNKNOWN',  # TODO better DOI error handling
                    'valid': False,
                    'error': None
                },
                {
                    'accession': 'GSM12345',
                    'prefix': 'GSM',
                    'valid': True,
                    'error': None
                },
                {
                    'accession': 'GSE567890',
                    'prefix': 'GSE',
                    'valid': True,
                    'error': None
                },
            ],
            ffq.validate_accessions([
                "SRR244234", "SRT44322", '10.1016/j.cell.2018.06.052',
                'ASA10.1016/j.cell.2018.06.052', "GSM12345", "GSE567890"
            ], SEARCH_TYPES)
        )

    def test_parse_run(self):
        self.maxDiff = None
        with mock.patch('ffq.ffq.get_files_metadata_from_run') as get_files_metadata_from_run, \
            mock.patch('ffq.ffq.ncbi_fetch_fasta') as ncbi_fetch_fasta, \
            mock.patch('ffq.ffq.parse_ncbi_fetch_fasta') as parse_ncbi_fetch_fasta:
            with open(self.run_path, 'r') as f:
                soup = BeautifulSoup(f.read(), 'xml')

            get_files_metadata_from_run.return_value = []
            ncbi_fetch_fasta.return_value = []
            parse_ncbi_fetch_fasta.return_value = []
            self.assertEqual({
                'accession':
                    'SRR8426358',
                'experiment':
                    'SRX5234128',
                'study':
                    'SRP178136',
                'sample':
                    'SRS4237519',
                'title':
                    'Illumina HiSeq 4000 paired end sequencing; GSM3557675: old_Dropseq_1; Mus musculus; RNA-Seq',
                'attributes': {
                    'ENA-SPOT-COUNT': 109256158,
                    'ENA-BASE-COUNT': 21984096610,
                    'ENA-FIRST-PUBLIC': '2019-01-27',
                    'ENA-LAST-UPDATE': '2019-01-27'
                },
                'files': {
                    'aws': [],
                    'ftp': [],
                    'gcp': [],
                    'ncbi': []
                }
            }, ffq.parse_run(soup))

    def test_parse_run_bam(self):
        with open(self.run2_path, 'r') as f:
            soup = BeautifulSoup(f.read(), 'xml')
        self.maxDiff = None
        self.assertEqual({
            'accession':
                'SRR6835844',
            'attributes': {
                'ENA-BASE-COUNT': 12398988240,
                'ENA-FIRST-PUBLIC': '2018-03-30',
                'ENA-LAST-UPDATE': '2018-03-30',
                'ENA-SPOT-COUNT': 137766536,
                'assembly': 'mm10',
                'dangling_references': 'treat_as_unmapped'
            },
            'experiment':
                'SRX3791763',
            'files': {
                "ftp": [{
                    "accession":
                        "SRR6835844",
                    "filename":
                        "10X_P4_0.bam",
                    "filetype":
                        "bam",
                    "filesize":
                        17093057664,
                    "filenumber":
                        1,
                    "md5":
                        "5355fe6a07155026085ce46631268ab1",
                    "urltype":
                        "ftp",
                    "url":
                        "ftp://ftp.sra.ebi.ac.uk/vol1/SRA653/SRA653146/bam/10X_P4_0.bam",
                }],
                "aws": [{
                    "accession":
                        "SRR6835844",
                    "filename":
                        "10X_P4_0.bam.1",
                    "filetype":
                        "bam",
                    "filesize":
                        None,
                    "filenumber":
                        1,
                    "md5":
                        None,
                    "urltype":
                        "aws",
                    "url":
                        "https://sra-pub-src-1.s3.amazonaws.com/SRR6835844/10X_P4_0.bam.1"
                }, {
                    'accession':
                        'SRR6835844',
                    'filename':
                        'SRR6835844',
                    'filenumber':
                        1,
                    'filesize':
                        None,
                    'filetype':
                        'sra',
                    'md5':
                        None,
                    'url':
                        'https://sra-pub-run-odp.s3.amazonaws.com/sra/SRR6835844/SRR6835844',
                    'urltype':
                        'aws'
                }],
                "gcp": [{
                    "accession": "SRR6835844",
                    "filename": "10X_P4_0.bam.1",
                    "filetype": "bam",
                    "filesize": None,
                    "filenumber": 1,
                    "md5": None,
                    "urltype": "gcp",
                    "url": "gs://sra-pub-src-1/SRR6835844/10X_P4_0.bam.1"
                }, {
                    'accession': 'SRR6835844',
                    'filename': 'SRR6835844.1',
                    'filenumber': 1,
                    'filesize': None,
                    'filetype': 'sra',
                    'md5': None,
                    'url': 'gs://sra-pub-crun-7/SRR6835844/SRR6835844.1',
                    'urltype': 'gcp'
                }],
                "ncbi": []
            },
            'sample':
                'SRS3044236',
            'study':
                'SRP131661',
            'title':
                'Illumina NovaSeq 6000 sequencing; GSM3040890: library 10X_P4_0; Mus musculus; RNA-Seq'
        }, ffq.parse_run(soup))

    def test_parse_sample(self):
        with open(self.sample_path, 'r') as f:
            soup = BeautifulSoup(f.read(), 'xml')

        self.assertEqual({
            'accession': 'SRS4237519',
            'title': 'old_Dropseq_1',
            'organism': 'Mus musculus',
            'attributes': {
                'source_name': 'Whole lung',
                'tissue': 'Whole lung',
                'age': '24 months',
                'number of cells': '799',
                'ENA-SPOT-COUNT': 109256158,
                'ENA-BASE-COUNT': 21984096610,
                'ENA-FIRST-PUBLIC': '2019-01-11',
                'ENA-LAST-UPDATE': '2019-01-11'
            },
            'experiments': 'SRX5234128'
        }, ffq.parse_sample(soup))

    def test_parse_experiment_with_run(self):
        with open(self.experiment_path, 'r') as f:
            soup = BeautifulSoup(f.read(), 'xml')
        self.maxDiff = None
        self.assertEqual(
            {
                'accession': 'SRX3517583',
                'instrument': 'HiSeq X Ten',
                'platform': 'ILLUMINA',
                'runs': {
                    'SRR6425163': {
                        'accession': 'SRR6425163',
                        'attributes': {
                            'ENA-BASE-COUNT': 74994708900,
                            'ENA-FIRST-PUBLIC': '2017-12-30',
                            'ENA-LAST-UPDATE': '2017-12-30',
                            'ENA-SPOT-COUNT': 249982363
                        },
                        'experiment': 'SRX3517583',
                        'files': {
                            'aws': [
                                {
                                    'accession': 'SRR6425163',
                                    'filename': 'J2_S1_L001_R1_001.fastq.gz',
                                    'filenumber': 1,
                                    'filesize': None,
                                    'filetype': 'fastq',
                                    'md5': None,
                                    'url': 's3://sra-pub-src-6/SRR6425163/J2_S1_L001_R1_001.fastq.gz',
                                    'urltype': 'aws'
                                },
                                {
                                    'accession': 'SRR6425163',
                                    'filename': 'J2_S1_L001_R2_001.fastq.gz',
                                    'filenumber': 2,
                                    'filesize': None,
                                    'filetype': 'fastq',
                                    'md5': None,
                                    'url': 's3://sra-pub-src-6/SRR6425163/J2_S1_L001_R2_001.fastq.gz',
                                    'urltype': 'aws'
                                },
                                {
                                    'accession': 'SRR6425163',
                                    'filename': 'SRR6425163',
                                    'filenumber': 1,
                                    'filesize': None,
                                    'filetype': 'sra',
                                    'md5': None,
                                    'url': 'https://sra-pub-run-odp.s3.amazonaws.com/sra/SRR6425163/SRR6425163',
                                    'urltype': 'aws'
                                }
                            ],
                            'ftp': [
                                {
                                    'accession': 'SRR6425163',
                                    'filename': 'SRR6425163_1.fastq.gz',
                                    'filenumber': 1,
                                    'filesize': 21858866426,
                                    'filetype': 'fastq',
                                    'md5': '2dcf9ae4cfb30ec0aaf06edf0e3ca49a',
                                    'url': 'ftp://ftp.sra.ebi.ac.uk/vol1/fastq/SRR642/003/SRR6425163/SRR6425163_1.fastq.gz',
                                    'urltype': 'ftp'
                                },
                                {
                                    'accession': 'SRR6425163',
                                    'filename': 'SRR6425163_2.fastq.gz',
                                    'filenumber': 2,
                                    'filesize': 22946392178,
                                    'filetype': 'fastq',
                                    'md5': '1d0703967a2331527a3aebf97a3f1c32',
                                    'url': 'ftp://ftp.sra.ebi.ac.uk/vol1/fastq/SRR642/003/SRR6425163/SRR6425163_2.fastq.gz',
                                    'urltype': 'ftp'
                                }
                            ],
                            'gcp': [
                                {
                                    'accession': 'SRR6425163',
                                    'filename': 'J2_S1_L001_R1_001.fastq.gz',
                                    'filenumber': 1,
                                    'filesize': None,
                                    'filetype': 'fastq',
                                    'md5': None,
                                    'url': 'gs://sra-pub-src-6/SRR6425163/J2_S1_L001_R1_001.fastq.gz',
                                    'urltype': 'gcp'
                                },
                                {
                                    'accession': 'SRR6425163',
                                    'filename': 'J2_S1_L001_R2_001.fastq.gz',
                                    'filenumber': 2,
                                    'filesize': None,
                                    'filetype': 'fastq',
                                    'md5': None,
                                    'url': 'gs://sra-pub-src-6/SRR6425163/J2_S1_L001_R2_001.fastq.gz',
                                    'urltype': 'gcp'
                                },
                                {
                                    'accession': 'SRR6425163',
                                    'filename': 'SRR6425163.1',
                                    'filenumber': 1,
                                    'filesize': None,
                                    'filetype': 'sra',
                                    'md5': None,
                                    'url': 'gs://sra-pub-crun-7/SRR6425163/SRR6425163.1',
                                    'urltype': 'gcp'
                                }
                            ],
                            'ncbi': [
                                {
                                    'accession': 'SRR6425163',
                                    'filename': 'SRR6425163.1',
                                    'filenumber': 1,
                                    'filesize': None,
                                    'filetype': 'sra',
                                    'md5': None,
                                    'url': 'https://sra-downloadb.be-md.ncbi.nlm.nih.gov/sos2/sra-pub-run-13/SRR6425163/SRR6425163.1',
                                    'urltype': 'ncbi'
                                }
                            ]
                        },
                        'sample': 'SRS2792433',
                        'study': 'SRP127624',
                        'title': 'HiSeq X Ten paired end sequencing; GSM2905292: BMPa-1; Homo sapiens; RNA-Seq'
                    }
                },
                'title': 'HiSeq X Ten paired end sequencing; GSM2905292: BMPa-1; Homo sapiens; RNA-Seq'
            },
            ffq.parse_experiment_with_run(soup, 10)
        )

    def test_parse_study(self):
        with open(self.study_path, 'r') as f:
            soup = BeautifulSoup(f.read(), 'xml')

        self.assertEqual({
            'accession':
                'SRP178136',
            'title':
                'Multi-modal analysis of the aging mouse lung at cellular resolution',
            'abstract':
                'A) Whole lung tissue from 24 months (n=7) '
                'and 3 months old (n=8) mice was dissociated and single-cell '
                'mRNAseq libraries generated with Drop-Seq. B) Bulk RNA-seq '
                'data was generated from whole mouse lung tissue of old (n=3) '
                'and young (n=3) samples. C) Bulk RNA-seq data was generated '
                'from flow-sorted macrophages from old (n=7) and young (n=5) '
                'mice and flow-sorted epithelial cells from old (n=4) and '
                'young (n=4) mice. Overall design: Integration of bulk RNA-seq '
                'from whole mouse lung tissue and bulk RNA-seq from flow-sorted '
                'lung macrophages and epithelial cells was used to validate results '
                'obtained from single cell RNA-seq of whole lung tissue.',
            'accession':
                'SRP178136'
        }, ffq.parse_study(soup))

    def test_gse_search_json(self):
        with open(self.gse_search_path, 'r') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            self.assertEqual({
                'accession': 'GSE93374',
                'geo_id': '200093374'
            }, ffq.parse_gse_search(soup))

    def test_gse_summary_json(self):
        with open(self.gse_summary_path, 'r') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            self.assertEqual({'accession': 'SRP096361'},
                             ffq.parse_gse_summary(soup))

    def test_ffq_gse(self):
        # Need to figure out how to add for loop test for adding individual runs
        with mock.patch('ffq.ffq.get_gse_search_json') as get_gse_search_json, \
            mock.patch('ffq.ffq.parse_gse_search') as parse_gse_search, \
            mock.patch('ffq.ffq.gse_to_gsms') as gse_to_gsms, \
            mock.patch('ffq.ffq.ffq_gsm') as ffq_gsm, \
            mock.patch('ffq.ffq.geo_to_suppl') as geo_to_suppl:

            parse_gse_search.return_value = {
                'accession': 'GSE1',
                'geo_id': 'GEOID1'
            }

            gse_to_gsms.return_value = ['GSM_1', 'GSM_2']
            geo_to_suppl.return_value = {
                'filename': 'file',
                'size': 'size',
                'url': 'url'
            }
            ffq_gsm.side_effect = [{
                'accession': 'GSM1'
            }, {
                'accession': 'GSM2'
            }, 'test', 'test']

            self.assertEqual({
                'accession': 'GSE1',
                'supplementary_files': {
                    'filename': 'file',
                    'size': 'size',
                    'url': 'url'
                },
                'geo_samples': {
                    'GSM1': {
                        'accession': 'GSM1'
                    },
                    'GSM2': {
                        'accession': 'GSM2'
                    }
                }
            }, ffq.ffq_gse('GSE1'))

            get_gse_search_json.assert_called_once_with('GSE1')
            gse_to_gsms.assert_called_once_with('GSE1')
            ffq_gsm.assert_has_calls([call('GSM_1', None), call('GSM_2', None)])

    def test_ffq_gsm(self):
        # Need to figure out how to add for loop test for adding individual runs
        with mock.patch('ffq.ffq.get_gsm_search_json') as get_gsm_search_json, \
            mock.patch('ffq.ffq.geo_to_suppl') as geo_to_suppl, \
            mock.patch('ffq.ffq.gsm_to_platform') as gsm_to_platform, \
            mock.patch('ffq.ffq.gsm_id_to_srs') as gsm_id_to_srs, \
            mock.patch('ffq.ffq.ffq_sample') as ffq_sample:

            get_gsm_search_json.return_value = {
                'accession': 'GSM1',
                'geo_id': 'GSMID1'
            }
            geo_to_suppl.return_value = {'supplementary_files': 'supp'}
            gsm_to_platform.return_value = {'platform': 'platform'}
            gsm_id_to_srs.return_value = 'SRS1'
            ffq_sample.return_value = {'accession': 'SRS1'}

            self.assertEqual({
                'accession': 'GSM1',
                'supplementary_files': {
                    'supplementary_files': 'supp'
                },
                'platform': 'platform',
                'samples': {
                    'SRS1': {
                        'accession': 'SRS1'
                    }
                }
            }, ffq.ffq_gsm('GSM1'))
            get_gsm_search_json.assert_called_once_with('GSM1')
            geo_to_suppl.assert_called_once_with('GSM1', 'GSM')
            gsm_to_platform.assert_called_once_with('GSM1')
            gsm_id_to_srs.assert_called_once_with('GSMID1')
            ffq_sample.assert_called_once_with('SRS1', None)

    def test_ffq_run(self):
        with mock.patch('ffq.ffq.get_xml') as get_xml,\
            mock.patch('ffq.ffq.parse_run') as parse_run:
            run = mock.MagicMock()
            parse_run.return_value = run
            self.assertEqual(run, ffq.ffq_run('SRR8426358'))
            get_xml.assert_called_once_with('SRR8426358')

    def test_ffq_study(self):
        with mock.patch('ffq.ffq.get_xml') as get_xml,\
            mock.patch('ffq.ffq.parse_study') as parse_study,\
            mock.patch('ffq.ffq.ffq_sample') as ffq_sample,\
            mock.patch('ffq.ffq.get_samples_from_study') as get_samples_from_study:
            parse_study.return_value = {'study': 'study_id'}
            get_samples_from_study.return_value = ["sample_id1", "sample_id2"]
            ffq_sample.side_effect = [{
                'accession': 'id1'
            }, {
                'accession': 'id2'
            }]
            self.assertEqual({
                'study': 'study_id',
                'samples': {
                    'id1': {
                        'accession': 'id1'
                    },
                    'id2': {
                        'accession': 'id2'
                    }
                },
            }, ffq.ffq_study('SRP226764'))
            get_xml.assert_called_once_with('SRP226764')
            self.assertEqual(2, ffq_sample.call_count)
            ffq_sample.assert_has_calls([
                call('sample_id1', None),
                call('sample_id2', None)
            ])

    def test_ffq_experiment(self):
        with mock.patch('ffq.ffq.get_xml') as get_xml,\
            mock.patch('ffq.ffq.parse_experiment_with_run') as parse_experiment_with_run:
            parse_experiment_with_run.return_value = {
                'experiments': 'experiment',
                'runs': {
                    'run': 'run'
                }
            }

            self.assertEqual({
                'experiments': 'experiment',
                'runs': {
                    'run': 'run'
                }
            }, ffq.ffq_experiment('SRX7048194'))
            get_xml.assert_called_once_with('SRX7048194')

    # Do one per accession, simply asserting equal to the expected list of links.

    # def test_ffq_links_gse_ftp(self):
    #     self.maxDiff = None
    #     capturedOutput = io.StringIO()
    #     sys.stdout = capturedOutput
    #     ffq.ffq_links([('GSE', 'GSE112570')], 'ftp')
    #     sys.stdout = sys.__stdout__
    #     self.assertEqual(
    #         capturedOutput.getvalue(),
    #         (
    #             'accession\tfiletype\tfilenumber\tlink\n'
    #             'GSM3073088\t\tbam\t1\tftp://ftp.sra.ebi.ac.uk/vol1/SRA678/SRA678017/bam/H17w_K1.bam\n'  # noqa
    #             'GSM3073089\t\tbam\t1\tftp://ftp.sra.ebi.ac.uk/vol1/SRA678/SRA678017/bam/H17w_K2.bam\n'  # noqa
    #         )
    #     )

    # def test_ffq_links_srs_ftp(self):
    #     capturedOutput = io.StringIO()  # Create StringIO object
    #     sys.stdout = capturedOutput  # and redirect stdout.
    #     ffq.ffq_links([('SRS', 'SRS4629239')], 'ftp')  # Call function.
    #     sys.stdout = sys.__stdout__
    #     self.assertEqual(
    #         capturedOutput.getvalue(),
    #         'ftp://ftp.sra.ebi.ac.uk/vol1/fastq/SRR890/000/SRR8903510/SRR8903510.fastq.gz '
    #     )

    # def test_ffq_links_gsm_aws(self):
    #     capturedOutput = io.StringIO()
    #     sys.stdout = capturedOutput
    #     ffq.ffq_links([('GSM', 'GSM3396164')], 'AWS')
    #     sys.stdout = sys.__stdout__
    #     self.assertEqual(
    #         capturedOutput.getvalue(),
    #         'https://sra-pub-src-1.s3.amazonaws.com/SRR7881402/possorted_genome_bam_Ck.bam.1 '
    #     )

    # def test_ffq_links_srr_gcp(self):
    #     capturedOutput = io.StringIO()
    #     sys.stdout = capturedOutput
    #     ffq.ffq_links([('SRR', 'SRR8327928')], 'GCP')
    #     sys.stdout = sys.__stdout__
    #     self.assertEqual(
    #         capturedOutput.getvalue(),
    #         'gs://sra-pub-src-1/SRR8327928/PDX110_possorted_genome_bam.bam.1 '
    #     )

    # def test_ffq_links_srx_ncbi(self):
    #     capturedOutput = io.StringIO()
    #     sys.stdout = capturedOutput
    #     ffq.ffq_links([('SRX', 'SRX4063411')], 'NCBI')
    #     sys.stdout = sys.__stdout__
    #     self.assertEqual(
    #         capturedOutput.getvalue(),
    #         'https://sra-downloadb.be-md.ncbi.nlm.nih.gov/sos2/sra-pub-run-13/SRR7142647/SRR7142647.1 '
    #     )

    def test_ffq_doi(self):
        with mock.patch('ffq.ffq.get_doi') as get_doi,\
            mock.patch('ffq.ffq.search_ena_title') as search_ena_title,\
            mock.patch('ffq.ffq.ffq_study') as ffq_study:

            get_doi.return_value = {'title': ['title']}
            search_ena_title.return_value = ['SRP1']
            self.assertEqual([ffq_study.return_value], ffq.ffq_doi('doi'))
            get_doi.assert_called_once_with('doi')
            search_ena_title.assert_called_once_with('title')
            ffq_study.assert_called_once_with('SRP1', None)

    def test_ffq_doi_no_title(self):
        with mock.patch('ffq.ffq.get_doi') as get_doi,\
            mock.patch('ffq.ffq.search_ena_title') as search_ena_title,\
            mock.patch('ffq.ffq.ncbi_search') as ncbi_search,\
            mock.patch('ffq.ffq.ncbi_link') as ncbi_link,\
            mock.patch('ffq.ffq.geo_ids_to_gses') as geo_ids_to_gses,\
            mock.patch('ffq.ffq.ffq_gse') as ffq_gse:

            get_doi.return_value = {'title': ['title']}
            search_ena_title.return_value = []
            ncbi_search.return_value = ['PMID1']
            ncbi_link.return_value = ['GEOID1']
            geo_ids_to_gses.return_value = ['GSE1']
            self.assertEqual([ffq_gse.return_value], ffq.ffq_doi('doi'))
            get_doi.assert_called_once_with('doi')
            search_ena_title.assert_called_once_with('title')
            ncbi_search.assert_called_once_with('pubmed', 'doi')
            ncbi_link.assert_called_once_with('pubmed', 'gds', 'PMID1')
            geo_ids_to_gses.assert_called_once_with(['GEOID1'])
            ffq_gse.assert_called_once_with('GSE1')

    def test_ffq_doi_no_geo(self):
        with mock.patch('ffq.ffq.get_doi') as get_doi,\
            mock.patch('ffq.ffq.search_ena_title') as search_ena_title,\
            mock.patch('ffq.ffq.ncbi_search') as ncbi_search,\
            mock.patch('ffq.ffq.ncbi_link') as ncbi_link,\
            mock.patch('ffq.ffq.sra_ids_to_srrs') as sra_ids_to_srrs,\
            mock.patch('ffq.ffq.ffq_run') as ffq_run:

            get_doi.return_value = {'title': ['title']}
            search_ena_title.return_value = []
            ncbi_search.return_value = ['PMID1']
            ncbi_link.side_effect = [[], ['SRA1']]
            sra_ids_to_srrs.return_value = ['SRR1']
            ffq_run.return_value = {
                'accession': 'SRR1',
                'study': {
                    'accession': 'SRP1'
                }
            }
            self.assertEqual([{
                'accession': 'SRP1',
                'runs': {
                    'SRR1': {
                        'accession': 'SRR1',
                        'study': {
                            'accession': 'SRP1'
                        }
                    }
                }
            }], ffq.ffq_doi('doi'))
            get_doi.assert_called_once_with('doi')
            search_ena_title.assert_called_once_with('title')
            ncbi_search.assert_called_once_with('pubmed', 'doi')
            self.assertEqual(2, ncbi_link.call_count)
            ncbi_link.assert_has_calls([
                call('pubmed', 'gds', 'PMID1'),
                call('pubmed', 'sra', 'PMID1'),
            ])
            sra_ids_to_srrs.assert_called_once_with(['SRA1'])
            ffq_run.assert_called_once_with('SRR1')
