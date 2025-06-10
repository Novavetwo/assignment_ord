from dataclasses import dataclass
from sys import argv
import io

@dataclass
class Registro:
    offset: int
    tamanho: int
    offsetProx: int

#----------Main--------------------
def main(operacoes):
    try:
        filmes = open('filmes.dat', 'r+b')
    except FileNotFoundError as e:
        print(f"Erro ao abrir filmes.dat: {e}")

    '''
    try:
        arq = open(operacoes, 'r')
    except FileNotFoundError as e:
        print(f"Erro ao abrir operacoes.txt: {e}")
    Desnecessário, pois o arquivo de operações é passado como argumento
    '''

    operacoes = arq.readlines()
    operacoes = removeQuebra(operacoes)
    for linha in operacoes:
            linha = linha.strip()
            if not linha:
                continue
            comando = linha[0]
            conteudo = linha[2:]
    for linha in operacoes:
        operacao = linha[0]
        if operacao == 'b':
            filmes.seek(0)
            buscaRegistro(filmes, int(linha[2:]))
        elif operacao == 'r':
            filmes.seek(0)
            removeRegistro(filmes, int(linha[2:]))
        elif operacao == 'i':
            filmes.seek(0)
            insereRegistro(filmes, linha[2:])
    
def removeQuebra(operacoes: list[str]) -> list[str]:
    '''Remove '\n' de cada string da lista *operacoes*.'''
    return [item.replace('\n', '') for item in operacoes]

#----------Busca--------------------
def buscaRegistro(filmes: io.BufferedReader, id:int) -> None:
    '''Imprime o registro de ID *id* do arquivo *filmes*. Se ID não for 
       encontrado, imprime ID não encontrado.'''
    offset = offsetRegistro(filmes, id)
    if offset == -1:
        print(f"Registro com ID {id} não encontrado.")
        return
    else:
        filmes.seek(offset)
        tamanho = int.from_bytes(filmes.read(2), 'big', signed=True)
        registro = filmes.read(tamanho).decode()
        print(f"Busca pelo registro de chave: '{id}'\n")
        print(f"{registro} '{tamanho} bytes'\n")
        print("")


def offsetRegistro(filmes: io.BufferedReader, id: int) -> int:
    '''Retorna o offset do registro com ID *id* no arquivo *filmes*. Se o ID
       não for encontrado, retorna -1.''' 
    EOF = False

    # pular cabeçalho
    filmes.seek(4)

    # loop para ler registros até que encontre o ID ou chegue ao fim do arquivo
    while not EOF:
        # calcular o offset do registro atual
        offsetAtual = filmes.tell()

        # ler tamanho do registro atual
        tamanho = int.from_bytes(filmes.read(2), 'big', signed=True)

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
            continue
        # se não foi removido, continuar a leitura
        else:
            # ler o campo ID
            idAtual = caractere + leCampo(filmes, filmes.tell())

        # verificar se o ID atual é igual ao ID procurado
        if int(idAtual) == id:
            return offsetAtual
        
        filmes.seek(offsetProx)
    
    return -1

def leCampo(filmes: io.BufferedReader, offsetAtual: int) -> int:
    ''' Retorna o primeiro campo do registro no offset *offsetAtual* de *filmes*.'''
    buffer = ""
    filmes.seek(offsetAtual)
    caractere = filmes.read(1)
    caractere = caractere.decode()
    while caractere != '|':
        buffer += caractere
        caractere = filmes.read(1)
        caractere = caractere.decode()

    return buffer

#----------Remoção--------------------
def removeRegistro(filmes: io.BufferedRandom, id: int) -> None:
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
            tamanho = int.from_bytes(filmes.read(2), 'big', signed=True)
            registro = filmes.read(tamanho).decode()
            print(f"Remoção do registro de chave: {id} ({tamanho} bytes) \n")
            print(registro)
            print(f"Local: offset = {offset}")
        else:
            print(f"Erro ao inserir registro na LED.")
            return


def remocaoLogicaRegistro(filmes: io.BufferedRandom, offset: int) -> None:
    '''Remove logicamente o registro de ID *id* no arquivo *filmes*. Se o ID não
       for encontrado, imprime ID não encontrado.'''
    
    # remover logicamente o registro
    filmes.seek(offset+2)
    caractereRemocao = '*'.encode()
    filmes.write(caractereRemocao)

    # indicar o 'próximo' registro da LED
    proximo = -2
    proximoBinario = proximo.to_bytes(4, 'big', signed=True)
    filmes.seek(offset+2+1)
    filmes.write(proximoBinario)

