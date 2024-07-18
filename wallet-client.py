import sys

import grpc

import wallet_pb2
import wallet_pb2_grpc


def run():
    wallet = sys.argv[1]
    host, port = sys.argv[2].split(":")
    port = int(port)

    channel = grpc.insecure_channel(f"{host}:{port}")
    stub = wallet_pb2_grpc.WalletStub(channel)

    while True:
        line = input()
        command, *args = line.split(" ")
        match command:
            case "S":
                response = stub.balance(wallet_pb2.BalanceRequest(wallet=wallet))
                print(response.retval)
            case "O":
                value = int(args[0])
                response = stub.create_payment_order(
                    wallet_pb2.CreatePaymentOrderRequest(wallet=wallet, value=value)
                )
                print(response.retval)
            case "X":
                opag, value, destination = args
                opag = int(opag)
                value = int(value)
            case "F":
                pass
            case _:
                pass


if __name__ == "__main__":
    run()
