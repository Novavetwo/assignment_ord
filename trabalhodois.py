import os
import sys

# --- Funções utilitárias para manipulação do arquivo binário ---

def ler_cabeca_led(arquivo):
    """Lê o offset da cabeça da LED (4 bytes iniciais do arquivo)."""
    with open(arquivo, 'rb') as f:
        return int.from_bytes(f.read(4), byteorder='big', signed=True)

def atualizar_cabeca_led(arquivo, novo_offset):
    """Atualiza o offset da cabeça da LED (4 bytes iniciais do arquivo)."""
    mode = 'r+b' if os.path.exists(arquivo) else 'w+b'
    with open(arquivo, mode) as f:
        f.seek(0)
        f.write(novo_offset.to_bytes(4, byteorder='big', signed=True))

def buscar(arquivo, id_busca):
    """Busca um registro pelo ID e imprime no formato especificado."""
    id_busca = int(id_busca)
    print(f'Busca pelo registro de chave "{id_busca}"')
    with open(arquivo, 'rb') as f:
        f.seek(4)
        offset = 4
        while True:
            if len(tam_bytes) < 2:
                raise ValueError("Erro: arquivo corrompido ou truncado - tamanho insuficiente para leitura.")
                break
            tamanho = int.from_bytes(tam_bytes, byteorder='big', signed=False)
            if len(id_bytes) < 4:
                raise ValueError("Erro: arquivo corrompido ou truncado - tamanho insuficiente para leitura.")
                break
            id_filme = int.from_bytes(id_bytes, byteorder='big', signed=True)
            dados = f.read(tamanho - 6)
            # Só considera registros válidos (id_filme > 0)
            if id_filme > 0 and id_filme == id_busca:
                registro = f"{id_filme}|{dados.decode('utf-8').rstrip('|')}"
                print(f'{registro} ({tamanho} bytes)')
                print(f'Local: offset = {offset} bytes (0x{offset:x})\n')
                return offset
            offset += tamanho
    print('Erro: registro nao encontrado!\n')
    return None

def inserir(arquivo):
    """Retorna função de inserção para uso em executar_operacoes."""
    def _inserir(id_filme, campos):
        id_filme = int(id_filme)
        dados = campos.encode('utf-8')
        tamanho = 2 + 4 + len(dados)  # 2 bytes do tamanho, 4 do id, resto dos campos

        led_cabeca = ler_cabeca_led(arquivo)
        melhor_offset = None
        melhor_tam = None
        melhor_ant = None
        ant_offset = -1
        atual_offset = led_cabeca

        with open(arquivo, 'r+b') as f:
            # Busca best-fit na LED
            while atual_offset != -1:
                f.seek(atual_offset)
                tam_espaco = int.from_bytes(f.read(2), byteorder='big', signed=False)
                prox_led = int.from_bytes(f.read(4), byteorder='big', signed=True)
                # Check if the current space is large enough for the record
                is_large_enough = tam_espaco >= tamanho
                
                # Check if this space is better than the current best-fit
                is_better_fit = melhor_tam is None or tam_espaco < melhor_tam
                
                if is_large_enough and is_better_fit:
                    melhor_offset = atual_offset
                    melhor_tam = tam_espaco
                    melhor_ant = ant_offset
                    
                    # Stop searching if a perfect best-fit is found
                    if tam_espaco == tamanho:
                        break
                ant_offset = atual_offset
                atual_offset = prox_led

            if melhor_offset is not None:
                # Remove espaço da LED
                f.seek(melhor_offset + 2)
                prox_led = int.from_bytes(f.read(4), byteorder='big', signed=True)
                if melhor_ant == -1:
                    atualizar_cabeca_led(arquivo, prox_led)
                else:
                    f.seek(melhor_ant + 2)
                    f.write(prox_led.to_bytes(4, byteorder='big', signed=True))
                f.seek(melhor_offset)
                f.write(tamanho.to_bytes(2, byteorder='big', signed=False))
                f.write(id_filme.to_bytes(4, byteorder='big', signed=True))
                f.write(dados)
                print(f'Inserção do registro de chave "{id_filme}" ({tamanho} bytes)')
                print(f'Tamanho do espaço reutilizado: {melhor_tam} bytes')
                print(f'Local: offset = {melhor_offset} bytes (0x{melhor_offset:x})\n')
                return melhor_offset
            else:
                f.seek(0, 2)
                offset = f.tell()
                f.write(tamanho.to_bytes(2, byteorder='big', signed=False))
                f.write(id_filme.to_bytes(4, byteorder='big', signed=True))
                f.write(dados)
                print(f'Inserção do registro de chave "{id_filme}" ({tamanho} bytes)')
                print(f'Local: fim do arquivo\n')
                return offset
    return _inserir

