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


    Args:
        filmes (io.BufferedReader): O arquivo filmes.dat aberto.
        caminho (str): O caminho do arquivo filmes.dat.


    Returns:
        io.BufferedReader: Um novo arquivo filmes.dat aberto em
        modo 'r+b'.
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
    filmes = open('filmes.dat', 'r+b')
    filmes.seek(offset+2)
    caractere_remocao = '*'.encode()
    filmes.write(caractere_remocao)

    # Indica o próximo registro da LED.
    led_proximo = -1
    led_proximo = led_proximo.to_bytes(
        4, 'big', signed=True
        )
    filmes.seek(offset+2+1)
    filmes.write(led_proximo)


def monta_registro(filmes: io.BufferedReader, offset: int) -> Registro:
    """
    Monta o registro de offset *offset* no arquivo *filmes*
    pertinentes à LED.
    Se o offset for 0, retorna o cabeçalho da LED.
    Se o offset for -1, retorna o final da LED.
    """

    filmes = open('filmes.dat', 'r+b')

    if offset == 0: # Offset 0 indica o cabeçalho da LED.
        filmes.seek(0)
        offset_prox = int.from_bytes(
            filmes.read(4), 'big', signed=True
            )

        return Registro(offset, 0, offset_prox)

    elif offset == -1: # Offset -1 indica o final da LED.
        return Registro(offset, 0, -1)

    # Lê os dados do registro de offset *offset*.
    else:
        filmes.seek(offset)
        tamanho = int.from_bytes(filmes.read(2), 'big', signed=True)
        status = filmes.read(1).decode(errors='ignore')

        if status == '*':
            offset_prox = int.from_bytes(
                filmes.read(4), 'big', signed=True
                )
            # FIXME: print temporário para depuração.
            print(f"Próximo registro da LED: {offset_prox}")

        else:
            # Registro ativo: não tem offset_prox.
            offset_prox = -1

        registro_montado = Registro(
            offset, tamanho, offset_prox
            )

        # FIXME: print temporário para depuração.
        print(f"Registro montado: {registro_montado}")
        filmes = pausa_para_verificacao(filmes, 'filmes.dat')

        return registro_montado

        # FIXME: código comentado que não foi utilizado,
        # mas pode ser útil para referência futura.
        # filmes.seek(offset+2+1)
        # offset_prox = int.from_bytes(
        # filmes.read(4), 'big', signed=True)

        # # FIXME: print temporário para depuração.
        # print(f"Próximo registro da LED: {offset_prox}")
        # filmes = pausa_para_verificacao(filmes, 'filmes.dat')

        # registro_montado = Registro(offset, tamanho, offset_prox)

        # # FIXME: print temporário para depuração.
        # print(f"Registro montado: {registro_montado}")
        # filmes = pausa_para_verificacao(filmes, 'filmes.dat')

        # return registro_montado


def atualiza_registro_led(
        filmes: io.BufferedWriter,
        registro: Registro
) -> None:
    """
    Atualiza o registro *registro* no arquivo *filmes* após
    ser realizada uma inserção ou remoção na LED.
    """

    filmes = open('filmes.dat', 'r+b')
    offset_registro = registro.offset
    offset_prox = registro.offset_prox

    # Verifica se o registro é a cabeça da LED.
    if offset_registro == 0:
        filmes.seek(0)
        filmes.write(offset_prox.to_bytes(4, 'big', signed=True))

    # Verifica se o registro é o seguinte à cabeça da LED.
    else:
        # Para registros removidos:
        # offset+2 (tamanho) +1 ('*') = offset+3.
        filmes.seek(offset_registro+2+1)
        filmes.write(offset_prox.to_bytes(4, 'big', signed=True))


def encontra_offset_led(filmes: io.BufferedReader, offset: int) -> Registro:
    """
    Encontra o registro na LED do arquivo *filmes* com o
    offset *offset*.
    Retorna o registro encontrado ou None se não for encontrado.
    """


    filmes.seek(0)  # Pula o cabeçalho da LED.
    led_atual = monta_registro(filmes, 0)

    while led_atual.offset != -1:
        if led_atual.offset == offset:
            return led_atual
        led_atual = monta_registro(filmes, led_atual.offset_prox)

    return None


