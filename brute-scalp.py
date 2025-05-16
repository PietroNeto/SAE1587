import serial
from datetime import datetime

PORT = "/dev/ttyUSB0"
BAUD = 9600

# with serial.Serial(PORT, BAUD, timeout=0.5) as ser, open("raw_capture.txt", "w") as log:
#     index = 0
#     while True:
#         data = ser.read(1)
#         if data:
#             for b in data:
#                 print(f"{b:02X}", end = " ")
#                 index +=1
#                 if (index == 10):
#                     print("")
#                     index = 0


with serial.Serial(PORT, BAUD, timeout=0.5) as ser, open("raw_capture.txt", "w") as log:
    while True:
        data = ser.read(1)
        if data:
            b = data[0]
            if b == 0x6B:
                print("")
                log.write("\n")
            print(f"{b:02X}", end=" ")
            log.write(f"{b:02X} ")
                





