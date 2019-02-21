import re
import urllib.request
import urllib.parse
import json
from purbeurre.utils import wash_product
from django.utils.text import slugify


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
            if response.geturl() != url:
                bar_code = re.search(
                    r'^/(produit|product)/(\d+)/?[0-9a-zA-Z_\-]*/?$',
                    urllib.parse.urlparse(response.geturl()).path).group(2)

                with urllib.request.urlopen(
                        cls.product_url.format(bar_code)) as response2:
                    _dict = json.loads(response2.read().decode('utf8'))
                    if _dict.get('product', None):
                        products = (_dict['product'],)
            else:
                products = json.loads(response.read().decode('utf8'))

                if products.get('count', 0) > 0:
                    products = products['products']

        for product in products:
            wash_product(product)

        return products

    @classmethod
    def get_substitutes(cls, product: dict):
        """Get the best substitutes for a category"""

        substitutes = []
        nutrition_grades = product.get('nutrition_grades', 'e')
        categories = product.get('categories_hierarchy', None)

        if not categories:
            return substitutes

        category = slugify(categories[-1])

        url = cls.marks_for_a_category_url.format(category)
        with urllib.request.urlopen(url) as response:
            if response.geturl() != url:
                category = re.search(r'^/categorie/([0-9a-z_\-]*).json$',
                                     urllib.parse.urlparse(
                                         response.geturl()).path).group(1)

                with urllib.request.urlopen(
                        cls.marks_for_a_category_url.format(
                            category)) as response2:
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

            for substitute in substitutes:
                wash_product(substitute)

        return substitutes

    @classmethod
    def get_product(cls, bar_code: str):
        """Get products from the openfoodfacts API by bar code"""

        with urllib.request.urlopen(
                cls.product_url.format(bar_code)) as response:
            _dict = json.loads(response.read().decode('utf8'))
            if _dict.get('product', None):
                product = _dict['product']
                wash_product(product)
            else:
                product = None

        return product