def atualiza_led(filmes: io.BufferedRandom, offset_removido: int) -> None:
    """
    Remove da LED o offset do registro no qual
    foi realizada uma inserção ou remoção.
    Se o offset removido for a cabeça da LED, atualiza o topo da LED.
    Se o offset removido for o seguinte à cabeça da LED,
    atualiza o próximo.


    Args:
        filmes (io.BufferedRandom): O arquivo filmes.dat aberto.
        offset_removido (int): O offset do registro removido ou
        inserido na LED.
    """


    filmes = open('filmes.dat', 'r+b')
    led_atual = monta_registro(filmes, 0)

    if offset_removido == led_atual.offset_prox:
        # Remove da cabeça da LED o offset removido.
        led_proximo = monta_registro(
            filmes, led_atual.offset_prox
            )
        filmes.seek(0)
        filmes.write(led_proximo.offset_prox.to_bytes(
            4, 'big', signed=True)
            )

    else:
        # Procura o offset na LED.
        led_anterior = led_atual
        led_atual = monta_registro(filmes, led_atual.offset_prox)

        while led_atual.offset != -1 and (
            led_atual.offset != offset_removido
        ):
            led_anterior = led_atual
            led_atual = monta_registro(filmes, led_atual.offset_prox)
        
        if led_atual.offset == offset_removido:
            # Encontrou o registro, remove da LED.
            led_anterior.offset_prox = led_atual.offset_prox
            filmes.seek(led_anterior.offset+2+1)
            filmes.write(led_atual.offset_prox.to_bytes(
                4, 'big', signed=True)
                )
        else:
            raise ValueError(
                f"Erro: offset {offset_removido} não encontrado na LED."
            )

    # # Offset seguinte à cabeça da LED.
    # elif offset_removido == led_atual.offset_prox:
    #     print("Atualizando próximo da cabeça da LED.")
    #     led_proximo = monta_registro(
    #         filmes, led_atual.offset_prox
    #         )
    #     filmes.seek(led_atual.offset+2+1)
    #     filmes.write(led_proximo.offset_prox.to_bytes(
    #         4, 'big', signed=True)
    #         )

    # FIXME: há um erro de lógica aqui.
    # Offset removido não é a cabeça da LED nem o seguinte à cabeça.
    # else:
    #     # Encontra o offset removido na LED.
    #     led_anterior = led_atual
    #     led_atual = monta_registro(filmes, led_atual.offset_prox)

    #     # FIXME: código sugerido que não foi utilizado,
    #     # mas pode ser útil para referência futura.
    #     # led_atual = encontra_offset_led(filmes, offset_removido)

    #     filmes.seek(0)  # Pula o cabeçalho da LED.
    #     led_atual = monta_registro(filmes, 0)

    #     # FIXME: print temporário para depuração.
    #     print(f"led_atual: {led_atual}")
    #     print(f"Offset removido: {offset_removido}")
    #     filmes = pausa_para_verificacao(filmes, 'filmes.dat')

    #     # Percorre a LED até encontrar o offset removido.
    #     while offset_removido != led_atual.offset:
    #         led_anterior = led_atual
    #         if not led_atual.offset_prox == -1:
    #             led_atual = monta_registro(
    #                 filmes, led_atual.offset_prox
    #                 )
    #         else:
    #             raise ValueError(
    #                 f"Erro: offset {offset_removido} não encontrado na LED."
    #             )

    #     # FIXME: print temporário para depuração.
    #     print(f"led_atual.offset: {led_atual.offset}")
    #     print(f"led_atual removido encontrado: {led_atual}")
    #     print(f"led_anterior: {led_anterior}")
    #     print(f"led_anterior.offset_prox: {led_anterior.offset_prox}")
    #     print(f"led_atual.offset_prox: {led_atual.offset_prox}")
    #     filmes = pausa_para_verificacao(filmes, 'filmes.dat')

    #     # Remove o offset da LED.
    #     led_anterior.offset_prox = led_atual.offset_prox

    #     """
    #     FIXME: Código comentado que não foi utilizado,
    #     mas pode ser útil para referência futura.

    #     led_proximo = dados_led(filmes, led_atual.offset_prox)
    #     """

    #     # FIXME: Verificar a lógica de atualização da LED.
    #     # Atualiza o registro anterior ao removido.
    #     filmes.seek(led_anterior.offset+2+1)
    #     filmes.write(led_atual.offset_prox.to_bytes(
    #         4, 'big', signed=True)
    #         )

