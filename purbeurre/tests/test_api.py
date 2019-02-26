from django.test import TestCase
from unittest.mock import patch, MagicMock
from io import BytesIO
from .mock_data import mock_data
from purbeurre.managers.api import ApiManager
import types


def side_effect(url):
    m = BytesIO(mock_data['views'][url].encode())
    m.geturl = MagicMock(return_value=url)
    return m


class ApiTestCase(TestCase):

    @patch('urllib.request.urlopen')
    def test_do_research(self, mock_urllib_request_urlopen):
        """ test do_research function of api manager """

        mock_urllib_request_urlopen.side_effect = side_effect
        products = ApiManager.do_research('nutella')
        self.assertEqual(len(products), 9)

    @patch('urllib.request.urlopen')
    def test_get_product(self, mock_urllib_request_urlopen):
        """ test get_product function of api manager """

        mock_urllib_request_urlopen.side_effect = side_effect
        product = ApiManager.get_product("3029330003458")
        self.assertIsNotNone(product)

    @patch('urllib.request.urlopen')
    def test_get_substitutes(self, mock_urllib_request_urlopen):
        """ test get_substitutes function of api manager """

        mock_urllib_request_urlopen.side_effect = side_effect
        product = ApiManager.get_product("3029330003458")
        substitutes = ApiManager.get_substitutes(product)

        self.assertIsNotNone(product)
        self.assertEqual(len(substitutes), 9)

    @patch('urllib.request.urlopen')
    def test_wash_product(self, mock_urllib_request_urlopen):
        """ test wash_product function of api manager """

        mock_urllib_request_urlopen.side_effect = side_effect
        product = ApiManager.get_product("3029330003458")
        washed_product = product

        for category in washed_product.get('categories_hierarchy', ()):
            self.assertNotIn(':', category)

        self.assertIsInstance(washed_product.get('categories'), (list, tuple))

        for category in washed_product.get('categories'):
            self.assertNotIn(':', category)

        self.assertIsInstance(washed_product.get('ingredients_text_fr', ()),
                              (tuple, types.GeneratorType))

        if not washed_product.get('ingredients_text_fr', None):
            self.assertIsInstance(washed_product.get('ingredients', ()),
                                  (tuple, types.GeneratorType))
