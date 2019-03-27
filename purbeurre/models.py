from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    """add category model"""

    name = models.CharField(max_length=200, unique=True)
    searched_substitutes = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Store(models.Model):
    """add Store model"""

    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """add Ingredient model"""

    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name


class Brand(models.Model):
    """add Brand model"""

    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    """add Product model"""

    product_url = "https://fr.openfoodfacts.org/product/{}"

    name = models.CharField(max_length=255)
    generic_name = models.CharField(max_length=255, null=True, blank=True)
    nutrition_grades = models.CharField(max_length=1, null=True, blank=True)
    bar_code = models.CharField(max_length=20, unique=True)
    fat = models.CharField(max_length=5, null=True, blank=True)
    saturated_fat = models.CharField(max_length=5, null=True, blank=True)
    sugars = models.CharField(max_length=5, null=True, blank=True)
    salt = models.CharField(max_length=10, null=True, blank=True)
    image_url = models.URLField(null=True, blank=True)

    brands = models.ManyToManyField(Brand)
    ingredients = models.ManyToManyField(Ingredient)
    stores = models.ManyToManyField(Store)
    categories = models.ManyToManyField(Category, through='ProductCategory')
    substitutes = models.ManyToManyField('self',
                                         through='ProductSubstituteProduct',
                                         through_fields=('from_product',
                                                         'to_product'),
                                         symmetrical=False)

    def get_openfoodfacts_url(self):
        return self.product_url.format(self.bar_code)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return self.name


class ProductCategory(models.Model):
    """ add ProductCategory model """

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    hierarchy = models.IntegerField(default=1)


class ProductSubstituteProduct(models.Model):
    """add ProductSubstituteProduct model"""

    from_product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                     related_name='from_product')
    to_product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                   related_name="to_product")
    users = models.ManyToManyField(User)

    class Meta:
        unique_together = (('from_product', 'to_product'),)
