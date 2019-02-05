from purbeurre.models import Brand, Ingredient, Store, Category, Product, \
    ProductSubstituteProduct
from django.db import transaction


class DatabaseManager:
    @classmethod
    def save_product(cls, user, product: dict, substitutes: (tuple, None)):
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
                for category in product.get('categories', ()):
                    category_db, created = Category.objects.get_or_create(
                        name=category)
                    categories.append(category_db)
                product_db.categories.add(*categories)

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

            if substitutes is not None:
                for substitute in substitutes:
                    substitute_db = cls.save_product(user, substitute, None)
                    DatabaseManager.save_link_p_s_p(user, product_db,
                                                    substitute_db)

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
