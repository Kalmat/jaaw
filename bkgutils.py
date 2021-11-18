#!/usr/bin/python
# -*- coding: utf-8 -*-

import ctypes
import pywintypes
import pythoncom
import win32con
import win32gui
from win32comext.shell import shell, shellcon
from typing import List

user32 = ctypes.windll.user32

EnumWindows = ctypes.windll.user32.EnumWindows
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
GetWindowText = ctypes.windll.user32.GetWindowTextW
GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
IsWindowVisible = ctypes.windll.user32.IsWindowVisible


def get_desktop():
    """Get the window of the icons, the desktop window contains this window"""
    shell_window = ctypes.windll.user32.GetShellWindow()
    shell_dll_defview = win32gui.FindWindowEx(shell_window, 0, "SHELLDLL_DefView", "")
    sys_listview = None
    if shell_dll_defview == 0:
        sys_listview_container = []
        try:
            win32gui.EnumWindows(_callback, sys_listview_container)
        except pywintypes.error as e:
            if e.winerror != 0:
                raise
            if sys_listview_container:
                sys_listview = sys_listview_container[0]
    else:
        sys_listview = win32gui.FindWindowEx(shell_dll_defview, 0, "SysListView32", "FolderView")
    return sys_listview


def _callback(hwnd, extra):
    class_name = win32gui.GetClassName(hwnd)
    if class_name == "WorkerW":
        child = win32gui.FindWindowEx(hwnd, 0, "SHELLDLL_DefView", "")
        if child != 0:
            sys_listview = win32gui.FindWindowEx(child, 0, "SysListView32", "FolderView")
            extra.append(sys_listview)
            return False
    return True


def getWHandleByName(name):
    # https://stackoverflow.com/questions/61151811/how-to-get-handle-for-a-specific-application-window-in-python-using-pywin32

    thelist = []

    def findit(hwnd, ctx):
        if name == win32gui.GetWindowText(hwnd):
            thelist.append(hwnd)

    win32gui.EnumWindows(findit, None)
    return thelist


def getWorkerW():

    thelist = []

    def findit(hwnd, ctx):
        p = win32gui.FindWindowEx(hwnd, None, "SHELLDLL_DefView", "")
        if p != 0:
            thelist.append(win32gui.FindWindowEx(None, hwnd, "WorkerW", ""))

    win32gui.EnumWindows(findit, None)
    return thelist


def sendBehind(name):
    # https://www.codeproject.com/Articles/856020/Draw-Behind-Desktop-Icons-in-Windows-plus
    hWnd = getWHandleByName(name)
    progman = win32gui.FindWindow("Progman", None)
    win32gui.SendMessageTimeout(progman, 0x052C, 0, 0, win32con.SMTO_NORMAL, 1000)
    workerw = getWorkerW()
    if hWnd and workerw:
        win32gui.SetParent(hWnd[0], workerw[0])
    return


def closeWindow(hWnd):
    win32gui.PostMessage(hWnd, win32con.WM_CLOSE, 0, 0)


def clearWindow(hWnd):
    win32gui.PostMessage(hWnd, win32con.WM_CLEAR, 0, 0)


def findWindowsWithClass(klass):

    thelist = []

    def findit(hwnd, ctx):
        name = win32gui.GetClassName(hwnd)
        if name == klass and (win32gui.GetWindowText(hwnd) == "" or win32gui.GetWindowText(hwnd) is None):
            thelist.append(hwnd)

    win32gui.EnumWindows(findit, None)
    return thelist


def refreshDesktop():
    # https://newbedev.com/how-to-refresh-reload-desktop

    hWnd = win32gui.GetWindow(win32gui.FindWindow("Progman", "Program Manager"), win32con.GW_CHILD)
    if not hWnd:
        ptrs = findWindowsWithClass("WorkerW")
        for i in range(len(ptrs)):
            hWnd = win32gui.FindWindowEx(ptrs[i], 0, "SHELLDLL_DefView", "")
    if hWnd:
        win32gui.SendMessage(hWnd, 0x111, 0x7402, 0)


def toggleDesktopIcons():

    thelist = []

    def findit(hwnd, ctx):
        p = win32gui.FindWindowEx(hwnd, None, "SHELLDLL_DefView", "")
        if p != 0:
            thelist.append(p)

    win32gui.EnumWindows(findit, None)
    if thelist:
        win32gui.SendMessage(thelist[0], 0x111, 0x7402, 0)


def refreshDesktopC():
    win32gui.SendMessage(win32con.HWND_BROADCAST, win32con.WM_SETTINGCHANGE, 0, 1)


def setWallPaper(img=""):
    # ctypes.windll.user32.SystemParametersInfoA(SPI_SETDESKWALLPAPER, 0, img, 0)
    win32gui.SystemParametersInfo(win32con.SPI_SETDESKWALLPAPER, img, win32con.SPIF_UPDATEINIFILE | win32con.SPIF_SENDCHANGE)


def getWallPaper():
    wp = win32gui.SystemParametersInfo(win32con.SPI_GETDESKWALLPAPER, 260, 0)
    return wp


"""IMPRESSIVE WORK!!!"""
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


def find_window_handles(parent: int = None, window_class: str = None, title: str = None) -> List[int]:
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


def force_refresh():
    user32.UpdatePerUserSystemParameters(1)


def enable_activedesktop():
    """https://stackoverflow.com/a/16351170"""
    try:
        progman = find_window_handles(window_class='Progman')[0]
        cryptic_params = (0x52c, 0, 0, 0, 500, None)
        user32.SendMessageTimeoutW(progman, *cryptic_params)
    except IndexError as e:
        raise WindowsError('Cannot enable Active Desktop') from e


def set_wallpaper(image_path: str, use_activedesktop: bool = True, iad=None):
    if use_activedesktop:
        enable_activedesktop()
    pythoncom.CoInitialize()
    if not iad:
        # Two things I did to boost performance.
        # (1) Only enable active desktop once and reuse the 'iad' instance.
        # (2) Disable the "Automatically pick an accent color from my background" in Windows settings
        iad = pythoncom.CoCreateInstance(shell.CLSID_ActiveDesktop,
                                         None,
                                         pythoncom.CLSCTX_INPROC_SERVER,
                                         shell.IID_IActiveDesktop)
    iad.SetWallpaper(str(image_path), 0)
    iad.ApplyChanges(shellcon.AD_APPLY_ALL)
    force_refresh()
    return iad
