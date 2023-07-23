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


def getWindowElementLocation(element_image, scaling_factor=1.0, confidence=0.8):
    img = Image.open(element_image)

    new_width = int(img.width * scaling_factor)
    new_height = int(img.height * scaling_factor)

    resized_image = img.resize((new_width, new_height))
    resized_image.save(r"targetElement.jpg")

    template = cv2.imread("targetElement.jpg", cv2.IMREAD_UNCHANGED)
    sample = cv2.imread("windowCapture.bmp", cv2.IMREAD_UNCHANGED)

    try:
        result = cv2.matchTemplate(sample, template, cv2.TM_CCOEFF_NORMED)
        minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(result)

        # print(f"template: {element_image}, confidence: {maxVal:.2%}")

        if maxVal < confidence:
            return None

        print(f"template: {element_image}, confidence: {maxVal:.2%}")

        return maxLoc

    except cv2.error:
        print("waiting for window...")
        return None


class Client:

    def __init__(self, actionQueue):
        self.title = "BlueStacks App Player"  # to store the title of the window
        self.process = "HD-Player.exe"
        self.width = 0
        self.height = 0
        self.nativeWindowDimensions = (2302, 1326)
        self.actions = {

            "sign-in": {"GFLapp":         {"timeout": -1, "repeats": 1, "confidence": 0.8},
                        "GFLstart":       {"timeout": 20, "repeats": 1, "confidence": 0.8},
                        "GFLupdate":      {"timeout": 20, "repeats": 1, "confidence": 0.8},
                        "GFLgamestart":   {"timeout": -1, "repeats": 1, "confidence": 0.8},
                        "GFLfacebook":    {"timeout": 15, "repeats": 1, "confidence": 0.8},
                        "GFLclosebanner": {"timeout": 35, "repeats": 5, "confidence": 0.8},
                        "GFLexitevent":   {"timeout": 3, "repeats": 1, "confidence": 0.8}
                        },

            "logistics": {"GFLlogistics":     {"timeout": 10, "repeats": 1, "confidence": 0.8},
                          "GFLlogisticsOkay": {"timeout": 10, "repeats": 1, "confidence": 0.8}
                          },

            "intelligence": {"GFLbase":                  {"timeout": 10, "repeats": 1, "confidence": 0.8},
                             "GFLintelligence":          {"timeout": 10, "repeats": 1, "confidence": 0.8},
                             "GFLdataHub":               {"timeout": 20, "repeats": 1, "confidence": 0.8},
                             "dummy":                    {"timeout": 1, "repeats": 1, "confidence": 0.8},
                             "GFLanalysisTerminal":      {"timeout": 5, "repeats": 1, "confidence": 0.8},
                             "GFLconfirmDataCollection": {"timeout": 5, "repeats": 3, "confidence": 0.98},
                             "GFLdataStart":             {"timeout": 5, "repeats": 1, "confidence": 0.8},
                             "GFLpureSample":            {"timeout": 2, "repeats": 1, "confidence": 0.95},
                             "GFLdataOkay":              {"timeout": 5, "repeats": 1, "confidence": 0.8},
                             "GFLdataClose":             {"timeout": 2, "repeats": 1, "confidence": 0.8},
                             "GFLdataCancel":            {"timeout": 2, "repeats": 1, "confidence": 0.8},
                             "GFLanalysisTerminalExit":  {"timeout": 10, "repeats": 1, "confidence": 0.8}
                             },

            "exploration": {"GFLbase":            {"timeout": 10, "repeats": 1, "confidence": 0.8},
                            "GFLforwardBasecamp": {"timeout": 10, "repeats": 1, "confidence": 0.8},
                            "GFLlootCrate":       {"timeout": 20, "repeats": 1, "confidence": 0.8},
                            "dummy":              {"timeout": 1, "repeats": 1, "confidence": 0.8}
                            },

            "battery": {"GFLbase":           {"timeout": 10, "repeats": 1, "confidence": 0.8},
                        "GFLdorm":           {"timeout": 10, "repeats": 1, "confidence": 0.8},
                        "GFLsuperCapacitor": {"timeout": 20, "repeats": 2, "confidence": 0.8}
                        },

            "combat": {"GFLcombat": {"timeout": 10, "repeats": 1, "confidence": 0.8}},

            "home": {"GFLhome": {"timeout": 10, "repeats": 1, "confidence": 0.8}}
        }
        self.actionQueue = actionQueue
        self.window = None  # to store the window handle
        self.device = None  # to store the ADB device handle
        self.port = None
        self.client = AdbClient(host="127.0.0.1", port=5037)
        self.adb_path = r"C:\platform-tools\adb.exe"
        self.clock = time.time()
        self.emulatorThread = Thread(target=self.launchEmulator)  # to store the emulator thread
        self.debugThread = Thread(target=self.getRelativeMousePosition)  # to store the debug thread

    def launchEmulator(self):
        print("starting up...")
        subprocess.call([rf"C:\Program Files\BlueStacks_nxt\{self.process}"], shell=True)

    def getWindow(self):
        try:
            # wait up to 5 seconds for WINDOW
            self.window = ahk.win_wait(title=self.title, timeout=5)
            self.window.to_bottom()
            self.width = self.window.get_position()[2]
            self.height = self.window.get_position()[3]
            print(f"Got AHK window handle at {self.window}")
        except TimeoutError:
            print(f'{self.title} was not found!')

    def getPort(self):
        with open("C:/ProgramData/BlueStacks_nxt/bluestacks.conf") as infile:
            matches = [line for line in infile.readlines() if "bst.instance.Pie64.status.adb_port" in line]
        self.port = matches[0][36:-2]

    def getDevice(self):
        subprocess.run([self.adb_path, "devices"])
        subprocess.run([self.adb_path, "connect", f"localhost:{self.port}"])

        self.device = self.client.device(f"localhost:{self.port}")

    def getRelativeMousePosition(self):
        while self.process is not None:
            print(ahk.mouse_position[0]-self.window.position[0], ahk.mouse_position[1]-self.window.position[1])
            time.sleep(1)

    def click(self, x, y):
        try:
            cmdParam = str(x)+" "+str(y)+" "+str(x)+" "+str(y)
            self.device.shell("input touchscreen swipe " + cmdParam)
        except RuntimeError:
            print("\nERROR: Device offline - restarting daemon...")
            subprocess.run([self.adb_path, "kill-server"])
            subprocess.run([self.adb_path, "start-server"])
            self.getDevice()
            self.click(x, y)

    def clickWindowElement(self, element, timeout=-1, repeats=1, confidence=0.8):
        scaling_factor = np.mean([self.width / self.nativeWindowDimensions[0], self.height / self.nativeWindowDimensions[1]])

        imgObject = Image.open(f"images//{element}.png")
        imgObject = imgObject.resize((int(imgObject.width*scaling_factor), int(imgObject.height*scaling_factor)))

        elementWidth, elementHeight = imgObject.size
        yOffset = int(66*scaling_factor)

        img = None
        self.clock = time.time()

        while img is None:

            if (time.time() - self.clock > timeout) and (timeout != -1):
                print(f"Element interation at [{element}] timed out.")
                return False

            captureWindow(self.title, self.width, self.height)

            img = getWindowElementLocation(f"images//{element}.png", scaling_factor=scaling_factor, confidence=confidence)  # get a screenshot of window and return coords of element

        for _ in range(repeats):
            time.sleep(np.random.uniform(1, 2))
            self.click(img[0] + elementWidth // 2, img[1] + elementHeight // 2 - yOffset)

        return True

    def executeAgenda(self, agenda):
        for action in agenda:
            actionDict = self.actions[action]
            for element, elementAttr in actionDict.items():
                time.sleep(0.5)
                """========================[Custom Clauses]==========================="""

                if element == "dummy":  # rid pop-up panel
                    time.sleep(2)
                    self.click(self.width//2, self.height//4)
                    print("dummy click...")
                    continue

                if element == "GFLpureSample":  # maintain varying sample selection
                    if np.random.randint(1, 5) <= 3:
                        continue

                """===================================================================="""
                self.clickWindowElement(element,
                                        timeout=elementAttr["timeout"],
                                        repeats=elementAttr["repeats"],
                                        confidence=elementAttr["confidence"])

    def run(self):
        try:
            self.emulatorThread.start()
            self.getWindow()
            self.getPort()
            self.getDevice()

            self.executeAgenda(self.actionQueue)

            time.sleep(3)

        finally:
            subprocess.call(['taskkill', '/F', '/IM', self.process], shell=True)
            print("Finished executing operations.")