# FIXME: É em uma inserção que ocorre um problema, em que o offset -1 é
# perdido, e o loop não para.

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


    filmes = open('filmes.dat', 'r+b')
    EOF = False # End Of File — indica o fim do arquivo.

    filmes.seek(4) # Pula cabeçalho do arquivo.

    # Lê registros até encontrar o ID ou chegar ao fim do arquivo.
    while not EOF:
        offset_atual = filmes.tell()
        tamanho = int.from_bytes(filmes.read(2), 'big', signed=True)
        caractere = filmes.read(1).decode(errors='ignore')

        if not caractere:
            EOF = True

            break

        # Verifica se o registro atual foi removido.
        if caractere == '*':
            # Registro removido, pula o offset_prox e o restante.
            filmes.seek(offset_atual + 2 + tamanho)

            continue

        else:
            # Lê o ID.
            id_atual = caractere
            caractere = filmes.read(1).decode(errors='ignore')

            # Lê o ID até encontrar o caractere '|'.
            while caractere != "|":
                id_atual += caractere
                caractere = filmes.read(1).decode(errors='ignore')

            if id_atual == id:
                return offset_atual

            filmes.seek(offset_atual + 2 + tamanho)

    return -1


def impressao_led(nome_filmes: str) -> None:
    """
    Imprime a LED do arquivo *nome_filmes*.
    Se o arquivo não for encontrado, imprime mensagem de erro.
    """

    # Abre o arquivo *nome_filmes* em modo leitura binária.

    filmes = open(nome_filmes, 'rb')

    # Lê o cabeçalho da LED, que contém o offset da cabeça.
    filmes.seek(0)
    offset_led = int.from_bytes(filmes.read(4), 'big', signed=True)
    registros_led: list[Registro] = []

    # Armazena todos os espaços informados na LED em *registrosLED*.
    while offset_led != -1:
        # FIXME: print temporário para depuração.
        # Remover antes da entrega final.
        print(f"Offset LED: {offset_led}")
        filmes = pausa_para_verificacao(filmes, nome_filmes)

        led_atual = monta_registro(filmes, offset_led)
        registros_led.append(led_atual)
        led_atual = monta_registro(filmes, led_atual.offset_prox)
        offset_led = led_atual.offset

    # Imprime os registros da LED.
    lista_registros_led = [
        f"[offset: {registro.offset}, "
        f"tam: {registro.tamanho}]"
        for registro in registros_led
    ]
    string_registros_led = ' -> '.join(lista_registros_led) + ' -> fim'
    print(f"LED -> {string_registros_led}")

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


    led_atual = monta_registro(filmes, cabeca)
    registro_atual = monta_registro(filmes, offset_registro)

    # Lê o offset da cabeça da LED.
    filmes = open('filmes.dat', 'r+b')
    filmes.seek(0)
    led_cabeca = filmes.read(4)
    led_cabeca = int.from_bytes(led_cabeca, 'big', signed=True)

    # LED vazia: nenhum espaço disponível.
    if led_cabeca == -1:
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
        led_atual = monta_registro(filmes, led_cabeca)

        # Verifica se o registro removido é menor que a cabeça da LED.
        if registro_atual.tamanho <= led_atual.tamanho:
            # Insere o registro removido na cebeça da LED.
            registro_atual.offset_prox = led_atual.offset
            filmes.seek(0)
            offset_bytes = registro_atual.offset.to_bytes(
                4, 'big', signed=True
                )
            filmes.write(offset_bytes)
            atualiza_registro_led(filmes, registro_atual)

            return 1

        else:
            # Encontra o local de inserção do registro removido.
            while (registro_atual.tamanho > led_atual.tamanho) and (
                led_atual.offset != -1
                ):

                anterior_led = led_atual
                led_atual = monta_registro(filmes, led_atual.offset_prox)

            if led_atual.offset == -1: # Verifica se a LED acabou.
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
                registro_atual.offset_prox = led_atual.offset

            atualiza_registro_led(filmes, anterior_led)
            atualiza_registro_led(filmes, registro_atual)

            return 1


