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
        self.index = 1

    def balance(self, request, context):
        retval = -1
        if request.wallet in self.wallets:
            retval = self.wallets[request.wallet]
        return wallet_pb2.BalanceReply(retval=retval)

    def create_payment_order(self, request, context):
        if request.wallet in self.wallets:
            if self.wallets[request.wallet] < request.value:
                return wallet_pb2.CreatePaymentOrderReply(retval=-2)
            else:
                self.payment_orders[self.index] = request.value
                # debita na carteira?
                self.index += 1
                return wallet_pb2.CreatePaymentOrderReply(retval=self.index - 1)
        else:
            return wallet_pb2.CreatePaymentOrderReply(retval=-1)

    def transfer(self, request, context):
        pass

    def end_execution(self, request, context):
        # do the rest
        self._stop_event.set()
        return wallet_pb2.ShutdownResponse()


def run():
    wallets = {}
    for line in sys.stdin:
        id, value = line[:-1].split(" ")
        wallets[id] = int(value)

    port = int(sys.argv[1])

    stop_event = threading.Event()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    wallet_pb2_grpc.add_WalletServicer_to_server(Wallet(stop_event, wallets), server)
    server.add_insecure_port(f"localhost:{port}")
    server.start()
    print(f"Server listening on port {port}...")
    stop_event.wait()
    server.wait_for_termination()


if __name__ == "__main__":
    run()
