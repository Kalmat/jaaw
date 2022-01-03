# Jaaw! - Just Anoher Animated Wallpaper

## What is this for

This is a python3 cross-platform script, based on PyQt5, compatible with Windows 8-10, macOS (>= High Sierra) and Linux Mint (by the moment)

It will allow you to customize your desktop wallpaper, using an image, a folder (Carousel-mode) or a VIDEO!

Furthermore, you won't need any Admin privileges to install it (it's fully portable) or use it.

## Requires

KalmaTools v.0.0.1 or higher, that you can find here: https://bitbucket.org/Kalmat/kalmatools

Download the wheel file located on dist folder, and install it on your system or virtual environment (venv) using:

    pip install kalmatools-0.0.1-py3-none-any.whl

## How to use it

Run it, and right-click on the Jaaw! tray icon to access options menu:

* Image / Single image - Select an image as static Wallpaper
* Image / Folder - Select a folder containing all images you want to show in carousel mode
* Video / Local - Select a local video file to show as wallpaper... looks awesome!
* Video / YouTube - YES! Enter a YT video URL and play it in the background!!! (Try the "pre-loaded" videos to start)
* Web / Chromecast random daily image (links from: https://bing.gifposter.com)
* Web / Bing image of the day (links from: https://github.com/dconnolly/chromecast-backgrounds/blob/master/backgrounds.json)
* Web / Enter any URL of your choice and use it as wallpaper (if compatible)
* Help
* Quit

#### IMPORTANT

This module stores no images or videos from any web site or source of any kind. It just uses public links to show them as your wallpaper

The application and tray icons are... well, horrible. I have no graphic design capabilities at all. Download or design your own! Don't forget to place them on "resources" folder and rename them accordingly (Jaaw.ico, Jaaw.png)

#### LINUX WARNING

If you get this error: 

    defaultServiceProvider::requestService(): no service found for - "org.qt-project.qt.mediaplayer"

- Install pyqt5 plugins (run this on a terminal):


    sudo apt-get install libqt5-multimedia-plugins

- Also install all codecs from App Store: gstreamer-qt5, gstreamer-bad, gstreamer-ugly, ubuntu-restricted-extras, gstreamer-ffmpeg
