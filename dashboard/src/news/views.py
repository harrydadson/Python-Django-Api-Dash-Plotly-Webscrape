from django.shortcuts import render, redirect

import requests
import urllib3

#requests.packages.urllib3.disable_warnings()

from bs4 import BeautifulSoup
from datetime import timezone, timedelta, datetime

import os
import shutil
import math

from .models import Headline, UserProfile

def news_list(request):
    #user can only scrape once every 24 hours
    user_p = UserProfile.objects.filter(user=request.user).first()
    now = datetime.now(timezone.utc)
    time_diff = now - user_p.last_scrape
    time_diff_hrs = time_diff / timedelta(minutes=60)
    next_scrape = 24 - time_diff_hrs
    if time_diff_hrs <= 24:
        hide_me = True
    else:
        hide_me = False

    headlines = Headline.objects.all()
    context = {
        'objects_list': headlines,
        'hide_me': hide_me,
        'next_scrape': math.ceil(next_scrape)
    }
    return render(request, "news/home.html", context)

# Create your views here.
def scrape(request):
    user_p = UserProfile.objects.filter(user=request.user).first()
    if user_p is not None:
        user_p.last_scrape = datetime.now(timezone.utc)
        user_p.save()

    session = requests.Session()
    session.headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.109 Safari/537.36"}
    url = 'https://www.theonion.com/'

    content = session.get(url, verify=False).content

    soup = BeautifulSoup(content, "html.parser")

    posts = soup.find_all('div', {'class': 'curation-module__item'}) #returns a list

    for i in posts:
        link = i.find_all('a', {'class': 'js_curation-click'})[1]['href']
        title = i.find_all('a', {'class': 'js_curation-click'})[1].text
        image_source = i.find('img', {'class': 'featured-image'})['data-src']

        #stackoverflow solution

        media_root = 'C:/Users/harry/OneDrive/Desktop/DJANGO-CRUD-API/dashboard/media_root'
        if not image_source.startswith(("data;image", "javascript")):
            local_filename = image_source.split('/')[-1].split('?')[0]
            r = session.get(image_source, stream=True, verify=False)
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    f.write(chunk)

            current_image_absolute_path = os.path.abspath(local_filename)
            shutil.move(current_image_absolute_path, media_root)

        new_headline = Headline()
        new_headline.title = title
        new_headline.url = link
        new_headline.image = local_filename
        new_headline.save()

    return redirect('/home/')




