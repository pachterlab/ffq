import os
from unittest import TestCase


class TestMixin(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_dir = os.path.dirname(os.path.abspath(__file__))
        cls.fixtures_dir = os.path.join(cls.base_dir, "fixtures")
        cls.run_path = os.path.join(cls.fixtures_dir, "SRR8426358.txt")
        cls.sample_path = os.path.join(cls.fixtures_dir, "SRS4237519.txt")
        cls.experiment_path = os.path.join(cls.fixtures_dir, "SRX3517583.txt")
        cls.study_path = os.path.join(cls.fixtures_dir, "SRP178136.txt")
        cls.fastqs_path = os.path.join(cls.fixtures_dir, "fastqs.txt")

        # BAM
        cls.fastqs2_path = os.path.join(cls.fixtures_dir, "fastqs_empty.txt")
        cls.run2_path = os.path.join(cls.fixtures_dir, "SRR6835844.txt")
        cls.bam_path = os.path.join(cls.fixtures_dir, "bam.txt")
        cls.bam2_path = os.path.join(cls.fixtures_dir, "bam_empty.txt")

        # GEO
        cls.gse_search_path = os.path.join(cls.fixtures_dir, "GSE93374_search.txt")
        cls.gse_summary_path = os.path.join(cls.fixtures_dir, "GSE93374_summary.txt")

        cls.gsm_summary_path = os.path.join(cls.fixtures_dir, "GSM3717978_summary.txt")

        # ENCODE
        cls.encode_experiment_path = os.path.join(cls.fixtures_dir, "ENCSR998WNE.txt")
        cls.encode_experiment_output_path = os.path.join(
            cls.fixtures_dir, "ENCSR998WNE_output.txt"
        )
        cls.biosample_path = os.path.join(cls.fixtures_dir, "ENCBS941ZTJ.txt")
        cls.donor_path = os.path.join(cls.fixtures_dir, "ENCDO072AAA.txt")

        # Bioproject

        cls.bioproject_path = os.path.join(cls.fixtures_dir, "CRX118013.txt")
        # keyed jsons
        cls.srr_keyed = os.path.join(cls.fixtures_dir, "SRR5398235_keyed.json")

        # Alt links
        cls.alt_links = os.path.join(cls.fixtures_dir, "SRR6835844_altlinks_new.txt")

        # SRA
        cls.srx_xml = os.path.join(cls.fixtures_dir, "SRX5692097_xml.txt")
        cls.study_with_run_path = os.path.join(
            cls.fixtures_dir, "SRP096361_with_runlist.txt"
        )
