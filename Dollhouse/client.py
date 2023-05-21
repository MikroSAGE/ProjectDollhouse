import subprocess
import time
import numpy as np
import cv2
from ppadb.client import Client as AdbClient
from PIL import Image
import win32con, win32gui, win32ui
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

    print(f"template: {ElementImage}, confidence: {maxVal}")

    if maxVal < confidence:
        return None

    return maxLoc


def checkElementWithinTimeout(elem1, elem2, timeout=30):
    start_time = time.time()
    element = elem1
    while time.time() - start_time < timeout:
        img = getWindowElementLocation(f"images//{element}.png", confidence=0.8)

        if img is not None and element == elem2:
            return True
        else:
            element = elem2 if element == elem1 else elem1

    return False


class Client:

    def __init__(self, actionQueue=["sign-in", "logistics"]):
        self.title = "BlueStacks App Player"  # to store the title of the window
        self.actions = {

            "sign-in": {"GFLapp":         {"timeout": -1, "repeats": 1},
                        "GFLstart":       {"timeout": -1, "repeats": 1},
                        "GFLgamestart":   {"timeout": -1, "repeats": 1},
                        "GFLfacebook":    {"timeout": -1, "repeats": 1},
                        "GFLclosebanner": {"timeout": 1, "repeats": 5},
                        "GFLexitevent":   {"timeout": 5, "repeats": 1}
                        },

            "logistics": {"GFLlogistics":     {"timeout": 5, "repeats": 1},
                          "GFLlogisticsOkay": {"timeout": 5, "repeats": 1}
                          }
        }
        self.actionQueue = actionQueue
        self.window = None  # to store the window handle
        self.process = None  # to store the emulator process
        self.device = None  # to store the ADB device handle
        self.port = None
        self.client = AdbClient(host="127.0.0.1", port=5037)
        self.clock = time.time()
        self.emulatorThread = Thread(target=self.launchEmulator)  # to store the emulator thread
        self.debugThread = Thread(target=self.getRelativeMousePosition)  # to store the debug thread

    def launchEmulator(self):
        print("starting up...")
        self.process = subprocess.Popen([r"C:\Program Files\BlueStacks_nxt\HD-Player.exe"])

    def getWindow(self):
        try:
            # wait up to 5 seconds for WINDOW
            self.window = ahk.win_wait(title=self.title, timeout=5)
            # self.window.to_bottom()
            print(f"Got AHK window handle at {self.window}")
        except TimeoutError:
            print(f'{self.title} was not found!')

    def getPort(self):
        with open("C:/ProgramData/BlueStacks_nxt/bluestacks.conf") as infile:
            matches = [line for line in infile.readlines() if "bst.instance.Pie64.status.adb_port" in line]
        self.port = matches[0][36:-2]

    def getDevice(self):
        adb_path = r"C:\platform-tools\adb.exe"
        subprocess.run([adb_path, "devices"])
        subprocess.run([adb_path, "connect", f"localhost:{self.port}"])

        self.device = self.client.device(f"localhost:{self.port}")

    def getRelativeMousePosition(self):
        while self.process is not None:
            print(ahk.mouse_position[0]-self.window.position[0], ahk.mouse_position[1]-self.window.position[1])
            time.sleep(1)

    def click(self, x, y):
        cmdParam = str(x)+" "+str(y)+" "+str(x)+" "+str(y)
        self.device.shell("input touchscreen swipe " + cmdParam)

    def clickWindowElement(self, element, timeout=-1, repeats=1):
        imgObject = Image.open(f"images//{element}.png")
        elementWidth, elementHeight = imgObject.size
        yOffset = 66

        img = None
        self.clock = time.time()

        while img is None:

            if (time.time() - self.clock > timeout) and (timeout != -1):
                print(f"Element interation at [{element}] timed out.")
                return False

            captureWindow(self.title, self.window.width, self.window.height)
            img = getWindowElementLocation(f"images//{element}.png", confidence=0.8)  # get a screenshot of window and return coords of element

        for _ in range(repeats):
            time.sleep(np.random.uniform(0.5, 1))
            self.click(img[0] + elementWidth // 2, img[1] + elementHeight // 2 - yOffset)

        return True

    def executeAgenda(self, agenda, interval=np.random.uniform(1, 3)):
        for action in agenda:
            switch = False
            actionDict = self.actions[action]
            for element, elementAttr in actionDict.items():
                time.sleep(interval)
                status = self.clickWindowElement(element,
                                                 timeout=elementAttr["timeout"],
                                                 repeats=elementAttr["repeats"])
                if status is False:
                    if element == "GFLclosebanner":
                        switch = checkElementWithinTimeout("GFLclosebanner", "GFLlogistics", timeout=25)

                if switch:
                    break

    def run(self):
        try:
            self.emulatorThread.start()
            self.getWindow()
            self.getPort()
            self.getDevice()

            self.executeAgenda(self.actionQueue)

            time.sleep(3)

        finally:
            self.process.kill()
            print("Finished executing operations.")