import subprocess
import time
import numpy as np
import cv2
from PIL import Image
import win32api, win32con, win32gui, win32ui
from threading import Thread
from ahk import AHK

ahk = AHK()


def captureWindow(window_title, width, height):
    hwnd = win32gui.FindWindow(None, window_title)
    wDC = win32gui.GetWindowDC(hwnd)
    dcObj = win32ui.CreateDCFromHandle(wDC)
    cDC = dcObj.CreateCompatibleDC()
    dataBitMap = win32ui.CreateBitmap()
    dataBitMap.CreateCompatibleBitmap(dcObj, width, height)
    cDC.SelectObject(dataBitMap)
    cDC.BitBlt((0, 0), (width, height), dcObj, (0, 0), win32con.SRCCOPY)
    dataBitMap.SaveBitmapFile(cDC, 'windowCapture.bmp')
    dcObj.DeleteDC()
    cDC.DeleteDC()
    win32gui.ReleaseDC(hwnd, wDC)
    win32gui.DeleteObject(dataBitMap.GetHandle())


def getWindowElementLocation(ElementImage, confidence=0.8):
    sample = cv2.imread("windowCapture.bmp", cv2.IMREAD_UNCHANGED)
    template = cv2.imread(ElementImage, cv2.IMREAD_UNCHANGED)

    result = cv2.matchTemplate(sample, template, cv2.TM_CCOEFF_NORMED)
    minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(result)

    # print(f"template: {ElementImage}, confidence: {maxVal}")

    if maxVal < confidence:
        return None

    return maxLoc


class Dollhouse:

    def __init__(self):
        self.title = "MuMu Player"  # to store the title of the window
        self.window = None  # to store the window handle
        self.process = None  # to store the emulator process
        self.clock = time.time()
        self.emulatorThread = Thread(target=self.launchEmulator)  # to store the emulator thread
        self.debugThread = Thread(target=self.getRelativeMousePosition)  # to store the debug thread
        self.suppressionThread = Thread(target=self.suppressWindow)  # to store the suppression thread

    def launchEmulator(self):
        print("starting up...")
        self.process = subprocess.Popen([r"C:\Program Files\MuMu\emulator\nemu\EmulatorShell\NemuPlayer.exe"])

    def getWindow(self):
        try:
            # wait up to 5 seconds for WINDOW
            self.window = ahk.win_wait(title=self.title, timeout=5)
            print(f"Got AHK window handle at {self.window}")
        except TimeoutError:
            print(f'{self.title} was not found!')

    def suppressWindow(self):
        while self.process is not None:
            if self.window.active:
                self.window.to_bottom()

    def getRelativeMousePosition(self):
        while self.process is not None:
            print(ahk.mouse_position[0]-self.window.position[0], ahk.mouse_position[1]-self.window.position[1])
            time.sleep(1)

    def clickWindowElement(self, element, repeat=False, timeout=-1):
        win = self.window.position
        imgObject = Image.open(f"images//{element}.png")
        elementWidth, elementHeight = imgObject.size
        yOffset = 36  # bezel height of the window
        counter = 0

        while repeat or counter < 1:

            img = None
            self.clock = time.time()

            while img is None:

                if (time.time() - self.clock > timeout) and (timeout != -1):
                    print(f"Element interation at [{element}] timed out.")
                    return

                captureWindow(self.title, 2560, 1528)
                img = getWindowElementLocation(f"images//{element}.png", confidence=0.8)  # get a screenshot of window and return coords of element

            ahk.click(img[0] + win[0] + elementWidth // 2,    # x-coordinate of click
                      img[1] + win[1] + elementHeight // 2)   # y-coordinate of click

            counter += 1

    def clickElementsInWindow(self, elements, interval=1, timeout=-1):
        for element in elements:
            time.sleep(interval)

            if element == "GFLapp":
                self.clickWindowElement(element)
                self.title = "Girls' Frontline - MuMu Player"
                continue

            if element == "GFLfacebook":
                self.clickWindowElement(element, timeout=10)
                continue

            if element == "GFLclosebtn":
                self.clickWindowElement(element, repeat=True, timeout=30)
                continue

            self.clickWindowElement(element, timeout=timeout)

            # a222lin@uwaterloo.ca

    def run(self):
        try:
            self.emulatorThread.start()
            self.getWindow()
            # self.suppressionThread.start()
            # self.debugThread.start()

            time.sleep(5)

            self.clickElementsInWindow(["closebtn",
                                        "GFLapp",
                                        "GFLstart",
                                        "GFLgamestart",
                                        "GFLfacebook",
                                        "GFLclosebtn"])

            self.clickElementsInWindow(["GFLdashboard",
                                        "GFLlogistics",
                                        "GFLlogisticsOkay"],
                                       timeout=10)

            time.sleep(10)

        finally:
            self.process.kill()
            print("Finished executing operations.")


def main():
    mu01 = Dollhouse()
    mu01.run()


if __name__ == '__main__':
    main()