def insereLED(filmes: io.BufferedRandom, cabeca: int, registro: int):

    registroAtual = dadosLED(filmes, registro)
    # caso especial: LED vazia
    if cabeca == -1:
        # novo registro vira a cabeça da LED
        filmes.seek(0)
        offsetAtualBytes = registroAtual.offset.to_bytes(4, 'big', signed=True)
        filmes.write(offsetAtualBytes)
        registroAtual.offsetProx = -1
        atualizaRegistroLED(filmes, registroAtual)
        return 1

    anterior = None
    atual = dadosLED(filmes, cabeca)

    # percorrer a LED até achar o local correto
    while atual.offset != -1 and registroAtual.tamanho > atual.tamanho:
        anterior = atual
        atual = dadosLED(filmes, atual.offsetProx)

    # inserir no início (antes da cabeça)
    if anterior is None:
        filmes.seek(0)
        filmes.write(registroAtual.offset.to_bytes(4, 'big', signed=True))
        registroAtual.offsetProx = atual.offset
        atualizaRegistroLED(filmes, registroAtual)
    else:
        anterior.offsetProx = registroAtual.offset
        registroAtual.offsetProx = atual.offset
        atualizaRegistroLED(filmes, anterior)
        atualizaRegistroLED(filmes, registroAtual)
    return 1
    

def dadosLED(filmes: io.BufferedReader, offset: int) -> Registro:
    '''Retorna os dados do registro de offset *offset* no arquivo *filmes* 
       pertinentes à LED.'''
    # cabeçalho do arquivo
    if offset == 0:
        offsetProx = int.from_bytes(filmes.read(4), 'big', signed=True)
        return Registro(offset, 0, offsetProx)
    # final da LED
    elif offset == -1:
        offsetProx = -1
        return Registro(offset, 0, offsetProx)
    # meio da LED
    else:
        filmes.seek(offset)
        tamanho = int.from_bytes(filmes.read(2), 'big', signed=True)
        filmes.seek(offset+3)
        offsetProx = int.from_bytes(filmes.read(4), 'big', signed=True)
        return Registro(offset, tamanho, offsetProx)

def atualizaRegistroLED(filmes: io.BufferedWriter, registro: Registro) -> None:
    '''Atualiza o registro *registro* no arquivo *filmes* após ser realizada uma
       inserção ou remoção na LED.'''
    offsetRegistro = registro.offset
    offsetProx = registro.offsetProx

    if offsetRegistro == 0:
        filmes.seek(0)
        filmes.write(offsetProx.to_bytes(4, 'big', signed=True))
    else:
        filmes.seek(offsetRegistro+3)
        filmes.write(offsetProx.to_bytes(4, 'big', signed=True))

#----------Insersão---------------
def insereRegistro(filmes: io.BufferedRandom, registro: str) -> None:
    '''Insere *registro* no arquivo binário *filmes*'''
    # transformar *registro* em binário e obter seu tamanho
    registroBinario = registro.encode()
    tamanhoRegistro = len(registroBinario)
    tamanhoBinario = tamanhoRegistro.to_bytes(2, 'big', signed=True)

    # obter o topo da led e verificar seu tamanho
    filmes.seek(0)
    offsetAtualLED = int.from_bytes(filmes.read(4), 'big', signed=True)
    atualLED = dadosLED(filmes, offsetAtualLED)
    tamanhoAtualLED = atualLED.tamanho
    print(offsetAtualLED)

    EOL = False

    # verificar se a LED está vazia
    if offsetAtualLED == -1:
        EOL = True
    
    # encontrar |offset da LED| >= |registro| 
    while (tamanhoRegistro > tamanhoAtualLED) and (not EOL):
        atualLED = dadosLED(filmes, atualLED.offsetProx)
        tamanhoAtualLED = atualLED.tamanho
        if atualLED.offset == -1:
            EOL = True

    # verificar se a LED chegou ao fim
    if not EOL:
        # inserir registro no offset da LED caso ela não tenha acabado
        filmes.seek(atualLED.offset)
        filmes.write(tamanhoBinario)
        filmes.seek(atualLED.offset+2)
        filmes.write(registroBinario)
        atualizaLED(filmes, atualLED.offset)
    # inserir *registro* no final de *filmes* se a LED tiver acabado
    elif EOL:
        # inserir *registro* no final de *filmes*
        filmes.seek(0, 2)
        filmes.write(tamanhoBinario)
        filmes.write(registroBinario)

    idRegistro = registro.split('|')[0]
    print(f"Insersão do registro de chave {idRegistro} ({tamanhoRegistro} bytes)")
    if offsetAtualLED != -2:
        print(f"\nLocal: offset {offsetAtualLED} bytes ({hex(offsetAtualLED)})")
    else: 
        print("\nLocal: fim do arquivo")

