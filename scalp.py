import serial
import time
import csv
from datetime import datetime

# CONFIGURAÇÕES DA SERIAL
PORT = "/dev/ttyUSB0"
BAUD = 9600
CSV_FILE = "j1587_log.csv"

# ARMAZENAMENTO PARA DETECTAR MUDANÇAS
last_values = {}

# Função para calcular o checksum J1587
def calculate_checksum(data):
    return (256 - sum(data)) % 256

# Função para decodificar uma mensagem J1587
def decode_j1587_message(msg_bytes):
    if len(msg_bytes) < 3:
        return None

    mid = msg_bytes[0]
    pid = msg_bytes[1]
    data = msg_bytes[2:-1]
    checksum = msg_bytes[-1]

    if calculate_checksum(msg_bytes[:-1]) != checksum:
        return None

    return {
        "mid": mid,
        "pid": pid,
        "data": data,
        "checksum": checksum
    }

# Inicializa o CSV
def init_csv():
    with open(CSV_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Timestamp', 'MID', 'PID', 'Data (hex)'])

# Salva uma linha no CSV
def save_to_csv(mid, pid, data):
    timestamp = datetime.utcnow().isoformat()
    with open(CSV_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, f"{mid:#04x}", f"{pid:#04x}", ' '.join(f"{b:02X}" for b in data)])

# Loop de leitura do barramento
def log_j1587():
    with serial.Serial(PORT, BAUD, timeout=0.1) as ser:
        buffer = []
        while True:
            byte = ser.read(1)
            if byte:
                buffer.append(ord(byte))
                if len(buffer) > 2 and buffer[-1] == calculate_checksum(buffer[:-1]):
                    msg = decode_j1587_message(buffer)
                    if msg:
                        key = (msg['mid'], msg['pid'])
                        data_hex = tuple(msg['data'])
                        if key not in last_values or last_values[key] != data_hex:
                            print(f"[{datetime.utcnow().isoformat()}] MID={hex(key[0])} PID={hex(key[1])} Data={data_hex}")
                            last_values[key] = data_hex
                            save_to_csv(key[0], key[1], msg['data'])
                    buffer = []
            else:
                time.sleep(0.01)

# Execução principal
if __name__ == "__main__":
    try:
        init_csv()
        print("Iniciando leitura e salvamento J1587...")
        log_j1587()
    except KeyboardInterrupt:
        print("\nEncerrado pelo usuário.")
