# Cliente do servidor de carteiras
# Vinicius Gomes - 2021421869

import sys

import grpc

import wallet_pb2
import wallet_pb2_grpc


# Realiza a requisição pelo saldo
def balance(stub, wallet):
    response = stub.balance(wallet_pb2.BalanceRequest(wallet=wallet))
    print(response.balance)


# Realiza a requisição para criar uma ordem de pagamento
def create_payment_order(stub, wallet, value):
    response = stub.create_payment_order(
        wallet_pb2.CreatePaymentOrderRequest(wallet=wallet, value=value)
    )
    print(response.retval)


# Realiza a requisição para fazer a transferência do valor de uma ordem de
# pagamento para uma carteira
def transfer(stub, payment_order, value, wallet):
    response = stub.transfer(
        wallet_pb2.TransferRequest(
            payment_order=payment_order,
            recount=value,
            wallet=wallet,
        )
    )
    print(response.status)


# Realiza a requisição para terminar a execução do servidor de carteiras
def end_execution(stub):
    response = stub.end_execution(wallet_pb2.EndExecutionRequest())
    print(response.pendencies)


def run(wallet, wallet_addr):
    # Abre um canal para se comunicar com o servidor de carteiras
    channel = grpc.insecure_channel(f"{wallet_addr[0]}:{wallet_addr[1]}")
    # Cria o stub
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
