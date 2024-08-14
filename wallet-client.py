# Cliente do servidor de carteiras
# Vinicius Gomes - 2021421869

from __future__ import print_function

import sys

import grpc

import wallet_pb2
import wallet_pb2_grpc


def balance(stub, wallet):
    """
    Realiza uma requisição para o servidor de carteiras pedindo pelo saldo
    da carteira do cliente. Essa função também exibe na tela o saldo obtido
    como resposta ou o código de erro -1, caso a carteira informada não exista.

    Parâmetros:
        stub: stub gRPC para se comunicar com seguindo a interface do
              servidor de carteiras
        wallet (str): identificador da carteira do cliente
    """

    response = stub.balance(wallet_pb2.BalanceRequest(wallet=wallet))
    print(response.balance)


def create_payment_order(stub, wallet, value):
    """
    Realiza uma requisição para o servidor de carteiras para criar uma ordem
    de pagamento. Essa função também exibe na tela o número da ordem de
    pagamento criada ou os códigos de erro -1, caso a carteira informada não
    exista, ou -2, caso o saldo em conta seja insuficiente.

    Parâmetros:
        stub: stub gRPC para se comunicar com seguindo a interface do
              servidor de carteiras
        wallet (str): identificador da carteira do cliente que terá o
                         dinheiro debitado
        value (int): valor da ordem de pagamento (valor também será debitado
                     da carteira informada)
    """

    response = stub.create_payment_order(
        wallet_pb2.CreatePaymentOrderRequest(wallet=wallet, value=value)
    )
    print(response.retval)


def transfer(stub, payment_order, value, wallet):
    """
    Realiza uma requisição para o servidor de carteiras para transferir o
    dinheiro de uma ordem de pagamento para a carteira informada como
    parâmetro. Essa função também exibe na tela o status 0, caso a
    transferência tenha ocorrido com sucesso, ou os códigos de erro -1,
    caso a ordem de pagamento informada não exista, -2, caso o valor de
    conferência seja diferente do valor contido na ordem de pagamento, ou
    -3 caso a carteira informada não exista.


    Parâmetros:
        stub: stub gRPC para se comunicar com seguindo a interface do
              servidor de carteiras
        payment_order (int): número de ordem de pagamento referente a
                             transferência que se deseja fazer
        value (int): valor de conferência da ordem de pagamento (uma comparação
                     será feita se esse valor é igual ao valor registrado na
                     ordem de pagamento especificada pelo número informado
                     como parâmetro)
        wallet (str): identificador da carteira do cliente que receberá o
                         valor contido na ordem de pagamento
    """

    response = stub.transfer(
        wallet_pb2.TransferRequest(
            payment_order=payment_order,
            recount=value,
            wallet=wallet,
        )
    )
    print(response.status)


def end_execution(stub):
    """
    Realiza uma requisição para o servidor de carteiras para encerrar a sua
    execução. Essa função também exibe na tela o número de ordens de pagamento
    pendentes no momento em que o servidor é terminado.

    Parâmetros:
        stub: stub gRPC para se comunicar com seguindo a interface do
              servidor de carteiras
    """

    response = stub.end_execution(wallet_pb2.EndExecutionRequest())
    print(response.pendencies)


def run(wallet, wallet_addr):
    """
    Inicia o cliente do servidor de carteiras e processa os comandos
    do usuário.

    Parâmetros:
        wallet (str): identificador da carteira do cliente
        wallet_addr (tuple[str, int]): endereço do servidor de carteiras
    """

    # Abre um canal para se comunicar com o servidor de carteiras
    channel = grpc.insecure_channel(f"{wallet_addr[0]}:{wallet_addr[1]}")
    # Gera o stub para se comunicar com o servidor de carteiras
    stub = wallet_pb2_grpc.WalletStub(channel)

    while True:
        # Lê uma linha da entrada e em caso de EOFError
        # (fim da leitura) sai do loop
        try:
            line = input()
        except EOFError:
            break

        if not line:
            continue

        # Separa o comando do restante do conteúdo da linha lida
        command = line[0]
        match command:
            # Lê o saldo
            case "S":
                balance(stub, wallet)

            # Cria ordem de pagamento
            case "O":
                # Faz o parsing dos parâmetros do comando
                _, *args = line.split()
                value = int(args[0])

                create_payment_order(stub, wallet, value)

            # Realiza uma transferência
            case "X":
                # Faz o parsing dos parâmetros do comando
                _, *args = line.split()
                payment_order = int(args[0])
                value = int(args[1])
                wallet = args[2]

                transfer(stub, payment_order, value, wallet)

            # Termina a execução
            case "F":
                end_execution(stub)

                break

            case _:
                pass

    # Fecha os canal de comunicação criado
    channel.close()


if __name__ == "__main__":
    # Identificador da carteira do cliente
    wallet = sys.argv[1]

    # Endereço do servidor de carteiras
    host, port = sys.argv[2].split(":")
    wallet_addr = (host, int(port))

    # Chama a função que inicia o cliente
    run(wallet, wallet_addr)
