#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from bs4 import BeautifulSoup
import requests
import traceback


def getChromecastImages():

    images = {}

    URL = "https://raw.githubusercontent.com/dconnolly/chromecast-backgrounds/master/backgrounds.json"
    headers = {'Accept-Encoding': 'identity'}
    try:
        with requests.get(URL, timeout=20, headers=headers) as response:
            page = response.json()
    except:
        print("Error getting HTML page from:", URL)
        print(traceback.format_exc())
        return images

    images["chromecast"] = page

    return images


def getBingImages():

    images = []

    URL = "https://bing.gifposter.com/list/new/desc/slide.html?p=1"
    headers = {'Accept-Encoding': 'identity'}
    try:
        with requests.get(URL, timeout=20, headers=headers) as response:
            page = response.text
    except:
        print("Error getting HTML page from:", URL)
        print(traceback.format_exc())
        return images

    soup = BeautifulSoup(page, 'html.parser')

    imgEntries = soup.find_all('a', attrs={'itemprop':'contentUrl'})

    for image in imgEntries:
        images.append(image.get('href'))

    return images


def getBingTodayImage():

    image = ""

    URL = "https://bing.gifposter.com"
    headers = {'Accept-Encoding': 'identity'}
    try:
        with requests.get(URL, timeout=20, headers=headers) as response:
            page = response.text
    except:
        print("Error getting HTML page from:", URL)
        print(traceback.format_exc())
        return image

    soup = BeautifulSoup(page, 'html.parser')
    image = soup.find("meta", attrs={"name":"twitter:image"})["content"]

    return image


def download(url: str, filename: str):
    # https://stackoverflow.com/questions/56950987/download-file-from-url-and-save-it-in-a-folder-python

    dest_folder = str(os.sep + filename).rsplit(os.sep)[0]
    if dest_folder and not os.path.exists(dest_folder):
        os.makedirs(dest_folder)

    r = requests.get(url, stream=True, timeout=20)
    if r.ok:
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024 * 8):
                if chunk:
                    f.write(chunk)
                    f.flush()
                    os.fsync(f.fileno())
    else:
        r.raise_for_status()


def ping(url):
    try:
        r = requests.get(url, timeout=20)
    except:
        return False
    return r.ok
