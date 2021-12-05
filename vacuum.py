#!/usr/bin/python3

import logging
import logging.handlers
import time
import traceback
import threading
import signal
import argparse


#--- Global variables ---------------------------------------------------------
logger = None
g_bRun = True
g_Vacuum = None
g_iStatus = "Charging"
g_sButtons = set()  # Set containing selected buttons
# GPIO ID: [ 0:LED 1:Button, "Description", GPIO handler, Button callback, LED ID for button, Room ID]
g_gpioMap = {
    2: [1,  "Kupatilo",                       None, lambda: ButtonPress(2), 15, 19],
    3: [1,  "Vešernica",                      None, lambda: ButtonPress(3), 17,  2],
    4: [0,  "Kuhinja",                        None, None,                   14,  0],
    5: [0,  "Status",                         None, None,                   0,  0], 
    6: [1,  "Održavanje",                     None, lambda: ButtonPress(6), 0,  0], 
    7: [1,  "Stop",                           None, lambda: ButtonPress(7), 0,  0], 
    8: [1,  "Dnevna soba - ispod prozora",    None, lambda: ButtonPress(8), 11, 18],
    9: [1,  "Dnevna soba - tepih",            None, lambda: ButtonPress(9), 25, 16],
   10: [0,  "Djordjeva soba",                 None, None,                   24,  0],
   11: [0,  "Dnevna soba - ispod prozora",    None, None,                   8,  0], 
   12: [1,  "Hodnik - kod vešernice",         None, lambda: ButtonPress(12),13, 25],
   13: [0,  "Hodnik - kod vešernice",         None, None,                   12,  0],
   14: [1,  "Kuhinja",                        None, lambda: ButtonPress(14),4,  20],
   15: [0,  "Kupatilo",                       None, None,                   2,  0], 
   16: [1,  "Hodnik - kod špajza",            None, lambda: ButtonPress(16),19, 22],
   17: [0,  "Vešernica",                      None, None,                   3,  0], 
   18: [1,  "Spavaća soba",                   None, lambda: ButtonPress(18),27, 23],
   19: [0,  "Hodnik - kod špajza",            None, None,                   16,  0],
   20: [0,  "Hodnik - kod ulaza",             None, None,                   26,  0],
   21: [1,  "Start",                          None, lambda: ButtonPress(21),0,  0], 
   22: [1,  "Isidorina soba",                 None, lambda: ButtonPress(22),23, 17],
   23: [0,  "Isidorina soba",                 None, None,                   22,  0],
   24: [1,  "Djordjeva soba",                 None, lambda: ButtonPress(24),10,  6],
   25: [0,  "Dnevna soba - tepih",            None, None,                   9,  0], 
   26: [1,  "Hodnik - kod ulaza",             None, lambda: ButtonPress(26),20, 24],
   27: [0,  "Spavaća soba",                   None, None,                   18,  0] 
}
# TODO: get rid of globals :(


#--- Functions and classes definitions ----------------------------------------
def SystemInit():
    global logger

    parser = argparse.ArgumentParser()
    parser.add_argument("ip", help="Vacuum IP address")
    parser.add_argument("token", help="Vacuum token")
    args = parser.parse_args()
    _ip = str(args.ip)
    _token = str(args.token)

    # Configure logger
    logger = logging.getLogger("Vacuum log")
    logger.setLevel(logging.INFO)

    # Add a rotating handler
    handler = logging.handlers.RotatingFileHandler("/tmp/vacuum.log", maxBytes=1024*1024, backupCount=5)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s]: %(message)s"))
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)

    # Assign Ctrl+C callback
    signal.signal(signal.SIGINT, CtrlCHandler)

    logger.info(" __      __                                _____                      _       ")
    logger.info(" \ \    / /                               |  __ \                    | |      ")
    logger.info("  \ \  / /_ _  ___ _   _ _   _ _ __ ___   | |__) |___ _ __ ___   ___ | |_ ___ ")
    logger.info("   \ \/ / _` |/ __| | | | | | | \'_ ` _ \\  |  _  // _ \\ \'_ ` _ \ / _ \\| __/ _ \\")
    logger.info("    \  / (_| | (__| |_| | |_| | | | | | | | | \ \  __/ | | | | | (_) | ||  __/")
    logger.info("     \/ \__,_|\___|\__,_|\__,_|_| |_| |_| |_|  \_\___|_| |_| |_|\___/ \__\___|")
    logger.info("                                                                              ")

    return (_ip, _token)