def atualizaLED(filmes: io.BufferedRandom, offsetRemovido: int) -> None:
    '''Remove da LED o offset do registro no qual foi realizada uma insersão'''
    atualLED = dadosLED(filmes, 0)

    # quando o offset removido for a cabeça da LED
    if offsetRemovido == 0:
        offsetCabecaNova = atualLED.offsetProx
        filmes.seek(0)
        filmes.write(offsetCabecaNova.to_bytes(4, 'big', signed=True))
    # quando o offset removido for o seguinte à cabeça da LED 
    elif offsetRemovido == atualLED.offsetProx:
        proximoLED = dadosLED(filmes, atualLED.offsetProx)
        filmes.seek(atualLED.offsetProx+3)
        filmes.write(proximoLED.offsetProx)
    # quando o offset removido for qualquer outro
    else:
        # encontrar o offset removido na LED
        while offsetRemovido != atualLED.offsetProx:
            atualLED = dadosLED(filmes, atualLED.offsetProx)
        
        # remover o offset da LED
        proximoLED = dadosLED(filmes, atualLED.offsetProx)
        filmes.seek(atualLED.offsetProx+3)
        filmes.write(proximoLED.offsetProx)

        

    # # verificar se *registro* cabe no espaço atual da LED
    # if tamanhoRegistro > tamanhoAtualLED:
    #     # se couber, atualizar o topo da LED
    #     offsetNovoTopo = atualLED.offsetProx
    #     offsetNovoTopo = offsetNovoTopo.to_bytes(4, 'big')
    #     filmes.seek(0)
    #     filmes.write(offsetNovoTopo)

    #     # inserir *registro* no offset anteriormente indicado pelo topo
    #     filmes.seek(offsetAtualLED)
    #     filmes.write(tamanhoRegistro)
    #     filmes.seek(offsetAtualLED+2)
    #     filmes.write(registro)

    #     idRegistro = registro[:2]
    #     print(f"Insersão do registro de chave {idRegistro} ({tamanhoRegistro} bytes)")
    #     if offsetAtualLED != -2:
    #         print(f"\nLocal: offset {offsetAtualLED} bytes ({hex(offsetAtualLED)})")
    #     else: 
    #         print("\nLocal: fim do arquivo")

    #     # calcular o espaço disponível resultante da insersão e seu offset
    #     espacoDisponivel = tamanhoAtualLED - tamanhoRegistro
    #     offsetEspacoDisponivel = offsetAtualLED + 2 + tamanhoRegistro

def impressaoLED(filmes: io.BufferedReader) -> None:
    '''Imprime a LED resultante das operações realizadas'''
    try:
        open(filmes, 'rb')
    except FileNotFoundError as e:
        print(f"Erro impressaoLED: {e}")
    
    # ler a cabeca da LED
    filmes.seek(0)
    offsetLED = int.from_bytes(filmes.read(4), 'big')
    
    registrosLED: list[Registro] = []

    # armazenar todos os espaços informados na LED em *registrosLED*
    while offsetLED != -1:
        atualLED = dadosLED(filmes, offsetLED)
        registrosLED.append(atualLED)
        atualLED = dadosLED(filmes, atualLED.offsetProx)
    
    # imprimir a LED
    print("LED -> ")
    for registro in registrosLED:
        print(f"[offset: {registro.offset}, tam: {registro.tamanho}] -> ")
    print("FIM")

    # imprimir o tamanho da LED
    espacosLED = len(registrosLED)
    print("\nTotal: {espacosLED} espaços disponíveis")
    print("\nA LED foi impressa com sucesso")





if __name__ == "__main__":
    if argv[1] == '-e':
        arquivo_operacoes = argv[2]
        main(arquivo_operacoes)
    elif argv[1] == '-p':
        impressaoLED('filmes copy.dat')
    elif argv[1] == '-c':
        compactacao()
    else:
        raise ValueError("Erro: argumentos inválidos. Use -e, -p ou -c.")
