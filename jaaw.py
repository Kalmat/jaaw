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

CAPTION = "Jaaw!"  # Just Another Animated Wallpaper!
SETTINGS_FILE = "settings.json"
CONFIG_ICON = utils.resource_path("resources/Jaaw.png")
SYSTEM_ICON = utils.resource_path("resources/Jaaw.ico")

PLAY_WARNING = 0
SETTINGS_WARNING = 1
IMG_WARNING = 2
FOLDER_WARNING = 3
HELP_WARNING = 4


class Window(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        QtWidgets.QMainWindow.__init__(self, *args, **kwargs)

        self.setupUi()
        self.xmax, self.ymax, self.widgets = qtutils.initDisplay(parent=self,
                                                                 setAsWallpaper=True,
                                                                 icon=SYSTEM_ICON,
                                                                 caption=CAPTION)
        self.currentWP = bkgutils.getWallPaper()

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.loadNextImg)

        self.imgList = []
        self.imgIndex = 0
        self.mouse_pos = QtCore.QPoint(0, 0)

        self.menu = Config(self)
        self.menu.reloadSettings.connect(self.reloadSettings)
        self.menu.closeAll.connect(self.closeAll)
        self.menu.showHelp.connect(self.showHelp)
        self.menu.show()

        self.loadSettings()
        self.start()

    def setupUi(self):

        screenSize = qtutils.getScreenSize()

        self.setStyleSheet("background-color:black")

        self.bkg_label = QtWidgets.QLabel()
        self.bkg_label.hide()
        self.bkg_label.setGeometry(0, 0, screenSize.width(), screenSize.height())
        self.layout().addWidget(self.bkg_label)

        self.mediaPlayer = QtMultimedia.QMediaPlayer(None, QtMultimedia.QMediaPlayer.VideoSurface)
        self.mediaPlayer.setVolume(0)
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

        with open(SETTINGS_FILE, encoding='UTF-8') as file:
            self.config = json.load(file)

        self.contentFolder = self.config["folder"]
        self.wallPaperMode = self.config["mode"]
        self.imgMode = self.config["img_mode"]
        self.imgPeriods = self.config["Available_periods"]
        self.imgPeriod = self.config["img_period"]
        self.img = self.config["img"]
        self.video = self.config["video"]

        self.IMGMODE = self.config["Available_modes"][0]
        self.VIDMODE = self.config["Available_modes"][1]
        self.IMGFIXED = self.config["Available_img_modes"][0]
        self.IMGCAROUSEL = self.config["Available_img_modes"][1]

        if self.config["firstRun"] == "True":
            self.showWarning(SETTINGS_WARNING)

    def start(self):

        if self.wallPaperMode == self.IMGMODE:

            if self.imgMode == self.IMGCAROUSEL:
                self.imgList = self.getImgInFolder(self.contentFolder)
                self.timer.start(self.imgPeriod * 1000)
                self.loadNextImg()

            elif self.imgMode == self.IMGFIXED:
                self.loadImg(self.img)

            else:
                self.showWarning(SETTINGS_WARNING)

        elif self.wallPaperMode == self.VIDMODE:
            self.loadVideo(utils.resource_path(self.video))

        elif self.wallPaperMode == "":
            self.img = "D:/Users/alesc/Documents/Proyectos/PycharmProjects/jaaw/resourcesB/jaaw.png"
            self.loadImg(self.img)

        else:
            self.showWarning(SETTINGS_WARNING)

    @QtCore.pyqtSlot()
    def reloadSettings(self):
        self.timer.stop()
        self.loadSettings()
        self.start()

    def loadImg(self, img, keepAspect=False):
        pixmap = qtutils.resizeImageWithQT(img, self.xmax, self.ymax, keepAspect=keepAspect)
        if pixmap:
            self.playlist.clear()
            self.mediaPlayer.setPlaylist(self.playlist)
            self.videoWidget.hide()
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
        # https://stackoverflow.com/questions/57842104/how-to-play-videos-in-pyqt/57842233
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
        self.showWarning(PLAY_WARNING)

    def showWarning(self, msg):

        if msg == PLAY_WARNING:
            self.msgBox.setIcon(QtWidgets.QMessageBox.Warning)
            self.msgBox.setText("Video not supported or corrupted")
            self.msgBox.setWindowTitle("Jaaw! Warning")
            self.msgBox.setDetailedText("Right-click the Jaaw! tray icon to open settings and select a new one\n"+
                                        self.mediaPlayer.errorString())
            self.msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            self.msgBox.exec_()
            self.loadImg(self.currentWP, keepAspect=True)

        elif msg == SETTINGS_WARNING:
            self.msgBox.setIcon(QtWidgets.QMessageBox.Warning)
            self.msgBox.setText("Configure your own settings and media to use as wallpaper")
            self.msgBox.setWindowTitle("Jaaw! Warning")
            self.msgBox.setDetailedText("Right-click the Jaaw! tray icon to open settings")
            self.msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            self.msgBox.exec_()
            self.loadImg(self.currentWP, keepAspect=True)

        elif msg == IMG_WARNING:
            self.msgBox.setIcon(QtWidgets.QMessageBox.Warning)
            self.msgBox.setText("Image not supported or corrupted")
            self.msgBox.setWindowTitle("Jaaw! Warning")
            self.msgBox.setDetailedText("Right-click the Jaaw! tray icon to open settings and select a new one")
            self.msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            self.msgBox.exec_()
            self.loadImg(self.currentWP, keepAspect=True)

        elif msg == FOLDER_WARNING:
            self.msgBox.setIcon(QtWidgets.QMessageBox.Warning)
            self.msgBox.setText("Folder contains no valid images to show")
            self.msgBox.setWindowTitle("Jaaw! Warning")
            self.msgBox.setDetailedText("Right-click the Jaaw! tray icon to open settings and select a new one")
            self.msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            self.timer.stop()
            self.msgBox.exec_()
            self.loadImg(self.currentWP)

        elif msg == HELP_WARNING:
            self.msgBox.setIcon(QtWidgets.QMessageBox.Information)
            self.msgBox.setText("Right-click on the Jaaw icon at the bottom-right of your screen"
                                " to enter configuration settings")
            self.msgBox.setWindowTitle("Jaaw! Help")
            self.msgBox.setDetailedText("Image mode will allow you to select one single image or a folder\n"
                                        "to show all images inside as a carousel\n\n"
                                        "Video mode will let you set a video as your wallpaper,\n"
                                        "giving it a fully customized and totally awsome aspect!")
            self.msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            self.msgBox.exec_()

        return

    def keyPressEvent(self, event):

        if event.key() in (QtCore.Qt.Key_Q, QtCore.Qt.Key_Escape):
            self.closeAll()
        super(Window, self).keyPressEvent(event)

    def closeEvent(self, event):
        self.closeAll()
        super(Window, self).closeEvent(event)

    def mousePressEvent(self, event):
        self.mouse_pos = event.pos()
        super(Window, self).mousePressEvent(event)

    @QtCore.pyqtSlot()
    def closeAll(self):
        self.timer.stop()
        self.mediaPlayer.stop()
        bkgutils.set_wallpaper(self.currentWP, use_activedesktop=False)
        QtWidgets.QApplication.quit()


