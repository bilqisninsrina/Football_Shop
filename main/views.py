import datetime
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import HttpResponse
from django.core import serializers
from django.shortcuts import render, redirect, get_object_or_404
from main.forms import ProductForm
from main.models import Product
from django.http import HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db.models import F
from django.utils.html import strip_tags 
from django.views.decorators.http import require_http_methods
from django.contrib.auth import login as auth_login

@login_required(login_url='/login')
def show_main(request):
    filter_type = request.GET.get("filter", "all")  # default 'all'

    if filter_type == "all":
        product_list = Product.objects.all()
    else:
        product_list = Product.objects.filter(user=request.user)

    context = {
        'nama_aplikasi' : 'B-Athletica',
        'name': request.user.username,
        'class': 'PBP C',
        'product_list': product_list,
        'last_login': request.COOKIES.get('last_login', 'Never')
    }

    return render(request, "main.html", context)

def create_product(request):
    form = ProductForm(request.POST or None)

    if form.is_valid() and request.method == 'POST':
            product_entry = form.save(commit = False)
            product_entry.user = request.user
            product_entry.save()
            return redirect('main:show_main')

    context = {
            'form': form
    }
    return render(request, "create_product.html", context)

@login_required(login_url='/login')
def show_product(request, id):
    product = get_object_or_404(Product, pk=id)
    Product.objects.filter(pk=id).update(product_views=F('product_views') + 1)

    context = {
        'product': product
    }

    return render(request, "product_detail.html", context)

def show_xml(request):
     product_list = Product.objects.all()
     xml_data = serializers.serialize("xml", product_list)
     return HttpResponse(xml_data, content_type="application/xml")

def show_json(request):
    product_list = Product.objects.all()
    data = [
        {
            'id': str(p.id),
            'name': p.name,
            'price': p.price,
            'description': p.description,
            'thumbnail': p.thumbnail,
            'category': p.category,
            'stock': p.stock,
            'is_featured': p.is_featured,
            'brand': p.brand,
            'user_id': p.user_id,
            'product_views': p.product_views,
        }
        for p in product_list
    ]
    return JsonResponse(data, safe=False)

def show_xml_by_id(request, product_id):
   try:
       product_item = Product.objects.filter(pk=product_id)
       xml_data = serializers.serialize("xml", product_item)
       return HttpResponse(xml_data, content_type="application/xml")
   except Product.DoesNotExist:
       return HttpResponse(status=404)
   
def show_json_by_id(request, product_id):
    try:
        p = Product.objects.select_related('user').get(pk=product_id)
        data = {
            'id': str(p.id),
            'name': p.name,
            'price': p.price,
            'description': p.description,
            'thumbnail': p.thumbnail,
            'category': p.category,
            'stock': p.stock,
            'is_featured': p.is_featured,
            'brand': p.brand,
            'user_id': p.user_id,
            'user_username': p.user.username if p.user_id else None,
            'product_views': p.product_views,
        }
        return JsonResponse(data)
    except Product.DoesNotExist:
        return JsonResponse({'detail': 'Not found'}, status=404)
        
def register(request):
    form = UserCreationForm()
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your account has been successfully created!')
            return redirect('main:login')
        else:
            messages.error(request, 'Please correct the errors and try again.')
    return render(request, 'register.html', {'form': form})

def login_user(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            response = HttpResponseRedirect(reverse("main:show_main"))
            response.set_cookie('last_login', str(datetime.datetime.now()))
            return response
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm(request)
    return render(request, 'login.html', {'form': form})

def logout_user(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    response = HttpResponseRedirect(reverse('main:login'))
    response.delete_cookie('last_login')
    return response

def edit_product(request, id):
    product = get_object_or_404(Product, pk=id)
    form = ProductForm(request.POST or None, instance=product)
    if form.is_valid() and request.method == 'POST':
        form.save()
        return redirect('main:show_main')

    context = {
        'form': form
    }

    return render(request, "edit_product.html", context)

def delete_product(request, id):
    product = get_object_or_404(Product, pk=id)
    product.delete()
    return HttpResponseRedirect(reverse('main:show_main'))

@csrf_exempt
@require_POST
def add_product_entry_ajax(request):
    # Ambil & sanitize input (ikuti pola tutorial)
    name = strip_tags(request.POST.get("name", "")).strip()
    description = strip_tags(request.POST.get("description", "")).strip()
    category = request.POST.get("category", "others")
    thumbnail = request.POST.get("thumbnail", "") or ""
    is_featured = request.POST.get("is_featured") == 'on'

    # price (int > 0)
    try:
        price = int(request.POST.get("price", "0"))
    except ValueError:
        price = 0

    # stock & brand → gunakan default aman
    try:
        stock = int(request.POST.get("stock", "0"))
    except ValueError:
        stock = 0
    brand = (request.POST.get("brand") or "").strip() or "Flexora"

    if not name or not description or price <= 0:
        return HttpResponse(b"BAD_REQUEST", status=400)

    new_product = Product(
        user=request.user if request.user.is_authenticated else None,
        name=name,
        price=price,
        description=description,
        thumbnail=thumbnail,
        category=category,
        is_featured=is_featured,
        stock=stock,
        brand=brand,
    )
    new_product.save()
    return HttpResponse(b"CREATED", status=201)

@require_http_methods(["POST"])
@login_required(login_url='/login')
def edit_product_entry_ajax(request, id):
    """
    Update product via AJAX.
    Payload: name, price, description, thumbnail, category, is_featured, stock, brand
    """
    product = get_object_or_404(Product, pk=id, user=request.user)

    # bersihkan & parse (ikuti pola tutorial + strip_tags)
    name = strip_tags(request.POST.get("name", "")).strip()
    description = strip_tags(request.POST.get("description", "")).strip()
    category = request.POST.get("category", "others")
    thumbnail = (request.POST.get("thumbnail") or "").strip()
    is_featured = request.POST.get("is_featured") == 'on'

    def to_int(s, default=0):
        try: return int(s)
        except (TypeError, ValueError): return default

    price = to_int(request.POST.get("price"), 0)
    stock = to_int(request.POST.get("stock"), 0)
    brand = (request.POST.get("brand") or "").strip() or "Flexora"

    if not name or not description or price <= 0:
        return JsonResponse({'detail':'BAD_REQUEST'}, status=400)

    product.name = name
    product.price = price
    product.description = description
    product.thumbnail = thumbnail
    product.category = category
    product.is_featured = is_featured
    product.stock = stock
    product.brand = brand
    product.save()

    return JsonResponse({'detail':'UPDATED'}, status=200)


@require_http_methods(["POST"])
@login_required(login_url='/login')
def delete_product_entry_ajax(request, id):
    product = get_object_or_404(Product, pk=id, user=request.user)
    product.delete()
    return JsonResponse({'detail':'DELETED'}, status=200)

@require_http_methods(["POST"])
def login_user_ajax(request):
    form = AuthenticationForm(data=request.POST)
    if form.is_valid():
        user = form.get_user()
        auth_login(request, user)
        resp = JsonResponse({'detail': 'OK', 'username': user.username})
        resp.set_cookie('last_login', str(datetime.datetime.now()))
        return resp
    return JsonResponse({'detail': 'INVALID_CREDENTIALS', 'errors': form.errors}, status=400)


@require_http_methods(["POST"])
def register_ajax(request):
    form = UserCreationForm(request.POST)
    if form.is_valid():
        form.save()
        return JsonResponse({'detail': 'CREATED'}, status=201)
    return JsonResponse({'detail': 'INVALID_FORM', 'errors': form.errors}, status=400)
