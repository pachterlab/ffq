import os
from unittest import TestCase


class TestMixin(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.base_dir = os.path.dirname(os.path.abspath(__file__))
        cls.fixtures_dir = os.path.join(cls.base_dir, 'fixtures')
        cls.run_path = os.path.join(cls.fixtures_dir, 'SRR8426358.txt')
        cls.sample_path = os.path.join(cls.fixtures_dir, 'SRS4237519.txt')
        cls.experiment_path = os.path.join(cls.fixtures_dir, 'SRX5234128.txt')
        cls.study_path = os.path.join(cls.fixtures_dir, 'SRP178136.txt')
        cls.fastqs_path = os.path.join(cls.fixtures_dir, 'fastqs.txt')

        # BAM
        cls.fastqs2_path = os.path.join(cls.fixtures_dir, 'fastqs_empty.txt')
        cls.run2_path = os.path.join(cls.fixtures_dir, 'SRR6835844.txt')
        cls.bam_path = os.path.join(cls.fixtures_dir, 'bam.txt')
        cls.bam2_path = os.path.join(cls.fixtures_dir, 'bam_empty.txt')
