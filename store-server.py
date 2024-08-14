# Servidor de lojas
# Vinicius Gomes - 2021421869

import sys
import threading
from concurrent import futures

import grpc
import store_pb2
import store_pb2_grpc
import wallet_pb2
import wallet_pb2_grpc


# Classe que provê os métodos que implementam o serviço de loja
class Store(store_pb2_grpc.StoreServicer):
    def __init__(
        self,
        stop_event: threading.Event,
        wallet_addr: tuple[str, int],
        seller_wallet: str,
        price: int,
    ) -> None:
        # Evento de término do servidor
        self._stop_event = stop_event

        # Carteira do vendedor
        self.seller_wallet = seller_wallet
        print("seller wallet:", self.seller_wallet)

        # Preço do produto
        self.price = price
        print("price:", self.price)

        # Abre um canal para se comunicar com o servidor de carteiras
        wallet_channel = grpc.insecure_channel(f"{wallet_addr[0]}:{wallet_addr[1]}")

        # Cria o stub para se comunicar com o servidor de carteiras
        # Esse stub será usado para buscar o saldo da carteira do vendedor e
        # realizar a operação de venda (que precisa se comunicar com o servidor
        # de carteiras para chamar o procedimento de transferência)
        self.wallet_stub = wallet_pb2_grpc.WalletStub(wallet_channel)

        balance_response = self.wallet_stub.balance(
            wallet_pb2.BalanceRequest(wallet=self.seller_wallet)
        )
        self.balance = balance_response.retval
        print("balance:", self.balance)

    # Procedimento que lê o preço do produto
    def read_price(self, request, context):
        # Monta a resposta com o preço do produto recebido como parâmetro
        return store_pb2.ReadPriceReply(price=self.price)

    # Procedimento que realiza uma venda
    def sell(self, request, context):
        transfer_response = self.wallet_stub.transfer(
            wallet_pb2.TransferRequest(
                payment_order=request.payment_order,
                recount=self.price,
                wallet=self.seller_wallet,
            )
        )
        transfer_status = transfer_response.status
        print("sell")
        print("transfer status:", transfer_status)
        if transfer_status in [-1, -2, -3]:
            # erro de comunicacao com o servidor?
            return store_pb2.SellReply(status=-9)
        self.balance += self.price
        print("updated balance:", self.balance)
        return store_pb2.SellReply(status=transfer_status)

    # Procedimento que termina o servidor da loja
    def end_execution(self, request, context):
        # Chama o procedimento de término do servidor de carteiras
        end_execution_response = self.wallet_stub.end_execution(
            wallet_pb2.EndExecutionRequest()
        )
        pendencies = end_execution_response.pendencies

        # Sinaliza o evento de encerramento do servidor
        self._stop_event.set()

        # Monta a resposta com o saldo atual do vendedor e o número de ordens
        # de pagamento pendentes
        return store_pb2.EndExecutionReply(balance=self.balance, pendencies=pendencies)


def run(price, port, seller_wallet, wallet_addr):
    # Define o evento de parada do servidor
    stop_event = threading.Event()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Liga o servidor à classe que implementa os métodos disponibilizados
    # pelo servidor
    store_pb2_grpc.add_StoreServicer_to_server(
        Store(stop_event, wallet_addr, seller_wallet, price), server
    )
    server.add_insecure_port(f"0.0.0.0:{port}")

    server.start()

    # Espera a ocorrência do evento de término do servidor
    stop_event.wait()
    # Quando detectado, o servidor é terminado
    server.stop(None)


if __name__ == "__main__":
    # Preço do produto vendido
    price = int(sys.argv[1])

    # Porta que o servidor irá usar
    port = int(sys.argv[2])

    # Identificador da carteira do vendedor
    seller_wallet = sys.argv[3]

    # Endereço do servidor de carteiras
    wallet_host, wallet_port = sys.argv[4].split(":")
    wallet_addr = (wallet_host, int(wallet_port))

    # Chama a função que inicia o servidor
    run(price, port, seller_wallet, wallet_addr)
