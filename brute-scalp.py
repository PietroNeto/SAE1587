import serial
from collections import defaultdict
import time

PORT = "/dev/ttyUSB0"
BAUD = 38400
DATALEN = 10

ser = None

try:
    ser = serial.Serial(
        port=PORT,
        baudrate=BAUD,
        timeout=2,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS
    )
except Exception as e:
    print(f"Erro ao abrir a porta serial: {e}")

if ser and ser.is_open:

    # Limpa buffers de entrada e saída
    ser.reset_input_buffer()
    ser.reset_output_buffer()

    log = open("raw_capture.txt", "w")
    line = 0
    print("Iniciando captura...")

    try:
        while True:
            data = ser.read(1)

            if data:
                byte = data[0]
                timestamp = time.time()
                hex_byte = f"{byte:02X}"
                
                print(f"{hex_byte}", end=" ")
                if log:
                    log.write(f"{hex_byte} ")

                line += 1
                if line == DATALEN:
                    print()
                    line = 0

    except KeyboardInterrupt:
        print("\nInterrompido pelo usuário.")
    except Exception as e:
        print(f"\nErro durante leitura: {e}")
    finally:
        ser.close()
        log.close()
        print("Porta serial fechada e log salvo.")

print("Processando dados...")

# ---------- ANÁLISE DOS DADOS ----------

def ler_bytes_arquivo(caminho):
    with open(caminho, "r") as f:
        conteudo = f.read()
    hex_bytes = conteudo.strip().split()
    return [int(b, 16) for b in hex_bytes]

def contar_janelas(byte_array, tamanho_janela):
    contagem = defaultdict(int)
    for i in range(len(byte_array) - tamanho_janela + 1):
        janela = tuple(byte_array[i:i + tamanho_janela])
        contagem[janela] += 1
    return contagem

def imprimir_top(contagem, tamanho_janela, prefixo=None, reverse=True):
    if prefixo is not None:
        contagem = {seq: count for seq, count in contagem.items() if seq[0] == prefixo}
        titulo = f"Top 5 janelas de {tamanho_janela} bytes começando com {prefixo:02X}:"
    else:
        titulo = f"Top 5 janelas de {tamanho_janela} bytes:"
    
    print(f"\n{titulo}")
    top = sorted(contagem.items(), key=lambda x: x[1], reverse=reverse)[:20]
    for seq, count in top:
        hex_seq = ' '.join(f'{b:02X}' for b in seq)
        print(f"{hex_seq} -> {count} vezes")

arquivo = "raw_capture.txt"
bytes_lidos = ler_bytes_arquivo(arquivo)

contagens = {
    1: contar_janelas(bytes_lidos, 1),
    2: contar_janelas(bytes_lidos, 2),
    3: contar_janelas(bytes_lidos, 3),
    4: contar_janelas(bytes_lidos, 4),
    5: contar_janelas(bytes_lidos, 5),
}

print("\n\nMaior repetição:")
for tamanho, contagem in contagens.items():
    imprimir_top(contagem, tamanho)