class Config(QtWidgets.QWidget):

    reloadSettings = QtCore.pyqtSignal()
    closeAll = QtCore.pyqtSignal()
    showHelp = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, *args, **kwargs)

        self.loadSettings()
        self.setupUI()

    def loadSettings(self):

        with open(SETTINGS_FILE, encoding='UTF-8') as file:
            self.config = json.load(file)

        self.contentFolder = self.config["folder"]
        self.wallPaperMode = self.config["mode"]
        self.imgMode = self.config["img_mode"]
        self.imgPeriods = self.config["Available_periods"]
        self.imgPeriod = self.config["img_period"]
        self.img = self.config["img"]
        self.video = self.config["video"]

        self.IMGMODE = self.config["Available_modes"][0]
        self.VIDMODE = self.config["Available_modes"][1]
        self.IMGFIXED = self.config["Available_img_modes"][0]
        self.IMGCAROUSEL = self.config["Available_img_modes"][1]

    def setupUI(self):

        self.contextMenu = QtWidgets.QMenu(self)
        self.contextMenu.setStyleSheet("""
            QMenu {border: 1px inset #666; font-size: 18px; background-color: #333; color: #fff; padding: 5; padding-left: 20}
            QMenu:selected {background-color: #666; color: #fff;}""")

        self.imgAct = self.contextMenu.addMenu("Image")
        self.fimgAct = self.imgAct.addAction("Select image (single)", self.openSingleImage)
        self.cimgAct = self.imgAct.addAction("Select folder (carousel)", self.openFolder)
        # self.cimgAct = self.imgAct.addMenu("Select image carousel")
        # self.imgfAct = self.cimgAct.addAction("Select folder", self.openFolder)
        # self.pimgAct = self.cimgAct.addMenu("Select carousel interval")
        # for interval in self.imgPeriods:
        #     self.pimgAct.addAction(interval["text"], (lambda: self.assignPeriod(interval)))

        self.videoAct = self.contextMenu.addMenu("Video")
        self.fvideoAct = self.videoAct.addAction("Select video file", self.openVideo)

        self.contextMenu.addSeparator()
        self.helpAct = self.contextMenu.addAction("Help", self.sendShowHelp)
        self.quitAct = self.contextMenu.addAction("Quit", self.sendCloseAll)

        self.trayIcon = QtWidgets.QSystemTrayIcon(utils.resource_path(QtGui.QIcon(CONFIG_ICON)), self)
        self.trayIcon.setContextMenu(self.contextMenu)
        self.trayIcon.setToolTip("Jaaw!")
        self.trayIcon.show()

    def assignPeriod(self, interval):
        self.imgPeriod = interval["duration"]

    def openSingleImage(self):

        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select image",
                                            ".", "Image Files (*.png *.jpg *.jpeg *.bmp)")

        if fileName:
            self.config["img"] = fileName
            self.config["mode"] = self.IMGMODE
            self.config["img_mode"] = self.IMGFIXED
            self.saveSettings()

    def openFolder(self):

        fileName = QtWidgets.QFileDialog.getExistingDirectory(self, "Select folder", ".")

        if fileName:
            self.config["folder"] = fileName
            self.config["mode"] = self.IMGMODE
            self.config["img_mode"] = self.IMGCAROUSEL
            self.saveSettings()

    def openVideo(self):

        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select image",
                                            ".", "Video Files (*.mp4 *.flv *.ts *.mts *.avi *.wmv)")

        if fileName:
            self.config["video"] = fileName
            self.config["mode"] = self.VIDMODE
            self.saveSettings()

    def sendShowHelp(self):
        self.showHelp.emit()

    def sendCloseAll(self):
        self.closeAll.emit()

    def saveSettings(self):

        self.config["firstRun"] = "False"
        with open(SETTINGS_FILE, "w", encoding='UTF-8') as file:
            json.dump(self.config, file, ensure_ascii=False, sort_keys=False, indent=4)

        self.reloadSettings.emit()


def sigint_handler(*args):
    # https://stackoverflow.com/questions/4938723/what-is-the-correct-way-to-make-my-pyqt-application-quit-when-killed-from-the-co
    app.closeAllWindows()


def exception_hook(exctype, value, traceback):
    sys._excepthook(exctype, value, traceback)
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
