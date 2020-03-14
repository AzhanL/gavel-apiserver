from django.shortcuts import render
from django.http import JsonResponse
from datetime import datetime, timedelta
from .lib.webscrape.ManitobaCourtsScraper import ManitobaCourtsScraper


# Create your views here.
def index(request):
    return JsonResponse({'gavel-api-version': '0.0.1'})
