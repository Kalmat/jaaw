#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import platform
import random
import time
import json
import sys
import qtutils
import bkgutils
import utils
import webutils
from PyQt5 import QtWidgets, QtCore, QtGui, QtMultimedia, QtMultimediaWidgets, QtWebEngineWidgets
import signal
import traceback

_CAPTION = "Jaaw!"  # Just Another Animated Wallpaper!
_CONFIG_ICON = utils.resource_path("resources/Jaaw.png")
_SYSTEM_ICON = utils.resource_path("resources/Jaaw.ico")
_ICON_SELECTED = utils.resource_path("resources/tick.png")
_ICON_NOT_SELECTED = utils.resource_path("resources/notick.png")
_SETTINGS_FILE = "settings.json"

_IMGMODE = "IMAGE"
_IMGFIXED = "FIXED"
_IMGCAROUSEL = "CAROUSEL"
_VIDMODE = "VIDEO"
_VIDLOCAL = "LOCAL"
_VIDYT = "YOUTUBE"
_WEBMODE = "WEB"
_CHROMEMODE = "CHROME"
_BINGMODE = "BING"
_URLMODE = "URL"

_SETTINGS_WARNING = 1
_IMG_WARNING = 2
_FOLDER_WARNING = 3
_VID_WARNING = 4
_YT_WARNING = 5
_CHROME_WARNING = 6
_BING_WARNING = 7
_WEB_WARNING = 8
_HELP_MSG = 9


