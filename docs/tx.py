# transmitter
# BUTTON PRESS TRANSMITTER (CLIENT)
# -Mo added external LED connected to Pin A1 to indicate button press on TX
# import BLE radio libraries from adafruit
from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService

# adafruit logging import... (unknown if necessary)
import adafruit_logging as logging

# base64 encoding/decoding and string hexadecimal representation conversion
from adafruit_binascii import hexlify, unhexlify, a2b_base64, b2a_base64

# time for sleep (broken? unknown. unused.)
import time
import board # BOARD KEEP... ACCESS TO PINS

# DotStar colored LED
import adafruit_dotstar

import digitalio # DIGITAL IO FOR BOARD SWITCH (SW BUTTON)
from adafruit_debouncer import Debouncer # DEBOUNCER. BECAUSE OF SIGNAL VARIATIONS. NOT BROKEN.

import aesio # AESIO... AES encryption... Military grade... Symmetric.. Always change key on new build (at factory)

key = b'5!!t33n byt3|<3y' # CHANGE ME EACH BUILD... Always 16-byte key for AES ECB mode. Mandatory 16 bytes please. Or it will break.
cipher = aesio.AES(key, aesio.MODE_ECB) # SET AES in ELECTRONIC CIPHER BOOK MODE.

pin = digitalio.DigitalInOut(board.SWITCH) # Get the switch from it's pin into a reference
pin.direction = digitalio.Direction.INPUT # Set switch button in input mode
pin.pull = digitalio.Pull.UP # Set switch pull to up (current direction?)
switch = Debouncer(pin) # Create a debouncer object from pin... used instead of pin to read press of button.

# Get led set to reference of DotStar LED using PIN locations.
led = adafruit_dotstar.DotStar(board.APA102_SCK, board.APA102_MOSI, 1)
led2 = digitalio.DigitalInOut(board.A1) #this is led connected to A1 Mo
led2.direction = digitalio.Direction.OUTPUT # From adafruit eg Mo

# set up logger as main logger
logger = logging.getLogger('main')

logger.setLevel(logging.INFO) # Set logger level to info. Other modes not tested.
logger.info('Welcome to Button Pusher') # Log message, not serial out call. Will not stop if not connected to laptop.


print("Starting scan") # Simple print all languages
led[0] = (25, 25, 24) # Set LED Blue for connecting
ble = BLERadio() # create a ble radio object


led[0]=(1,1,25) # turn dotstar led green
while True: # endless but breakable loop... (escapable)
    while ble.connected and any(
        UARTService in connection for connection in ble.connections
    ): # if it gets past here it's connected, and looping until disconnection, and checking for a UART service (async read/write)
        for connection in ble.connections:
            if UARTService not in connection:
                continue # skip the code below if there is no UART Service (adafruit stability?) (continue the loop)
            uart = connection[UARTService] # set up uart object from connection...
            switch.update() # update the switch... in a loop we will know if raised/depressed via the debouncer.
            if switch.fell: # switch fell means switch pressed... boolean
                print("transmitter pressed button")
                inp = b'BUTTON PRESS!!!!' # Note: 16-bytes long because of ECB mode... Keep ECB mode and 16 bits... please.
                outp = bytearray(len(inp)) # create output byte array the length of inp... byte string of "BUTTON PRESS!!!!"
                cipher.encrypt_into(inp, outp) # encrypt inp byte buffer into outp
                try:
                    uart.write(bytearray(hexlify(outp))) # simply write the byte array of the hexademical representation of outp to uart
                except:
                    print("Couldn't write encrypted message to UART. Failure.")

            if switch.rose: # rose means button released.
                print("transmitter released button")
                inp = b'BUTTON RLSSS!!!!' # Note: 16-bytes long because of ECB. RLS means Release.
                outp = bytearray(len(inp)) # create outp buffer of length inp
                cipher.encrypt_into(inp, outp) # same encrypt_into... outp will be encrypted
                try:
                    uart.write(bytearray(hexlify(outp))) # same write uart encrypted output... yes different with each device because of factory Mu edits... key and device id only.
                except:
                    print("Couldn't write encrypted message to UART. Failure.")
            # add encryption to the below if you want to send back
            # from device A
            input_read = uart.read(1)
            if input_read:
                if input_read == bytearray(b'A'):
                    print("Transmitter received confirmation of button release. (Trigger off confirmed.)")
                    led2.value = True #Mo
                    time.sleep(1)# Mo
                    led2.value = False #Mo
    print("disconnected, scanning")
    for advertisement in ble.start_scan(): # loop through all BLE advertisements during scan ... while setting advertisement variable
        if(advertisement.complete_name == "CIRCUITPY86fa"): # FACTORY SET ME... ADA SAYS NAME CAN BE CHANGED IN SCRIPT TOO, with ble.name = "helper101" etc
            ble.connect(advertisement) # since there is an above if... only connect to the advertisement of the "brother" device
            print("Transmitter successfully connected to receiver.")
            led[0] = (1,30,1) # Set green because transmitter is ready to transmit
            break # exit this loop because we connected
    ble.stop_scan() # this is next after break. we have to stop scan because we connected.

# below code is to check if broken or insane... it should never run...
while True:
    led[0] = (50,20, 10)
    time.sleep(2)
    led[0] = (20,50, 10)
    time.sleep(2)