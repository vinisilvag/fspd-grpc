# Cliente do servidor de lojas
# Vinicius Gomes - 2021421869

import sys

import grpc

import store_pb2
import store_pb2_grpc
import wallet_pb2
import wallet_pb2_grpc


def run(buyer_wallet, wallet_addr, store_addr):
    # Abre um canal para se comunicar com o servidor de carteiras
    wallet_channel = grpc.insecure_channel(f"{wallet_addr[0]}:{wallet_addr[1]}")
    # Cria o stub para se comunicar com o servidor da loja
    wallet_stub = wallet_pb2_grpc.WalletStub(wallet_channel)

    # Abre um canal para se comunicar com o servidor da loja
    store_channel = grpc.insecure_channel(f"{store_addr[0]}:{store_addr[1]}")
    # Cria o stub para se comunicar com o servidor da loja
    store_stub = store_pb2_grpc.StoreStub(store_channel)

    # Lê e exibe o preço do produto vendido pelo servidor daquela loja
    price_response = store_stub.read_price(store_pb2.ReadPriceRequest())
    price = price_response.price
    print(price)

    while True:
        line = input()
        command, *args = line.split(" ")
        match command:
            # Realiza a compra de um produto
            case "C":
                # Cria a ordem de pagamento, debitando o valor do produto
                # da conta do usuário que comprou
                payment_order_response = wallet_stub.create_payment_order(
                    wallet_pb2.CreatePaymentOrderRequest(
                        wallet=buyer_wallet, value=price
                    )
                )
                retval = payment_order_response.retval

                # Caso a criação da ordem de pagamento tenha sido um sucesso
                if payment_order_response.retval not in [-1, -2]:
                    # Chama o procedimento de venda no servidor, que será
                    # responsável por transferir o valor da ordem de pagamento
                    # para a carteira do vendedor
                    sell_response = store_stub.sell(
                        store_pb2.SellRequest(payment_order=retval)
                    )
                    print(retval)
                    print(sell_response.status)

            # Termina a execução
            case "T":
                # Chama o procedimento através do stub
                response = store_stub.end_execution(store_pb2.EndExecutionRequest())
                print(response.balance, response.pendencies)

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
