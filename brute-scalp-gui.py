import serial
import threading
import tkinter as tk
from tkinter import ttk

# Configuração da porta serial
SERIAL_PORT = '/dev/ttyUSB0'  # ou COMx no Windows
BAUD_RATE = 9600

def parse_j1708_message(buffer):
    if len(buffer) < 19:
        return None  # Mensagem incompleta
    
    ID = f"{buffer[0]:02X}"
    CMD = ' '.join(f"{b:02X}" for b in buffer[1:2])
    PAYLOAD = ' '.join(f"{b:02X}" for b in buffer[2:4])
    RODAPE = ' '.join(f"{b:02X}" for b in buffer[16:19])
    
    return (ID, CMD, PAYLOAD, RODAPE)

class J1708GUI:
    def __init__(self, master):
        self.master = master
        master.title("Leitor J1708/J1587 - 9600bps")

        self.tree = ttk.Treeview(master, columns=('ID', 'CMD', 'PAYLOAD', 'RODAPÉ'), show='headings')
        for col in ('ID', 'CMD', 'PAYLOAD', 'RODAPÉ'):
            self.tree.heading(col, text=col)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Botão start/stop
        self.is_running = False
        self.btn_start_stop = ttk.Button(master, text="Start", command=self.toggle_reading)
        self.btn_start_stop.pack(pady=10)

        self.serial_thread = None

    def toggle_reading(self):
        if self.is_running:
            # Parar leitura
            self.is_running = False
            self.btn_start_stop.config(text="Start")
        else:
            # Iniciar leitura
            self.is_running = True
            self.btn_start_stop.config(text="Stop")
            if self.serial_thread is None or not self.serial_thread.is_alive():
                self.serial_thread = threading.Thread(target=self.read_serial)
                self.serial_thread.daemon = True
                self.serial_thread.start()

    def read_serial(self):
        try:
            with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser:
                buffer = []
                while self.is_running:
                    byte = ser.read(1)
                    if byte:
                        b = byte[0]
                        buffer.append(b)
                        if b == 0x6B and len(buffer) >= 19:
                            parsed = parse_j1708_message(buffer)
                            if parsed and buffer[1] == 0xF2:
                                self.master.after(0, self.insert_row, parsed)
                            buffer = []
                        if len(buffer) > 50:
                            buffer = []
        except serial.SerialException as e:
            print(f'Erro na porta serial: {e}')

    def insert_row(self, parsed):
        self.tree.insert('', 0, values=parsed)
        if len(self.tree.get_children()) > 100:
            self.tree.delete(self.tree.get_children()[-1])

if __name__ == '__main__':
    root = tk.Tk()
    app = J1708GUI(root)
    root.mainloop()
