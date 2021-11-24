#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import random
import time
from os import listdir
from os.path import isfile, join
import json
import sys
import qtutils
import bkgutils
import utils
import webutils
from PyQt5 import QtWidgets, QtCore, QtGui, QtMultimedia, QtMultimediaWidgets, QtWebEngineWidgets
import signal
import traceback

CAPTION = "Jaaw!"  # Just Another Animated Wallpaper!
CONFIG_ICON = utils.resource_path("resources/Jaaw.png")
SYSTEM_ICON = utils.resource_path("resources/Jaaw.ico")
ICON_SELECTED = utils.resource_path("resources/tick.png")
SETTINGS_FILE = "settings.json"
DEFAULT_SETTINGS_FILE = utils.resource_path("resources/defsett.json")

IMGMODE = "IMAGE"
IMGFIXED = "FIXED"
IMGCAROUSEL = "CAROUSEL"
VIDMODE = "VIDEO"
WEBMODE = "WEB"
CHROMEMODE = "CHROME"
BINGMODE = "BING"
URLMODE = "URL"

PLAY_WARNING = 0
SETTINGS_WARNING = 1
IMG_WARNING = 2
FOLDER_WARNING = 3
HELP_MSG = 4


class Window(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        QtWidgets.QMainWindow.__init__(self, *args, **kwargs)

        self.currentWP = utils.resource_path(bkgutils.getWallPaper())
        self.parent = self.parent()

        self.setupUi()
        self.xmax, self.ymax = qtutils.initDisplay(parent=self,
                                                   setAsWallpaper=True,
                                                   icon=SYSTEM_ICON,
                                                   caption=CAPTION)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.loadNextImg)

        self.imgList = []
        self.imgIndex = 0
        self.chrome = {"chromecast": []}

        if not self.loadSettings():
            self.config["mode"] = IMGMODE
            self.config["img_mode"] = IMGFIXED
            self.config["img"] = self.currentWP

        self.menu = Config(self, self.config)
        self.menu.reloadSettings.connect(self.reloadSettings)
        self.menu.closeAll.connect(self.closeAll)
        self.menu.showHelp.connect(self.showHelp)
        self.menu.show()

        bkgutils.sendBehind(CAPTION)
        self.start()

    def setupUi(self):

        screenSize = qtutils.getScreenSize()

        self.widget = QtWidgets.QWidget(self)
        self.myLayout = QtWidgets.QHBoxLayout()
        self.myLayout.setContentsMargins(0, 0, 0, 0)

        self.bkg_label = QtWidgets.QLabel()
        self.bkg_label.hide()
        self.bkg_label.setGeometry(0, 0, screenSize.width(), screenSize.height())
        self.bkg_label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)

        # Reduce CPU?
        # Explorer.exe shell:appsFolder\Microsoft.ZuneVideo_8wekyb3d8bbwe!Microsoft.ZuneVideo
        # https://stackoverflow.com/questions/57015932/how-to-attach-and-detach-an-external-app-with-pyqt5-or-dock-an-external-applicat
        self.mediaPlayer = QtMultimedia.QMediaPlayer(None, QtMultimedia.QMediaPlayer.VideoSurface)
        self.mediaPlayer.setMuted(True)
        self.playlist = QtMultimedia.QMediaPlaylist()
        self.playlist.setPlaybackMode(QtMultimedia.QMediaPlaylist.CurrentItemInLoop)
        self.videoWidget = QtMultimediaWidgets.QVideoWidget()
        self.videoWidget.hide()
        self.videoWidget.setGeometry(0, 0, screenSize.width(), screenSize.height())
        self.mediaPlayer.setVideoOutput(self.videoWidget)
        self.mediaPlayer.error.connect(self.handlePlayError)

        # https://recursospython.com/codigos-de-fuente/navegador-web-simple-con-pyqt-5/
        self.webView = QtWebEngineWidgets.QWebEngineView()
        self.webView.hide()
        frame = self.webView.page()
        frame.setAudioMuted(True)

        self.myLayout.addWidget(self.bkg_label)
        self.myLayout.addWidget(self.videoWidget)
        self.myLayout.addWidget(self.webView)
        self.widget.setLayout(self.myLayout)
        self.setCentralWidget(self.widget)

        self.msgBox = QtWidgets.QMessageBox()

    def loadSettings(self):

        ret = True

        try:
            with open(SETTINGS_FILE, encoding='UTF-8') as file:
                self.config = json.load(file)
            self.loadSettingsValues()

        except:
            ret = False
            with open(utils.resource_path(DEFAULT_SETTINGS_FILE), encoding='UTF-8') as file:
                self.config = json.load(file)
            self.loadSettingsValues()
            self.img = self.currentWP
            self.showWarning(SETTINGS_WARNING)

        return ret

    def loadSettingsValues(self):
        self.contentFolder = self.config["folder"]
        self.wallPaperMode = self.config["mode"]
        self.imgMode = self.config["img_mode"]
        self.imgPeriods = self.config["Available_periods"]
        self.imgPeriod = self.config["img_period"]
        self.img = self.config["img"]
        self.video = self.config["video"]
        self.webMode = self.config["web_mode"]
        self.url = self.config["url"]
        self.last = self.config["last"]

    def start(self):

        if self.wallPaperMode == IMGMODE:

            if self.imgMode == IMGCAROUSEL:
                self.imgList = self.getImgInFolder(self.contentFolder)
                self.timer.start(self.imgPeriod * 1000)
                self.loadNextImg()

            elif self.imgMode == IMGFIXED:
                self.loadImg(self.img)

            else:
                self.showWarning(SETTINGS_WARNING)

        elif self.wallPaperMode == VIDMODE:
            self.loadVideo(utils.resource_path(self.video))

        elif self.wallPaperMode == WEBMODE:
            if self.webMode == CHROMEMODE:
                self.loadChrome()
            elif self.webMode == BINGMODE:
                self.loadBing()
            elif self.webMode == URLMODE:
                self.loadWebPage(self.url)

        else:
            self.showWarning(SETTINGS_WARNING)

    @QtCore.pyqtSlot()
    def reloadSettings(self):
        self.timer.stop()
        self.loadSettings()
        self.start()

    def loadImg(self, img, keepAspect=True, expand=True):
        pixmap = qtutils.resizeImageWithQT(img, self.xmax, self.ymax, keepAspectRatio=keepAspect, expand=expand)
        if pixmap:
            self.bkg_label.clear()
            self.mediaPlayer.stop()
            self.playlist.clear()
            self.mediaPlayer.setPlaylist(self.playlist)
            self.bkg_label.setPixmap(pixmap)
            self.videoWidget.hide()
            self.webView.hide()
            self.move(QtCore.QPoint(0, 0 + int((self.screen().size().height() - pixmap.height())/2)))
            self.bkg_label.show()
        else:
            self.showWarning(IMG_WARNING)

    def loadNextImg(self):
        if self.imgList:
            self.loadImg(self.imgList[self.imgIndex])
            self.imgIndex = (self.imgIndex + 1) % len(self.imgList)
        else:
            self.showWarning(FOLDER_WARNING)

    def loadVideo(self, video):
        self.playlist.clear()
        self.playlist.addMedia(QtMultimedia.QMediaContent(QtCore.QUrl.fromLocalFile(video)))
        self.mediaPlayer.setPlaylist(self.playlist)
        self.bkg_label.hide()
        self.webView.hide()
        self.setGeometry(QtCore.QRect(0, 0, self.screen().size().width(), self.screen().size().height()))
        self.videoWidget.show()
        self.mediaPlayer.play()
        self.videoWidget.setGeometry(QtCore.QRect(0, 0, self.screen().size().width(), self.screen().size().height()))

    def loadChrome(self):
        filename = utils.resource_path("032k-8738jd7-00")
        current = time.strftime("%Y%m%d")
        found = True
        if not os.path.isfile(filename) or self.last < current:
            self.last = current
            if not self.chrome["chromecast"]:
                self.chrome = webutils.getChromecastImages()
            rand = random.Random()
            index = rand.randint(0, len(self.chrome["chromecast"]))
            found = False
            tries = 0
            while not found and tries < 10:
                img = self.chrome["chromecast"][index]["url"]
                try:
                    webutils.download(img, filename)
                    found = True
                except:
                    index = rand.randint(0, len(self.chrome["chromecast"]))
                    tries += 1
        if not found:
            filename = self.currentWP
        self.loadImg(filename)
        self.menu.saveLast(self.last)

    def loadBing(self):
        filename = utils.resource_path("032k-8738jd7-01")
        current = time.strftime("%Y%m%d")
        found = True
        if not os.path.isfile(filename) or self.last < current:
            self.last = current
            image = webutils.getBingTodayImage()
            try:
                webutils.download(image, filename)
            except:
                images = webutils.getBingImages()
                rand = random.Random()
                index = rand.randint(0, len(images))
                found = False
                tries = 0
                while not found and tries < 10:
                    try:
                        webutils.download(images[index], filename)
                        found = True
                    except:
                        index = rand.randint(0, len(images))
                        tries += 1
        if not found:
            filename = self.currentWP
        self.loadImg(filename)
        self.menu.saveLast(self.last)

    def loadWebPage(self, url):
        self.bkg_label.hide()
        self.videoWidget.hide()
        self.setGeometry(QtCore.QRect(0, 0, self.screen().size().width(), self.screen().size().height()))
        self.webView.show()
        try:
            self.webView.load(QtCore.QUrl(url))
        except:
            self.loadImg(self.currentWP)

    def getImgInFolder(self, folder):
        try:
            files = [file for file in listdir(folder) if isfile(join(folder, file))]
            imgList = []
            for file in files:
                if file.split(".")[-1].lower() in ("png", "jpg", "jpeg", "bmp"):
                    imgList.append(join(folder, file))
        except:
            imgList = []
        return imgList

    @QtCore.pyqtSlot()
    def showHelp(self):
        self.showWarning(HELP_MSG)

    def handlePlayError(self):
        self.playlist.clear()
        self.mediaPlayer.setPlaylist(self.playlist)
        self.videoWidget.hide()
        self.showWarning(PLAY_WARNING)

    def showWarning(self, msg):

        if msg == SETTINGS_WARNING:
            self.loadImg(self.currentWP)
            self.msgBox.setIcon(QtWidgets.QMessageBox.Warning)
            self.msgBox.setText("Configure your own settings and media to use as wallpaper\n"
                                "Right-click the Jaaw! tray icon to open settings")
            self.msgBox.setWindowTitle("Jaaw! Warning")
            self.msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            self.msgBox.exec_()

        elif msg == IMG_WARNING:
            self.loadImg(self.currentWP)
            self.msgBox.setIcon(QtWidgets.QMessageBox.Warning)
            self.msgBox.setText("Image not supported, moved or corrupted")
            self.msgBox.setWindowTitle("Jaaw! Warning")
            self.msgBox.setDetailedText("Right-click the Jaaw! tray icon to open settings and select a new one")
            self.msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            self.msgBox.exec_()

        elif msg == FOLDER_WARNING:
            self.loadImg(self.currentWP)
            self.msgBox.setIcon(QtWidgets.QMessageBox.Warning)
            self.msgBox.setText("Folder contains no valid images to show")
            self.msgBox.setWindowTitle("Jaaw! Warning")
            self.msgBox.setDetailedText("Right-click the Jaaw! tray icon to open settings and select a new one")
            self.msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            self.timer.stop()
            self.msgBox.exec_()

        elif msg == PLAY_WARNING:
            self.loadImg(self.currentWP)
            self.msgBox.setIcon(QtWidgets.QMessageBox.Warning)
            self.msgBox.setText("Video not supported, moved or corrupted")
            self.msgBox.setWindowTitle("Jaaw! Warning")
            self.msgBox.setDetailedText("Right-click the Jaaw! tray icon to open settings and select a new one\n" +
                                        self.mediaPlayer.errorString())
            self.msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            self.msgBox.exec_()

        elif msg == HELP_MSG:
            self.msgBox.setIcon(QtWidgets.QMessageBox.Information)
            self.msgBox.setText("Right-click on the Jaaw! icon at the bottom-right of your screen"
                                " to enter configuration settings")
            self.msgBox.setWindowTitle("Jaaw! Help")
            self.msgBox.setDetailedText("Image mode will allow you to select one single image or a folder\n"
                                        "to show all images inside as a carousel, and its changing interval\n\n"
                                        "Video mode will let you set a video as your wallpaper,\n"
                                        "giving it a fully customized and totally awesome aspect!")
            self.msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            self.msgBox.exec_()

        return

    def closeEvent(self, event):
        self.closeAll()
        super(Window, self).closeEvent(event)

    @QtCore.pyqtSlot()
    def closeAll(self):
        bkgutils.setWallpaper(self.currentWP)
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

        self.iconSelected = QtGui.QIcon(ICON_SELECTED)
        self.iconNotSelected = QtGui.QIcon()

        self.contextMenu = QtWidgets.QMenu(self)
        self.contextMenu.setStyleSheet("""
            QMenu {border: 1px inset #666; font-size: 18px; background-color: #333; color: #fff; padding: 10px;}
            QMenu:selected {background-color: #666; color: #fff;}""")

        self.imgAct = self.contextMenu.addMenu("Image")
        self.fimgAct = self.imgAct.addAction("Single image", self.openSingleImage)
        self.cimgAct = self.imgAct.addMenu("Carousel of images")
        self.imgfAct = self.cimgAct.addAction("Select folder", self.openFolder)
        self.pimgAct = self.cimgAct.addMenu("Select carousel interval")
        imgPeriod = self.config["img_period"]
        periods = self.config["Available_periods"]
        for key in periods.keys():
            self.addOptions(self.pimgAct, key, periods[key], selected=(imgPeriod == periods[key]))

        self.videoAct = self.contextMenu.addMenu("Video")
        self.fvideoAct = self.videoAct.addAction("Select video file", self.openVideo)

        self.webAct = self.contextMenu.addMenu("Web")
        self.chromeAct = self.webAct.addAction("Daily Chromecast Wallpaper", self.openChromecast)
        self.bingAct = self.webAct.addAction("Daily Bing Wallpaper", self.openBing)
        self.uwebAct = self.webAct.addAction("Enter URL", self.showUrlDialog)

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
        self.videoDialog.setNameFilter("Video Files (*.flv *.ts *.mts *.avi *.wmv)")

        self.trayIcon = QtWidgets.QSystemTrayIcon(QtGui.QIcon(CONFIG_ICON), self)
        self.trayIcon.setToolTip("Jaaw!")
        self.trayIcon.setContextMenu(self.contextMenu)
        self.trayIcon.show()

        self.urlDialog = QtWidgets.QDialog()
        self.urlDialog.setWindowTitle("Enter URL")
        self.urlDialog.setStyleSheet("background-color: #333; color: #ddd;")
        dialogLayout = QtWidgets.QHBoxLayout()
        self.urlEdit = QtWidgets.QLineEdit()
        self.urlEdit.setMinimumWidth(300)
        self.urlButton = QtWidgets.QPushButton("Go")
        self.urlButton.setStyleSheet("background-color: #333; border:1px solid #ddd;; color: #ddd;")
        self.urlButton.setMinimumWidth(40)
        self.urlButton.clicked.connect(self.openURL)
        dialogLayout.addWidget(self.urlEdit)
        dialogLayout.addWidget(self.urlButton)
        self.urlDialog.setLayout(dialogLayout)

    def showUrlDialog(self):
        self.urlDialog.show()

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

    def updateCheck(self):
        self.imgAct.setIcon(self.iconNotSelected)
        self.fimgAct.setIcon(self.iconNotSelected)
        self.cimgAct.setIcon(self.iconNotSelected)
        self.videoAct.setIcon(self.iconNotSelected)
        self.webAct.setIcon(self.iconNotSelected)
        self.chromeAct.setIcon(self.iconNotSelected)
        self.bingAct.setIcon(self.iconNotSelected)
        self.uwebAct.setIcon(self.iconNotSelected)
        if self.config["mode"] == IMGMODE:
            self.imgAct.setIcon(self.iconSelected)
            if self.config["img_mode"] == IMGFIXED:
                self.fimgAct.setIcon(self.iconSelected)
            elif self.config["img_mode"] == IMGCAROUSEL:
                self.cimgAct.setIcon(self.iconSelected)
        elif self.config["mode"] == VIDMODE:
            self.videoAct.setIcon(self.iconSelected)
        elif self.config["mode"] == WEBMODE:
            self.webAct.setIcon(self.iconSelected)
            if self.config["web_mode"] == CHROMEMODE:
                self.chromeAct.setIcon(self.iconSelected)
            elif self.config["web_mode"] == BINGMODE:
                self.bingAct.setIcon(self.iconSelected)
            elif self.config["web_mode"] == URLMODE:
                self.uwebAct.setIcon(self.iconSelected)
        self.contextMenu.update()

    def openSingleImage(self):

        fileName = ""
        if self.imgDialog.exec_() == QtWidgets.QFileDialog.Accepted:
            fileName = self.imgDialog.selectedFiles()[0]

        if fileName:
            self.config["img"] = fileName
            self.config["mode"] = IMGMODE
            self.config["img_mode"] = IMGFIXED
            self.updateCheck()
            self.saveSettings()

    def openFolder(self):

        fileName = ""
        if self.folderDialog.exec_() == QtWidgets.QFileDialog.Accepted:
            fileName = self.folderDialog.selectedFiles()[0]

        if fileName:
            self.config["folder"] = fileName
            self.config["mode"] = IMGMODE
            self.config["img_mode"] = IMGCAROUSEL
            self.updateCheck()
            self.saveSettings()

    def openVideo(self):

        fileName = ""
        if self.videoDialog.exec_() == QtWidgets.QFileDialog.Accepted:
            fileName = self.videoDialog.selectedFiles()[0]

        if fileName:
            self.config["video"] = fileName
            self.config["mode"] = VIDMODE
            self.updateCheck()
            self.saveSettings()

    def openChromecast(self):
        self.config["mode"] = WEBMODE
        self.config["web_mode"] = CHROMEMODE
        self.updateCheck()
        self.saveSettings()

    def openBing(self):
        self.config["mode"] = WEBMODE
        self.config["web_mode"] = BINGMODE
        self.updateCheck()
        self.saveSettings()

    def openURL(self):
        self.urlDialog.close()
        self.config["mode"] = WEBMODE
        self.config["web_mode"] = URLMODE
        self.config["url"] = self.urlEdit.text()
        self.updateCheck()
        self.saveSettings()

    def sendShowHelp(self):
        self.showHelp.emit()

    def sendCloseAll(self):
        self.closeAll.emit()

    def saveSettings(self, reload=True):

        try:
            with open(SETTINGS_FILE, "w", encoding='UTF-8') as file:
                json.dump(self.config, file, ensure_ascii=False, sort_keys=False, indent=4)
            if reload:
                self.reloadSettings.emit()
        except:
            print("Error saving Settings. Your changes will not take effect.")

    def saveLast(self, last):
        self.config["last"] = last
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
        # This will allow to manage Ctl-C interruption (e.g. when running from IDE)
        signal.signal(signal.SIGINT, sigint_handler)
        timer = QtCore.QTimer()
        timer.start(500)
        timer.timeout.connect(lambda: None)
        # This will allow to show some tracebacks (not all, anyway)
        sys._excepthook = sys.excepthook
        sys.excepthook = exception_hook
    win = Window()
    win.show()
    try:
        app.exec_()
    except:
        pass
