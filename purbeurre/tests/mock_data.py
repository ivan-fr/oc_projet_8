import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(BASE_DIR, 'do_research.json')) as f:
    views_1 = f.read()

with open(os.path.join(BASE_DIR, 'get_product.json')) as f:
    views_2 = f.read()

with open(os.path.join(BASE_DIR, 'get_category_nutrition_grades.json')) as f:
    views_3 = f.read()

with open(os.path.join(BASE_DIR, 'get_category_note_a.json')) as f:
    views_4 = f.read()

with open(os.path.join(BASE_DIR, 'get_product_2.json')) as f:
    views_5 = f.read()

mock_data = {
    'views': {
        'https://fr.openfoodfacts.org/cgi/search.pl?search_terms=nutella&'
        'search_simple=1&action=process&page_size=9&json=1': views_1,
        'http://fr.openfoodfacts.org/api/v0'
        '/product/3029330003458.json': views_2,
        'https://fr.openfoodfacts.org/categorie/wholemeal-english-bread'
        '/notes-nutritionnelles.json': views_3,
        'https://fr.openfoodfacts.org/categorie/wholemeal-english-bread'
        '/note-nutritionnelle/a.json': views_4,
        'http://fr.openfoodfacts.org/api/v0/product/3029330003533.json': views_5
    }
}
