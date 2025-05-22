import tkinter as tk
from tkinter import ttk
import crcmod
from datetime import datetime
import serial
import threading

# Função CRC-16-ANSI
crc16 = crcmod.mkCrcFun(0x18005, rev=True, initCrc=0x0000, xorOut=0x0000)

# ---- GUI principal ----
root = tk.Tk()
root.title("Mensagens por FC")

# Variáveis de controle
porta_var = tk.StringVar(value="/dev/ttyUSB0")
baudrate_var = tk.StringVar(value="38400")
thread_ativa = False
serial_thread_ref = None
ser = None

# ---- Área de controle superior ----
control_frame = ttk.Frame(root)
control_frame.pack(fill="x", padx=10, pady=5)

ttk.Label(control_frame, text="Porta Serial:").pack(side="left")
porta_entry = ttk.Entry(control_frame, textvariable=porta_var, width=15)
porta_entry.pack(side="left", padx=5)

ttk.Label(control_frame, text="Baudrate:").pack(side="left")
baudrate_entry = ttk.Entry(control_frame, textvariable=baudrate_var, width=10)
baudrate_entry.pack(side="left", padx=5)

start_button = ttk.Button(control_frame, text="Iniciar")
start_button.pack(side="left", padx=10)

# ---- Notebook de abas ----
notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill='both')

treeviews = {}
ultima_linha_por_fc = {}

def extract_messages_from_frame(frame):
    messages = []
    index = 2
    total_len = len(frame)
    ido = fc = frame[0]
    idd = fc = frame[1]

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

def adicionar_mensagem(msg):
    fc_key = f"0x{msg['fc']:02X}"
    if fc_key not in treeviews:
        frame = ttk.Frame(notebook)
        notebook.add(frame, text=f"FC {fc_key}")

        tree_frame = ttk.Frame(frame)
        tree_frame.pack(expand=True, fill="both")

        tree = ttk.Treeview(tree_frame)
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        vsb.pack(side='right', fill='y')
        tree.configure(yscrollcommand=vsb.set)

        max_payload_len = 30
        columns = ["Timestamp", "ID_O", "ID_D", "Len"] + [f"B{i}" for i in range(max_payload_len)] + ["CRC", "Check"]
        tree["columns"] = columns
        tree["show"] = "headings"
        for col in columns:
            tree.heading(col, text=col)
            if col.startswith("B"):
                tree.column(col, anchor="center", width=70, stretch=False)
            else:
                tree.column(col, anchor="center", width=140, stretch=False)

        tree.pack(expand=True, fill="both")
        treeviews[fc_key] = (tree, max_payload_len)

    tree, max_payload_len = treeviews[fc_key]
    row = [
        msg["timestamp"],
        f"{msg['id_o']:02X}",
        f"{msg['id_d']:02X}",
        msg["len"]
    ] + [f"{b:02X}" for b in msg["payload"]]
    row += [""] * (max_payload_len - len(msg["payload"]))
    row += [f"{msg['crc_le']:04X}", "✔" if msg["crc_ok"] else "✘"]

    if ultima_linha_por_fc.get(fc_key) != row[1:]:
        tree.insert("", 0, values=row)
        ultima_linha_por_fc[fc_key] = row[1:]

def serial_loop():
    global ser, thread_ativa
    try:
        ser = serial.Serial(
            port=porta_var.get(),
            baudrate=int(baudrate_var.get()),
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
                            root.after(0, adicionar_mensagem, msg)
                        current_frame = []
                        collecting = False
                        start_byte_2 = None

    if ser and ser.is_open:
        ser.close()

def toggle_serial():
    global thread_ativa, serial_thread_ref
    if not thread_ativa:
        thread_ativa = True
        serial_thread_ref = threading.Thread(target=serial_loop, daemon=True)
        serial_thread_ref.start()
        start_button.config(text="Parar")
    else:
        thread_ativa = False
        start_button.config(text="Iniciar")

start_button.config(command=toggle_serial)

# ---- Estilização ----
style = ttk.Style()
style.configure("Treeview", font=("Helvetica", 11), rowheight=30)
style.configure("Treeview.Heading", font=("Helvetica", 13, "bold"))

# ---- Rodar GUI ----
root.mainloop()
