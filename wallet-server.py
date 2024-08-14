# Servidor de carteiras
# Vinicius Gomes - 2021421869

import sys
import threading
from concurrent import futures

import grpc

import wallet_pb2
import wallet_pb2_grpc


# Classe que provê os procedimentos que implementam o serviço de carteira
class Wallet(wallet_pb2_grpc.WalletServicer):
    def __init__(self, stop_event: threading.Event, wallets: dict[str, int]) -> None:
        # Evento de término do servidor
        self._stop_event = stop_event

        # Carteiras
        self.wallets = wallets

        # Ordens de pagamento
        self.payment_orders: dict[int, int] = {}

        # Índice das ordens de pagamento
        self.payment_orders_index = 1

    # Procedimento que retorna o saldo de uma carteira
    def balance(self, request, context):
        # Verifica se a carteira informada existe
        if request.wallet in self.wallets:
            # Caso sim, retorna o saldo na carteira
            return wallet_pb2.BalanceReply(balance=self.wallets[request.wallet])
        else:
            # Caso não, retorna o código de erro -1
            return wallet_pb2.BalanceReply(balance=-1)

    # Procedimento que cria uma ordem de pagamento
    def create_payment_order(self, request, context):
        # Verifica se a carteira informada existe, caso não retorna o status de erro -1
        if request.wallet not in self.wallets:
            return wallet_pb2.CreatePaymentOrderReply(retval=-1)

        # Verifica se a carteira informada tem saldo suficiente, caso não
        # retorna o status de erro -2
        if self.wallets[request.wallet] < request.value:
            return wallet_pb2.CreatePaymentOrderReply(retval=-2)

        # Cria a ordem de pagamento
        self.payment_orders[self.payment_orders_index] = request.value
        self.payment_orders_index += 1

        # Debita o valor da ordem de pagamento na carteira informada
        self.wallets[request.wallet] -= request.value

        # Retorna o ID da ordem de pagamento criada
        return wallet_pb2.CreatePaymentOrderReply(retval=self.index)

    # Procedimento que transfere o valor de uma ordem de pagamento para a carteira informada
    def transfer(self, request, context):
        # Verifica se a ordem de pagamento informada existe, caso não
        # retorna o status de erro -1
        if request.payment_order not in self.payment_orders:
            return wallet_pb2.TransferReply(status=-1)

        # Verifica se o valor de conferência é igual ao valor da ordem de
        # pagamento, caso não retorna o status de erro -2
        if self.payment_orders[request.payment_order] != request.recount:
            return wallet_pb2.TransferReply(status=-2)

        # Verifica se a carteira informada existe, caso não retorna o status de erro -3
        if request.wallet not in self.wallets:
            return wallet_pb2.TransferReply(status=-3)

        # Transfere o valor da ordem de pagamento para a carteira
        self.wallets[request.wallet] += self.payment_orders[request.payment_order]

        # Deleta a ordem de pagamento
        del self.payment_orders[request.payment_order]

        # Retorna o status 0 (sucesso)
        return wallet_pb2.TransferReply(status=0)

    # Procedimento de término da execução do servidor
    def end_execution(self, request, context):
        # Imprime na saída padrão as carteiras e os saldos
        for wallet, value in self.wallets.items():
            print(wallet, value)

        # Sinaliza o evento de encerramento do servidor
        self._stop_event.set()

        # Monta a resposta com o número de ordens de pagamento pendentes e envia para o cliente
        return wallet_pb2.EndExecutionReply(pendencies=len(self.payment_orders))


def run(port, wallets):
    # Define o evento de parada do servidor
    stop_event = threading.Event()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Liga o servidor à classe que implementa os métodos disponibilizados pelo servidor
    wallet_pb2_grpc.add_WalletServicer_to_server(Wallet(stop_event, wallets), server)
    server.add_insecure_port(f"0.0.0.0:{port}")

    server.start()

    # Espera a ocorrência do evento de término do servidor
    stop_event.wait()
    # Quando detectado, o servidor é terminado
    server.stop(None)


if __name__ == "__main__":
    # Lê as carteiras da entrada padrão
    wallets = {}
    for line in sys.stdin:
        id, value = line[:-1].split(" ")
        wallets[id] = int(value)

    # Porta que o servidor irá usar
    port = int(sys.argv[1])

    # Chama a função que inicia o servidor
    run(port, wallets)
