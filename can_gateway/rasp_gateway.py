import crcmod
import serial
from datetime import datetime
import threading
import RPi.GPIO as GPIO
import serial
import can
import os

# Configuração porta
PORT = "/dev/ttyUSB0"
BAUD = 38400
DATA_FILTER = 0x0D

#Globais
thread_ativa = True
serial_thread_ref = None
ser = None

# Função CRC-16-ANSI
crc16 = crcmod.mkCrcFun(0x18005, rev=True, initCrc=0x0000, xorOut=0x0000)

#Enable 485
EN_485 =  4
GPIO.setmode(GPIO.BCM)
GPIO.setup(EN_485,GPIO.OUT)
GPIO.output(EN_485,GPIO.LOW)

def extract_messages_from_frame(frame):
    messages = []
    index = 2
    total_len = len(frame)
    ido = frame[0]
    idd = frame[1]

    while index < total_len - 3:
        fc = frame[index]
        den = frame[index + 1]
        length = frame[index + 2]
        payload_start = index + 3
        payload_end = payload_start + length
        crc_start = payload_end
        crc_end = crc_start + 2

        if crc_end > total_len:
            break

        payload = frame[payload_start:payload_end]
        crc_le = frame[crc_start] | (frame[crc_start + 1] << 8)
        crc_calc = crc16(bytes([fc, den, length] + payload))

        messages.append({
            'id_o': ido,
            'id_d': idd,
            'fc': fc,
            'den': den,
            'len': length,
            'payload': payload,
            'crc_le': crc_le,
            'crc_ok': crc_le == crc_calc,
            'timestamp': datetime.now().strftime("%H:%M:%S")
        })
        index = crc_end

    return messages

def send_can(Msg_485):

    payload = Msg_485['payload']

    can0 = can.interface.Bus(channel = 'can0', bustype = 'socketcan')# socketcan_native
    msg = can.Message(arbitration_id=0x123, data=payload[:8], is_extended_id=True)
    can0.send(msg)

    msg = can.Message(arbitration_id=0x123, data=payload[8:16], is_extended_id=True)
    can0.send(msg)

    msg = can.Message(arbitration_id=0x123, data=payload[16:24], is_extended_id=True)
    can0.send(msg)

def serial_loop():

    global ser, thread_ativa
    try:
        ser = serial.Serial(
            port=PORT,
            baudrate=BAUD,
            timeout=2,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS
        )
        ser.reset_input_buffer()
        ser.reset_output_buffer()
    except Exception as e:
        print("Erro ao abrir porta serial:", e)
        return

    collecting = False
    current_frame = []
    start_byte_2 = None
    thread_ativa = True

    try:
        while thread_ativa:
            if ser.in_waiting > 0:
                byte = ser.read(1)[0]
                if not collecting:
                    current_frame.append(byte)
                    if len(current_frame) == 3:
                        if current_frame[0] == 0x0D and current_frame[2] in (0x02, 0x28):
                            collecting = True
                            start_byte_2 = current_frame[1]
                        else:
                            current_frame.pop(0)
                else:
                    current_frame.append(byte)
                    if len(current_frame) >= 5:
                        if current_frame[-2] == 0x0D and current_frame[-1] == start_byte_2:
                            timestamp = datetime.now().strftime("%H:%M:%S")
                            print(f"[{timestamp}] {' '.join(f'{byte:02X}' for byte in current_frame)}")
                            messages = extract_messages_from_frame(current_frame[2:])
                            for msg in messages:
                                if msg['fc'] == DATA_FILTER: send_can(msg)
                            current_frame = []
                            collecting = False
                            start_byte_2 = None
    except:
        thread_ativa = False

    if ser and ser.is_open:
        ser.close()

## MAIN ##
while True:

    #Habilita CAN
    os.system('sudo ip link set can0 type can bitrate 100000')
    os.system('sudo ifconfig can0 up')

    try:
        serial_loop()
    except:
        print("Reiniciando...")

    #Derruba CAN
    os.system('sudo ifconfig can0 down')