def CtrlCHandler(sig, frame):
    global g_bRun

    logger.info("Ctrl+C detected. Exiting script...")
    g_bRun = False


class VacuumStatus():
    def __init__(self):
        self.m_status = str("")
        self.m_mtx = threading.Lock()
        self.m_statusOld = str("")

    def Get(self):
        self.m_mtx.acquire()
        _st = self.m_status
        self.m_mtx.release()
        return _st

    def Set(self, _stXML):
        _start = _stXML.find("state=") + len("state=")
        _end = _stXML.find(",")
        self.m_mtx.acquire()
        self.m_status = _stXML[_start:_end]
        self.m_mtx.release()

    def Changed(self):
        self.m_mtx.acquire()
        if self.m_statusOld != self.m_status:
            self.m_statusOld = self.m_status
            self.m_mtx.release()
            return True
        self.m_mtx.release()
        return False


class VacuumThread(threading.Thread):
    def __init__(self, _ipAddr, _token, _statusChangeClb):
        threading.Thread.__init__(self)
        self.m_ipAddr = _ipAddr
        self.m_token = _token
        self.m_statusChangeFn = _statusChangeClb
        self.m_mtx = threading.Lock()
        self.m_vacuum = None
        self.m_x = 25500+9000
        self.m_y = 25500+500

    def run(self):
        global g_sButtons
        global g_gpioMap
        global g_bRun

        logger.info("Starting vacuum communication thread")
        from miio import Vacuum
        logger.info("Loaded miio library")
        self.m_vacuum = Vacuum(self.m_ipAddr, self.m_token)
        logger.info("Created Vacuum object")
        g_status = VacuumStatus()
        while g_bRun:
            try:
                while g_bRun:
                    self.m_mtx.acquire()
                    _status = str(self.m_vacuum.status())
                    self.m_mtx.release()
                    logger.debug("Retrieved vacuum status: " + _status)
                    _oldSt = g_status.Get()
                    g_status.Set(_status)
                    if g_status.Changed():
                        self.m_statusChangeFn(_oldSt, g_status.Get())
                    time.sleep(5)
            except Exception as _err:
                if self.m_mtx.locked(): self.m_mtx.release()
                g_sButtons.clear()
                g_gpioMap[5][2].blink(on_time=0,off_time=4,fade_in_time=0,fade_out_time=1,background=True)
                logger.warning("Recovered from exception ["+str(_err)+"]. Restarting...")
            # TODO: Add longer sleep if exception occured multiple times in a row
        logger.info("Exiting vacuum communication thread")

    def clean(self, _rooms):
        # TODO: add cycling between: segment_clean, pause and resume_segment_clean
        if self.m_vacuum == None:
            logger.warning("Must start thread before using it")
        self.m_mtx.acquire()
        self.m_vacuum.segment_clean(list(_rooms))
        self.m_mtx.release()
        logger.info("Command: segment_clean("+str(list(_rooms))+")")
        
    def find(self):
        if self.m_vacuum == None:
            logger.warning("Must start thread before using it")
        self.m_mtx.acquire()
        self.m_vacuum.find()
        self.m_mtx.release()
        logger.info("Command: find()")

    def home(self):
        if self.m_vacuum == None:
            logger.warning("Must start thread before using it")
        self.m_mtx.acquire()
        self.m_vacuum.home()
        self.m_mtx.release()
        logger.info("Command: home()")

    def maintenance(self):
        if self.m_vacuum == None:
            logger.warning("Must start thread before using it")
        self.m_mtx.acquire()
        self.m_vacuum.goto(self.m_x, self.m_y)
        self.m_mtx.release()
        logger.info("Command: goto("+str(self.m_x)+","+str(self.m_y)+")")


