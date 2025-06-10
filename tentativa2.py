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
    
    try:
        arq = open(operacoes, 'r')
    except FileNotFoundError as e:
        print(f"Erro ao abrir operacoes.txt: {e}")

    operacoes = arq.readlines()
    operacoes = removeQuebra(operacoes)
    for linha in operacoes:
        operacao = linha[0]
        if operacao == 'b':
            filmes.seek(0)
            buscaRegistro(filmes, linha[2:])
        elif operacao == 'r':
            filmes.seek(0)
            #breakpoint()
            #print("Fim")
            # if linha[2:] == '160':
            #     arq.close()
            #     return
            removeRegistro(filmes, linha[2:])
            #impressaoLED(filmes)
            #filmes = pausaParaVerificacao(filmes, "filmes.dat")

        elif operacao == 'i':
            filmes.seek(0)
            insereRegistro(filmes, linha[2:])
    
def removeQuebra(operacoes: list[str]) -> list[str]:
    '''Remove '\n' de cada string da lista *operacoes*.'''
    return [item.replace('\n', '') for item in operacoes]

def pausaParaVerificacao(filmes: io.BufferedReader, caminho:str) -> io.BufferedReader:
    filmes.close()
    input()
    return open(caminho, 'r+b')


#----------Busca--------------------
def buscaRegistro(filmes: io.BufferedReader, id:str) -> None:
    '''Imprime o registro de ID *id* do arquivo *filmes*. Se ID não for 
       encontrado, imprime ID não encontrado.'''
    offset = offsetRegistro(filmes, id)
    if offset == -1:
        print(f"Busca pelo registro de chave '{id}'.")
        print("Erro: registro não encontrado\n")
        return
    else:
        filmes.seek(offset)
        tamanho = int.from_bytes(filmes.read(2), 'big', signed=True)
        registro = filmes.read(tamanho).decode()
        print(f"Busca pelo registro de chave: '{id}'")
        print(f"{registro} '{tamanho} bytes'\n")


def offsetRegistro(filmes: io.BufferedReader, id: str) -> int:
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


##############OLA TAMO DEBUGANDO
        # if id == '160':
        #     filmes.close()
        #     print(f"Tamanho registro atual lido {tamanho} - Offset {offsetAtual}")

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
            idAtual = caractere
            caractere = filmes.read(1).decode()
            while caractere != "|":
                idAtual = idAtual + caractere
                caractere = filmes.read(1).decode()

        # verificar se o ID atual é igual ao ID procurado
        if idAtual == id:
            return offsetAtual
        
        filmes.seek(offsetProx)
    
    return -1

#----------Remoção--------------------
def removeRegistro(filmes: io.BufferedRandom, id: str) -> None:
    '''Imprime as informações do registro de ID *id* removido. Se o ID não
       for encontrado, imprime ID não encontrado.'''
    # identificar o offset do registro
    offset = offsetRegistro(filmes, id)
    print(f"Removendo registro: {id}")

    # verificar se o registro foi encontrado
    if offset == -1:
        print(f"Remoção do registro de chave '{id}'")
        print(f"Erro: registro não encontrado!\n")
        return
    # remover logicamente o registro se ele foi encontrado
    else:
        remocaoLogicaRegistro(filmes, offset)
        insere = insereLED(filmes, 0, offset)

        if insere == 1:
            filmes.seek(offset)
            tamanho = int.from_bytes(filmes.read(2), 'big', signed=True)
            print(f"Remoção do registro de chave: {id}")
            print(f"Registro removido! ({tamanho} bytes)")
            print(f"Local: offset = {offset}\n")
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

