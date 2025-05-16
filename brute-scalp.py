import serial
from collections import defaultdict

PORT = "/dev/ttyUSB0"
BAUD = 9600
DATALEN = 10

ser = {}

try:
    ser = serial.Serial(PORT, BAUD, timeout=0.5)
except:
    pass

if ser:
    log = open("raw_capture.txt", "w")
    while True:
        try:
            data = ser.read(DATALEN)
            if data:
                hex_line = ' '.join(f"{b:02X}" for b in data)
                print(hex_line)
                if log: log.write(hex_line)
        except:
            break


print("processing data")

# Função para ler e converter o conteúdo do arquivo em bytes
def ler_bytes_arquivo(caminho):
    with open(caminho, "r") as f:
        conteudo = f.read()
    hex_bytes = conteudo.strip().split()
    return [int(b, 16) for b in hex_bytes]

# Função para contar sequências repetidas de tamanho N
def contar_janelas(byte_array, tamanho_janela):
    contagem = defaultdict(int)
    for i in range(len(byte_array) - tamanho_janela + 1):
        janela = tuple(byte_array[i:i + tamanho_janela])
        contagem[janela] += 1
    return contagem

# Função genérica para imprimir os top N resultados de qualquer contagem
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

# Caminho do arquivo
arquivo = "raw_capture.txt"
bytes_lidos = ler_bytes_arquivo(arquivo)

# Processa janelas de 2, 3, 4 e 5 bytes
contagens = {
    2: contar_janelas(bytes_lidos, 2),
    3: contar_janelas(bytes_lidos, 3),
    4: contar_janelas(bytes_lidos, 4),
    5: contar_janelas(bytes_lidos, 5),
}

print("\n\nMaior repetição")
# Imprime os top 20 de cada
for tamanho, contagem in contagens.items():
    imprimir_top(contagem, tamanho)

# Imprime os top 20 de cada
for tamanho, contagem in contagens.items():
    imprimir_top(contagem, tamanho, 0x08)

# Imprime os top 20 de cada
for tamanho, contagem in contagens.items():
    imprimir_top(contagem, tamanho, 0x6B)

print("\n\nMenor repetição")
# Imprime os top 20 de cada
for tamanho, contagem in contagens.items():
    imprimir_top(contagem, tamanho,reverse=False)

# Imprime os top 20 de cada
for tamanho, contagem in contagens.items():
    imprimir_top(contagem, tamanho, 0x08,reverse=False)