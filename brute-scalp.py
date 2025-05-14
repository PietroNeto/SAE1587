import serial
from datetime import datetime

PORT = "/dev/ttyUSB0"
BAUD = 9600

with serial.Serial(PORT, BAUD, timeout=0.5) as ser, open("raw_capture.csv", "w") as log:
    log.write("timestamp,data\n")
    while True:
        data = ser.read_until(b'\\x0D')  # Exemplo: até carriage return (ajustável)
        if data:
            hex_str = ' '.join(f"{b:02X}" for b in data)
            timestamp = datetime.now().isoformat()
            log.write(f"{timestamp},{hex_str}\\n")
            print(f"{timestamp} | {hex_str}")
