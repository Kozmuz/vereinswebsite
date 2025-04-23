from django.shortcuts import render

def home(request):
    return render(request, 'main/home.html')

def about(request):
    return render(request, 'main/about.html')

def contact_view(request):
    return render(request, 'main/contact.html')
from django.shortcuts import render, redirect
from .forms import Anmeldeformular

def anmeldung_view(request):
    if request.method == 'POST':
        form = Anmeldeformular(request.POST)
        if form.is_valid():
            form.save()
            return redirect('anmeldung_erfolg')
    else:
        form = Anmeldeformular()
    return render(request, 'main/anmeldung.html', {'form': form})
def anmeldung_erfolg_view(request):
    return render(request, 'main/anmeldung_erfolg.html')