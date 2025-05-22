import crcmod
import binascii

def checksum8(data: bytes) -> int:
    return sum(data) & 0xFF

def checksum16(data: bytes) -> int:
    return sum(data) & 0xFFFF

def crc8_simple(data: bytes) -> int:
    crc8_func = crcmod.mkCrcFun(0x107, rev=False, initCrc=0x00, xorOut=0x00)
    return crc8_func(data)

def crc8_dallas_maxim(data: bytes) -> int:
    crc8_func = crcmod.mkCrcFun(0x131, rev=True, initCrc=0x00, xorOut=0x00)
    return crc8_func(data)

def crc32_binascii(data: bytes) -> int:
    return binascii.crc32(data) & 0xFFFFFFFF

crc_algorithms = {
    "CRC-16-IBM": crcmod.mkCrcFun(0x18005, rev=True, initCrc=0x0000, xorOut=0x0000),
    "CRC-16-MODBUS": crcmod.mkCrcFun(0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0000),
    "CRC-16-ANSI": crcmod.mkCrcFun(0x18005, rev=True, initCrc=0x0000, xorOut=0x0000),
    "CRC-16-CCITT-FALSE": crcmod.mkCrcFun(0x11021, rev=False, initCrc=0xFFFF, xorOut=0x0000),
    "CRC-16-CCITT (Augmented)": crcmod.mkCrcFun(0x11021, rev=False, initCrc=0x1D0F, xorOut=0x0000),
    "CRC-16-XMODEM": crcmod.mkCrcFun(0x11021, rev=False, initCrc=0x0000, xorOut=0x0000),
    "CRC-16-DNP": crcmod.mkCrcFun(0x13D65, rev=True, initCrc=0x0000, xorOut=0xFFFF),
    "CRC-16-IRDA": crcmod.mkCrcFun(0x18005, rev=True, initCrc=0x0000, xorOut=0xFFFF),
    "CRC-16-OPENSAFETY-A": crcmod.mkCrcFun(0x11021, rev=False, initCrc=0x0000, xorOut=0x0000),
    "CRC-16-CAN-FD": crcmod.mkCrcFun(0x18005, rev=True, initCrc=0x0000, xorOut=0x0000),
    "CRC-16-USB-PD": crcmod.mkCrcFun(0x18005, rev=False, initCrc=0xFFFF, xorOut=0x0000),
    "CRC-16-EN13757": crcmod.mkCrcFun(0x13D65, rev=True, initCrc=0x0000, xorOut=0xFFFF),
    "CRC-16-SICK": crcmod.mkCrcFun(0x11021, rev=False, initCrc=0x0000, xorOut=0xFFFF),
    "CRC-16-KERMIT": crcmod.mkCrcFun(0x11021, rev=True, initCrc=0x0000, xorOut=0x0000),

    "Checksum-8": checksum8,
    "Checksum-16": checksum16,
    "CRC-8-Simple": crc8_simple,
    "CRC-8-Dallas-Maxim": crc8_dallas_maxim,
    "CRC-32-Binascii": crc32_binascii,
}

def test_crc_with_var_start_and_crc_len(frame_hex: str, max_start=24):
    frame = bytes.fromhex(frame_hex)
    frame_len = len(frame)

    found_any = False
    # Vamos testar CRC de 1 e 2 bytes (8 ou 16 bits)
    for crc_len in [1, 2]:
        if frame_len < crc_len + 1:
            continue
        # Tentando o CRC nos últimos crc_len bytes do frame, mas testando a posição inicial dos dados
        for crc_pos_start in range(frame_len - crc_len, frame_len):
            # CRC esperado no frame, nos últimos crc_len bytes a partir de crc_pos_start
            if crc_pos_start + crc_len > frame_len:
                continue

            crc_bytes = frame[crc_pos_start:crc_pos_start+crc_len]

            if crc_len == 1:
                expected_crc = crc_bytes[0]
            else:
                # Tentar both big e little endian para 2 bytes
                expected_crc_be = int.from_bytes(crc_bytes, byteorder='big')
                expected_crc_le = int.from_bytes(crc_bytes, byteorder='little')

            # Para cada posição inicial do dado antes do CRC, testar
            for start in range(0, crc_pos_start):
                data = frame[start:crc_pos_start]

                for name, fn in crc_algorithms.items():
                    crc_calc = fn(data)

                    if crc_len == 1:
                        crc_val = crc_calc & 0xFF
                        # Garante que data e frame tenham bytes para exibir
                        data_byte = data[0] if len(data) > 0 else 0
                        crc_byte = frame[crc_pos_start] if crc_pos_start < len(frame) else 0
                        if crc_val == expected_crc:
                            print(f"Start={start:02d}[{data_byte:02X}], CRCPos={crc_pos_start:02d}[{crc_byte:02X}], Len={crc_len}B, {name:20} => Calc: 0x{crc_val:02X} | Esperado: 0x{expected_crc:02X} ✅")
                            found_any = True
                    else:
                        crc_val = crc_calc & 0xFFFF
                        data_byte = data[0] if len(data) > 0 else 0
                        crc_byte = frame[crc_pos_start] if crc_pos_start < len(frame) else 0
                        if crc_val == expected_crc_be or crc_val == expected_crc_le:
                            print(f"Start={start:02d}[{data_byte:02X}], CRCPos={crc_pos_start:02d}[{crc_byte:02X}], Len={crc_len}B, {name:20} => Calc: 0x{crc_val:04X} | Esperado: 0x{expected_crc_be:04X} (BE) / 0x{expected_crc_le:04X} (LE) ✅")
                            found_any = True

    if not found_any:
        print("Nenhum CRC/checksum válido encontrado.")

# Exemplo para testar

frames_hex = {
    "cheio": "0D2A02280AFF18044C470DFFFF11FFFF000010001000FD5B3C3AFF000076015E47",
    "meio":  "0D2A02280AFF18044C470DFFFF11FFFF000010001000FD3A3C3AFF0000760199A3",
    "vazio": "0D2A02280AFF18044C470DFFFF11FFFF000010001000FD083C3AFF000076011B6E",
    "outro": "66FF07000B051A05E101B441"
}

for label, frame_hex in frames_hex.items():
    print(f"\nTestando frame '{label}':")
    test_crc_with_var_start_and_crc_len(frame_hex, max_start=24)