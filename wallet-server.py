import sys
import threading
from concurrent import futures

import grpc

import wallet_pb2
import wallet_pb2_grpc


class Wallet(wallet_pb2_grpc.WalletServicer):
    def __init__(self, stop_event: threading.Event, wallets: dict[str, int]) -> None:
        self._stop_event = stop_event
        self.wallets = wallets
        self.payment_orders: dict[int, int] = {}
        self.index = 0

    def balance(self, request, context):
        retval = -1
        if request.wallet in self.wallets:
            retval = self.wallets[request.wallet]
        return wallet_pb2.BalanceReply(retval=retval)

    def create_payment_order(self, request, context):
        if request.wallet not in self.wallets:
            return wallet_pb2.CreatePaymentOrderReply(retval=-1)

        if self.wallets[request.wallet] < request.value:
            return wallet_pb2.CreatePaymentOrderReply(retval=-2)

        self.index += 1
        self.payment_orders[self.index] = request.value
        return wallet_pb2.CreatePaymentOrderReply(retval=self.index)

    def transfer(self, request, context):
        if request.payment_order not in self.payment_orders:
            return wallet_pb2.TransferReply(status=-1)

        if self.payment_orders[request.payment_order] != request.recount:
            return wallet_pb2.TransferReply(status=-2)

        if request.wallet not in self.wallets:
            return wallet_pb2.TransferReply(status=-3)

        self.wallets[request.wallet] -= request.recount
        del self.payment_orders[request.payment_order]

        return wallet_pb2.TransferReply(status=0)

    def end_execution(self, request, context):
        for wallet, value in self.wallets.items():
            print(wallet, value)

        self._stop_event.set()
        return wallet_pb2.EndExecutionReply(pendencies=len(self.payment_orders))


def run():
    wallets = {}
    for line in sys.stdin:
        id, value = line[:-1].split(" ")
        wallets[id] = int(value)

    port = int(sys.argv[1])

    stop_event = threading.Event()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    wallet_pb2_grpc.add_WalletServicer_to_server(Wallet(stop_event, wallets), server)
    server.add_insecure_port(f"0.0.0.0:{port}")
    server.start()
    stop_event.wait()
    server.stop(None)


if __name__ == "__main__":
    run()
