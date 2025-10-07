# main/models.py
from datetime import timezone
from django.contrib.auth.models import User
import uuid
from django.db import models

class Product(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

    CATEGORY_CHOICES = [
        ('fitness', 'Fitness'),
        ('apparel', 'Apparel'),
        ('shoes', 'Shoes'),
        ('outdoor', 'Outdoor'),
        ('ball', 'Ball'),
        ('racket', 'Racket'),
        ('accessories', 'Accessories'),
        ('supplements', 'Supplements'),
        ('others', 'Lainnya'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    price = models.IntegerField()
    description = models.TextField()
    thumbnail = models.URLField(blank=True)  # biar nggak error saat kosong
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='others')
    is_featured = models.BooleanField(default=False)
    stock = models.IntegerField(default=0)
    brand = models.CharField(max_length=50, default="Flexora")

    product_views = models.IntegerField(default=0)

    def __str__(self):
        return self.name
