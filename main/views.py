from django.shortcuts import render

# Create your views here.
def show_main(request):
    context = {
        'nama_aplikasi' : 'Bili Shop',
        'name': 'Bilqis Nisrina Dzahabiyah Mulyadi',
        'class': 'PBP C'
    }

    return render(request, "main.html", context)