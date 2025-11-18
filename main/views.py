import datetime
import json
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods
from django.utils.html import strip_tags
from django.db.models import F
from django.contrib.auth.models import User
from django.contrib.auth import login as auth_login

from main.forms import ProductForm
from main.models import Product

# --- VIEWS WEB (HTML) Standard ---
@login_required(login_url='/login')
def show_main(request):
    filter_type = request.GET.get("filter", "all")
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
    context = {'form': form}
    return render(request, "create_product.html", context)

@login_required(login_url='/login')
def show_product(request, id):
    product = get_object_or_404(Product, pk=id)
    Product.objects.filter(pk=id).update(product_views=F('product_views') + 1)
    context = {'product': product}
    return render(request, "product_detail.html", context)

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
    context = {'form': form}
    return render(request, "edit_product.html", context)

def delete_product(request, id):
    product = get_object_or_404(Product, pk=id)
    product.delete()
    return HttpResponseRedirect(reverse('main:show_main'))

def show_xml(request):
     product_list = Product.objects.all()
     xml_data = serializers.serialize("xml", product_list)
     return HttpResponse(xml_data, content_type="application/xml")

def show_xml_by_id(request, product_id):
   try:
       product_item = Product.objects.filter(pk=product_id)
       xml_data = serializers.serialize("xml", product_item)
       return HttpResponse(xml_data, content_type="application/xml")
   except Product.DoesNotExist:
       return HttpResponse(status=404)

# AJAX Handlers untuk WEB
@csrf_exempt
@require_POST
def add_product_entry_ajax(request):
    name = strip_tags(request.POST.get("name", "")).strip()
    description = strip_tags(request.POST.get("description", "")).strip()
    category = request.POST.get("category", "others")
    thumbnail = request.POST.get("thumbnail", "") or ""
    is_featured = request.POST.get("is_featured") == 'on'
    try:
        price = int(request.POST.get("price", "0"))
        stock = int(request.POST.get("stock", "0"))
    except ValueError:
        price = 0; stock = 0
    brand = (request.POST.get("brand") or "").strip() or "Flexora"

    if not name or not description or price <= 0:
        return HttpResponse(b"BAD_REQUEST", status=400)

    new_product = Product(
        user=request.user if request.user.is_authenticated else None,
        name=name, price=price, description=description,
        thumbnail=thumbnail, category=category,
        is_featured=is_featured, stock=stock, brand=brand,
    )
    new_product.save()
    return HttpResponse(b"CREATED", status=201)

@csrf_exempt
def edit_product_entry_ajax(request, id):
    product = get_object_or_404(Product, pk=id)
    if request.method == "POST":
        product.name = strip_tags(request.POST.get("name", "")).strip()
        product.description = strip_tags(request.POST.get("description", "")).strip()
        product.price = int(request.POST.get("price", 0))
        product.category = request.POST.get("category", "others")
        product.save()
        return JsonResponse({'detail': 'UPDATED'}, status=200)
    return JsonResponse({'detail': 'Method not allowed'}, status=405)

@csrf_exempt
def delete_product_entry_ajax(request, id):
    product = get_object_or_404(Product, pk=id)
    if request.method == "POST":
        product.delete()
        return JsonResponse({'detail': 'DELETED'}, status=200)
    return JsonResponse({'detail': 'Method not allowed'}, status=405)


# ==============================================================================
#                  ENDPOINT API KHUSUS FLUTTER (JSON ONLY)
# ==============================================================================

@csrf_exempt
def show_json(request):
    # LOGIKA FILTER: Jika ada parameter filter_user=true, filter by user
    if request.GET.get('filter_user') == 'true' and request.user.is_authenticated:
        product_list = Product.objects.filter(user=request.user)
    else:
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

@csrf_exempt
@require_http_methods(["POST"])
def login_user_ajax(request):
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
        else:
            username = request.POST.get('username')
            password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return JsonResponse({'status': True, 'message': 'Login berhasil!', 'username': user.username}, status=200)
        else:
            return JsonResponse({'status': False, 'message': 'Username atau password salah.'}, status=401)
    except Exception as e:
        return JsonResponse({'status': False, 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def register_ajax(request):
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
        else:
            username = request.POST.get('username')
            password = request.POST.get('password')

        if not username or not password:
            return JsonResponse({'status': False, 'message': 'Data tidak lengkap'}, status=400)
        if User.objects.filter(username=username).exists():
            return JsonResponse({'status': False, 'message': 'Username sudah ada'}, status=409)

        new_user = User.objects.create_user(username=username, password=password)
        new_user.save()
        return JsonResponse({'status': True, 'message': 'Akun berhasil dibuat!'}, status=201)
    except Exception as e:
        return JsonResponse({'status': False, 'message': str(e)}, status=500)

@csrf_exempt
def logout_flutter(request):
    try:
        logout(request)
        return JsonResponse({"status": True, "message": "Logout berhasil!"}, status=200)
    except Exception as e:
        return JsonResponse({"status": False, "message": "Gagal logout."}, status=500)

@csrf_exempt
@require_POST
def create_product_flutter(request):
    try:
        data = json.loads(request.body)
        new_product = Product.objects.create(
            user=request.user,
            name=data["name"],
            price=int(data["price"]),
            description=data["description"],
            category=data["category"],
            thumbnail=data.get("thumbnail", ""),
            is_featured=data["is_featured"],
            stock=int(data.get("stock", 10)),
            brand=data.get("brand", "Flexora"),
        )
        new_product.save()
        return JsonResponse({"status": "success"}, status=200)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

@require_http_methods(["GET"])
def show_json_by_user(request, user_id):
    product_list = Product.objects.filter(user_id=user_id)
    data = [{'id': str(p.id), 'name': p.name, 'price': p.price, 'description': p.description, 'thumbnail': p.thumbnail, 'category': p.category} for p in product_list]
    return JsonResponse(data, safe=False)