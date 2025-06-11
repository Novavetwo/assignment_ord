import io

from dataclasses import dataclass
from sys import argv


@dataclass
class Registro:
    offset: int
    tamanho: int
    offset_prox: int


def remove_quebra(operacoes: list[str]) -> list[str]:
    """
    Remove '\n' de cada string da lista *operacoes*.
    """


    return [item.replace('\n', '') for item in operacoes]


# FIXME: código temporário para testes manuais.
# Remover antes da entrega final.
def pausa_para_verificacao(
        filmes: io.BufferedReader,
        caminho: str
) -> io.BufferedReader:
    """
    Pausa a execução do programa para verificação do arquivo *filmes*.
    Fecha o arquivo *filmes* e retorna um novo
    arquivo aberto em modo 'r+b'.
    """


    filmes.close()
    input()

    return open(caminho, 'r+b')


def remocao_logica_registro(
        filmes: io.BufferedRandom,
        offset: int
) -> None:
    """
    Remove logicamente o registro de ID *id* no arquivo *filmes*.
    Se o ID não for encontrado, imprime ID não encontrado.
    """


    # Remove logicamente o registro.
    filmes.seek(offset+2)
    caractere_remocao = '*'.encode()
    filmes.write(caractere_remocao)

    # Indica o próximo registro da LED.
    proximo_reg_led = -2
    proximo_reg_led_binario = proximo_reg_led.to_bytes(
        4, 'big', signed=True
        )
    filmes.seek(offset+2+1)
    filmes.write(proximo_reg_led_binario)


def dados_led(filmes: io.BufferedReader, offset: int) -> Registro:
    """
    Retorna os dados do registro de offset *offset* no arquivo *filmes*
    pertinentes à LED.
    Se o offset for 0, retorna o cabeçalho da LED.
    Se o offset for -1, retorna o final da LED.
    """

    # FIXME: print para depuração.
    # Remover antes da entrega final.
    print(f"Dados LED: offset {offset}")

    if offset == 0: # Offset 0 indica o cabeçalho da LED.
        filmes.seek(offset)
        offsetProx = int.from_bytes(filmes.read(4), 'big', signed=True)
        return Registro(offset, 0, offsetProx)

    elif offset == -1: # Offset -1 indica o final da LED.
        offsetProx = -1
        return Registro(offset, 0, offsetProx)

    # Lê os dados do registro de offset *offset*.
    else:
        filmes.seek(offset)
        tamanho = int.from_bytes(filmes.read(2), 'big', signed=True)
        filmes.seek(offset+3)
        offsetProx = int.from_bytes(filmes.read(4), 'big', signed=True)
        
        return Registro(offset, tamanho, offsetProx)


def atualiza_registro_led(
        filmes: io.BufferedWriter,
        registro: Registro
) -> None:
    """
    Atualiza o registro *registro* no arquivo *filmes* após
    ser realizada uma inserção ou remoção na LED.
    """


    offset_registro = registro.offset
    offset_prox = registro.offset_prox

    # Verifica se o registro é a cabeça da LED.
    if offset_registro == 0:
        filmes.seek(0)
        filmes.write(offset_prox.to_bytes(4, 'big', signed=True))

    # Verifica se o registro é o seguinte à cabeça da LED.
    else:
        filmes.seek(offset_registro+3)
        filmes.write(offset_prox.to_bytes(4, 'big', signed=True))


