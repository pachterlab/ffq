from unittest import mock, TestCase

import fqc.fqc as fqc
from fqc.technologies import OrderedTechnology, TECHNOLOGIES, TECHNOLOGIES_MAPPING


class TestFqc(TestCase):

    def test_all_ordered_technologies(self):
        self.assertEqual([
            OrderedTechnology(TECHNOLOGIES_MAPPING['10xv1'], (0, 1)),
            OrderedTechnology(TECHNOLOGIES_MAPPING['10xv1'], (1, 0))
        ], fqc.all_ordered_technologies([TECHNOLOGIES_MAPPING['10xv1']], 2))

    def test_extract_barcodes_umis(self):
        with mock.patch('fqc.fqc.fastq_reads') as fastq_reads:
            reads_1 = ['1' * 50, '2' * 50]
            reads_2 = ['3' * 50, '4' * 50]
            fastq_reads.side_effect = [reads_1, reads_2]

            self.assertEqual(
                ({
                    '10xv1': {(0, 1): [['22222222222222']]}
                }, {
                    '10xv1': {(0, 1): [['4444444444']]}
                }, {
                    '10xv1': set()
                }),
                fqc.extract_barcodes_umis([1, 2], 1, 1, [
                    OrderedTechnology(TECHNOLOGIES_MAPPING['10xv1'], (0, 1))
                ])
            )

    def test_extract_barcodes_umis_invalid(self):
        with mock.patch('fqc.fqc.fastq_reads') as fastq_reads:
            reads_1 = ['1', '2']
            reads_2 = ['3', '4']
            fastq_reads.side_effect = [reads_1, reads_2]

            self.assertEqual(
                ({
                    '10xv1': {}
                }, {
                    '10xv1': {}
                }, {
                    '10xv1': {(0, 1)}
                }),
                fqc.extract_barcodes_umis([1, 2], 1, 1, [
                    OrderedTechnology(TECHNOLOGIES_MAPPING['10xv1'], (0, 1))
                ])
            )

    def test_filter_files(self):
        fastqs = [1, 2, 3]
        result = fqc.filter_files(
            fastqs, [
                OrderedTechnology(TECHNOLOGIES_MAPPING['10xv1'], (0, 1, 2)),
                OrderedTechnology(TECHNOLOGIES_MAPPING['10xv2'], (0, 1))
            ]
        )
        self.assertListEqual([
            OrderedTechnology(TECHNOLOGIES_MAPPING['10xv1'], (0, 1, 2))
        ], result)

    def test_filter_barcodes_umis(self):
        pass

    def test_fqc(self):
        with mock.patch('fqc.fqc.all_ordered_technologies') as all_ordered_technologies,\
            mock.patch('fqc.fqc.filter_files') as filter_files,\
            mock.patch('fqc.fqc.filter_barcodes_umis') as filter_barcodes_umis:
            skip = mock.MagicMock()
            n = mock.MagicMock()
            fqc.fqc([1, 2, 3], skip, n)

            all_ordered_technologies.assert_called_once_with(TECHNOLOGIES, 3)
            filter_files.assert_called_once_with([1, 2, 3],
                                                 all_ordered_technologies())
            filter_barcodes_umis.assert_called_once_with([1, 2, 3], skip, n,
                                                         filter_files())
