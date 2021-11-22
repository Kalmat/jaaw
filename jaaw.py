#!/usr/bin/python
# -*- coding: utf-8 -*-

from os import listdir
from os.path import isfile, join
import json
import sys
import qtutils
import bkgutils
import utils
from PyQt5 import QtWidgets, QtCore, QtGui, QtMultimedia, QtMultimediaWidgets
import signal
import traceback

CAPTION = "Jaaw!"  # Just Another Animated Wallpaper!
CONFIG_ICON = utils.resource_path("resources/Jaaw.png")
SYSTEM_ICON = utils.resource_path("resources/Jaaw.ico")
SETTINGS_FILE = "settings.json"
DEFAULT_SETTINGS_FILE = "resources/defsett.json"

IMGMODE = "IMAGE"
VIDMODE = "VIDEO"
IMGFIXED = "FIXED"
IMGCAROUSEL = "CAROUSEL"

PLAY_WARNING = 0
SETTINGS_WARNING = 1
IMG_WARNING = 2
FOLDER_WARNING = 3
HELP_WARNING = 4

INDICATOR = u'\u2713'  # UTF "tick" character


class Window(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        QtWidgets.QMainWindow.__init__(self, *args, **kwargs)

        self.currentWP = bkgutils.getWallPaper()

        self.setupUi()
        self.xmax, self.ymax, self.widgets = qtutils.initDisplay(parent=self,
                                                                 setAsWallpaper=True,
                                                                 icon=SYSTEM_ICON,
                                                                 caption=CAPTION)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.loadNextImg)

        self.imgList = []
        self.imgIndex = 0

        if self.loadSettings():
            self.start()
        else:
            self.config["img"] = self.currentWP

        self.menu = Config(self, self.config)
        self.menu.reloadSettings.connect(self.reloadSettings)
        self.menu.closeAll.connect(self.closeAll)
        self.menu.showHelp.connect(self.showHelp)
        self.menu.show()

        bkgutils.sendBehind(CAPTION)

    def setupUi(self):

        screenSize = qtutils.getScreenSize()

        self.setStyleSheet("background-color:black")

        self.bkg_label = QtWidgets.QLabel()
        self.bkg_label.hide()
        self.bkg_label.setGeometry(0, 0, screenSize.width(), screenSize.height())
        self.bkg_label.setAlignment(QtCore.Qt.AlignCenter)
        self.layout().addWidget(self.bkg_label)

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
        self.layout().addWidget(self.videoWidget)
        self.mediaPlayer.setVideoOutput(self.videoWidget)
        self.mediaPlayer.error.connect(self.handlePlayError)

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
        self.videoWidget.show()
        self.mediaPlayer.play()

    def getImgInFolder(self, folder):
        files = [file for file in listdir(folder) if isfile(join(folder, file))]
        imgList = []
        for file in files:
            if file.split(".")[-1].lower() in ("png", "jpg", "jpeg", "bmp"):
                imgList.append(join(folder, file))
        return imgList

    @QtCore.pyqtSlot()
    def showHelp(self):
        self.showWarning(HELP_WARNING)

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

        elif msg == HELP_WARNING:
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

        self.indicator = " " + INDICATOR
        self.leftIndicator = INDICATOR + " "
        self.gap = "     "

        self.config = config

        self.setupUI()

    def setupUI(self):

        self.defaultStyleSeet = self.styleSheet()

        self.contextMenu = QtWidgets.QMenu(self)
        self.contextMenu.setStyleSheet("""
            QMenu {border: 1px inset #666; font-size: 18px; background-color: #333; color: #fff; padding: 5}
            QMenu:selected {background-color: #666; color: #fff;}""")

        self.imgAct = self.contextMenu.addMenu(self.gap + "Image")
        self.fimgAct = self.imgAct.addAction(self.gap + "Single image", self.openSingleImage)
        self.cimgAct = self.imgAct.addMenu(self.gap + "Carousel of images")
        self.imgfAct = self.cimgAct.addAction(self.gap + "Select folder", self.openFolder)
        self.pimgAct = self.cimgAct.addMenu(self.gap + "Select carousel interval")
        imgPeriod = self.config["img_period"]
        periods = self.config["Available_periods"]
        for key in periods.keys():
            if imgPeriod == periods[key]:
                indicator = self.indicator
            else:
                indicator = ""
            self.addOptions(self.pimgAct, key + indicator, periods[key])

        self.videoAct = self.contextMenu.addMenu(self.gap + "Video")
        self.fvideoAct = self.videoAct.addAction(self.gap + "Select video file", self.openVideo)

        self.contextMenu.addSeparator()
        self.helpAct = self.contextMenu.addAction(self.gap + "Help", self.sendShowHelp)
        self.quitAct = self.contextMenu.addAction(self.gap + "Quit", self.sendCloseAll)
        self.updateCheck()

        self.trayIcon = QtWidgets.QSystemTrayIcon(QtGui.QIcon(CONFIG_ICON), self)
        self.trayIcon.setToolTip("Jaaw!")
        self.trayIcon.setContextMenu(self.contextMenu)
        self.trayIcon.show()

    def addOptions(self, option, text, value):
        option.addAction(text, (lambda: self.execAction(text, value)))

    def execAction(self, text, interval):
        text = text.replace(self.indicator, self.gap)
        for option in self.pimgAct.children():
            option.setText(option.text().replace(self.indicator, self.gap))
            if option.text() == text:
                option.setText(text + self.indicator)
        self.pimgAct.update()
        self.config["img_period"] = int(interval)
        self.saveSettings()

    def updateCheck(self):
        self.imgAct.setTitle((self.imgAct.title().replace(self.gap, self.leftIndicator) if self.config["mode"] == IMGMODE else self.imgAct.title().replace(self.leftIndicator, self.gap)))
        self.fimgAct.setText((self.fimgAct.text().replace(self.gap, self.leftIndicator) if self.config["mode"] == IMGMODE and self.config["img_mode"] == IMGFIXED else self.fimgAct.text().replace(self.leftIndicator, self.gap)))
        self.cimgAct.setTitle((self.cimgAct.title().replace(self.gap, self.leftIndicator) if self.config["mode"] == IMGMODE and self.config["img_mode"] == IMGCAROUSEL else self.cimgAct.title().replace(self.leftIndicator, self.gap)))
        self.videoAct.setTitle((self.videoAct.title().replace(self.gap, self.leftIndicator) if self.config["mode"] == VIDMODE else self.videoAct.title().replace(self.leftIndicator, self.gap)))
        self.contextMenu.update()

    def openSingleImage(self):

        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select image",
                                                            ".", "Image Files (*.png *.jpg *.jpeg *.bmp)")

        if fileName:
            self.config["img"] = fileName
            self.config["mode"] = IMGMODE
            self.config["img_mode"] = IMGFIXED
            self.updateCheck()
            self.saveSettings()

    def openFolder(self):

        fileName = QtWidgets.QFileDialog.getExistingDirectory(self, "Select folder", ".")

        if fileName:
            self.config["folder"] = fileName
            self.config["mode"] = IMGMODE
            self.config["img_mode"] = IMGCAROUSEL
            self.updateCheck()
            self.saveSettings()

    def openVideo(self):

        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select video",
                                                            ".", "Video Files (*.flv *.ts *.mts *.avi *.wmv)")

        if fileName:
            self.config["video"] = fileName
            self.config["mode"] = VIDMODE
            self.updateCheck()
            self.saveSettings()

    def sendShowHelp(self):
        self.showHelp.emit()

    def sendCloseAll(self):
        self.closeAll.emit()

    def saveSettings(self):

        try:
            with open(SETTINGS_FILE, "w", encoding='UTF-8') as file:
                json.dump(self.config, file, ensure_ascii=False, sort_keys=False, indent=4)
            self.reloadSettings.emit()
        except:
            print("Error saving Settings. Your changes will not take effect.")


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