def atualiza_led(filmes: io.BufferedRandom, offset_removido: int) -> None:
    """
    Remove da LED o offset do registro no qual
    foi realizada uma inserção ou remoção.
    Se o offset removido for a cabeça da LED, atualiza o topo da LED.
    Se o offset removido for o seguinte à cabeça da LED,
    atualiza o próximo.
    """


    led_atual = dados_led(filmes, 0)

    if offset_removido == 0: # Offset 0 indica a cabeça da LED.
        offset_cabeca_nova = led_atual.offset_prox
        filmes.seek(0)
        filmes.write(offset_cabeca_nova.to_bytes(
            4, 'big', signed=True)
            )

    # Offset seguinte à cabeça da LED.
    elif offset_removido == led_atual.offset_prox:
        proximo_led = dados_led(filmes, led_atual.offset_prox)
        filmes.seek(led_atual.offset+3)
        filmes.write(proximo_led.offset_prox.to_bytes(
            4, 'big', signed=True)
            )

    # FIXME: há um erro de lógica aqui.
    else: # Offset removido não é a cabeça da LED.
        # Encontra o offset removido na LED.
        anterior = None

        while offset_removido != led_atual.offset:
            anterior = led_atual
            led_atual = dados_led(filmes, led_atual.offset_prox)

        # Remove o offset da LED.
        anterior.offset_prox = led_atual.offset_prox

        """
        FIXME: Código comentado que não foi utilizado,
        mas pode ser útil para referência futura.

        proximo_led = dados_led(filmes, led_atual.offset_prox)
        """

        # FIXME: Verificar a lógica de atualização da LED.
        # Atualiza o registro anterior ao removido.
        filmes.seek(anterior.offset+3)
        filmes.write(led_atual.offset_prox.to_bytes(
            4, 'big', signed=True)
            )
"""
FIXME: Código comentado que não foi utilizado,
mas pode ser útil para referência futura.

# Verifica se *registro* cabe no espaço atual da LED.
if tamanho_registro > tamanho_atual_led:
    # Atualiza o topo da LED.
    offset_topo_novo = atualLED.offsetProx
    offset_topo_novo = offset_topo_novo.to_bytes(4, 'big')
    filmes.seek(0)
    filmes.write(offset_topo_novo)

    # Insere *registro* no offset anteriormente indicado pelo topo.
    filmes.seek(offset_atual_led)
    filmes.write(tamanho_registro)
    filmes.seek(offset_atual_led+2)
    filmes.write(registro)

    id_registro = registro[:2]
    print(f"Inserção do registro de chave {id_registro} (
    {tamanho_registro} bytes)"
    )

    if offset_atual_led != -2:
        print(f"\nLocal: offset {offset_atual_led} bytes (
        {hex(offset_atual_led)})"
        )

    else:
        print("\nLocal: fim do arquivo")

        # Calcula o espaço disponível resultante 
        # da inserção e seu offset.
        espaco_disponivel = tamanho_atual_led - tamanho_registro
        offset_espaco_disponivel = (
        offset_atual_led + 2 + tamanho_registro
        )
"""


def offset_registro(filmes: io.BufferedReader, id: str) -> int:
    """
    Retorna o offset do registro com ID *id* no arquivo *filmes*.
    Se o ID não for encontrado, retorna -1.
    """


    EOF = False # End Of File — indica o fim do arquivo.

    filmes.seek(4) # Pula cabeçalho do arquivo.

    """
    FIXME: Código sugerido que não foi utilizado,
    mas pode ser útil para referência futura.

    id = id.strip()  # Remove espaços em branco desnecessários.
    """

    # Lê registros até encontrar o ID ou chegar ao fim do arquivo.
    while not EOF:
        offset_atual = filmes.tell()
        tamanho = int.from_bytes(filmes.read(2), 'big', signed=True)
        offset_prox = offset_atual + tamanho + 2

        # Lê o primeiro caractere do campo ID.
        caractere = filmes.read(1).decode()

        if not caractere:
            EOF = True

        # Verifica se o registro atual foi removido.
        elif caractere == '*':
            filmes.seek(offset_prox)
            continue

        else:
            # Lê o ID.
            id_atual = caractere
            caractere = filmes.read(1).decode()

            # Lê o ID até encontrar o caractere '|'.
            while caractere != "|":
                id_atual = id_atual + caractere
                caractere = filmes.read(1).decode()

        if id_atual == id:
            return offset_atual

        filmes.seek(offset_prox)

    return -1


