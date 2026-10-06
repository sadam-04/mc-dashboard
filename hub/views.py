from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

# Create your views here.
@login_required
def home(request):
    return render(request, 'hub/index.html')

def secret(request):
    return render(request, 'hub/secret.html')

def map(request):
    return render(request, 'hub/map.html')