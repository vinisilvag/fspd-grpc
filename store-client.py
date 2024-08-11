import sys

import grpc

import store_pb2
import store_pb2_grpc
import wallet_pb2
import wallet_pb2_grpc


def run():
    buyer_wallet = sys.argv[1]
    wallet_host, wallet_port = sys.argv[2].split(":")
    wallet_port = int(wallet_port)
    wallet_addr = (wallet_host, wallet_port)
    store_host, store_port = sys.argv[3].split(":")
    store_port = int(store_port)
    store_addr = (store_host, store_port)

    wallet_channel = grpc.insecure_channel(f"{wallet_addr[0]}:{wallet_addr[1]}")
    wallet_stub = wallet_pb2_grpc.WalletStub(wallet_channel)

    store_channel = grpc.insecure_channel(f"{store_addr[0]}:{store_addr[1]}")
    store_stub = store_pb2_grpc.StoreStub(store_channel)

    price_response = store_stub.read_price(store_pb2.ReadPriceRequest())
    price = price_response.price
    print(price)

    while True:
        line = input()
        command, *args = line.split(" ")
        match command:
            case "C":
                payment_order_response = wallet_stub.create_payment_order(
                    wallet_pb2.CreatePaymentOrderRequest(
                        wallet=buyer_wallet, value=price
                    )
                )
                retval = payment_order_response.retval

                if payment_order_response.retval not in [-1, -2]:
                    sell_response = store_stub.sell(
                        store_pb2.SellRequest(payment_order=retval)
                    )
                    print(retval)
                    print(sell_response.status)

            case "T":
                response = store_stub.end_execution(store_pb2.EndExecutionRequest())
                print(response.balance, response.pendencies)
                break
            case _:
                pass


if __name__ == "__main__":
    run()
