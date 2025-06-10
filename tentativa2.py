from dataclasses import dataclass
from sys import argv
import io

@dataclass
class Registro:
    offset: int
    tamanho: int
    offsetProx: int

#----------Main--------------------
def main():
    try:
        filmes = open('filmes.dat', 'rb')
    except FileNotFoundError as e:
        print(f"Erro ao abrir filmes.dat: {e}")
    
    try:
        arq = open('operacoes.txt', 'r')
    except FileNotFoundError as e:
        print(f"Erro ao abrir operacoes.txt: {e}")
    
    operacoes = arq.readlines()
    operacoes = removeEspacos(operacoes)
    for linha in operacoes:
        operacao = linha[0]
        if operacao == 'b':
            buscaRegistro(filmes, int(linha[2:]))
        elif operacao == 'r':
            removeRegistro(filmes, int(linha[2:]))
        else:
            insereRegistro(filmes, linha[2:])
    
def removeEspacos(operacoes: list[str]) -> list[str]:
    '''Remove os espaços de cada linha da lista *operacoes*.'''
    for linha in operacoes:
        linha = linha.strip()

    return operacoes

#----------Busca--------------------
def buscaRegistro(filmes: io.TextIOWrapper, id:int) -> None:
    '''Imprime o registro de ID *id* do arquivo *filmes*. Se ID não for 
       encontrado, imprime ID não encontrado.'''
    offset = offsetRegistro(filmes, id)
    if offset == -1:
        print(f"Registro com ID {id} não encontrado.")
        return
    else:
        filmes.seek(offset)
        tamanho = int.from_bytes(filmes.read(2), 'big')
        registro = filmes.read(tamanho).decode()
        print(f"Busca pelo registro de chave: '{id}'\n")
        print(f"{registro} '{tamanho} bytes'\n")
        print("")


def offsetRegistro(filmes: io.TextIOWrapper, id: int) -> int:
    '''Retorna o offset do registro com ID *id* no arquivo *filmes*. Se o ID
       não for encontrado, retorna -1.''' 
    EOF = False
    offsetAtual = filmes.tell()

    # pular cabeçalho
    filmes.seek(4)

    # loop para ler registros até que encontre o ID ou chegue ao fim do arquivo
    while not EOF:

        # ler tamanho do registro atual
        tamanho = int.from_bytes(filmes.read(2), 'big')

        # calcular offset do próximo registro
        offsetProx = offsetAtual + tamanho + 2

        # ler o primeiro caractere do campo ID
        caractere = filmes.read(1).decode()

        # verificar se o arquivo chegou ao fim
        if not caractere:
            EOF = True
        # verificar se o registro atual foi removido
        elif caractere == '*':
            filmes.seek(offsetProx)     
        # se não foi removido, continuar a leitura
        else:
            # ler o campo ID
            idAtual = caractere + leCampo(filmes.dat, offsetAtual)

        # verificar se o ID atual é igual ao ID procurado
        if int(idAtual) == id:
            return offsetAtual
        
        filmes.seek(offsetProx)
    
    return -1

def leCampo(filmes: io.TextIOWrapper, offsetAtual: int) -> int:
    ''' Retorna o primeiro campo do registro no offset *offsetAtual* de *filmes*.'''
    buffer = ""
    caractere = filmes.read(1)
    while caractere != '|':
        buffer += caractere
        caractere = filmes.read(1)

    return buffer

#----------Remoção--------------------
def removeRegistro(filmes: io.TextIOWrapper, id: int) -> None:
    '''Imprime as informações do registro de ID *id* removido. Se o ID não
       for encontrado, imprime ID não encontrado.'''
    # identificar o offset do registro
    offset = offsetRegistro(filmes, id)

    # verificar se o registro foi encontrado
    if offset == -1:
        print(f"Registro com ID {id} não encontrado.")
        return
    # remover logicamente o registro se ele foi encontrado
    else:
        remocaoLogicaRegistro(filmes, offset)
        insere = insereLED(filmes, 0, offset)

        if insere == 1:
            filmes.seek(offset)
            tamanho = int.from_bytes(filmes.read(2), 'big')
            registro = filmes.read(tamanho).decode()
            print(f"Remoção do registro de chave: {id} ({tamanho} bytes) \n")
            print(registro)
            print(f"Local: offset = {offset}")
        else:
            print(f"Erro ao inserir registro na LED.")
            return


def remocaoLogicaRegistro(filmes: io.TextIOWrapper, offset: int) -> None:
    '''Remove logicamente o registro de ID *id* no arquivo *filmes*. Se o ID não
       for encontrado, imprime ID não encontrado.'''
    
    # remover logicamente o registro
    filmes.seek(offset+2)
    caractereRemocao = '*'.encode()
    filmes.write(caractereRemocao)

    # indicar o 'próximo' registro da LED
    proximo = -2
    proximoBinario = proximo.to_bytes(4, 'big')
    filmes.seek(offset+2+1)
    filmes.write(proximoBinario)

def insereLED(filmes: io.TextIOWrapper, cabeca: int, registro: int):

    # pegar os dados da posição atual da LED
    atualLED = dadosLED(filmes, cabeca)
    # pegar os dados do registro a ser inserido na LED
    registroAtual = dadosLED(filmes, registro)
    # pegar os dados do próximo registro da LED
    proximoLED = dadosLED(filmes, atualLED.offsetProx)

    # verificar se o registro a ser inserido é maior ou igual ao próximo registro da LED
    if registroAtual.tamanho >= proximoLED.tamanho:
        #inserir o registro na LED
        registroAtual.offsetProx = proximoLED.offset
        atualLED.offsetProx = registroAtual.offset

        #atualizar os registros em filmes
        atualizaRegistroLED(filmes, atualLED)
        atualizaRegistroLED(filmes, registroAtual)
        return 1
    # se for menor, chamar a função recursivamente
    else:
        return insereLED(filmes, atualLED.offsetProx, registro)
    

def dadosLED(filmes: io.TextIOWrapper, offset: int) -> Registro:
    '''Retorna os dados do registro de offset *offset* no arquivo *filmes* 
       pertinentes à LED.'''
    # cabeçalho do arquivo
    if offset == 0:
        offsetProx = int.from_bytes(filmes.read(4), 'big')
        return Registro(offset, 0, offsetProx)
    # final da LED
    elif offset == -1:
        offsetProx = -1
        return Registro(offset, 0, offsetProx)
    # meio da LED
    else:
        filmes.seek(offset)
        tamanho = int.from_bytes(filmes.read(2), 'big')
        offsetProx = int.from_bytes(filmes.read(4), 'big')
        return Registro(offset, tamanho, offsetProx)

def atualizaRegistroLED(filmes: io.TextIOWrapper, registro: Registro) -> None:
    '''Atualiza o registro *registro* no arquivo *filmes* após ser realizada uma
       inserção ou remoção na LED.'''
    offsetRegistro = registro.offset
    offsetProx = registro.offsetProx

    if offsetRegistro == 0:
        filmes.seek(0)
        filmes.write(offsetProx.to_bytes(4, 'big'))
    else:
        filmes.seek(offsetRegistro+3)
        filmes.write(offsetProx.to_bytes(4, 'big'))

if __name__ == "__main_":
    if argv[1] == '-e':
        arquivo_operacoes = argv[2]
        main(arquivo_operacoes)
    elif argv[1] == '-p':
        impressaoLED()
    elif argv[1] == '-c':
        compactacao()
    else:
        raise ValueError("Erro: argumentos inválidos. Use -e, -p ou -c.")