def insereLED(filmes: io.BufferedRandom, cabeca: int, offsetRegistro: int):

    atualLED = dadosLED(filmes, cabeca)
    registroAtual = dadosLED(filmes, offsetRegistro)

    # ler o offset da cabeça da LED
    filmes.seek(0)
    cabecaLED = filmes.read(4)
    cabecaLED = int.from_bytes(cabecaLED, 'big', signed=True)

    # caso especial: LED vazia
    if cabecaLED == -1:
        # o registro removido vira a cabeça da LED
        filmes.seek(0)
        offsetAtualBytes = registroAtual.offset.to_bytes(4, 'big', signed=True)
        filmes.write(offsetAtualBytes)
        registroAtual.offsetProx = -1
        atualizaRegistroLED(filmes, registroAtual)
        return 1
    # LED não vazia
    else:
        # verificar se o registro removido é menor que a cabeça da LED
        atualLED = dadosLED(filmes, cabecaLED)
        if registroAtual.tamanho <= atualLED.tamanho:
            # inserir o registro removido na cebeça da LED
            registroAtual.offsetProx = atualLED.offset
            filmes.seek(0)
            offsetBytes = registroAtual.offset.to_bytes(4, 'big', signed=True)
            filmes.write(offsetBytes)
            atualizaRegistroLED(filmes, registroAtual)
            return 1
        else:
            # encontrar o local de insersão do registro removido
            while (registroAtual.tamanho > atualLED.tamanho) and (atualLED.offset != -1):
                anteriorLED = atualLED
                atualLED = dadosLED(filmes, atualLED.offsetProx)
            
            # verificar se a LED acabou
            if atualLED.offset == -1:
                # inserir o registro removido no final da LED
                anteriorLED.offsetProx = registroAtual.offset
                registroAtual.offsetProx = -1
            else:
                # inserir o registr removido no meio da LED
                anteriorLED.offsetProx = registroAtual.offset
                registroAtual.offsetProx = atualLED.offset
            
            atualizaRegistroLED(filmes, anteriorLED)
            atualizaRegistroLED(filmes, registroAtual)
            return 1
    

def dadosLED(filmes: io.BufferedReader, offset: int) -> Registro:
    '''Retorna os dados do registro de offset *offset* no arquivo *filmes* 
       pertinentes à LED.'''
    # cabeçalho do arquivo
    if offset == 0:
        filmes.seek(offset)
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
    print(f"Insersão do registro de chave '{idRegistro}' ({tamanhoRegistro} bytes)")
    #breakpoint()
    if offsetAtualLED != -1:
        print(f"Local: offset {offsetAtualLED} bytes ({hex(offsetAtualLED)})\n")
    else: 
        print("Local: fim do arquivo\n")

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
        filmes.seek(atualLED.offset+3)
        filmes.write(proximoLED.offsetProx.to_bytes(4, 'big', signed=True))
    # quando o offset removido for qualquer outro
    else:
        # encontrar o offset removido na LED
        anterior = None
        while offsetRemovido != atualLED.offset:
            anterior = atualLED
            atualLED = dadosLED(filmes, atualLED.offsetProx)
        
        # remover o offset da LED
        anterior.offsetProx = atualLED.offsetProx
        #proximoLED = dadosLED(filmes, atualLED.offsetProx)
        filmes.seek(anterior.offset+3)
        filmes.write(atualLED.offsetProx.to_bytes(4, 'big', signed=True))

        

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

#----------Impressão da LED---------------
def impressaoLED(nomefilmes: str) -> None:
    '''Imprime a LED resultante das operações realizadas'''
    try:
        filmes = open(nomefilmes, 'rb')
    except FileNotFoundError as e:
        print(f"Erro impressaoLED: {e}")
    
    # ler a cabeca da LED
    filmes.seek(0)
    offsetLED = int.from_bytes(filmes.read(4), 'big', signed=True)
    registrosLED: list[Registro] = []

    # armazenar todos os espaços informados na LED em *registrosLED*
    while offsetLED != -1:
        atualLED = dadosLED(filmes, offsetLED)
        registrosLED.append(atualLED)
        atualLED = dadosLED(filmes, atualLED.offsetProx)
        offsetLED = atualLED.offset
    
    # imprimir a LED
    print("LED -> ")
    for registro in registrosLED:
        print(f"[offset: {registro.offset}, tam: {registro.tamanho}] -> ")
    print("FIM")

    # imprimir o tamanho da LED
    espacosLED = len(registrosLED)
    print(f"Total: {espacosLED} espaços disponíveis")
    print("A LED foi impressa com sucesso!")


if __name__ == "__main__":
    if argv[1] == '-e':
        arquivo_operacoes = argv[2]
        main(arquivo_operacoes)
    elif argv[1] == '-p':
        impressaoLED('filmes.dat')
    elif argv[1] == '-c':
        compactacao()
    else:
        raise ValueError("Erro: argumentos inválidos. Use -e, -p ou -c.")