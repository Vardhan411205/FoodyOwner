from django.db import models

class FoodItem(models.Model):
    CATEGORY_CHOICES = [
        ('fruits', 'Fruits & Vegetables'),
        ('dairy', 'Dairy & Breakfast'),
        ('snacks', 'Snacks & Munchies'),
        ('beverages', 'Cold Drinks & Juices'),
        ('staples', 'Atta, Rice & Dal'),
        ('spices', 'Masala & Spices'),
        ('cleaning', 'Cleaning Essentials'),
        ('personal_care', 'Personal Care'),
        ('baby_care', 'Baby Care'),
        ('home_kitchen', 'Home & Kitchen'),
        ('paan_corner', 'Paan Corner'),
        ('pharma_wellness', 'Pharma & Wellness'),
        ('electronics', 'Electronics & Accessories'),
        ('beauty', 'Beauty & Makeup'),
        ('pet_supplies', 'Pet Care'),
        ('meat_fish', 'Meat & Fish'),
        ('instant_food', 'Ready to Cook & Eat'),
        ('bakery', 'Bakery & Biscuits'),
        ('household', 'Household Items'),
    ]

    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    image_url = models.URLField()
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']
