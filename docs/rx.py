# Button Press Receiver
# (ALMA PURA RED RECEIVER)

# Can receive an AES encrypted button press, change led, and receive released, and change back light red.

# Status lights: Blue means advertising for connection to transmitter through BLE
# * Dark red means button press received. Light red means released.
# * Green on transmitter means ready for button press and connected. Light red on receiver means receiver ready for remote button press.
# Check code for other colors

# START Exception printing capability
# Copied from https://github.com/tuupola/circuitpython/blob/master/tests/misc/print_exception.py
# -Mo added external LED connected to Pin A1 to indicate button press on TX
import sys
try:
    try:
        import uio as io
    except ImportError:
        import io
except ImportError:
    print("SKIP")
    raise SystemExit

if hasattr(sys, 'print_exception'):
    print_exception = sys.print_exception
else:
    import traceback
    print_exception = lambda e, f: traceback.print_exception(None, e, sys.exc_info()[2], file=f)

def print_exc(e):
    buf = io.StringIO()
    print_exception(e, buf)
    s = buf.getvalue()
    for l in s.split("\n"):
        # uPy on pyboard prints <stdin> as file, so remove filename.
        if l.startswith("  File "):
            l = l.split('"')
            print(l[0], l[2])
        # uPy and CPy tracebacks differ in that CPy prints a source line for
        # each traceback entry. In this case, we know that offending line
        # has 4-space indent, so filter it out.
        elif not l.startswith("    "):
            print(l)
# END Exception printing capability

# BLE radio imports (library requires... adafruit and stable.)
from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService

# same logging as transmitter. not always used.
import adafruit_logging as logging
import digitalio # DIGITAL IO FOR BOARDfor external LED -Mo
# time because probably need it... but not necessarily always used...
import time
import board # board still to be able to get pins. board access.

import adafruit_dotstar # dotstar access.. same as tx.. multicolor fun LED.
import sys # sys, python system access..
import aesio # aesio, same as tx... symmetric encryption... embedded key... again, change device id and encryption for each set of units.
from binascii import hexlify, unhexlify # get hex and unhex functions for encryption

i = 0 # set up an iterator variable if needed...

key = b'5!!t33n byt3|<3y' # CHANGEME: always 16 bytes... or ECB mode of AES will break. Other modes not known to work.
cipher = aesio.AES(key, aesio.MODE_ECB)

led = adafruit_dotstar.DotStar(board.APA102_SCK, board.APA102_MOSI, 1) # make led variable of the DotStar colored led.
# Get external LED connected to Pin A1  From Adafruit Example -Mo
led2 = digitalio.DigitalInOut(board.A1) #this is led connected to A1 -Mo
led2.direction = digitalio.Direction.OUTPUT # From adafruit eg -Mo

logger = logging.getLogger('main') # set up a logger on main

logger.setLevel(logging.INFO) # logger info like tx
logger.info('Welcome to Button Push Receiver') # log a log message to logger.


ble = BLERadio() # set up BLERadio object... creator function... same as tx...
uart = UARTService() # set up UARTService object.. also creator function.. same as tx.
advertisement = ProvideServicesAdvertisement(uart) # create an advertisement linked to the UART object
led[0] = (1,1,20)

while True: # breakable endless loop... ("Infinite Loop")
    ble.start_advertising(advertisement) # start advertising the created advertisement
    while not ble.connected: # Adafruit stable connection code... Helps wait for connection and not continue to false connected state.
        pass

    # Now we're connected

    if ble.connected: # briefly set light green... in the nanoseconds... for connected.. on rx.
        print("connected")
        led[0] = (1,30,1)

    while ble.connected: # loop while connected... if you exit this loop, you lost connection... but will regain automatically (usually?)
        led[0] = (27, 13, 3) # light red ready color of RX (BUTTON PRESS RECEIVER)
        input_read = uart.readline() # readline... get a line of last transmission (received on uart) (input_read is the variable)
        if input_read: # we check for existence of input_read (it is not nil or null or "falsy")
            try:
                decr = bytearray(len(unhexlify(input_read))) # get byte array length of unhexadecimal'd input_read from uart...
                try:
                    cipher.decrypt_into(unhexlify(input_read), decr) # try to decrypt, into decr bytearray, the unhexadecimal'd of input_read (DECRYPT FUNCTION)
                except ValueError:
                    print("do nothing") # don't crash if decryption failed... adafruit-like stability code.
                print(decr)
                if decr == bytearray(b'BUTTON PRESS!!!!'): # check what was decrypted... if it is button press...
                    i = 0
                    print("Receiver: Remote button press received.")
                    #Turn external LED at A1 on and then OFF -Mo
                    led2.value = True #Mo
                    time.sleep(2)# 2 second wait -Mo
                    led2.value = False #Mo
                    while True: # breakable endless loop
                        led[0] = (25, 1, 1) # Dark red of button press received... TRIGGERED!!!!

                        # Code for button release to cancel trigger (break triggered state...)
                        input_read2= uart.readline() # same uart readline... reliable
                        decr2 = bytearray(len(unhexlify(input_read2))) # same bytearray setup for decryption
                        try:
                            cipher.decrypt_into(unhexlify(input_read2), decr2) # actual decryption of button release
                        except ValueError:
                            print("do nothing") # failure, don't crash... hope for the best.
                        if decr2 == bytearray(b'BUTTON RLSSS!!!!'): # actually checking if decrypted message is button release
                            print("Receiver: Remote button release received.")
                            led[0] = (1, 25, 1) # briefly 0.1ns green but really straight back to light red
                            uart.write(b'A') # this unencrypted 1 byte send means that receiver says button press release happened to the transmitter... that the light is light red now.
                            break # this is what breaks us out of the infinite loop of button triggered (which makes it stay dark red)

            except Exception as e: # K added this for stability.
                print_exc(e)
    led[0] = (10,1,1) # brief light-light red for lost connection... too fast to be seen...
    print("Receiver disconnected from transmitter.")
    # If we got here, we lost the connection. Go up to the top and start
    # advertising again and waiting for a connection. (ADAFRUIT WROTE THIS COMMENT.)