def remover(arquivo):
    """Retorna função de remoção para uso em executar_operacoes."""
    def _remover(id_remover):
        id_remover = int(id_remover)
        print(f'Remoção do registro de chave "{id_remover}"')
        led_cabeca = ler_cabeca_led(arquivo)
        with open(arquivo, 'r+b') as f:
            f.seek(4)
            offset = 4
            while True:
                pos = f.tell()
                if id_filme > 0 and id_filme == id_remover:
                    if pos + 2 + 4 > os.path.getsize(arquivo):  # Check file size before seeking
                        print("Erro: arquivo corrompido ou truncado - estrutura inválida.")
                        return False
                    f.seek(pos + 2)
                    f.write(led_cabeca.to_bytes(4, byteorder='big', signed=True))
                    atualizar_cabeca_led(arquivo, pos)
                    print(f'Registro removido! ({tamanho} bytes)')
                    print(f'Local: offset = {pos} bytes (0x{pos:x})\n')
                    return True
                id_filme = int.from_bytes(id_bytes, byteorder='big', signed=True)
                if id_filme > 0 and id_filme == id_remover:
                    f.seek(pos + 2)
                    f.write(led_cabeca.to_bytes(4, byteorder='big', signed=True))
                    atualizar_cabeca_led(arquivo, pos)
                    print(f'Registro removido! ({tamanho} bytes)')
                    print(f'Local: offset = {pos} bytes (0x{pos:x})\n')
                    return True
                f.seek(pos + tamanho)
                offset += tamanho
        print('Erro: registro nao encontrado!\n')
        return False
    return _remover

    atual = led_cabeca
    total = 0
    visited_offsets = set()
    print("LED -> ", end='')
    with open(arquivo, 'rb') as f:
        while atual != -1:
            if atual in visited_offsets:
                print("\nErro: ciclo detectado na LED!")
                return
            if atual < 0 or atual >= os.path.getsize(arquivo):
                print("\nErro: offset inválido na LED!")
                return
            visited_offsets.add(atual)
            print(f"[offset: {atual}", end='')
            f.seek(atual)
            tam_espaco = int.from_bytes(f.read(2), byteorder='big', signed=False)
            print(f", tam: {tam_espaco}]", end=' -> ')
            prox_led = int.from_bytes(f.read(4), byteorder='big', signed=True)
            atual = prox_led
            total += 1
            prox_led = int.from_bytes(f.read(4), byteorder='big', signed=True)
            atual = prox_led
            total += 1
    print("fim")
    print(f"Total: {total} espaços disponíveis")
    print("A LED foi impressa com sucesso!")

def executar_operacoes(arquivo, caminho_operacoes):
    """Executa as operações do arquivo de operações, na ordem."""
    inserir_func = inserir(arquivo)
    remover_func = remover(arquivo)
    with open(caminho_operacoes, 'r', encoding='utf-8') as f:
        for linha in f:
            linha = linha.strip()
            if not linha:
                continue
            comando = linha[0]
            conteudo = linha[2:]
            if comando == 'i':
                id_filme, *resto = conteudo.split('|')
                campos = '|'.join(resto)
                inserir_func(id_filme, campos)
def main():
    # Expected command-line arguments:
    # sys.argv[1]: Flag indicating the operation mode ('-e' for executing operations, '-p' for printing LED).
    # sys.argv[2]: Path to the operations file (required if sys.argv[1] is '-e').
    if len(sys.argv) < 2:
        print("Uso: python trabalho_final.py -e operacoes.txt")
        print("     python trabalho_final.py -p")
        exit(1)

# --- main() ---

def main():
    if len(sys.argv) < 2:
        print("Uso: python trabalho_final.py -e operacoes.txt")
        print("     python trabalho_final.py -p")
        exit(1)
    arquivo = "filmes.dat"
    if not os.path.exists(arquivo):
        print("Erro: arquivo não existe!")
        exit(1)
    if sys.argv[1] == "-e":
        if len(sys.argv) < 3:
            print("Uso: python trabalho_final.py -e operacoes.txt")
            exit(1)
        executar_operacoes(arquivo, sys.argv[2])
    elif sys.argv[1] == "-p":
        imprimir_led(arquivo)
    else:
        print("Erro: Flag não reconhecida.")

if __name__ == "__main__":
    main()