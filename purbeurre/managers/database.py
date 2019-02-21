from purbeurre.models import Brand, Ingredient, Store, Category, Product, \
    ProductSubstituteProduct, ProductCategory
from django.db import transaction
import string


class DatabaseManager:
    @classmethod
    def save_product(cls, product: dict, substitutes: (tuple, None) = None,
                     user=None):
        """Save a product and his substitutes in the database."""

        nutriments = product.get('nutriments', {})
        with transaction.atomic():
            product_db, created = Product.objects.get_or_create(
                name=product.get('product_name', None),
                generic_name=product.get('generic_name', None),
                nutrition_grades=product.get('nutrition_grades', None),
                bar_code=product['code'],
                fat=str(nutriments.get('fat_100g', None)),
                saturated_fat=str(nutriments.get('saturated-fat_100g', None)),
                sugars=str(nutriments.get('sugars_100g', None)),
                salt=str(nutriments.get('salt_100g', None)),
                image_url=product.get('image_url', None)
            )

            if created:
                categories = []
                for category in reversed(
                        product.get('categories_hierarchy', ())):
                    category_db, created = Category.objects.get_or_create(
                        name=category)
                    categories.append(category_db)
                ProductCategory.objects.bulk_create(
                    [ProductCategory(product=product_db, category=category,
                                     hierarchy=i)
                     for i, category in enumerate(categories, start=1)]
                )

                ingredients = []
                iteration_ingredients = ()
                if product.get('ingredients_text_fr', ()):
                    iteration_ingredients = product.get('ingredients_text_fr')
                elif product.get('ingredients', ()):
                    iteration_ingredients = product.get('ingredients')

                for ingredient in iteration_ingredients:
                    ingredient_db, created = Ingredient.objects.get_or_create(
                        name=ingredient)
                    ingredients.append(ingredient_db)

                product_db.ingredients.add(*ingredients)

                brands = []
                for brand in product.get('brands_tags', ()):
                    brand_db, created = Brand.objects.get_or_create(name=brand)
                    brands.append(brand_db)
                product_db.brands.add(*brands)

                stores = []
                for store in product.get('stores_tags', ()):
                    store_db, created = Store.objects.get_or_create(name=store)
                    stores.append(store_db)
                product_db.stores.add(*stores)

            if substitutes is not None and user is not None:
                for substitute in substitutes:
                    substitute_db = cls.save_product(substitute)
                    cls.save_link_p_s_p(user, product_db, substitute_db)

        return product_db

    @staticmethod
    def save_link_p_s_p(user, product_db, substitute_db):
        """save relationship beetween products"""

        if product_db.id != substitute_db.id:
            p_s_p_db, created = ProductSubstituteProduct.objects.get_or_create(
                from_product=product_db,
                to_product=substitute_db,
            )

            p_s_p_db.users.add(user)
        else:
            raise Exception('Product and substitute cannot be the same.')

    @classmethod
    def save_substitutes(cls, category, substitutes):

        with transaction.atomic():
            Category.objects.update_or_create(
                name=category,
                searched_substitutes=True
            )

            for substitute in substitutes:
                cls.save_product(substitute)

    @classmethod
    def get_substitutes(cls, product):
        category = product.categories.filter(searched_substitutes=True,
                                             productcategory__hierarchy=1) \
            .first()

        subsitutes = None

        if category:
            return cls.generate_substitutes(product.bar_code,
                                            product.nutrition_grades or 'e',
                                            category)

        return subsitutes

    @classmethod
    def get_substitutes_from_api(cls, product):
        subsitutes = None

        category_expected = product.get('categories_hierarchy', None)

        if not category_expected:
            return subsitutes

        category = Category.objects.filter(searched_substitutes=True,
                                           name=category_expected[-1]).first()

        if category:
            return cls.generate_substitutes(product['code'],
                                            product.get('nutrition_grades',
                                                        'e'),
                                            category)

        return subsitutes

    @classmethod
    def generate_substitutes(cls, bar_code, nutrition_grades, category):
        if nutrition_grades.lower() == 'a':
            subsitutes = Product.objects.filter(categories=category,
                                                nutrition_grades='a') \
                             .exclude(bar_code=bar_code).order_by(
                'nutrition_grades')[:9]
        else:
            _ascii = list(string.ascii_lowercase)
            _ascii = _ascii[:_ascii.index(nutrition_grades.lower())]

            subsitutes = Product.objects.filter(categories=category,
                                                nutrition_grades__in=_ascii) \
                             .exclude(bar_code=bar_code).order_by(
                'nutrition_grades')[:9]

        return subsitutes
