import serial
import time
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk

PORT = ""  # Porta inicial vazia
BAUD = 9600

last_values = {}  # (mid, pid) -> data
widgets = {}      # (mid, pid) -> tkinter StringVar
frames = {}       # MID -> LabelFrame
serial_thread = None
serial_running = False

# padrão de Msg
STX = 0x08
ETX = 0x6B

# Função para calcular o checksum
def isValid(data):
    if(data[0]==STX and data[-1]==ETX):
        return True
    
    return False

# Decodifica uma mensagem J1587
def decode_generic_message(msg_bytes):
    if len(msg_bytes) < 3:
        return None
    mid = msg_bytes[0]
    pid = msg_bytes[1]
    data = msg_bytes[2:-1]
    checksum = msg_bytes[-1]
    if isValid(msg_bytes):
        return None
    return {
        "mid": mid,
        "pid": pid,
        "data": data,
        "checksum": checksum
    }

# Atualiza a tabela na interface
def update_table(mid, pid, data):
    key = (mid, pid)
    data_str = ' '.join(f"{b}" for b in data)
    if key not in widgets:
        if mid not in frames:
            frames[mid] = ttk.LabelFrame(scrollable_frame, text=f"MID {mid:#04x}")
            frames[mid].pack(fill='x', expand=True, padx=10, pady=10)
        var = tk.StringVar()
        widgets[key] = var
        row = ttk.Frame(frames[mid])
        ttk.Label(row, text=f"PID {pid:#04x}", width=15).pack(side='left')
        ttk.Label(row, textvariable=var, width=100).pack(side='left')
        row.pack(anchor='w')
    widgets[key].set(data_str)

# Thread de leitura serial
def read_serial():
    global serial_running
    buffer = []
    try:
        with serial.Serial(PORT, BAUD, timeout=0.1) as ser:
            serial_running = True
            app.after(0, lambda: status_var.set(f"Conectado à porta {PORT}"))
            while serial_running:
                byte = ser.read(1)
                if byte:
                    buffer.append(ord(byte))
                    if len(buffer) > 2 and isValid(buffer):
                        msg = decode_generic_message(buffer)
                        if msg:
                            key = (msg['mid'], msg['pid'])
                            data = tuple(msg['data'])
                            if key not in last_values or last_values[key] != data:
                                last_values[key] = data
                                app.after(0, update_table, msg['mid'], msg['pid'], msg['data'])
                        buffer = []
                else:
                    time.sleep(0.01)
    except serial.SerialException:
        app.after(0, lambda: status_var.set("Erro ao abrir porta serial."))

# Inicia a leitura serial
def start_serial():
    global PORT, serial_thread, serial_running
    if serial_running:
        status_var.set("Leitura já em andamento.")
        return
    PORT = port_entry.get().strip()
    if not PORT:
        status_var.set("Informe uma porta serial válida.")
        return
    status_var.set(f"Tentando conectar na porta {PORT}...")
    serial_thread = threading.Thread(target=read_serial, daemon=True)
    serial_thread.start()

# Interface Tkinter
app = tk.Tk()
app.title("J1587 PID Monitor")
app.geometry("600x500")

# Topo: entrada de porta e botão iniciar
top_frame = ttk.Frame(app)
top_frame.pack(padx=10, pady=5, fill='x')

port_label = ttk.Label(top_frame, text="Porta Serial:")
port_label.pack(side='left')

port_entry = ttk.Entry(top_frame, width=15)
port_entry.pack(side='left', padx=5)

start_button = ttk.Button(top_frame, text="Iniciar", command=start_serial)
start_button.pack(side='left', padx=5)

status_var = tk.StringVar()
status_label = ttk.Label(top_frame, textvariable=status_var, foreground='blue')
status_label.pack(side='left', padx=10)
status_var.set("Aguardando porta...")

# Área principal com scrollbar
container = ttk.Frame(app)
container.pack(fill='both', expand=True, padx=10, pady=10)

canvas = tk.Canvas(container)
scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
scrollable_frame = ttk.Frame(canvas)

scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

app.mainloop()