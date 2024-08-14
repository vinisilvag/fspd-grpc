# Cliente do servidor de lojas
# Vinicius Gomes - 2021421869

from __future__ import print_function

import sys

import grpc

import store_pb2
import store_pb2_grpc
import wallet_pb2
import wallet_pb2_grpc


# Realiza a compra de um produto
# Primeiramente, cria a ordem de pagamento com o valor do produto
# e exibe na tela o resultado dessa chamada de procedimento
# Caso a ordem de pagamento tenha sido criada corretamente,
# uma requisição é feita para o servidor da loja que ficará
# responsável por processar a venda e transferir o valor da ordem
# de pagamento para a conta do vendedor
# Ao final, exibe o status enviado pela chamada do procedimento
# de venda
def buy(wallet_stub, store_stub, price):
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
        sell_response = store_stub.sell(
            store_pb2.SellRequest(payment_order=retval))
        print(sell_response.status)


# Realiza a requisição para terminar a execução do servidor de carteiras
def end_execution(store_stub):
    # Exibe na tela o saldo do vendedor e o número de ordens de
    # pagamento pendentes
    response = store_stub.end_execution(store_pb2.EndExecutionRequest())
    print(response.balance, response.pendencies)


def run(buyer_wallet, wallet_addr, store_addr):
    # Abre um canal para se comunicar com o servidor de carteiras
    wallet_channel = grpc.insecure_channel(
        f"{wallet_addr[0]}:{wallet_addr[1]}")
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
                buy(wallet_stub, store_stub, price)

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
