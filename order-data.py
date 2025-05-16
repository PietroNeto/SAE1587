from collections import defaultdict
import os

# Lista de sequências de início válidas
START_SEQS = [(0xE5, 0xAB), (0xE5, 0x01)]

def ler_bytes_arquivo(caminho):
    with open(caminho, "r") as f:
        conteudo = f.read()
    hex_bytes = conteudo.strip().split()
    return [int(b, 16) for b in hex_bytes]

def comeca_com_seq(byte_array, i):
    """Retorna a sequência de início correspondente a partir da posição i, ou None."""
    for seq in START_SEQS:
        if byte_array[i:i + len(seq)] == list(seq):
            return seq
    return None

def extrair_blocos_com_multiplos_START_SEQS(byte_array):
    blocos = []
    i = 0
    while i < len(byte_array) - 1:  # Precisa de pelo menos 2 bytes para comparar
        seq_encontrada = comeca_com_seq(byte_array, i)
        if seq_encontrada:
            inicio = i
            i += len(seq_encontrada)
            while i < len(byte_array) - 1:
                if comeca_com_seq(byte_array, i):
                    break
                i += 1
            blocos.append(tuple(byte_array[inicio:i]))
        else:
            i += 1
    return blocos

def contar_blocos(blocos):
    contagem = defaultdict(int)
    for bloco in blocos:
        contagem[bloco] += 1
    return contagem

def salvar_blocos_ordenados_formatados(contagem, caminho_original):
    saida_path = os.path.splitext(caminho_original)[0] + "_ordered.txt"
    
    blocos_ordenados = sorted(
        contagem.items(),
        key=lambda x: (-x[1], x[0])
    )

    with open(saida_path, "w") as f:
        f.write(f"Blocos que começam com qualquer um dos {START_SEQS} (ordenados por frequência e valor):\n\n")
        for seq, count in blocos_ordenados:
            bytes_formatados = '  '.join(f'{b:02X}' for b in seq)
            f.write(f"{bytes_formatados} [{count}x]\n")

    print(f"\nArquivo salvo como: {saida_path}")

# Main
if __name__ == "__main__":
    arquivo = "data.txt"  # Substitua pelo seu arquivo real
    bytes_lidos = ler_bytes_arquivo(arquivo)
    blocos = extrair_blocos_com_multiplos_START_SEQS(bytes_lidos)
    contagem = contar_blocos(blocos)
    salvar_blocos_ordenados_formatados(contagem, arquivo)
