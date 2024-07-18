import sys

import grpc

import store_pb2
import store_pb2_grpc


def run():
    # parse args

    channel = grpc.insecure_channel(f"{host}:{port}")
    stub = store_pb2_grpc.StoreStub(channel)

    while True:
        line = input()
        command, *args = line.split(" ")
        match command:
            case "C":
                pass
            case "T":
                pass
            case "F":
                pass
            case _:
                pass


if __name__ == "__main__":
    run()