def impressao_led(nome_filmes: str) -> None:
    """
    Imprime a LED do arquivo *nome_filmes*.
    Se o arquivo não for encontrado, imprime mensagem de erro.
    """

    # Abre o arquivo *nome_filmes* em modo leitura binária.
    try:
        filmes = open(nome_filmes, 'rb')
    except FileNotFoundError as e:
        print(f"Erro impressaoLED: {e}")

    # Lê o cabeçalho da LED, que contém o offset da cabeça.
    filmes.seek(0)
    offset_led = int.from_bytes(filmes.read(4), 'big', signed=True)
    registros_led: list[Registro] = []

    # FIXME: Após a inserção do registro 72, caso tente imprimir,
    # o loop não para.
    # Armazena todos os espaços informados na LED em *registrosLED*.
    while offset_led != -1:
        # FIXME: print temporário para depuração.
        # Remover antes da entrega final.
        print(f"Offset LED: {offset_led}")

        # FIXME: código temporário para testes manuais.
        # Remover antes da entrega final.
        filmes = pausa_para_verificacao(filmes, nome_filmes)

        led_atual = dados_led(filmes, offset_led)
        registros_led.append(led_atual)
        led_atual = dados_led(filmes, led_atual.offset_prox)
        offset_led = led_atual.offset

    # Imprime os registros da LED.
    print("LED -> ")
    for registro in registros_led:
        print(f"[offset: {registro.offset}, "
              f"tam: {registro.tamanho}] -> "
        )
    print("FIM")

    # Imprime o total de espaços disponíveis na LED.
    espacosLED = len(registros_led)
    print(f"Total: {espacosLED} espaços disponíveis")
    print("A LED foi impressa com sucesso!")


def compactacao() -> None:
    """
    Compacta o arquivo filmes.dat, removendo registros removidos
    e compactando os espaços disponíveis.
    """


    try:
        filmes = open('filmes.dat', 'r+b')
    except FileNotFoundError as e:
        print(f"Erro ao abrir filmes.dat: {e}")
        return

    # Lê o cabeçalho da LED.
    filmes.seek(0)
    cabeca_led = int.from_bytes(filmes.read(4), 'big', signed=True)

    if cabeca_led == -1:
        print("LED vazia. Nada a compactar.")
        return

    # Compacta o arquivo removendo registros removidos.
    offset_atual = 4  # Pula o cabeçalho.
    while offset_atual < os.path.getsize('filmes.dat'):
        filmes.seek(offset_atual)
        tamanho = int.from_bytes(filmes.read(2), 'big', signed=True)
        if tamanho < 0:  # Registro removido.
            filmes.seek(offset_atual)
            filmes.write(b'\x00\x00')  # Escreve espaço vazio.
            offset_atual += 2
        else:
            offset_atual += tamanho + 2

    print("Compactação concluída com sucesso!")


