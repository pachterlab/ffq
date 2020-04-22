from unittest import mock, TestCase

from bs4 import BeautifulSoup

import ffq.utils as utils
from ffq.config import ENA_URL


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

    def test_parse_tsv(self):
        s = 'header1\theader2\theader3\nvalue1\tvalue2\tvalue3'
        self.assertEqual([{
            'header1': 'value1',
            'header2': 'value2',
            'header3': 'value3'
        }], utils.parse_tsv(s))
