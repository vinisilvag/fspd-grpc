import sys
import threading
from concurrent import futures

import grpc

import store_pb2
import store_pb2_grpc
import wallet_pb2
import wallet_pb2_grpc


class Store(store_pb2_grpc.StoreServicer):
    def __init__(
        self,
        stop_event: threading.Event,
        wallet_addr: tuple[str, int],
        seller_wallet: str,
        price: int,
    ) -> None:
        self._stop_event = stop_event
        self.wallet_addr = wallet_addr
        self.seller_wallet = seller_wallet
        self.price = price

        wallet_channel = grpc.insecure_channel(f"{wallet_addr[0]}:{wallet_addr[1]}")
        self.wallet_stub = wallet_pb2_grpc.WalletStub(wallet_channel)

        balance_response = self.wallet_stub.balance(
            wallet_pb2.BalanceRequest(wallet=self.seller_wallet)
        )
        self.balance = balance_response.retval

    def read_price(self, request, context):
        return store_pb2.ReadPriceReply(price=self.price)

    def sell(self, request, context):
        transfer_response = self.wallet_stub.transfer(
            wallet_pb2.TransferRequest(
                payment_order=request.payment_order,
                recount=self.price,
                wallet=self.seller_wallet,
            )
        )
        transfer_status = transfer_response.status
        if transfer_status in [-1, -2, -3]:
            return store_pb2.SellReply(status=-9)
        return store_pb2.SellReply(status=transfer_status)

    def end_execution(self, request, context):
        end_execution_response = self.wallet_stub.end_execution(
            wallet_pb2.EndExecutionRequest()
        )
        pendencies = end_execution_response.pendencies

        self._stop_event.set()
        return store_pb2.EndExecutionReply(balance=self.balance, pendencies=pendencies)


def run():
    price = int(sys.argv[1])
    port = int(sys.argv[2])
    seller_wallet = sys.argv[3]
    wallet_host, wallet_port = sys.argv[4].split(":")
    wallet_port = int(wallet_port)
    wallet_addr = (wallet_host, wallet_port)

    stop_event = threading.Event()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    store_pb2_grpc.add_StoreServicer_to_server(
        Store(stop_event, wallet_addr, seller_wallet, price), server
    )
    server.add_insecure_port(f"0.0.0.0:{port}")
    server.start()
    stop_event.wait()
    server.stop(None)


if __name__ == "__main__":
    run()