def insere_led(
        filmes: io.BufferedRandom,
        cabeca: int,
        offset_registro: int
) -> int:
    """
    Insere o registro removido na LED do arquivo *filmes*.
    Retorna 1 se a inserção foi bem sucedida, ou 0 caso contrário.
    """


    espaco_atual_led = dados_led(filmes, cabeca)
    registro_atual = dados_led(filmes, offset_registro)

    # Lê o offset da cabeça da LED.
    filmes.seek(0)
    cabeca_led = filmes.read(4)
    cabeca_led = int.from_bytes(cabeca_led, 'big', signed=True)

    # LED vazia: nenhum espaço disponível.
    if cabeca_led == -1:
        # Torna o registro removido a cabeça da LED.
        filmes.seek(0)
        offset_atual_bytes = registro_atual.offset.to_bytes(
            4, 'big', signed=True
            )
        filmes.write(offset_atual_bytes)
        registro_atual.offset_prox = -1
        atualiza_registro_led(filmes, registro_atual)

        return 1

    else: # LED não vazia: há espaços disponíveis.
        espaco_atual_led = dados_led(filmes, cabeca_led)

        # Verifica se o registro removido é menor que a cabeça da LED.
        if registro_atual.tamanho <= espaco_atual_led.tamanho:
            # Insere o registro removido na cebeça da LED.
            registro_atual.offset_prox = espaco_atual_led.offset
            filmes.seek(0)
            offset_bytes = registro_atual.offset.to_bytes(
                4, 'big', signed=True
                )
            filmes.write(offset_bytes)
            atualiza_registro_led(filmes, registro_atual)

            return 1

        else:
            # Encontra o local de inserção do registro removido.
            while (registro_atual.tamanho > espaco_atual_led.tamanho) and (
                espaco_atual_led.offset != -1
                ):

                anterior_led = espaco_atual_led
                espaco_atual_led = dados_led(filmes, espaco_atual_led.offset_prox)

            if espaco_atual_led.offset == -1: # Verifica se a LED acabou.
                # Insere o registro removido no final da LED.
                anterior_led.offset_prox = registro_atual.offset
                registro_atual.offset_prox = -1

                '''
                FIXME: Código sugerido que não foi utilizado,
                mas pode ser útil para referência futura.

                atualiza_registro_led(filmes, anterior_led)
                '''

            else:
                # Insere o registro removido no meio da LED.
                anterior_led.offset_prox = registro_atual.offset
                registro_atual.offset_prox = espaco_atual_led.offset

            atualiza_registro_led(filmes, anterior_led)
            atualiza_registro_led(filmes, registro_atual)

            return 1


# Função para remover um registro do arquivo filmes.dat
def remove_registro(filmes: io.BufferedRandom, id: str) -> None:
    """
    Imprime as informações do registro de ID *id* removido.
    Se o ID não for encontrado, imprime ID não encontrado.
    """


    # Identifica o offset do registro.
    offset = offset_registro(filmes, id)
    print(f"Removendo registro: {id}")

    if offset == -1:
        print(f"Remoção do registro de chave '{id}'")
        print(f"Erro: registro não encontrado!\n")

        return

    else:
        remocao_logica_registro(filmes, offset)
        insere = insere_led(filmes, 0, offset)

        if insere == 1:
            filmes.seek(offset)
            tamanho = int.from_bytes(
                filmes.read(2), 'big', signed=True
                )

            print(f"Remoção do registro de chave: {id}")
            print(f"Registro removido! ({tamanho} bytes)")
            print(f"Local: offset = {offset}\n")

        else:
            print(f"Erro ao inserir registro na LED.")

            return


# Função para inserir um registro no arquivo filmes.dat
def insere_registro(filmes: io.BufferedRandom, registro: str) -> None:
    """
    Insere *registro* no arquivo binário *filmes*.
    O registro deve estar no formato 'id|nome|ano|genero'.
    Se o registro já existir, imprime mensagem de erro.
    """


    # Transforma *registro* em binário e obtém seu tamanho.
    registro_binario = registro.encode()
    tamanho_registro = len(registro_binario)
    tamanho_binario = tamanho_registro.to_bytes(2, 'big', signed=True)

    # Obtém o topo da LED e verifica seu tamanho.
    filmes.seek(0)
    offset_atual_led = int.from_bytes(
        filmes.read(4), 'big', signed=True
        )
    espaco_atual_led = dados_led(filmes, offset_atual_led)
    tamanho_espaco_atual_led = espaco_atual_led.tamanho

    EOL = False # End Of LED — indica o fim da LED.

    if offset_atual_led == -1: # Verifica se a LED está vazia.
        EOL = True

    # Encontra |offset da LED| >= |registro|.
    while (tamanho_registro > tamanho_espaco_atual_led) and (not EOL):
        espaco_atual_led = dados_led(
            filmes, espaco_atual_led.offset_prox
            )
        tamanho_espaco_atual_led = espaco_atual_led.tamanho

        if espaco_atual_led.offset == -1:
            EOL = True

    if not EOL:
        # Insere registro no offset da LED.
        filmes.seek(espaco_atual_led.offset+2)
        filmes.write(registro_binario)
        atualiza_led(filmes, espaco_atual_led.offset)

    elif EOL:
        # Insere *registro* no final de *filmes*.
        filmes.seek(0, 2)
        filmes.write(tamanho_binario)
        filmes.write(registro_binario)

    id_registro = registro.split('|')[0]
    print(f"Inserção do registro de chave '{id_registro}' "
          f"({tamanho_registro} bytes)"
    )

    if offset_atual_led != -1:
        print(f"Local: offset {offset_atual_led} bytes "
              f"{hex(offset_atual_led)})\n"
    )

    else:
        print("Local: fim do arquivo\n")