# Função para remover um registro do arquivo filmes.dat
def remove_registro(filmes: io.BufferedRandom, id: str) -> None:
    """
    Imprime as informações do registro de ID *id* removido.
    Se o ID não for encontrado, imprime ID não encontrado.
    """


    filmes = open('filmes.dat', 'r+b')
    # Identifica o offset do registro.
    offset = offset_registro(filmes, id)
    print(f"Removendo registro: {id}")

    if offset == -1:
        print(f"Remoção do registro de chave \"{id}\"")
        print(f"Erro: registro nao encontrado!\n")

        return

    else:
        remocao_logica_registro(filmes, offset)
        insere = insere_led(filmes, 0, offset)

        if insere == 1:
            filmes = open('filmes.dat', 'r+b')
            filmes.seek(offset)
            tamanho_registro_removido = int.from_bytes(
                filmes.read(2), 'big', signed=True
                )

            print(f"Remoção do registro de chave \"{id}\"")
            print(f"Registro removido! ("
                  f"{tamanho_registro_removido} bytes)"
            )
            print(f"Local: offset = {offset} bytes "
                  f"({hex(offset)})\n")

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


    filmes = open('filmes.dat', 'r+b')
    # Transforma *registro* em binário e obtém seu tamanho.
    registro_binario = registro.encode()

    # FIXME: tamanho_registro está errado.
    # O método de obtenção do tamanho no remover_registro
    # não é o mesmo que o utilizado aqui. Lá está correto.
    tamanho_registro = len(registro_binario)
    tamanho_binario = tamanho_registro.to_bytes(2, 'big', signed=True)

    # Obtém o topo da LED e verifica seu tamanho.
    filmes.seek(0)
    offset_atual_led = int.from_bytes(
        filmes.read(4), 'big', signed=True
        )

    # FIXME: Debugging print para verificar o offset atual da LED.
    print(f"Offset atual da LED: {offset_atual_led} bytes "
            f"({hex(offset_atual_led)})\n")
    filmes = pausa_para_verificacao(filmes, 'filmes.dat')

    EOL = False # End Of LED — indica o fim da LED.

    if offset_atual_led == -1: # Verifica se a LED está vazia.
        EOL = True

    else:
        led_atual = monta_registro(filmes, offset_atual_led)
        tamanho_led_atual = led_atual.tamanho

        # FIXME: Debugging print para verificar o tamanho da LED atual.
        print(f"led_atual: {led_atual}")
        print(f"Tamanho da LED atual: {tamanho_led_atual} bytes\n")
        filmes = pausa_para_verificacao(filmes, 'filmes.dat')

        # Encontra um espaço na LED que caiba o registro.
        while (tamanho_registro > tamanho_led_atual) and (not EOL):
            if led_atual.offset_prox == -1:
                EOL = True

            else:
                led_atual = monta_registro(
                    filmes, led_atual.offset_prox
                    )
                tamanho_led_atual = led_atual.tamanho

    if not EOL:
        # Insere registro no offset da LED.
        filmes.seek(led_atual.offset)
        filmes.write(tamanho_binario) # Escreve o tamanho do registro.
        filmes.write(registro_binario) # Escreve os dados do registro.
        atualiza_led(filmes, led_atual.offset)
        local_insercao = led_atual.offset
    else:
        # Insere no final do arquivo.
        filmes.seek(0, 2)
        local_insercao = filmes.tell()
        filmes.write(tamanho_binario)
        filmes.write(registro_binario)

    # Imprime resultados da inserção.
    id_registro = registro.split('|')[0]  # Obtém o ID do registro.
    print(f"Inserção do registro de chave \"{id_registro}\" "
          f"({tamanho_registro} bytes)"
    )

    if not EOL:
        print(f"Local: offset {local_insercao} bytes "
                f"({hex(local_insercao)})\n"
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
        print(f"Busca pelo registro de chave \"{id}\"")
        print("Erro: registro nao encontrado!\n")

        return
    
    # Se o registro foi encontrado, imprime suas informações.
    else:
        filmes.seek(offset)
        tamanho = int.from_bytes(filmes.read(2), 'big', signed=True)
        registro = filmes.read(tamanho).decode()

        print(f"Busca pelo registro de chave \"{id}\"")
        print(f"{registro} ({tamanho} bytes)")
        print(f"Local: offset {offset} bytes ({hex(offset)})\n")


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

    print("As operações do arquivo dados/operacoes.txt foram executadas com sucesso!")
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