def LEDsUpdate(_sButtons, _iStatus):
    # iterate through LEDs GPIO
    for key, value in g_gpioMap.items():
        if value[0] == 0 and key != 5:   # select only LED GPIO assigned to buttons
            if value[4] in _sButtons:
                if _iStatus == "Segment cleaning":
                    value[2].pulse(fade_in_time=0.5,fade_out_time=0.5,background=True)
                else:
                    value[2].on()
            else:
                value[2].off()
    if _iStatus == "Error":
        g_gpioMap[5][2].pulse(fade_in_time=0.1,fade_out_time=0.1,background=True)


def ButtonPress(_buttonID):
    global g_iStatus
    global g_sButtons

    logger.info("Pressed button #"+str(_buttonID)+"("+g_gpioMap[_buttonID][1]+")")
    _ledID = g_gpioMap[_buttonID][4]

    if _ledID != 0:
        if _buttonID in g_sButtons:
            if g_iStatus != "Segment cleaning": g_sButtons.remove(_buttonID)
        else:
            if g_iStatus != "Segment cleaning": g_sButtons.add(_buttonID)
        LEDsUpdate(g_sButtons,g_iStatus)
    else:
        if _buttonID == 21:     # Start
            _rooms = set()
            for _idx in g_sButtons:
                _roomId = g_gpioMap[_idx][5]
                _rooms.add(_roomId)
            if len(_rooms) == 0:
                logger.info("Looking for vacuum")
                g_Vacuum.find()
            else:
                logger.info("Scheduling the cleaning for rooms: "+str(list(_rooms)))
                g_Vacuum.clean(_rooms)
        elif _buttonID == 7:    # Stop
            g_Vacuum.home()
        elif _buttonID == 6:    # Maintenance
            g_Vacuum.maintenance()


class UIThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        global g_bRun

        logger.info("Starting UI thread")
        from gpiozero import PWMLED
        from gpiozero import Button
        logger.info("Loaded gpiozero library")
        GPIOInit(PWMLED, Button)
        while g_bRun: time.sleep(1)
        GPIOExit()
        logger.info("Exiting UI thread")


def GPIOInit(_pwmLed, _btn):
    # initiate all LEDs and Buttons
    for key, value in g_gpioMap.items():
        if value[0] == 0:
            value[2] = _pwmLed(key)
        elif value[0] == 1:
            value[2] = _btn(pin=key, pull_up=True, bounce_time=0.1)
            time.sleep(0.1)
            value[2].when_pressed = value[3]
            time.sleep(0.1) # without this delay button pressed callback is not set correctly

    for key, value in g_gpioMap.items():
        if value[0] == 0:
            value[2].off()
    logger.info("GPIO initialized")


def GPIOExit():
    # stop all LED PWM threads
    for key, value in g_gpioMap.items():
        if value[0] == 0:
            value[2].off()


def StatusChange(_oldStatus, _newStatus):
    global g_iStatus
    global g_sButtons

    logger.info("New vacuum status: ["+_oldStatus+"] -> [" + _newStatus + "]")
    if _oldStatus == "": # the very first response from vacuum
        g_gpioMap[5][2].blink(on_time=0,off_time=4,fade_in_time=0,fade_out_time=0.3,background=True)
    if _oldStatus == "Segment cleaning" and (_newStatus != "Segment cleaning" and _newStatus != "Paused"):
        g_sButtons.clear()
    elif _oldStatus == "Paused" and _newStatus != "Segment cleaning":
        g_sButtons.clear()
    g_iStatus = _newStatus
    LEDsUpdate(g_sButtons, g_iStatus)


#--- Main script --------------------------------------------------------------
ip,token = SystemInit()
g_Vacuum = VacuumThread(ip, token, StatusChange)
ui = UIThread()
ui.start()
g_Vacuum.start()
# application execution
ui.join()
g_Vacuum.join()
logger.info("Bye...")