# Função para buscar um registro no arquivo filmes.dat
def busca_registro(filmes: io.BufferedReader, id: str) -> None:
    """
    Imprime o registro de ID *id* do arquivo *filmes*.
    Se ID não for encontrado, imprime ID não encontrado.
    """


    offset = offset_registro(filmes, id)

    # Se o registro não foi encontrado, imprime mensagem de erro
    # e retorna.
    if offset == -1:
        print(f"Busca pelo registro de chave '{id}'.")
        print("Erro: registro não encontrado\n")

        return
    
    # Se o registro foi encontrado, imprime suas informações.
    else:
        filmes.seek(offset)
        tamanho = int.from_bytes(filmes.read(2), 'big', signed=True)
        registro = filmes.read(tamanho).decode()

        print(f"Busca pelo registro de chave: '{id}'")
        print(f"{registro} '{tamanho} bytes'\n")


# Função principal que executa as operações do arquivo operacoes.txt
def main(operacoes) -> None:
    """
    Executa as operações contidas no arquivo *operacoes* no arquivo
    binário filmes.dat.
    As operações são lidas do arquivo *operacoes* e podem ser:
    - 'b' para buscar um registro
    - 'r' para remover um registro
    - 'i' para inserir um registro
    """


    try:
        filmes = open('filmes.dat', 'r+b')
    except FileNotFoundError as e:
        print(f"Erro ao abrir filmes.dat: {e}")

    try:
        arq = open(operacoes, 'r')
    except FileNotFoundError as e:
        print(f"Erro ao abrir operacoes.txt: {e}")

    operacoes = arq.readlines()
    operacoes = remove_quebra(operacoes)

    for linha in operacoes:
        operacao = linha[0] # 'b', 'r' ou 'i'

        if operacao == 'b':
            filmes.seek(0)
            busca_registro(filmes, linha[2:])

            # FIXME: código temporário para verificar busca.
            # Remover antes da entrega final.
            filmes = pausa_para_verificacao(filmes, 'filmes.dat')
            #TOERASE

        elif operacao == 'r':
            filmes.seek(0)
            remove_registro(filmes, linha[2:])

            # FIXME: código temporário para verificar leitura.
            # Remover antes da entrega final.
            filmes = pausa_para_verificacao(filmes, 'filmes.dat')

        elif operacao == 'i':
            filmes.seek(0)
            insere_registro(filmes, linha[2:])

            # FIXME: código temporário para verificar inserção.
            # Remover antes da entrega final.
            filmes = pausa_para_verificacao(filmes, 'filmes.dat')

    filmes.close()
    arq.close()


if __name__ == "__main__":
    if argv[1] == '-e':
        arquivo_operacoes = argv[2]
        main(arquivo_operacoes)

    elif argv[1] == '-p':
        impressao_led('filmes.dat')

    elif argv[1] == '-c':
        compactacao()

    else:
        raise ValueError(
            "Erro: argumentos inválidos. Use -e, -p ou -c."
            )