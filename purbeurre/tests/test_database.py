from django.test import TestCase
from purbeurre.managers.database import DatabaseManager
from purbeurre.managers.api import ApiManager
from django.contrib.auth.models import User
from purbeurre.models import Product, ProductSubstituteProduct
from unittest.mock import patch, MagicMock
from io import BytesIO
from .mock_data import mock_data


def side_effect(url):
    m = BytesIO(mock_data['views'][url].encode())
    m.geturl = MagicMock(return_value=url)
    return m


class DatabaseTestCase(TestCase):

    def setUp(self):
        self.credentials = {'username': 'a-user', 'password': 'password'}
        self.user = User.objects.create_user(**self.credentials)

    @patch('urllib.request.urlopen')
    def test_do_research(self, mock_urllib_request_urlopen):
        mock_urllib_request_urlopen.side_effect = side_effect
        product = ApiManager.get_product("3029330003458")
        substitute = ApiManager.get_product("3029330003533")

        product_count = Product.objects.count()
        product_substitute_product = \
            ProductSubstituteProduct.objects.filter(users=self.user).count()

        DatabaseManager.save_product(self.user, product, (substitute,))

        product_count_new = Product.objects.count()
        product_substitute_product_new = \
            ProductSubstituteProduct.objects.filter(users=self.user).count()

        self.assertEqual(product_count,
                         product_count_new - 2)
        self.assertEqual(product_substitute_product,
                         product_substitute_product_new - 1)
