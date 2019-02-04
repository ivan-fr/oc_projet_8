from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch, MagicMock
from django.core import signing
from io import BytesIO
from .mock_data import mock_data

from purbeurre.models import Product, ProductSubstituteProduct
from django.contrib.auth.models import User


def side_effect(url):
    m = BytesIO(mock_data['views'][url].encode())
    m.geturl = MagicMock(return_value=url)
    return m


class IndexTestCase(TestCase):

    def test_get_index(self):
        response = self.client.get(reverse('purbeurre:index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'purbeurre/index.html')

    @patch('urllib.request.urlopen')
    def test_post_index(self, mock_urllib_request_urlopen):
        mock_urllib_request_urlopen.side_effect = side_effect

        response = self.client.post(reverse('purbeurre:index'), {
            'navbar-search': 'nutella'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'purbeurre/search.html')
        self.assertEqual(response.context['search'], 'nutella')
        self.assertEqual(len(response.context['products']), 9)

    def test_error_post_index(self):
        response = self.client.post(reverse('purbeurre:index'), {
            'navbar-search': '___ /// ___ ///::::'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'navbar_search_form', 'search',
                             'Entrez une recherche valide.')
        self.assertTemplateUsed(response, 'purbeurre/index.html')


class CreditsTestCase(TestCase):

    def test_get_credits(self):
        response = self.client.get(reverse('purbeurre:credits'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'purbeurre/mentions_legales.html')


class SubstitutesTestCase(TestCase):

    @patch('urllib.request.urlopen')
    def test_get_substitutes(self, mock_urllib_request_urlopen):
        mock_urllib_request_urlopen.side_effect = side_effect
        response = self.client.get(reverse('purbeurre:substitutes', kwargs={
            'bar_code': '3029330003458'
        }))

        sign = signing.dumps({
            'product': '3029330003458',
            'substitutes': list(
                substitute['code'] for substitute in
                response.context['substitutes'])
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'purbeurre/substitutes.html')
        self.assertLessEqual(len(response.context['substitutes']), 9)
        self.assertEqual(response.context['sign'], sign)


class ShowProductTestCase(TestCase):

    # ran before each test.
    def setUp(self):
        self.product, _ = Product.objects.get_or_create(
            name="produit test",
            bar_code="3029330003458"
        )

    # test that show_product page returns a 200 if the item exists
    def test_show_product_returns_200(self):
        produit_id = self.product.id
        response = self.client.get(reverse('purbeurre:show_product',
                                           args=(produit_id,)))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'purbeurre/show_product.html')

    # test that show_product page returns a 404 if the items does not exist
    def test_show_product_returns_404(self):
        produit_id = self.product.id + 1
        response = self.client.get(reverse('purbeurre:show_product',
                                           args=(produit_id,)))
        self.assertEqual(response.status_code, 404)


class AuthenticatedViewsTestCase(TestCase):

    def setUp(self):
        self.credentials = {'username': 'a-user', 'password': 'password'}
        self.user = User.objects.create_user(**self.credentials)
        self.client.login(**self.credentials)

    @patch('urllib.request.urlopen')
    def test_create_substitute_link(self, mock_urllib_request_urlopen):
        self.product, _ = Product.objects.get_or_create(
            name="produit test",
            bar_code="1"
        )
        self.substitute, _ = Product.objects.get_or_create(
            name="produit test",
            bar_code="2"
        )

        product_substitute_product = ProductSubstituteProduct.objects.count()

        sign = signing.dumps({
            'product': self.product.bar_code,
            'substitutes': [self.substitute.bar_code]
        })

        response = self.client.get(reverse('purbeurre:create_link',
                                           args=(sign,
                                                 self.substitute.bar_code)))

        product_substitute_product_new = \
            ProductSubstituteProduct.objects.count()

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'purbeurre/'
                                          'create_substitute_link.html')
        self.assertEqual(product_substitute_product,
                         product_substitute_product_new - 1)

    @patch('urllib.request.urlopen')
    def test_create_substitute_link_urllib(self, mock_urllib_request_urlopen):
        mock_urllib_request_urlopen.side_effect = side_effect
        product_substitute_product = ProductSubstituteProduct.objects.count()

        sign = signing.dumps({
            'product': '3029330003458',
            'substitutes': ['3029330003533']
        })

        response = self.client.get(reverse('purbeurre:create_link',
                                           args=(sign,
                                                 '3029330003533')))

        product_substitute_product_new = \
            ProductSubstituteProduct.objects.count()

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'purbeurre/'
                                          'create_substitute_link.html')
        self.assertEqual(product_substitute_product,
                         product_substitute_product_new - 1)

    def test_show_user_link(self):
        self.product, _ = Product.objects.get_or_create(
            name="produit test",
            bar_code="1"
        )
        self.substitute, _ = Product.objects.get_or_create(
            name="produit test",
            bar_code="2"
        )

        product_substitute_product, _ = ProductSubstituteProduct.objects \
            .get_or_create(from_product=self.product,
                           to_product=self.substitute)
        product_substitute_product.users.add(self.user)

        response = self.client.get(reverse('purbeurre:my_products'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'purbeurre/show_user_link.html')
        self.assertEqual(len(response.context['liste']), 1)

    def test_profile(self):
        response = self.client.get(reverse('purbeurre:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'purbeurre/profile.html')

    def test_login_redirect(self):
        self.client.logout()
        response = self.client.post(reverse('purbeurre:login'),
                                    self.credentials)
        self.assertRedirects(response, reverse('purbeurre:profile'))
