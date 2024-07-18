import sys
import threading
from concurrent import futures

import grpc

import store_pb2
import store_pb2_grpc


class Store(store_pb2_grpc.StoreServicer):
    def __init__(self, stop_event: threading.Event) -> None:
        self._stop_event = stop_event

    def read_price(self, request, context):
        pass

    def sell(self, request, context):
        pass

    def end_execution(self, request, context):
        # do the rest
        self._stop_event.set()
        return store_pb2.ShutdownResponse()


def run():
    # parse args

    stop_event = threading.Event()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    store_pb2_grpc.add_StoreServicer_to_server(Store(stop_event), server)
    server.add_insecure_port(f"localhost:{port}")
    server.start()
    print(f"Server listening on port {port}...")
    stop_event.wait()
    server.wait_for_termination()


if __name__ == "__main__":
    run()
