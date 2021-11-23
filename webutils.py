import os

from bs4 import BeautifulSoup
import requests
import shutil
import traceback


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


def download(url, filename):
    # https://stackoverflow.com/questions/50096286/how-can-i-download-file-using-pyqt-5-webengine-with-python-script-code

    # gets the filename from the url, and
    # creates the download file absolute path
    # filename = url.split("/")[-1]
    path = filename

    # Defines relevant proxies, see `requests` docs
    # WARNING: Not working and doesn't seem to be necessary in a domestic environment
    proxies = {
      'http': 'http://10.10.1.10:3128',
      'https': 'http://10.10.1.10:1080',
    }

    # Add proxies, and leave `stream=True` for file downloads
    r = requests.get(url, stream=True)  #, proxies=proxies)
    if r.status_code == 200:
        with open(path, 'wb') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)
    else:
        # Manually raise if status code is anything other than 200
        r.raise_for_status()


def downloadB(url: str, dest_folder: str):
    # https://stackoverflow.com/questions/56950987/download-file-from-url-and-save-it-in-a-folder-python

    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)  # create folder if it does not exist

    filename = url.split('/')[-1].replace(" ", "_")  # be careful with file names
    file_path = os.path.join(dest_folder, filename)

    r = requests.get(url, stream=True)
    if r.ok:
        print("saving to", os.path.abspath(file_path))
        with open(file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024 * 8):
                if chunk:
                    f.write(chunk)
                    f.flush()
                    os.fsync(f.fileno())
    else:  # HTTP status code 4XX/5XX
        print("Download failed: status code {}\n{}".format(r.status_code, r.text))
