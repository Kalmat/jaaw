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
_SETTINGS_FILE = "settings.json"
_DEFAULT_SETTINGS_FILE = utils.resource_path("resources/defsett.json")

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

        if "macOS" in platform.platform():
            self.currentMacWP = bkgutils.getWallpaper()
            self.currentWP = ""
        else:
            self.currentWP = bkgutils.getWallpaper()
            self.currentMacWP = ""

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

        if "Windows" in platform.platform() or "Linux" in platform.platform():
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
        # Explorer.exe shell:appsFolder\Microsoft.ZuneVideo_8wekyb3d8bbwe!Microsoft.ZuneVideo
        # https://stackoverflow.com/questions/57015932/how-to-attach-and-detach-an-external-app-with-pyqt5-or-dock-an-external-applicat
        # If you get this error: defaultServiceProvider::requestService(): no service found for - "org.qt-project.qt.mediaplayer"
        # Run: sudo apt-get install libqt5-multimedia-plugins
        # Also install all codecs: gstreamer-qt5, gstreamer-bad, gstreamer-ugly, ubuntu-restricted-extras, gstreamer-ffmpeg
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
        # Use this to adjust to the screen (but possibly cutting the page/video)
        # self.webFrame.setZoomFactor(1.0)

        self.myLayout.addWidget(self.bkg_label)
        self.myLayout.addWidget(self.videoWidget)
        self.myLayout.addWidget(self.webView)
        self.widget.setLayout(self.myLayout)
        self.setCentralWidget(self.widget)

        self.msgBox = QtWidgets.QMessageBox()

    def loadSettings(self):

        try:
            with open(_SETTINGS_FILE, encoding='UTF-8') as file:
                self.config = json.load(file)

        except:
            self.showWarning(_SETTINGS_WARNING)
            with open(utils.resource_path(_DEFAULT_SETTINGS_FILE), encoding='UTF-8') as file:
                self.config = json.load(file)

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
        self.ytUrl = self.config["yt_url"]
        try:
            ytRef = self.ytUrl.split("watch?v=")[1].split("&")[0]
        except:
            try:
                ytRef = self.ytUrl.split("playlist=")[1].split("&")[0]
            except:
                ytRef = "BHACKCNDMW8"
                self.showWarning(_YT_WARNING)
        self.ytUrlEmbed = "https://www.youtube.com/embed/%s?autoplay=1&loop=1&playlist=%s&mute=1&controls=0&rel=0" \
                          % (ytRef, ytRef)     # Add &qv=hd720 to select HD quality (or other)
        self.webMode = self.config["web_mode"]
        self.chromeLast = self.config["chrome_last"]
        self.bingLast = self.config["bing_last"]
        self.url = self.config["url"]

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
                self.loadVideo(utils.resource_path(self.video))
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

    def loadImg(self, img, keepAspect=True, expand=True, fallBack=True):

        error = False
        if self.img:
            pixmap = qtutils.resizeImageWithQT(img, self.xmax, self.ymax, keepAspectRatio=keepAspect, expand=expand)
            if pixmap:
                self.bkg_label.clear()
                self.mediaPlayer.stop()
                self.playlist.clear()
                self.mediaPlayer.setPlaylist(self.playlist)
                self.bkg_label.setPixmap(pixmap)
                self.videoWidget.hide()
                self.webView.stop()
                self.webView.hide()
                self.move(QtCore.QPoint(0, 0 + int((self.ymax - pixmap.height())/2)))
                self.bkg_label.show()
            else:
                error = True
        else:
            error = True

        if error:
            if fallBack:
                self.showWarning(_IMG_WARNING)
            else:
                self.setGeometry(0, 0, 1, 1)

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
        filename = utils.resource_path("032k-8738jd7-00")
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
        filename = utils.resource_path("032k-8738jd7-01")
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
        self.playlist.clear()
        self.mediaPlayer.setPlaylist(self.playlist)
        self.videoWidget.hide()
        self.showWarning(_VID_WARNING)

    def fallBack(self, recover=True):
        self.wallPaperMode = _IMGMODE
        self.imgMode = _IMGFIXED
        self.img = self.currentWP
        self.timer.stop()
        self.loadImg(self.currentWP, fallBack=recover)

    def showWarning(self, msg):

        if msg == _SETTINGS_WARNING:
            self.fallBack()
            self.msgBox.setIcon(QtWidgets.QMessageBox.Warning)
            self.msgBox.setText("Configure your own settings and media to use as wallpaper\n"
                                "Right-click the Jaaw! tray icon to open settings")
            self.msgBox.setWindowTitle("Jaaw! Warning")
            self.msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            self.msgBox.exec_()

        elif msg == _IMG_WARNING:
            self.fallBack(recover=False)
            self.msgBox.setIcon(QtWidgets.QMessageBox.Warning)
            self.msgBox.setText("Image not supported, moved or corrupted")
            self.msgBox.setWindowTitle("Jaaw! Warning")
            self.msgBox.setDetailedText("Right-click the Jaaw! tray icon to open settings and select a new one")
            self.msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            self.msgBox.exec_()

        elif msg == _FOLDER_WARNING:
            self.fallBack()
            self.msgBox.setIcon(QtWidgets.QMessageBox.Warning)
            self.msgBox.setText("Folder contains no valid images to show")
            self.msgBox.setWindowTitle("Jaaw! Warning")
            self.msgBox.setDetailedText("Right-click the Jaaw! tray icon to open settings and select a new one")
            self.msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            self.timer.stop()
            self.msgBox.exec_()

        elif msg == _VID_WARNING:
            self.fallBack()
            self.msgBox.setIcon(QtWidgets.QMessageBox.Warning)
            self.msgBox.setText("Video not supported, moved or corrupted")
            self.msgBox.setWindowTitle("Jaaw! Warning")
            self.msgBox.setDetailedText("Right-click the Jaaw! tray icon to open settings and select a new one\n" +
                                        self.mediaPlayer.errorString())
            self.msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            self.msgBox.exec_()

        elif msg == _CHROME_WARNING:
            self.fallBack()
            self.msgBox.setIcon(QtWidgets.QMessageBox.Warning)
            self.msgBox.setText("Unable to download Chromecast image!")
            self.msgBox.setWindowTitle("Jaaw! Warning")
            self.msgBox.setDetailedText("Maybe web site is down or your Internet connection is not available now")
            self.msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            self.msgBox.exec_()

        elif msg == _VID_WARNING:
            self.fallBack()
            self.msgBox.setIcon(QtWidgets.QMessageBox.Warning)
            self.msgBox.setText("Unable to download Bing image!")
            self.msgBox.setWindowTitle("Jaaw! Warning")
            self.msgBox.setDetailedText("Maybe web site is down or your Internet connection is not available now")
            self.msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            self.msgBox.exec_()

        elif msg == _YT_WARNING:
            self.fallBack()
            self.msgBox.setIcon(QtWidgets.QMessageBox.Warning)
            self.msgBox.setText("URL doesn't exist or it's malformed!")
            self.msgBox.setWindowTitle("Jaaw! Warning")
            self.msgBox.setDetailedText("Be sure the URL exists and looks like 'https://youtube.com/watch?v=XXXXXXXXXXX'")
            self.msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            self.msgBox.exec_()

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
        return

    def closeEvent(self, event):
        self.closeAll()
        super(Window, self).closeEvent(event)

    @QtCore.pyqtSlot()
    def closeAll(self):
        bkgutils.setWallpaper(self.currentWP or self.currentMacWP)
        QtWidgets.QApplication.quit()


