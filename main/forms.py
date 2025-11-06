from django.forms import ModelForm
from django import forms
from django.utils.html import strip_tags
from main.models import Product

class ProductForm(ModelForm):
    class Meta:
        model = Product
        fields = ["name", "price", "description", "thumbnail", "category", "is_featured", "stock", "brand"]

    def clean_name(self):
        return strip_tags(self.cleaned_data["name"]).strip()

    def clean_description(self):
        return strip_tags(self.cleaned_data["description"]).strip()

    def clean_price(self):
        price = self.cleaned_data.get("price")
        if price is None or price <= 0:
            raise forms.ValidationError("Price harus > 0")
        return price