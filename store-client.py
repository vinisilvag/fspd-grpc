# Cliente do servidor de lojas
# Vinicius Gomes - 2021421869

from __future__ import print_function

import sys

import grpc

import store_pb2
import store_pb2_grpc
import wallet_pb2
import wallet_pb2_grpc


def buy(buyer_wallet, wallet_stub, store_stub, price):
    """
    Realiza uma série de requisições para efetuar a compra do produto vendido
    pela loja. O primeiro passo é criar a ordem de pagamento, debitando o valor
    do produto da carteira do comrpador. Em seguida, uma requisição é feita
    para o servidor da loja. Essa requisição é responsável por efetuar de fato
    a venda do produto e transferir o dinheiro da ordem de pagamento para a
    conta do vendedor. Ao final, essa função exibe o status da criação da ordem
    de pagamento e o status da venda do produto (0 caso a operação ocorra com
    sucesso ou um dos possíveis códigos de erro).

    Parâmetros:
        buyer_wallet (str): identificador da carteira do comprador
        wallet_stub: stub gRPC para se comunicar com seguindo a interface do
                     servidor de carteiras
        store_stub: stub gRPC para se comunicar com seguindo a interface do
                    servidor de lojas
        price (int): preço do produto vendido pela loja
    """

    # Cria a ordem de pagamento, debitando o valor do produto
    # da conta do usuário que comprou
    payment_order_response = wallet_stub.create_payment_order(
        wallet_pb2.CreatePaymentOrderRequest(wallet=buyer_wallet, value=price)
    )
    retval = payment_order_response.retval
    print(retval)

    # Caso a criação da ordem de pagamento tenha sido um sucesso
    if retval not in [-1, -2]:
        # Chama o procedimento de venda no servidor, que será
        # responsável por transferir o valor da ordem de pagamento
        # para a carteira do vendedor
        sell_response = store_stub.sell(store_pb2.SellRequest(payment_order=retval))
        print(sell_response.status)


def end_execution(store_stub):
    """
    Realiza uma requisição para o servidor de lojas para encerrar a sua
    execução. Essa função também exibe na tela o saldo na conta do vendedor e o
    número de ordens de pagamento pendentes no momento em que os servidores são
    terminados.

    Parâmetros:
        store_stub: stub gRPC para se comunicar com seguindo a interface do
                    servidor de lojas
    """

    response = store_stub.end_execution(store_pb2.EndExecutionRequest())
    print(response.balance, response.pendencies)


def run(buyer_wallet, wallet_addr, store_addr):
    """
    Inicia o cliente do servidor de lojas e processa os comandos
    do usuário.

    Parâmetros:
        buyer_wallet (str): identificador da carteira do cliente
        wallet_addr (tuple[str, int]): endereço do servidor de carteiras
        store_addr (tuple[str, int]): endereço do servidor da loja
    """

    # Abre um canal para se comunicar com o servidor de carteiras
    wallet_channel = grpc.insecure_channel(f"{wallet_addr[0]}:{wallet_addr[1]}")
    # Gera o stub para se comunicar com o servidor da loja
    wallet_stub = wallet_pb2_grpc.WalletStub(wallet_channel)

    # Abre um canal para se comunicar com o servidor da loja
    store_channel = grpc.insecure_channel(f"{store_addr[0]}:{store_addr[1]}")
    # Gera o stub para se comunicar com o servidor da loja
    store_stub = store_pb2_grpc.StoreStub(store_channel)

    # Lê e exibe o preço do produto vendido pelo servidor daquela loja
    price_response = store_stub.read_price(store_pb2.ReadPriceRequest())
    price = price_response.price
    print(price)

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
            # Realiza a compra de um produto
            case "C":
                buy(buyer_wallet, wallet_stub, store_stub, price)

            # Termina a execução
            case "T":
                end_execution(store_stub)
                break

            case _:
                pass

    # Fecha os canais de comunicação criados
    wallet_channel.close()
    store_channel.close()


if __name__ == "__main__":
    # Identificador da carteira do comprador
    buyer_wallet = sys.argv[1]

    # Endereço do servidor de carteiras
    wallet_host, wallet_port = sys.argv[2].split(":")
    wallet_addr = (wallet_host, int(wallet_port))

    # Endereço do servidor da loja
    store_host, store_port = sys.argv[3].split(":")
    store_addr = (store_host, int(store_port))

    # Chama a função que inicia o cliente
    run(buyer_wallet, wallet_addr, store_addr)