class Config(QtWidgets.QWidget):

    reloadSettings = QtCore.pyqtSignal()
    closeAll = QtCore.pyqtSignal()
    showHelp = QtCore.pyqtSignal()

    def __init__(self, parent, config):
        QtWidgets.QWidget.__init__(self, parent)

        self.config = config
        self.setupUI()

    def setupUI(self):

        self.iconSelected = QtGui.QIcon(_ICON_SELECTED)
        self.iconNotSelected = QtGui.QIcon()

        self.contextMenu = QtWidgets.QMenu(self)
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
            self.addOptions(self.pimgAct, key, periods[key], selected=(imgPeriod == periods[key]))

        self.videoAct = self.contextMenu.addMenu("Video")
        self.lvideoAct = self.videoAct.addAction("Local video file", self.openVideo)
        self.yvideoAct = self.videoAct.addAction("YouTube video", self.showYTDialog)

        self.webAct = self.contextMenu.addMenu("Web")
        self.chromeAct = self.webAct.addAction("Chromecast daily random", self.openChromecast)
        self.bingAct = self.webAct.addAction("Bing image of the day", self.openBing)
        self.uwebAct = self.webAct.addAction("Web page", self.showUrlDialog)

        self.contextMenu.addSeparator()
        self.helpAct = self.contextMenu.addAction("Help", self.sendShowHelp)
        self.quitAct = self.contextMenu.addAction("Quit", self.sendCloseAll)
        self.updateCheck()

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

        self.trayIcon = QtWidgets.QSystemTrayIcon(QtGui.QIcon(_CONFIG_ICON), self)
        self.trayIcon.setToolTip("Jaaw!")

        self.trayIcon.setContextMenu(self.contextMenu)
        self.trayIcon.show()

        self.ytDialog = QtWidgets.QDialog()
        self.ytDialog.setWindowTitle("Enter YouTube URL")
        self.ytDialog.setStyleSheet("background-color: #333; color: #ddd;")
        ytLayout = QtWidgets.QHBoxLayout()
        self.ytEdit = QtWidgets.QLineEdit()
        self.ytEdit.setMinimumWidth(300)
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
        self.urlEdit.setMinimumWidth(300)
        self.urlButton = QtWidgets.QPushButton("Go")
        self.urlButton.setStyleSheet("background-color: #333; border:1px solid #ddd;; color: #ddd;")
        self.urlButton.setMinimumWidth(40)
        self.urlButton.clicked.connect(self.openURL)
        urlLayout.addWidget(self.urlEdit)
        urlLayout.addWidget(self.urlButton)
        self.urlDialog.setLayout(urlLayout)
        
    def addOptions(self, option, text, value, selected=False):
        act = option.addAction(text, (lambda: self.execAction(text, value)))
        if selected:
            act.setIcon(self.iconSelected)

    def execAction(self, text, interval):
        for option in self.pimgAct.children():
            if option.text() == text:
                option.setIcon(self.iconSelected)
            else:
                option.setIcon(self.iconNotSelected)
        self.pimgAct.update()
        self.config["img_period"] = int(interval)
        self.saveSettings()

    def showYTDialog(self):
        self.ytEdit.setText(self.config["yt_url"])
        self.ytDialog.show()

    def showUrlDialog(self):
        self.urlEdit.setText(self.config["url"])
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
        self.config["yt_url"] = self.ytEdit.text()
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
        self.config["url"] = self.urlEdit.text()
        self.updateCheck()
        self.saveSettings()

    def sendShowHelp(self):
        self.showHelp.emit()

    def sendCloseAll(self):
        self.closeAll.emit()

    def saveSettings(self, reload=True):

        try:
            with open(_SETTINGS_FILE, "w", encoding='UTF-8') as file:
                json.dump(self.config, file, ensure_ascii=False, sort_keys=False, indent=4)
            if reload:
                self.reloadSettings.emit()
        except:
            print("Error saving Settings. Your changes will not take effect.")

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
    if "macOS" in platform.platform():  # Not working if executed before win.show() or after app.exec_()
       bkgutils.sendBehind(_CAPTION)
    try:
        app.exec_()
    except:
        pass
