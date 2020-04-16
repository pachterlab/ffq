import os
import tempfile
import uuid
from unittest import TestCase

import fqc.utils as utils


class TestUtils(TestCase):

    def test_open_as_text_textfile(self):
        path = os.path.join(
            tempfile.gettempdir(), '{}.txt'.format(uuid.uuid4())
        )
        with utils.open_as_text(path, 'w') as f:
            f.write('TESTING')
        self.assertTrue(os.path.exists(path))
        with utils.open_as_text(path, 'r') as f:
            self.assertEqual(f.read(), 'TESTING')

    def test_open_as_text_gzip(self):
        path = os.path.join(tempfile.gettempdir(), '{}.gz'.format(uuid.uuid4()))
        with utils.open_as_text(path, 'w') as f:
            f.write('TESTING')
        self.assertTrue(os.path.exists(path))
        with utils.open_as_text(path, 'r') as f:
            self.assertEqual(f.read(), 'TESTING')

    def test_fastq_reads(self):
        path = os.path.join(tempfile.gettempdir(), '{}.gz'.format(uuid.uuid4()))
        with utils.open_as_text(path, 'w') as f:
            f.write('1\n2\n3\n4\n5\n6\n7\n8\n9')
        self.assertTrue(os.path.exists(path))
        self.assertEqual(['2', '6'], list(utils.fastq_reads(path)))

    def test_sequence_equals(self):
        self.assertTrue(utils.sequence_equals('ATC', 'ATC'))
        self.assertFalse(utils.sequence_equals('ATC', 'ATT'))

    def test_sequence_equals_distance(self):
        self.assertTrue(utils.sequence_equals('ATC', 'ATT', distance=1))
        self.assertFalse(utils.sequence_equals('ATC', 'TTT', distance=1))

    def test_sequence_equals_N(self):
        self.assertTrue(utils.sequence_equals('ATC', 'ATN'))
        self.assertFalse(utils.sequence_equals('ATC', 'ACN'))