class Window(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        QtWidgets.QMainWindow.__init__(self, *args, **kwargs)

        self.xmax, self.ymax = qtutils.getScreenSize()
        self.setupUi()
        qtutils.initDisplay(parent=self, setAsWallpaper=True, icon=_SYSTEM_ICON, caption=_CAPTION)

        self.isWindows = "Windows" in platform.platform()
        self.isLinux = "Linux" in platform.platform()
        self.isMacOS = "macOS" in platform.platform() or "Darwin" in platform.platform()

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.loadNextImg)

        self.imgList = []
        self.imgIndex = 0
        self.chrome = {"chromecast": []}

        self.loadSettings()

        self.menu = Config(self, self.config)
        self.menu.reloadSettings.connect(self.reloadSettings)
        self.menu.closeAll.connect(self.closeAll)
        self.menu.showHelp.connect(self.showHelp)
        self.menu.show()

        if self.isWindows or self.isLinux:
            bkgutils.sendBehind(_CAPTION)
        self.start()

    def setupUi(self):

        self.setGeometry(0, 0, self.xmax, self.ymax)
        self.setStyleSheet("background-color:transparent")

        self.widget = QtWidgets.QWidget(self)
        self.widget.setGeometry(0, 0, self.xmax, self.ymax)
        self.myLayout = QtWidgets.QHBoxLayout()
        self.myLayout.setContentsMargins(0, 0, 0, 0)

        self.bkg_label = QtWidgets.QLabel()
        self.bkg_label.hide()
        self.bkg_label.setGeometry(0, 0, self.xmax, self.ymax)
        self.bkg_label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)

        # Reduce CPU?
        #        Explorer.exe shell:appsFolder\Microsoft.ZuneVideo_8wekyb3d8bbwe!Microsoft.ZuneVideo
        #        https://stackoverflow.com/questions/57015932/how-to-attach-and-detach-an-external-app-with-pyqt5-or-dock-an-external-applicat
        # LINUX: If you get this error: defaultServiceProvider::requestService(): no service found for - "org.qt-project.qt.mediaplayer"
        #        Run: sudo apt-get install libqt5-multimedia-plugins
        #        Also install all codecs: gstreamer-qt5, gstreamer-bad, gstreamer-ugly, ubuntu-restricted-extras, gstreamer-ffmpeg
        self.mediaPlayer = QtMultimedia.QMediaPlayer(None, QtMultimedia.QMediaPlayer.VideoSurface)
        self.mediaPlayer.setMuted(True)
        self.playlist = QtMultimedia.QMediaPlaylist()
        self.playlist.setPlaybackMode(QtMultimedia.QMediaPlaylist.CurrentItemInLoop)
        self.videoWidget = QtMultimediaWidgets.QVideoWidget()
        self.videoWidget.hide()
        self.videoWidget.setGeometry(0, 0, self.xmax, self.ymax)
        # Use this to adjust to the screen (but possibly distorting the video)
        # self.videoWidget.setAspectRatioMode(QtCore.Qt.IgnoreAspectRatio)
        self.mediaPlayer.setVideoOutput(self.videoWidget)
        self.mediaPlayer.error.connect(self.handlePlayError)

        self.webView = QtWebEngineWidgets.QWebEngineView()
        self.webView.hide()
        self.webView.setGeometry(0, 0, self.xmax, self.ymax)
        self.webFrame = self.webView.page()
        self.webFrame.setAudioMuted(True)
        # Use this to adjust page/video to screen (but possibly cutting the page/video)
        # self.webFrame.setZoomFactor(1.5)

        self.myLayout.addWidget(self.bkg_label)
        self.myLayout.addWidget(self.videoWidget)
        self.myLayout.addWidget(self.webView)
        self.widget.setLayout(self.myLayout)
        self.setCentralWidget(self.widget)

        self.msgBox = QtWidgets.QMessageBox()

    def loadSettings(self):

        if os.path.isfile(_SETTINGS_FILE):
            file = _SETTINGS_FILE
        else:
            file = utils.resource_path("resources/" + _SETTINGS_FILE)

        try:
            with open(file, encoding='UTF-8') as file:
                self.config = json.load(file)
        except:
            pass

        self.loadSettingsValues()

    def loadSettingsValues(self):
        self.wallPaperMode = self.config["mode"]
        self.imgMode = self.config["img_mode"]
        self.img = self.config["img"]
        self.contentFolder = self.config["folder"]
        self.imgPeriods = self.config["Available_periods"]
        self.imgPeriod = self.config["img_period"]
        self.videoMode = self.config["video_mode"]
        self.video = self.config["video"]
        index = self.config["yt_index"] if 0 <= self.config["yt_index"] < len(self.config["yt_url"]) else 0
        self.ytUrl = self.config["yt_url"][index]
        try:
            ytRef = self.ytUrl.split("watch?v=")[1].split("&")[0]
        except:
            try:
                ytRef = self.ytUrl.split("playlist=")[1].split("&")[0]
            except:
                ytRef = "BHACKCNDMW8"
                self.showWarning(_YT_WARNING)
        # Remove &qv=hd720 in case videos with lower quality do not load
        self.ytUrlEmbed = "https://www.youtube.com/embed/%s?autoplay=1&loop=1&playlist=%s&mute=1&controls=0&rel=0&qv=hd720" \
                          % (ytRef, ytRef)
        self.webMode = self.config["web_mode"]
        self.chromeLast = self.config["chrome_last"]
        self.bingLast = self.config["bing_last"]
        index = self.config["url_index"] if 0 <= self.config["url_index"] < len(self.config["url"]) else 0
        self.url = self.config["url"][index]

        self.vidWarned = False

    @QtCore.pyqtSlot()
    def reloadSettings(self):
        self.timer.stop()
        self.loadSettings()
        self.start()

    def start(self):

        self.setGeometry(0, 0, self.xmax, self.ymax)

        if self.wallPaperMode == _IMGMODE:

            if self.imgMode == _IMGCAROUSEL:
                self.imgList = utils.getFilesInFolder(self.contentFolder, ("png", "jpg", "jpeg", "bmp"))
                self.timer.start(self.imgPeriod * 1000)
                self.loadNextImg()

            elif self.imgMode == _IMGFIXED:
                self.loadImg(self.img)

            else:
                self.showWarning(_SETTINGS_WARNING)

        elif self.wallPaperMode == _VIDMODE:
            if self.videoMode == _VIDLOCAL:
                self.loadVideo(self.video)
            elif self.videoMode == _VIDYT:
                self.loadWebPage(self.ytUrlEmbed)

        elif self.wallPaperMode == _WEBMODE:
            if self.webMode == _CHROMEMODE:
                self.loadChrome()
            elif self.webMode == _BINGMODE:
                self.loadBing()
            elif self.webMode == _URLMODE:
                self.loadWebPage(self.url)

        else:
            self.showWarning(_SETTINGS_WARNING)

    def loadImg(self, img, keepAspect=True, expand=True):

        error = False
        if img:
            pixmap = qtutils.resizeImageWithQT(img, self.xmax, self.ymax, keepAspectRatio=keepAspect, expand=expand)
            if not pixmap.isNull():
                self.bkg_label.clear()
                self.mediaPlayer.stop()
                self.playlist.clear()
                self.mediaPlayer.setPlaylist(self.playlist)
                self.videoWidget.hide()
                self.webView.stop()
                self.webView.hide()
                self.bkg_label.setPixmap(pixmap)
                self.move(QtCore.QPoint(0, 0 + int((self.ymax - pixmap.height())/2)))
                self.bkg_label.show()
            else:
                error = True
        else:
            error = True

        if error:
            self.showWarning(_IMG_WARNING)

    def loadNextImg(self):
        if self.imgList:
            self.loadImg(self.imgList[self.imgIndex])
            self.imgIndex = (self.imgIndex + 1) % len(self.imgList)
        else:
            self.showWarning(_FOLDER_WARNING)

    def loadVideo(self, video):
        self.playlist.clear()
        self.playlist.addMedia(QtMultimedia.QMediaContent(QtCore.QUrl.fromLocalFile(video)))
        self.mediaPlayer.setPlaylist(self.playlist)
        self.bkg_label.hide()
        self.webView.stop()
        self.webView.hide()
        self.setGeometry(QtCore.QRect(0, 0, self.xmax, self.ymax))
        self.videoWidget.show()
        self.mediaPlayer.play()
        self.videoWidget.setGeometry(QtCore.QRect(0, 0, self.xmax, self.ymax))

    def loadChrome(self):
        filename = "032k-8738jd7-00"
        if self.isMacOS:
            filename = utils.resource_path(filename)
        current = time.strftime("%Y%m%d")
        found = True
        if not os.path.isfile(filename) or self.chromeLast < current:
            self.chromeLast = current
            if not self.chrome["chromecast"]:
                self.chrome = webutils.getChromecastImages()
            rand = random.Random()
            index = rand.randint(0, len(self.chrome["chromecast"]))
            found = False
            tries = 0
            while not found and tries < 10:
                img = self.chrome["chromecast"][index]["url"]
                try:
                    # self.webFrame.download(QtCore.QUrl(img), filename)
                    webutils.download(img, filename)
                    found = True
                except:
                    index = rand.randint(0, len(self.chrome["chromecast"]))
                    tries += 1
        if found:
            self.loadImg(filename)
            self.menu.saveLast(chrome=self.chromeLast)
        else:
            self.showWarning(_CHROME_WARNING)

    def loadBing(self):
        filename = "032k-8738jd7-01"
        if self.isMacOS:
            filename = utils.resource_path(filename)
        current = time.strftime("%Y%m%d")
        found = True
        if not os.path.isfile(filename) or self.bingLast < current:
            self.bingLast = current
            img = webutils.getBingTodayImage()
            try:
                # self.webFrame.download(QtCore.QUrl(img), filename)
                webutils.download(img, filename)
            except:
                images = webutils.getBingImages()
                rand = random.Random()
                index = rand.randint(0, len(images))
                found = False
                tries = 0
                while not found and tries < 10:
                    try:
                        # self.webFrame.download(QtCore.QUrl(img), filename)
                        webutils.download(images[index], filename)
                        found = True
                    except:
                        index = rand.randint(0, len(images))
                        tries += 1
        if found:
            self.loadImg(filename)
            self.menu.saveLast(bing=self.bingLast)
        else:
            self.showWarning(_BING_WARNING)

    def loadWebPage(self, url):
        self.bkg_label.hide()
        self.videoWidget.hide()
        self.mediaPlayer.stop()
        self.playlist.clear()
        self.mediaPlayer.setPlaylist(self.playlist)
        self.webView.stop()
        try:
            self.webView.load(QtCore.QUrl(url))
            self.webView.show()
        except:
            self.showWarning(_WEB_WARNING)

    @QtCore.pyqtSlot()
    def showHelp(self):
        self.showWarning(_HELP_MSG)

    def handlePlayError(self):
        if not self.vidWarned:
            self.showWarning(_VID_WARNING)
            self.vidWarned = True

    def fallback(self):
        self.bkg_label.hide()
        if self.mediaPlayer.isVideoAvailable():
            self.mediaPlayer.stop()
        self.playlist.clear()
        self.mediaPlayer.setPlaylist(self.playlist)
        self.videoWidget.hide()
        self.webView.stop()
        self.webView.hide()
        self.setGeometry(0, 0, 1, 1)

    def showWarning(self, msg):

        if msg == _SETTINGS_WARNING:
            self.msgBox.setIcon(QtWidgets.QMessageBox.Warning)
            self.msgBox.setText("Configure your own settings and media to use as wallpaper\n"
                                "Right-click the Jaaw! tray icon to open settings")
            self.msgBox.setWindowTitle("Jaaw! Warning")
            self.msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            self.msgBox.exec_()
            self.fallback()

        elif msg == _IMG_WARNING:
            self.msgBox.setIcon(QtWidgets.QMessageBox.Warning)
            self.msgBox.setText("Image not supported, moved or corrupted")
            self.msgBox.setWindowTitle("Jaaw! Warning")
            self.msgBox.setDetailedText("Right-click the Jaaw! tray icon to open settings and select a new one")
            self.msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            self.msgBox.exec_()
            self.fallback()

        elif msg == _FOLDER_WARNING:
            self.msgBox.setIcon(QtWidgets.QMessageBox.Warning)
            self.msgBox.setText("Folder contains no valid images to show")
            self.msgBox.setWindowTitle("Jaaw! Warning")
            self.msgBox.setDetailedText("Right-click the Jaaw! tray icon to open settings and select a new one")
            self.msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            self.timer.stop()
            self.msgBox.exec_()
            self.fallback()

        elif msg == _VID_WARNING:
            self.msgBox.setIcon(QtWidgets.QMessageBox.Warning)
            self.msgBox.setText("Video not supported, moved or corrupted")
            self.msgBox.setWindowTitle("Jaaw! Warning")
            self.msgBox.setDetailedText("Right-click the Jaaw! tray icon to open settings and select a new one\n"
                                        + str(self.mediaPlayer.error()) + self.mediaPlayer.errorString())
            self.msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            self.msgBox.exec_()
            self.fallback()

        elif msg == _CHROME_WARNING:
            self.msgBox.setIcon(QtWidgets.QMessageBox.Warning)
            self.msgBox.setText("Unable to download Chromecast image!")
            self.msgBox.setWindowTitle("Jaaw! Warning")
            self.msgBox.setDetailedText("Maybe web site is down or your Internet connection is not available now")
            self.msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            self.msgBox.exec_()
            self.fallback()

        elif msg == _BING_WARNING:
            self.msgBox.setIcon(QtWidgets.QMessageBox.Warning)
            self.msgBox.setText("Unable to download Bing image!")
            self.msgBox.setWindowTitle("Jaaw! Warning")
            self.msgBox.setDetailedText("Maybe web site is down or your Internet connection is not available now")
            self.msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            self.msgBox.exec_()
            self.fallback()

        elif msg == _YT_WARNING:
            self.msgBox.setIcon(QtWidgets.QMessageBox.Warning)
            self.msgBox.setText("URL doesn't exist or it's malformed!")
            self.msgBox.setWindowTitle("Jaaw! Warning")
            self.msgBox.setDetailedText("Be sure the URL exists and looks like 'https://youtube.com/watch?v=XXXXXXXXXXX'")
            self.msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            self.msgBox.exec_()
            self.fallback()

        elif msg == _HELP_MSG:
            self.msgBox.setIcon(QtWidgets.QMessageBox.Information)
            self.msgBox.setText("Right-click the Jaaw! icon in your system tray or taskbar "
                                "to enter configuration settings")
            self.msgBox.setWindowTitle("Jaaw! Help")
            self.msgBox.setDetailedText("Image mode will allow you to select one single image or a folder "
                                        "to show all images inside as a carousel, and its changing interval\n\n"
                                        "Video mode will let you set a local or YouTube video as your "
                                        "wallpaper, for a fully customized and totally awesome aspect!\n\n"
                                        "Web mode will let you choose a Chromecast daily random image, "
                                        "the Bing image of the day, or even an URL! (*)\n"
                                        "(*) Bear in mind you won't be able to interact with the web page")
            self.msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            self.msgBox.exec_()

    def closeEvent(self, event):
        self.closeAll()
        super(Window, self).closeEvent(event)

    @QtCore.pyqtSlot()
    def closeAll(self):
        QtWidgets.QApplication.quit()


