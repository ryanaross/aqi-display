from machine import Pin, SPI
from pms7003 import Pms7003
from aqi_calc import AQI
import aqi_font
import aqi_calc
import time
import st7789  # custom firmware from https://github.com/russhughes/st7789_mpy

# How long to warm up fan before beginning to gather data
STARTUP_SEC = 60
# How long to do 1 minute refreshes before switching into Sleep Mode
SLEEP_MODE_SWITCH_SEC = 1800
# How many seconds to put the sensor to sleep between sleeps during Sleep Mode
SLEEP_MODE_SEC = 1800

# Current state one of `warming_up`, `gathering_data`, `sleeping`, `waiting`
state = "warming_up"
buttonPushed = False

# initialize components
pms = Pms7003()

spi = SPI(1, baudrate=30000000, sck=Pin(18), mosi=Pin(19))
tft = st7789.ST7789(
    spi,
    135,
    240,
    reset=Pin(23, Pin.OUT),
    cs=Pin(5, Pin.OUT),
    dc=Pin(16, Pin.OUT),
    backlight=Pin(4, Pin.OUT),
    rotation=1)
tft.init()

# record startup time
startTime = time.time()

# Let the sensor warm and display a progress bar


def wakeUp():
    global tft, pms, state

    state = "warming_up"
    print("Waking up.")
    pms.wakeup()
    tft.fill(st7789.BLACK)
    count = 0
    while count < STARTUP_SEC:
        count = count + 1
        tft.fill_rect(0, 0, int(count*(240/STARTUP_SEC)), 135, st7789.GREEN)
        time.sleep(1)

# Gathers PM2.5 data for 30 seconds


def gatherData():
    global pms, tft, state

    state = "gathering_data"
    print("Gathering data.")
    count = 0
    pms2s = []
    while count < 30:
        count = count + 1
        pms_data = pms.read()
        pms2s.append(pms_data['PM2_5_ATM'])
        tft.fill_rect(0, 0, int(count*(240/30)), 10, st7789.BLUE)
        tft.fill_rect(0, 125, int(count*(240/30)), 10, st7789.BLUE)
        time.sleep(1)
    print(f"PMS2.5: {pms2s}")
    pms2 = sum(pms2s) / len(pms2s)
    aqi = AQI.aqi(pms2)
    print("AQI: " + str(int(aqi)))
    return aqi

# Display the given AQI (integer, required)


def displayAQI(aqi):
    global tft

    # Pick a foreground and background color based on AQI
    if aqi < 50:
        # green to yellow, text black
        fillColor = st7789.color565(int(aqi*5.15), 255, 0)
        textColor = st7789.BLACK
    elif aqi >= 50 and aqi < 150:
        # yellow to red, text black
        remainder = aqi - 49
        fillColor = st7789.color565(255, int(255-(remainder*2.55)), 0)
        textColor = st7789.BLACK
    elif aqi >= 150 and aqi < 250:
        # red to black, text white
        remainder = aqi - 149
        fillColor = st7789.color565(int(255-(remainder*2.55)), 0, 0)
        textColor = st7789.WHITE
    else:
        # Ouch
        fillColor = st7789.BLACK
        textColor = st7789.YELLOW

    # Add string padding for right justification
    if aqi < 10:
        strAQI = "  " + str(aqi)
    elif aqi < 100:
        strAQI = " " + str(aqi)
    else:
        strAQI = str(aqi)

    # Display selected background color and AQI
    tft.fill(fillColor)
    tft.write(aqi_font, strAQI, 0, int(
        (135-103)/2), textColor, fillColor)


def handleTopButton(pin):
    global buttonPushed, state

    if state in ["warming_up", "gathering_data"]:
        print(f"Button was pushed while in a bad state: {state}")
    else:
        buttonPushed = True
        print("Button has been pushed")


def main():
    global state, buttonPushed

    while True:
        aqi = gatherData()

        displayAQI(int(aqi))

        currentTime = time.time()
        if currentTime - startTime < SLEEP_MODE_SWITCH_SEC:
            state = "waiting"
            wait = 0
            while wait < 30:
                wait = wait + 1
                if buttonPushed == True:
                    # Cancel the wait and start gathering data immediatly
                    buttonPushed = False
                    break
                time.sleep(1)
        else:
            # Sleep Mode - puts the sensor to sleep periodically to preserve the life of the fan
            state = "sleeping"
            pms.sleep()
            print(f"Sleeping for {SLEEP_MODE_SEC-60} seconds.")
            wait = 0
            while wait < (SLEEP_MODE_SEC-60):
                wait = wait + 1
                if buttonPushed == True:
                    # Cancel the wait and start gathering data immediatly
                    break
                time.sleep(1)
            if buttonPushed == True:
                buttonPushed = False
                # If the button was pushed, display startup progress bar again for immediate feedback
                wakeUp()
            else:
                state = "waiting"
                pms.wakeup()
                wait = 0
                while wait < STARTUP_SEC:
                    wait = wait + 1
                    if buttonPushed == True:
                        # Cancel the wait and start gathering data immediatly
                        buttonPushed = False
                        break
                    time.sleep(1)


topButton = Pin(35, Pin.IN)
topButton.irq(trigger=Pin.IRQ_RISING, handler=handleTopButton)

wakeUp()
main()
