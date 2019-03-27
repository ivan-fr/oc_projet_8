from io import BytesIO
from unittest.mock import patch, MagicMock

from django.contrib.auth.models import User
from django.test import TestCase

from purbeurre.managers.api import ApiManager
from purbeurre.managers.database import DatabaseManager
from purbeurre.models import Product, ProductSubstituteProduct, Category
from .mock_data import mock_data


def side_effect(url):
    m = BytesIO(mock_data['views'][url].encode())
    m.geturl = MagicMock(return_value=url)
    return m


class DatabaseTestCase(TestCase):
    """ test save product function of database manager """

    def setUp(self):
        self.credentials = {'username': 'a-user', 'password': 'password'}
        self.user = User.objects.create_user(**self.credentials)

    @patch('urllib.request.urlopen')
    def test_save_product(self, mock_urllib_request_urlopen):
        """ test save product function of database manager """

        mock_urllib_request_urlopen.side_effect = side_effect
        product = ApiManager.get_product("3029330003458")
        substitute = ApiManager.get_product("3029330003533")

        product_count = Product.objects.count()
        product_substitute_product = \
            ProductSubstituteProduct.objects.filter(users=self.user).count()

        DatabaseManager.save_product(product, (substitute,), user=self.user)

        product_count_new = Product.objects.count()
        product_substitute_product_new = \
            ProductSubstituteProduct.objects.filter(users=self.user).count()

        self.assertEqual(product_count, product_count_new - 2)
        self.assertEqual(product_substitute_product,
                         product_substitute_product_new - 1)

    @patch('urllib.request.urlopen')
    def test_save_substitutes_and_get_substitutes \
                    (self, mock_urllib_request_urlopen):
        """ test the save of substitues and get the substitutes """

        mock_urllib_request_urlopen.side_effect = side_effect

        product = ApiManager.get_product("3029330003458")
        substitute = ApiManager.get_product("3029330003533")

        category_count = Category.objects.count()
        product_count = Product.objects.count()

        DatabaseManager.save_substitutes(product['categories_hierarchy'][-1],
                                         (substitute,))

        category_count_new = Category.objects.filter(searched_substitutes=True) \
            .count()
        product_count_new = Product.objects.count()

        self.assertEqual(product_count, product_count_new - 1)
        self.assertEqual(category_count, category_count_new - 1)

        substitutes = DatabaseManager.get_substitutes_from_api(product)
        self.assertEqual(len(substitutes), 1)
