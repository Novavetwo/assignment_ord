from dataclasses import dataclass           # Importa o decorador para criar classes de dados simples.
from typing import List, Tuple              # Importa tipos para anotações de listas e tuplas.
import struct
import os                                   # Importa funções para manipulação de arquivos e sistema operacional.

# Estrutura para armazenar espaços livres
class EspacoLivre:
    def __init__(self, offset, tamanho, prox=-1):
        self.offset = offset
        self.tamanho = tamanho
        self.prox = prox  # ponteiro para o próximo espaço livre

# Gerenciador de Arquivo Binário com LED encadeada no próprio arquivo
class GerenciadorDeArquivos:
    def __init__(self, caminho_arquivo):
        self.arquivo = caminho_arquivo
        if not os.path.exists(self.arquivo):
            print("Erro: arquivo não existe!")
            exit(1)
        self.led_cabeca = self._ler_cabeca_led()

    # Lê o cabeçalho (offset da cabeça da LED)
    def _ler_cabeca_led(self):
        with open(self.arquivo, 'rb') as f:
            return int.from_bytes(f.read(4), byteorder='big', signed=True)

    # Atualiza o cabeçalho (offset da cabeça da LED)
    def _atualizar_cabeca_led(self, novo_offset):
        with open(self.arquivo, 'r+b') as f:
            f.seek(0)
            f.write(novo_offset.to_bytes(4, byteorder='big', signed=True))
        self.led_cabeca = novo_offset

    # Busca um registro pelo ID
    def buscar(self, id_busca):
        id_busca = int(id_busca)
        print(f'Busca pelo registro de chave "{id_busca}"')
        with open(self.arquivo, 'rb') as f:
            f.seek(4)
            offset = 4
            while True:
                tam_bytes = f.read(2)
                if len(tam_bytes) < 2:
                    break
                tamanho = int.from_bytes(tam_bytes, byteorder='big', signed=False)
                id_bytes = f.read(4)
                if len(id_bytes) < 4:
                    break
                id_filme = int.from_bytes(id_bytes, byteorder='big', signed=True)
                dados = f.read(tamanho - 6)
                # Verifica se o registro está na LED (espaço livre)
                # Se o offset do registro está na LED, ele não é válido!
                if not self._esta_na_led(offset) and id_filme == id_busca:
                    registro = f"{id_filme}|{dados.decode('utf-8').rstrip('|')}"
                    print(f'{registro} ({tamanho} bytes)')
                    print(f'Local: offset = {offset} bytes (0x{offset:x})\n')
                    return offset
                offset += tamanho
        print('Erro: registro nao encontrado!\n')
        return None

    # Adicione este método na sua classe:
    def _esta_na_led(self, offset):
        atual = self.led_cabeca
        with open(self.arquivo, 'rb') as f:
            while atual != -1:
                if atual == offset:
                    return True
                f.seek(atual + 2)
                prox_led = int.from_bytes(f.read(4), byteorder='big', signed=True)
                atual = prox_led
        return False

    # Insere um novo registro (best-fit na LED)
    def inserir(self, id_filme, campos):
        id_filme = int(id_filme)
        dados = campos.encode('utf-8')
        tamanho = 2 + 4 + len(dados)  # 2 bytes do tamanho, 4 do id, resto dos campos

        melhor_offset = None
        melhor_tam = None
        melhor_ant = None
        ant_offset = -1
        atual_offset = self.led_cabeca

        with open(self.arquivo, 'r+b') as f:
            # Busca best-fit na LED
            while atual_offset != -1:
                f.seek(atual_offset)
                tam_espaco = int.from_bytes(f.read(2), byteorder='big', signed=False)
                prox_led = int.from_bytes(f.read(4), byteorder='big', signed=True)
                if tam_espaco >= tamanho and (melhor_tam is None or tam_espaco < melhor_tam):
                    melhor_offset = atual_offset
                    melhor_tam = tam_espaco
                    melhor_ant = ant_offset
                    if tam_espaco == tamanho:
                        break  # best-fit perfeito
                ant_offset = atual_offset
                atual_offset = prox_led

            if melhor_offset is not None:
                # Remove espaço da LED
                f.seek(melhor_offset + 2)
                prox_led = int.from_bytes(f.read(4), byteorder='big', signed=True)
                if melhor_ant == -1:
                    self._atualizar_cabeca_led(prox_led)
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

    # Remove um registro pelo ID (insere espaço na LED)
    def remover(self, id_remover):
        id_remover = int(id_remover)
        print(f'Remoção do registro de chave "{id_remover}"')
        with open(self.arquivo, 'r+b') as f:
            f.seek(4)
            offset = 4
            while True:
                pos = f.tell()
                tam_bytes = f.read(2)
                if len(tam_bytes) < 2:
                    break
                tamanho = int.from_bytes(tam_bytes, byteorder='big', signed=False)
                id_bytes = f.read(4)
                if len(id_bytes) < 4:
                    break
                id_filme = int.from_bytes(id_bytes, byteorder='big', signed=True)
                if id_filme == id_remover:
                    f.seek(pos + 2)
                    f.write(self.led_cabeca.to_bytes(4, byteorder='big', signed=True))
                    self._atualizar_cabeca_led(pos)
                    print(f'Registro removido! ({tamanho} bytes)')
                    print(f'Local: offset = {pos} bytes (0x{pos:x})\n')
                    return True
                f.seek(pos + tamanho)
                offset += tamanho
        print('Erro: registro nao encontrado!\n')
        return False

    # Imprime a LED encadeada no arquivo
    def imprimir_led(self):
        atual = self.led_cabeca
        total = 0
        print("LED -> ", end='')
        with open(self.arquivo, 'rb') as f:
            while atual != -1:
                print(f"[offset: {atual}", end='')
                f.seek(atual)
                tam_espaco = int.from_bytes(f.read(2), byteorder='big', signed=False)
                print(f", tam: {tam_espaco}]", end=' -> ')
                prox_led = int.from_bytes(f.read(4), byteorder='big', signed=True)
                atual = prox_led
                total += 1
        print("[-1]")
        print(f"Total: {total} espacos disponiveis")

# Executa operações do arquivo de operações
def executar_operacoes(caminho_operacoes, gerenciador):
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
                gerenciador.inserir(id_filme, campos)
            elif comando == 'r':
                gerenciador.remover(conteudo)
            elif comando == 'b':
                gerenciador.buscar(conteudo)

# Execução principal
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Uso: python trabalho.py -e operacoes.txt")
        print("     python trabalho.py -p")
        exit(1)
    gerenciador = GerenciadorDeArquivos("filmes.dat")
    if sys.argv[1] == "-e":
        executar_operacoes(sys.argv[2], gerenciador)
    elif sys.argv[1] == "-p":
        gerenciador.imprimir_led()