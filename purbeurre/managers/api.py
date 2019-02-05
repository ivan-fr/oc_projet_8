import re
import urllib.request
import urllib.parse
import json
from purbeurre.utils import get_words_from_sentence
from django.utils.text import slugify
import logging

logger = logging.getLogger(__name__)


class ApiManager:
    """its role is to communicate with the Openfoodfacts JSON API."""

    # Init url from openfoodfacts api.
    search_url = "https://fr.openfoodfacts.org/cgi/search.pl"
    product_url = "http://fr.openfoodfacts.org/api/v0/product/{}.json"
    marks_for_a_category_url = "https://fr.openfoodfacts.org/categorie" \
                               "/{}/notes-nutritionnelles.json"
    product_marks_url = "https://fr.openfoodfacts.org/categorie/{}" \
                        "/note-nutritionnelle/{}.json"

    @classmethod
    def do_research(cls, research: str):
        """Get products from the openfoodfacts API by research"""

        payload = urllib.parse.urlencode({'search_terms': research,
                                          'search_simple': 1,
                                          'action': 'process',
                                          'page_size': 9,
                                          'json': 1})

        products = []
        url = cls.search_url + '?' + payload
        with urllib.request.urlopen(url) as response:
            logger.error(response.geturl())
            if response.geturl() != url:
                bar_code = re.search(
                    r'^/(produit|product)/(\d+)/?[0-9a-zA-Z_\-]*/?$',
                    urllib.parse.urlparse(response.geturl()).path).group(2)

                with urllib.request.urlopen(
                        cls.product_url.format(bar_code)) as response2:
                    logger.error(response2.geturl())
                    _dict = json.loads(response2.read().decode('utf8'))
                    if _dict.get('product', None):
                        products = (_dict['product'],)
            else:
                products = json.loads(response.read().decode('utf8'))

                if products.get('count', 0) > 0:
                    products = products['products']
        return products

    @classmethod
    def get_substitutes(cls, product: dict):
        """Get the best substitutes for a category"""

        substitutes = []
        cls.wash_product(product, wash_ingredients=False)

        nutrition_grades = product.get('nutrition_grades', 'e')
        categories = product.get('categories_hierarchy', None)

        if not categories:
            return substitutes

        category = slugify(categories[-1])

        url = cls.marks_for_a_category_url.format(category)
        with urllib.request.urlopen(url) as response:
            logger.error(response.geturl())
            if response.geturl() != url:
                category = re.search(r'^/categorie/([0-9a-z_\-]*).json$',
                                     urllib.parse.urlparse(
                                         response.geturl()).path).group(1)

                with urllib.request.urlopen(
                        cls.marks_for_a_category_url.format(
                            category)) as response2:
                    logger.error(response2.geturl())
                    result = json.loads(response2.read().decode('utf8'))
            else:
                result = json.loads(response.read().decode('utf8'))

        if result.get('count', 0) > 0:
            i_substitutes, imark = 0, 0
            while i_substitutes <= 8 and imark <= result['count'] - 1 and \
                    (result['tags'][imark]['id'] < nutrition_grades
                     or (nutrition_grades == 'a'
                         and result['tags'][imark]['id'] == nutrition_grades)):
                url = cls.product_marks_url.format(category,
                                                   result['tags'][imark]['id'])

                with urllib.request.urlopen(url) as response:
                    logger.error(response.geturl())
                    result_substitutes = json.loads(
                        response.read().decode('utf8'))

                    if nutrition_grades == 'a':
                        for i, substitute in enumerate(
                                result_substitutes['products'][:9]):
                            if substitute['code'] == product['code']:
                                del result_substitutes['products'][i]
                                break

                    substitutes += \
                        result_substitutes['products'][:9 - i_substitutes]
                    i_substitutes += \
                        len(result_substitutes['products'][:9 - i_substitutes])
                imark += 1

        return substitutes

    @classmethod
    def get_product(cls, bar_code: str, with_clean=False):
        """Get products from the openfoodfacts API by bar code"""

        with urllib.request.urlopen(
                cls.product_url.format(bar_code)) as response:
            logger.error(response.geturl())
            _dict = json.loads(response.read().decode('utf8'))
            if _dict.get('product', None):
                product = _dict['product']
                if with_clean:
                    cls.wash_product(product)
            else:
                product = None

        return product

    @staticmethod
    def wash_product(product: dict, wash_categories=True,
                     wash_ingredients=True):
        # wash categories keys
        if wash_categories:

            if product.get('categories_hierarchy'):
                i = 0
                while i <= len(product['categories_hierarchy']) - 1:
                    if ':' in product['categories_hierarchy'][i]:
                        product['categories_hierarchy'][i] = \
                            (product['categories_hierarchy'][i].split(':'))[1]
                    i += 1

            if product.get('categories'):
                product['categories'] = product['categories'].split(',')
                i = 0
                while i <= len(product['categories']) - 1:
                    if ':' in product['categories'][i]:
                        product['categories'][i] = \
                            (product['categories'][i].split(':'))[1]
                    i += 1

        # wash ingredients keys
        if wash_ingredients:
            if product.get('ingredients_text_fr', None):
                product['ingredients_text_fr'] = (
                    ' '.join(get_words_from_sentence(ingredient)) for ingredient
                    in
                    product['ingredients_text_fr'].split(','))
            else:
                product['ingredients'] = (
                    ' '.join(get_words_from_sentence(ingredient['text'])) for
                    ingredient
                    in product.get('ingredients', ()))

        return product
