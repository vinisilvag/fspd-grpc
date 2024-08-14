# Cliente do servidor de carteiras
# Vinicius Gomes - 2021421869

import sys

import grpc

import wallet_pb2
import wallet_pb2_grpc


def run(wallet, wallet_addr):
    # Abre um canal para se comunicar com o servidor de carteiras
    channel = grpc.insecure_channel(f"{wallet_addr[0]}:{wallet_addr[1]}")

    # Cria o stub
    stub = wallet_pb2_grpc.WalletStub(channel)

    while True:
        line = input()
        # Separa o comando e a possível de lista de argumentos que ele pode receber
        command, *args = line.split()
        match command:
            # Ler saldo
            case "S":
                # Chama o procedimento através do stub
                response = stub.balance(wallet_pb2.BalanceRequest(wallet=wallet))
                print(response.balance)
            # Cria ordem de pagamento
            case "O":
                # Faz o parsing dos parâmetros do comando
                value = int(args[0])

                # Chama o procedimento através do stub
                response = stub.create_payment_order(
                    wallet_pb2.CreatePaymentOrderRequest(wallet=wallet, value=value)
                )
                print(response.retval)
            # Realiza uma transferência
            case "X":
                # Faz o parsing dos parâmetros do comando
                payment_order = int(args[0])
                value = int(args[1])
                wallet = args[2]

                # Chama o procedimento através do stub
                response = stub.transfer(
                    wallet_pb2.TransferRequest(
                        payment_order=payment_order,
                        recount=value,
                        wallet=wallet,
                    )
                )
                print(response.status)
            # Termina a execução
            case "F":
                # Chama o procedimento através do stub
                response = stub.end_execution(wallet_pb2.EndExecutionRequest())
                print(response.pendencies)

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
