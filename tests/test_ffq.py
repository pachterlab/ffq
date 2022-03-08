from unittest import mock, TestCase
from unittest.mock import call
import io 
import sys

from bs4 import BeautifulSoup

import ffq.ffq as ffq
from tests.mixins import TestMixin


class TestFfq(TestMixin, TestCase):


    def test_validate_accession(self):
        SEARCH_TYPES = ('SRR', 'ERR', 'DRR', 'SRP', 'ERP', 'DRP', 'SRX', 'GSE','GSM', 'DOI')
        self.assertEqual([('SRR', 'SRR244234'),
                            False,
                            ('DOI', '10.1016/j.cell.2018.06.052'),
                            False,
                            ('GSM', 'GSM12345'),
                            ('GSE', 'GSE567890')
        ], ffq.validate_accession(["SRR244234", "SRT44322", '10.1016/j.cell.2018.06.052',
                                   'ASA10.1016/j.cell.2018.06.052', "GSM12345", "GSE567890"],
                                   SEARCH_TYPES))


    def test_parse_run(self):
        with mock.patch('ffq.ffq.get_files_metadata_from_run') as get_files_metadata_from_run:
            with open(self.run_path, 'r') as f:
                soup = BeautifulSoup(f.read(), 'xml')
            
            get_files_metadata_from_run.return_value = 'files'
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
                    'ENA-SPOT-COUNT': '109256158',
                    'ENA-BASE-COUNT': '21984096610',
                    'ENA-FIRST-PUBLIC': '2019-01-27',
                    'ENA-LAST-UPDATE': '2019-01-27'
                },
                'files': 'files'       
            }, ffq.parse_run(soup))

    def test_parse_run_bam(self):
        #with mock.patch('ffq.ffq.get_files_metadata_from_run') as get_files_metadata_from_run:
        with open(self.run2_path, 'r') as f:
            soup = BeautifulSoup(f.read(), 'xml')

        self.assertEqual({
            'accession':
                'SRR6835844',
            'experiment':
                'SRX3791763',
            'study':
                'SRP131661',
            'sample':
                'SRS3044236',
            'title':
                'Illumina NovaSeq 6000 sequencing; GSM3040890: library 10X_P4_0; Mus musculus; RNA-Seq',
            'attributes': {
                'assembly': 'mm10',
                'dangling_references': 'treat_as_unmapped',
                'ENA-SPOT-COUNT': '137766536',
                'ENA-BASE-COUNT': '12398988240',
                'ENA-FIRST-PUBLIC': '2018-03-30',
                'ENA-LAST-UPDATE': '2018-03-30'
            },
            'files': [{
                'url':
                    'ftp://ftp.sra.ebi.ac.uk/vol1/SRA653/SRA653146/bam/10X_P4_0.bam',
                'md5':
                    '5355fe6a07155026085ce46631268ab1',
                'size':
                    '17093057664'
            }, {
                'url':
                    'ftp://ftp.sra.ebi.ac.uk/vol1/run/SRR683/SRR6835844/10X_P4_0.bam.bai',
                'md5':
                    'c9396c2596254831470a9138ae86ded7',
                'size':
                    '7163216'
            }]

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
                'ENA-SPOT-COUNT': '109256158',
                'ENA-BASE-COUNT': '21984096610',
                'ENA-FIRST-PUBLIC': '2019-01-11',
                'ENA-LAST-UPDATE': '2019-01-11'
            },
            'experiment': 'SRX5234128'
        }, ffq.parse_sample(soup))

    def test_parse_experiment_with_run(self):
        with open(self.experiment_path, 'r') as f:
            soup = BeautifulSoup(f.read(), 'xml')

        self.assertEqual({'accession': 'SRX5234128',
 'instrument': 'Illumina HiSeq 4000',
 'platform': 'ILLUMINA',
 'runs': {'SRR8426358': {'accession': 'SRR8426358',
   'attributes': {'ENA-BASE-COUNT': '21984096610',
    'ENA-FIRST-PUBLIC': '2019-01-27',
    'ENA-LAST-UPDATE': '2019-01-27',
    'ENA-SPOT-COUNT': '109256158'},
   'experiment': 'SRX5234128',
   'files': [{'md5': 'be7e88cf6f6fd90f1b1170f1cb367123',
     'size': '5507959060',
     'url': 'ftp://ftp.sra.ebi.ac.uk/vol1/fastq/SRR842/008/SRR8426358/SRR8426358_1.fastq.gz'},
    {'md5': '2124da22644d876c4caa92ffd9e2402e',
     'size': '7194107512',
     'url': 'ftp://ftp.sra.ebi.ac.uk/vol1/fastq/SRR842/008/SRR8426358/SRR8426358_2.fastq.gz'}],
   'sample': 'SRS4237519',
   'study': 'SRP178136',
   'title': 'Illumina HiSeq 4000 paired end sequencing; GSM3557675: old_Dropseq_1; Mus musculus; RNA-Seq'}},
 'title': 'Illumina HiSeq 4000 paired end sequencing; GSM3557675: old_Dropseq_1; Mus musculus; RNA-Seq'}, ffq.parse_experiment_with_run(soup, 10))

    def test_parse_study(self):
        with open(self.study_path, 'r') as f:
            soup = BeautifulSoup(f.read(), 'xml')

        self.assertEqual({'accession': 'SRP178136',
                          'title': 'Multi-modal analysis of the aging mouse lung at cellular resolution',
                          'abstract': 'A) Whole lung tissue from 24 months (n=7) '
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
                          'accession': 'SRP178136'
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
            geo_to_suppl.return_value = {'filename': 'file', 'size': 'size', 'url': 'url'}
            ffq_gsm.side_effect = [{'accession': 'GSM1'}, {'accession': 'GSM2'}, 'test', 'test']

            self.assertEqual({
                'accession': 'GSE1',
                'supplementary_files': {
                    'filename': 'file',
                    'size': 'size',
                    'url': 'url'
                },    
                'samples': {
                    'GSM1': {
                        'accession': 'GSM1'
                    }, 
                    'GSM2': {
                        'accession' : 'GSM2'
                        }
                    }
                 }, ffq.ffq_gse('GSE1', 10))

            get_gse_search_json.assert_called_once_with('GSE1')
            gse_to_gsms.assert_called_once_with('GSE1')
            ffq_gsm.assert_has_calls([call('GSM_1', 9), call('GSM_2', 9)])


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
            geo_to_suppl.return_value = {'supplementary_files' : 'supp'}
            gsm_to_platform.return_value = {'platform' : 'platform'}
            gsm_id_to_srs.return_value = 'SRS1'
            ffq_sample.return_value = {'accession': 'SRS1'}

            self.assertEqual({
                'accession': 'GSM1',
                'supplementary_files' : {'supplementary_files' : 'supp'},
                'platform' : 'platform',
                'sample': {
                    'SRS1': {
                        'accession': 'SRS1'
                    }
                }
            }, ffq.ffq_gsm('GSM1', 10))
            get_gsm_search_json.assert_called_once_with('GSM1')
            geo_to_suppl.assert_called_once_with('GSM1', 'GSM')
            gsm_to_platform.assert_called_once_with('GSM1')
            gsm_id_to_srs.assert_called_once_with('GSMID1')
            ffq_sample.assert_called_once_with('SRS1', 9)

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
            ffq_sample.side_effect = [{'accession': 'id1'}, {'accession': 'id2'}]
            self.assertEqual({'study': 'study_id',
                'samples': {'id1': {'accession': 'id1'},
                 'id2': {'accession': 'id2'}
                     },
            }, ffq.ffq_study('SRP226764', 10))
            get_xml.assert_called_once_with('SRP226764')
            self.assertEqual(2, ffq_sample.call_count)
            ffq_sample.assert_has_calls([call('sample_id1', 9), call('sample_id2', 9)])

    def test_ffq_experiment(self):
        with mock.patch('ffq.ffq.get_xml') as get_xml,\
            mock.patch('ffq.ffq.parse_experiment_with_run') as parse_experiment_with_run:
            parse_experiment_with_run.return_value = {'experiment': 'experiment', 'runs' : {'run': 'run'}}

            self.assertEqual({'experiment': 'experiment', 'runs' : {'run': 'run'
            }}, ffq.ffq_experiment('SRX7048194', 10))
            get_xml.assert_called_once_with('SRX7048194')


        
    # Do one per accession, simply asserting equal to the expected list of links.


    def test_ffq_links_gse_ftp(self):
        self.maxDiff = None
        capturedOutput = io.StringIO()                 
        sys.stdout = capturedOutput                     
        ffq.ffq_links([('GSE', 'GSE119212')], 'ftp')                                 
        sys.stdout = sys.__stdout__
        self.assertEqual(capturedOutput.getvalue(), 
        'accession\tfiletype\tfilenumber\tlink\nGSM3360833\t\tbam\t1\tftp://ftp.sra.ebi.ac.uk/vol1/run/SRR776/SRR7767734/GW16_Hippocampus_possorted_genome_bam.bam.1\nGSM3360834\t\tbam\t1\tftp://ftp.sra.ebi.ac.uk/vol1/run/SRR776/SRR7767735/GW18_Hippocampus_possorted_genome_bam.bam.1\nGSM3360835\t\tbam\t1\tftp://ftp.sra.ebi.ac.uk/vol1/run/SRR776/SRR7767736/GW22_Hippocampus_01_possorted_genome_bam.bam.1\nGSM3360836\t\tbam\t1\tftp://ftp.sra.ebi.ac.uk/vol1/run/SRR776/SRR7767737/GW22_Hippocampus_02_possorted_genome_bam.bam.1\nGSM3360837\t\tbam\t1\tftp://ftp.sra.ebi.ac.uk/vol1/run/SRR776/SRR7767738/GW25_Hippocampus_possorted_genome_bam.bam.1\nGSM3360838\t\tbam\t1\tftp://ftp.sra.ebi.ac.uk/vol1/run/SRR776/SRR7767739/GW27_Hippocampus_possorted_genome_bam.bam.1\nGSM3770749\t\tbam\t1\tftp://ftp.sra.ebi.ac.uk/vol1/run/SRR907/SRR9072134/GW20_Hippocampus_01_possorted_genome_bam.bam.1\nGSM3770750\t\tbam\t1\tftp://ftp.sra.ebi.ac.uk/vol1/run/SRR907/SRR9072135/GW20_Hippocampus_02_possorted_genome_bam.bam.1\n'
        )                  


    def test_ffq_links_srs_ftp(self):
        capturedOutput = io.StringIO()                  # Create StringIO object
        sys.stdout = capturedOutput                     #  and redirect stdout.
        ffq.ffq_links([('SRS', 'SRS3815608')], 'ftp')                                    # Call function.
        sys.stdout = sys.__stdout__
        self.assertEqual(capturedOutput.getvalue(), 
        'ftp://ftp.sra.ebi.ac.uk/vol1/fastq/SRR789/003/SRR7895953/SRR7895953_1.fastq.gz ftp://ftp.sra.ebi.ac.uk/vol1/fastq/SRR789/003/SRR7895953/SRR7895953_2.fastq.gz '
        )                  
            
    def test_ffq_links_gsm_aws(self):
        capturedOutput = io.StringIO()                  # Create StringIO object
        sys.stdout = capturedOutput                     #  and redirect stdout.
        ffq.ffq_links([('GSM', 'GSM2905290')], 'AWS')                                    # Call function.
        sys.stdout = sys.__stdout__
        self.assertEqual(capturedOutput.getvalue(), 
        's3://sra-pub-src-6/SRR6425161/J4_S1_L001_R1_001.fastq.gz s3://sra-pub-src-6/SRR6425161/J4_S1_L001_R2_001.fastq.gz '
        )          

    def test_ffq_links_srp_aws(self):
        capturedOutput = io.StringIO()                  # Create StringIO object
        sys.stdout = capturedOutput                     #  and redirect stdout.
        ffq.ffq_links([('SRP', 'SRP162461')], 'AWS')                                    # Call function.
        sys.stdout = sys.__stdout__
        self.assertEqual(capturedOutput.getvalue(), 'SRR7895967\t\tfastq\t1\ts3://sra-pub-src-3/SRR7895967/P3V_DS_Placenta_11_S1_R1_001.fastq.gz\nSRR7895967\t\tfastq\t1\ts3://sra-pub-src-3/SRR7895967/P3V_DS_Placenta_11_S1_R2_001.fastq.gz\nSRR7895966\t\tfastq\t1\ts3://sra-pub-src-3/SRR7895966/P4V_DS_Placenta_5_S1_R1_001.fastq.gz\nSRR7895966\t\tfastq\t2\ts3://sra-pub-src-3/SRR7895966/P4V_DS_Placenta_5_S1_R2_001.fastq.gz\nSRR7895965\t\tfastq\t1\ts3://sra-pub-src-3/SRR7895965/P1V_DS_Placenta_20_S1_R1_001.fastq.gz\nSRR7895965\t\tfastq\t2\ts3://sra-pub-src-3/SRR7895965/P1V_DS_Placenta_20_S1_R2_001.fastq.gz\nSRR7895964\t\tfastq\t1\ts3://sra-pub-src-3/SRR7895964/P2V_DS_Placenta_12_S1_R1_001.fastq.gz\nSRR7895964\t\tfastq\t1\ts3://sra-pub-src-3/SRR7895964/P2V_DS_Placenta_12_S1_R2_001.fastq.gz\nSRR7895963\t\tfastq\t1\ts3://sra-pub-src-3/SRR7895963/P7V_10X_Placenta_17_R1.fastq.gz\nSRR7895963\t\tfastq\t1\ts3://sra-pub-src-3/SRR7895963/P7V_10X_Placenta_17_R2.fastq.gz\nSRR7895962\t\tfastq\t1\ts3://sra-pub-src-3/SRR7895962/P8V_10X_Placenta_23_S2_L002_R1_001.fastq.gz\nSRR7895962\t\tfastq\t1\ts3://sra-pub-src-3/SRR7895962/P8V_10X_Placenta_23_S2_L002_R2_001.fastq.gz\nSRR7895961\t\tfastq\t1\ts3://sra-pub-src-3/SRR7895961/P5V_DS_Placenta_23_S1_R1_001.fastq.gz\nSRR7895961\t\tfastq\t2\ts3://sra-pub-src-3/SRR7895961/P5V_DS_Placenta_23_S1_R2_001.fastq.gz\nSRR7895960\t\tfastq\t1\ts3://sra-pub-src-3/SRR7895960/P6V_DS_Placenta_10_S1_R1_001.fastq.gz\nSRR7895960\t\tfastq\t1\ts3://sra-pub-src-3/SRR7895960/P6V_DS_Placenta_10_S1_R2_001.fastq.gz\nSRR7895959\t\tfastq\t1\ts3://sra-pub-src-3/SRR7895959/P1D_DS_Placenta_20_S1_R1_001.fastq.gz\nSRR7895959\t\tfastq\t2\ts3://sra-pub-src-3/SRR7895959/P1D_DS_Placenta_20_S1_R2_001.fastq.gz\nSRR7895958\t\tfastq\t1\ts3://sra-pub-src-3/SRR7895958/P2D_DS_Placenta_22_S1_R1_001.fastq.gz\nSRR7895958\t\tfastq\t2\ts3://sra-pub-src-3/SRR7895958/P2D_DS_Placenta_22_S1_R2_001.fastq.gz\nSRR7895957\t\tfastq\t1\ts3://sra-pub-src-3/SRR7895957/P3D_DS_Placenta_21_S1_R1_001.fastq.gz\nSRR7895957\t\tfastq\t2\ts3://sra-pub-src-3/SRR7895957/P3D_DS_Placenta_21_S1_R2_001.fastq.gz\nSRR7895956\t\tfastq\t1\ts3://sra-pub-src-3/SRR7895956/P4D_DS_Placenta_23_S1_R1_001.fastq.gz\nSRR7895956\t\tfastq\t2\ts3://sra-pub-src-3/SRR7895956/P4D_DS_Placenta_23_S1_R2_001.fastq.gz\nSRR7895955\t\tfastq\t1\ts3://sra-pub-src-3/SRR7895955/P5D_DS_Placenta_22_S1_R1_001.fastq.gz\nSRR7895955\t\tfastq\t2\ts3://sra-pub-src-3/SRR7895955/P5D_DS_Placenta_22_S1_R2_001.fastq.gz\nSRR7895954\t\tfastq\t1\ts3://sra-pub-src-3/SRR7895954/P6D_10X_Placenta_23_S1_L001_R1_001.fastq.gz\nSRR7895954\t\tfastq\t1\ts3://sra-pub-src-3/SRR7895954/P6D_10X_Placenta_23_S1_L001_R2_001.fastq.gz\nSRR7895953\t\tfastq\t1\ts3://sra-pub-src-3/SRR7895953/T1-01P1_ACAGTG_L007_R1_001.fastq.gz\nSRR7895953\t\tfastq\t2\ts3://sra-pub-src-3/SRR7895953/T1-01P1_ACAGTG_L007_R2_001.fastq.gz\n<'
        )


#########
        ### Note: make it try twice before jumping to bam links....
#########



        ######
        # def test_ffg_srp:
            # SRP162461
            # """
            # SRX4733412		fastq	1	ftp://ftp.sra.ebi.ac.uk/vol1/fastq/SRR789/003/SRR7895953/SRR7895953_1.fastq.gz
            # SRX4733412		fastq	2	ftp://ftp.sra.ebi.ac.uk/vol1/fastq/SRR789/003/SRR7895953/SRR7895953_2.fastq.gz
            # """
            
            
        # def test_ffq_srs:
            # SRS3815608
            # 'ftp://ftp.sra.ebi.ac.uk/vol1/fastq/SRR789/003/SRR7895953/SRR7895953_1.fastq.gz ftp://ftp.sra.ebi.ac.uk/vol1/fastq/SRR789/003/SRR7895953/SRR7895953_2.fastq.gz'
            
        # def test_ffq_srx:
            # SRX4733412
            # 'ftp://ftp.sra.ebi.ac.uk/vol1/fastq/SRR789/003/SRR7895953/SRR7895953_1.fastq.gz ftp://ftp.sra.ebi.ac.uk/vol1/fastq/SRR789/003/SRR7895953/SRR7895953_2.fastq.gz'
            
        # def test_ffq_srr:
            # SRR7895953
            #'ftp://ftp.sra.ebi.ac.uk/vol1/fastq/SRR789/003/SRR7895953/SRR7895953_1.fastq.gz ftp://ftp.sra.ebi.ac.uk/vol1/fastq/SRR789/003/SRR7895953/SRR7895953_2.fastq.gz'
        


## To use for ffq_sample
#    def test_ffq_experiment(self):
#        with mock.patch('ffq.ffq.get_xml') as get_xml,\
#            mock.patch('ffq.ffq.parse_experiment') as parse_experiment,\
#            mock.patch('ffq.ffq.ffq_sample') as ffq_sample:
#            parse_experiment.return_value = {'experiment': 'experiment', 'sample': 'sample'}
 #           ffq_sample.return_value = {'accession': 'sample'}
#
 #           self.assertEqual({'experiment': 'experiment', 'sample': 'sample',
  #              'samples': {'sample': {'accession':'sample'
   #         }}}, ffq.ffq_experiment('SRX7048194'))
     #       get_xml.assert_called_once_with('SRX7048194')
    #        ffq_sample.assert_called_once_with('sample')
## To use for ffq_sample



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