class Config(QtWidgets.QWidget):

    reloadSettings = QtCore.pyqtSignal()
    closeAll = QtCore.pyqtSignal()
    showHelp = QtCore.pyqtSignal()

    def __init__(self, parent, config):
        QtWidgets.QWidget.__init__(self, parent)

        self.isWindows = "Windows" in platform.platform()
        self.isLinux = "Linux" in platform.platform()
        self.isMacOS = "macOS" in platform.platform() or "Darwin" in platform.platform()

        self.config = config
        self.setupUI()

    def setupUI(self):

        self.setGeometry(-1, -1, 1, 1)

        self.iconSelected = QtGui.QIcon(_ICON_SELECTED)
        self.iconNotSelected = QtGui.QIcon(_ICON_NOT_SELECTED)

        self.contextMenu = QtWidgets.QMenu(self)
        if self.isWindows:
            self.contextMenu.setStyleSheet("""
                QMenu {border: 1px inset #666; font-size: 18px; background-color: #333; color: #fff; padding: 10px;}
                QMenu:selected {background-color: #666; color: #fff;}""")
        self.imgAct = self.contextMenu.addMenu("Image")
        self.fimgAct = self.imgAct.addAction("Single Image", self.openSingleImage)
        self.cimgAct = self.imgAct.addMenu("Images carousel")
        self.imgfAct = self.cimgAct.addAction("Select folder", self.openFolder)
        self.pimgAct = self.cimgAct.addMenu("Select carousel interval")
        imgPeriod = self.config["img_period"]
        periods = self.config["Available_periods"]
        for key in periods.keys():
            self.addPeriodOpts(self.pimgAct, key, periods[key], selected=(imgPeriod == periods[key]))

        self.videoAct = self.contextMenu.addMenu("Video")
        self.lvideoAct = self.videoAct.addAction("Local video file", self.openVideo)
        self.yvideoAct = self.videoAct.addMenu("YouTube video")
        ytUrls = self.config["yt_url"]
        ytUrl = self.config["yt_url"][self.config["yt_index"] if 0 <= self.config["yt_index"] < len(ytUrls) else 0]
        self.yvideoAct.addAction("-- Enter New Youtube Video URL --", self.addNewYt)
        for item in ytUrls:
            self.addYtOpts(self.yvideoAct, item, selected=(ytUrl == item))

        self.webAct = self.contextMenu.addMenu("Web")
        self.chromeAct = self.webAct.addAction("Chromecast daily random", self.openChromecast)
        self.bingAct = self.webAct.addAction("Bing image of the day", self.openBing)
        self.uwebAct = self.webAct.addMenu("Web page")

        urls = self.config["url"]
        url = self.config["url"][self.config["url_index"] if 0 <= self.config["url_index"] < len(urls) else 0]
        self.uwebAct.addAction("-- Enter New Web Page URL --", self.addNewUrl)
        for item in urls:
            self.addUrlOpts(self.uwebAct, item, selected=(url == item))

        self.contextMenu.addSeparator()
        self.helpAct = self.contextMenu.addAction("Help", self.sendShowHelp)
        self.quitAct = self.contextMenu.addAction("Quit", self.sendCloseAll)

        self.updateCheck()

        self.trayIcon = QtWidgets.QSystemTrayIcon(QtGui.QIcon(_CONFIG_ICON), self)
        self.trayIcon.setToolTip("Jaaw!")
        self.trayIcon.setContextMenu(self.contextMenu)
        self.trayIcon.show()

        self.imgDialog = QtWidgets.QFileDialog()
        self.imgDialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        self.imgDialog.setWindowTitle("Select Image")
        self.imgDialog.setNameFilter("Image Files (*.png *.jpg *.jpeg *.bmp)")

        self.folderDialog = QtWidgets.QFileDialog()
        self.folderDialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
        self.folderDialog.setWindowTitle("Select images folder")

        self.videoDialog = QtWidgets.QFileDialog()
        self.videoDialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        self.videoDialog.setWindowTitle("Select video")
        self.videoDialog.setNameFilter("Video Files (*.flv *.ts *.mts *.avi *.wmv *.mp4)")

        self.ytDialog = QtWidgets.QDialog()
        self.ytDialog.setWindowTitle("Enter YouTube URL")
        self.ytDialog.setWhatsThis("Enter Youtube URL\nBe aware some videos may not work")
        self.ytDialog.setStyleSheet("background-color: #333; color: #ddd;")
        ytLayout = QtWidgets.QHBoxLayout()
        self.ytEdit = QtWidgets.QLineEdit()
        self.ytEdit.setMinimumWidth(400)
        self.ytButton = QtWidgets.QPushButton("Go")
        self.ytButton.setStyleSheet("background-color: #333; border:1px solid #ddd;; color: #ddd;")
        self.ytButton.setMinimumWidth(40)
        self.ytButton.clicked.connect(self.openYT)
        ytLayout.addWidget(self.ytEdit)
        ytLayout.addWidget(self.ytButton)
        self.ytDialog.setLayout(ytLayout)

        self.urlDialog = QtWidgets.QDialog()
        self.urlDialog.setWindowTitle("Enter URL")
        self.urlDialog.setWhatsThis("Enter URL\nBe aware you won't be able to interact!")
        self.urlDialog.setStyleSheet("background-color: #333; color: #ddd;")
        urlLayout = QtWidgets.QHBoxLayout()
        self.urlEdit = QtWidgets.QLineEdit()
        self.urlEdit.setMinimumWidth(400)
        self.urlButton = QtWidgets.QPushButton("Go")
        self.urlButton.setStyleSheet("background-color: #333; border:1px solid #ddd;; color: #ddd;")
        self.urlButton.setMinimumWidth(40)
        self.urlButton.clicked.connect(self.openURL)
        urlLayout.addWidget(self.urlEdit)
        urlLayout.addWidget(self.urlButton)
        self.urlDialog.setLayout(urlLayout)
        
    def addPeriodOpts(self, option, text, value, selected=False):
        act = option.addAction(text, (lambda: self.execPeriodAct(text, value)))
        if selected:
            act.setIcon(self.iconSelected)
        else:
            act.setIcon(self.iconNotSelected)

    def execPeriodAct(self, text, interval):
        for option in self.pimgAct.actions():
            if option.text() == text:
                option.setIcon(self.iconSelected)
            else:
                option.setIcon(self.iconNotSelected)
        self.pimgAct.update()
        self.config["img_period"] = int(interval)
        self.saveSettings()

    def addYtOpts(self, option, text, selected=False):
        act = option.addAction(text, (lambda: self.execYtAct(text)))
        if selected:
            act.setIcon(self.iconSelected)
        else:
            act.setIcon(self.iconNotSelected)

    def execYtAct(self, text):
        self.config["mode"] = _VIDMODE
        self.config["video_mode"] = _VIDYT
        for i, option in enumerate(self.yvideoAct.actions()):
            if i > 0 and option.text() == text:
                option.setIcon(self.iconSelected)
                self.config["yt_index"] = i - 1
            else:
                option.setIcon(self.iconNotSelected)
        self.yvideoAct.update()
        self.updateCheck()
        self.saveSettings()

    def addNewYt(self):
        self.ytDialog.show()

    def addUrlOpts(self, option, text, selected=False):
        act = option.addAction(text, (lambda: self.execUrlAct(text)))
        if selected:
            act.setIcon(self.iconSelected)
        else:
            act.setIcon(self.iconNotSelected)

    def execUrlAct(self, text):
        self.config["mode"] = _WEBMODE
        self.config["web_mode"] = _URLMODE
        for i, option in enumerate(self.uwebAct.actions()):
            if i > 0 and option.text() == text:
                option.setIcon(self.iconSelected)
                self.config["url_index"] = i - 1
            else:
                option.setIcon(self.iconNotSelected)
        self.uwebAct.update()
        self.updateCheck()
        self.saveSettings()

    def addNewUrl(self):
        self.urlDialog.show()

    def updateCheck(self):

        self.imgAct.setIcon(self.iconNotSelected)
        self.fimgAct.setIcon(self.iconNotSelected)
        self.cimgAct.setIcon(self.iconNotSelected)
        self.videoAct.setIcon(self.iconNotSelected)
        self.lvideoAct.setIcon(self.iconNotSelected)
        self.yvideoAct.setIcon(self.iconNotSelected)
        self.webAct.setIcon(self.iconNotSelected)
        self.chromeAct.setIcon(self.iconNotSelected)
        self.bingAct.setIcon(self.iconNotSelected)
        self.uwebAct.setIcon(self.iconNotSelected)

        if self.config["mode"] == _IMGMODE:
            self.imgAct.setIcon(self.iconSelected)
            if self.config["img_mode"] == _IMGFIXED:
                self.fimgAct.setIcon(self.iconSelected)
            elif self.config["img_mode"] == _IMGCAROUSEL:
                self.cimgAct.setIcon(self.iconSelected)

        elif self.config["mode"] == _VIDMODE:
            self.videoAct.setIcon(self.iconSelected)
            if self.config["video_mode"] == _VIDLOCAL:
                self.lvideoAct.setIcon(self.iconSelected)
            elif self.config["video_mode"] == _VIDYT:
                self.yvideoAct.setIcon(self.iconSelected)

        elif self.config["mode"] == _WEBMODE:
            self.webAct.setIcon(self.iconSelected)
            if self.config["web_mode"] == _CHROMEMODE:
                self.chromeAct.setIcon(self.iconSelected)
            elif self.config["web_mode"] == _BINGMODE:
                self.bingAct.setIcon(self.iconSelected)
            elif self.config["web_mode"] == _URLMODE:
                self.uwebAct.setIcon(self.iconSelected)

        self.contextMenu.update()

    def openSingleImage(self):

        fileName = ""
        folder = os.path.dirname(self.config["img"])
        if not os.path.isdir(folder):
            folder = "."
        self.imgDialog.setDirectory(folder)
        if self.imgDialog.exec_() == QtWidgets.QFileDialog.Accepted:
            fileName = self.imgDialog.selectedFiles()[0]

        if fileName:
            self.config["img"] = fileName
            self.config["mode"] = _IMGMODE
            self.config["img_mode"] = _IMGFIXED
            self.updateCheck()
            self.saveSettings()

    def openFolder(self):

        fileName = ""
        folder = self.config["folder"]
        if not os.path.isdir(folder):
            folder = "."
        self.folderDialog.setDirectory(folder)
        if self.folderDialog.exec_() == QtWidgets.QFileDialog.Accepted:
            fileName = self.folderDialog.selectedFiles()[0]

        if fileName:
            self.config["folder"] = fileName
            self.config["mode"] = _IMGMODE
            self.config["img_mode"] = _IMGCAROUSEL
            self.updateCheck()
            self.saveSettings()

    def openVideo(self):

        fileName = ""
        folder = os.path.dirname(self.config["video"])
        if not os.path.isdir(folder):
            folder = "."
        self.videoDialog.setDirectory(folder)
        if self.videoDialog.exec_() == QtWidgets.QFileDialog.Accepted:
            fileName = self.videoDialog.selectedFiles()[0]

        if fileName:
            self.config["video"] = fileName
            self.config["mode"] = _VIDMODE
            self.config["video_mode"] = _VIDLOCAL
            self.updateCheck()
            self.saveSettings()

    def openYT(self):
        self.ytDialog.close()
        self.config["mode"] = _VIDMODE
        self.config["video_mode"] = _VIDYT
        text = self.ytEdit.text().replace("www.youtube.com", "youtube.com")
        if text and text not in self.config["yt_url"]:
            if len(self.config["yt_url"]) >= 10:
                self.config["yt_url"].pop(0)
                self.yvideoAct.removeAction(self.yvideoAct.actions()[1])
            self.config["yt_url"].append(text)
            self.config["yt_index"] = len(self.config["yt_url"]) - 1
            for option in self.yvideoAct.actions():
                option.setIcon(self.iconNotSelected)
            option = self.yvideoAct.addAction(text, (lambda: self.execYtAct(text)))
            option.setIcon(self.iconSelected)
            self.updateCheck()
            self.saveSettings()

    def openChromecast(self):
        self.config["mode"] = _WEBMODE
        self.config["web_mode"] = _CHROMEMODE
        self.updateCheck()
        self.saveSettings()

    def openBing(self):
        self.config["mode"] = _WEBMODE
        self.config["web_mode"] = _BINGMODE
        self.updateCheck()
        self.saveSettings()

    def openURL(self):
        self.urlDialog.close()
        self.config["mode"] = _WEBMODE
        self.config["web_mode"] = _URLMODE
        text = self.urlEdit.text()
        if text and text not in self.config["url"]:
            if len(self.config["url"]) >= 10:
                self.config["url"].pop(0)
                self.uwebAct.removeAction(self.yvideoAct.actions()[1])
            self.config["url"].append(text)
            for option in self.uwebAct.actions():
                option.setIcon(self.iconNotSelected)
            option = self.uwebAct.addAction(text, (lambda: self.execUrlAct(text)))
            option.setIcon(self.iconSelected)
            self.config["url_index"] = len(self.config["url"]) - 1
            self.updateCheck()
            self.saveSettings()

    def sendShowHelp(self):
        self.showHelp.emit()

    def sendCloseAll(self):
        self.closeAll.emit()

    def saveSettings(self, reload=True):

        if os.path.isfile(_SETTINGS_FILE):
            file = _SETTINGS_FILE
        else:
            file = utils.resource_path("resources/" + _SETTINGS_FILE)
        try:
            with open(file, "w", encoding='UTF-8') as file:
                json.dump(self.config, file, ensure_ascii=False, sort_keys=False, indent=4)
        except:
            pass

        if reload:
            self.reloadSettings.emit()

    def saveLast(self, chrome="", bing=""):
        if chrome:
            self.config["chrome_last"] = chrome
        if bing:
            self.config["bing_last"] = bing
        self.saveSettings(reload=False)


def sigint_handler(*args):
    # https://stackoverflow.com/questions/4938723/what-is-the-correct-way-to-make-my-pyqt-application-quit-when-killed-from-the-co
    app.closeAllWindows()


def exception_hook(exctype, value, tb):
    # https://stackoverflow.com/questions/56991627/how-does-the-sys-excepthook-function-work-with-pyqt5
    traceback_formated = traceback.format_exception(exctype, value, tb)
    traceback_string = "".join(traceback_formated)
    print(traceback_string, file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    if "python" in sys.executable.lower():
        # This will let the script catching Ctl-C interruption (e.g. when running from IDE)
        signal.signal(signal.SIGINT, sigint_handler)
        timer = QtCore.QTimer()
        timer.start(500)
        timer.timeout.connect(lambda: None)
        # This will allow to show some tracebacks (not all, anyway)
        sys._excepthook = sys.excepthook
        sys.excepthook = exception_hook
    win = Window()
    win.show()
    if "macOS" in platform.platform() or "Darwin" in platform.platform():  # Not working if executed before win.show() or after app.exec_()
       bkgutils.sendBehind(_CAPTION)
    try:
        app.exec_()
    except:
        pass
