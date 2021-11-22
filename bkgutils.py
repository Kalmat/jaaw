#!/usr/bin/python
# -*- coding: utf-8 -*-

import platform
import subprocess
from typing import List

if "Windows" in platform.platform():
    import ctypes
    import pywintypes
    import win32con
    import win32gui


    def findWindowHandles(parent: int = None, window_class: str = None, title: str = None) -> List[int]:
    # https://stackoverflow.com/questions/56973912/how-can-i-set-windows-10-desktop-background-with-smooth-transition

        def _make_filter(class_name: str, title: str):
            """https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-enumwindows"""

            def enum_windows(handle: int, h_list: list):
                if not (class_name or title):
                    h_list.append(handle)
                if class_name and class_name not in win32gui.GetClassName(handle):
                    return True  # continue enumeration
                if title and title not in win32gui.GetWindowText(handle):
                    return True  # continue enumeration
                h_list.append(handle)

            return enum_windows

        cb = _make_filter(window_class, title)
        try:
            handle_list = []
            if parent:
                win32gui.EnumChildWindows(parent, cb, handle_list)
            else:
                win32gui.EnumWindows(cb, handle_list)
            return handle_list
        except pywintypes.error:
            return []


    def sendBehind(name):

        def getWorkerW():

            thelist = []

            def findit(hwnd, ctx):
                p = win32gui.FindWindowEx(hwnd, None, "SHELLDLL_DefView", "")
                if p != 0:
                    thelist.append(win32gui.FindWindowEx(None, hwnd, "WorkerW", ""))

            win32gui.EnumWindows(findit, None)
            return thelist

        # https://www.codeproject.com/Articles/856020/Draw-Behind-Desktop-Icons-in-Windows-plus
        hWnd = findWindowHandles(title=name)
        progman = win32gui.FindWindow("Progman", None)
        win32gui.SendMessageTimeout(progman, 0x052C, 0, 0, win32con.SMTO_NORMAL, 1000)
        workerw = getWorkerW()
        if hWnd and workerw:
            win32gui.SetParent(hWnd[0], workerw[0])
        return


    def getWallPaper():
        wp = win32gui.SystemParametersInfo(win32con.SPI_GETDESKWALLPAPER, 260, 0)
        return wp


    def setWallpaper(img=""):
        win32gui.SystemParametersInfo(win32con.SPI_SETDESKWALLPAPER, img, win32con.SPIF_UPDATEINIFILE | win32con.SPIF_SENDCHANGE)


    def closeWindow(hWnd):
        win32gui.PostMessage(hWnd, win32con.WM_CLOSE, 0, 0)


    def clearWindow(hWnd):
        win32gui.PostMessage(hWnd, win32con.WM_CLEAR, 0, 0)


    def refreshDesktop():
        # https://newbedev.com/how-to-refresh-reload-desktop

        hWnd = win32gui.GetWindow(win32gui.FindWindow("Progman", "Program Manager"), win32con.GW_CHILD)
        if not hWnd:
            ptrs = findWindowHandles(window_class="WorkerW")
            for i in range(len(ptrs)):
                hWnd = win32gui.FindWindowEx(ptrs[i], 0, "SHELLDLL_DefView", "")
        if hWnd:
            win32gui.SendMessage(hWnd, 0x111, 0x7402, 0)


    def refreshDesktopB():
        win32gui.SendMessage(win32con.HWND_BROADCAST, win32con.WM_SETTINGCHANGE, 0, 1)


    def force_refresh():
        ctypes.windll.user32.UpdatePerUserSystemParameters(1)


    def enable_activedesktop():
        """https://stackoverflow.com/a/16351170"""
        try:
            progman = findWindowHandles(window_class='Progman')[0]
            cryptic_params = (0x52c, 0, 0, 0, 500, None)
            ctypes.windll.user32.SendMessageTimeoutW(progman, *cryptic_params)
        except IndexError as e:
            raise WindowsError('Cannot enable Active Desktop') from e


    def toggleDesktopIcons():

        thelist = []

        def findit(hwnd, ctx):
            p = win32gui.FindWindowEx(hwnd, None, "SHELLDLL_DefView", "")
            if p != 0:
                thelist.append(p)

        win32gui.EnumWindows(findit, None)
        if thelist:
            win32gui.SendMessage(thelist[0], 0x111, 0x7402, 0)

elif "Linux" in platform.platform():
    import Xlib
    import Xlib.X
    import Xlib.display
    # import ewmh

    DISP = Xlib.display.Display()
    SCREEN = DISP.screen()
    ROOT = SCREEN.root
    # EWMH = ewmh.EWMH(_display=DISP, root=ROOT)


    def findWindowHandles(parent: int = None, window_class: str = None, title: str = None) -> List[int]:

        def getAllWindows(parent):
            if not parent:
                parent = ROOT
            windows = parent.query_tree().children
            return windows

        def getWindowsWithTitle(parent, title):
            matches = []
            for win in getAllWindows(parent):
                w = DISP.create_resource_object('window', win)
                if title == w.get_wm_name():
                    matches.append(win)
            return matches

        if title:
            windows = getWindowsWithTitle(parent, title)
        else:
            windows = getAllWindows(parent)

        return windows


    def sendBehind(name):

        # gc = ROOT.create_gc(foreground=SCREEN.white_pixel, background=SCREEN.black_pixel)
        win = findWindowHandles(name)
        if win:
            win = win[0]
            # Doesn't fail, but doesn't work either
            win.reparent(ROOT, 0, 0)


    def getWallPaper():
        cmd = 'gsettings set org.gnome.desktop.background picture-uri ""'
        wp = subprocess.check_output(cmd, shell=True).decode(encoding="utf-8").strip()
        return wp


    def setWallpaper(img=""):
        cmd = 'gsettings set org.gnome.desktop.background picture-uri "%s"' % img
        subprocess.Popen(cmd, shell=True)
