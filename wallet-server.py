# Servidor de carteiras
# Vinicius Gomes - 2021421869

import sys
import threading
from concurrent import futures

import grpc

import wallet_pb2
import wallet_pb2_grpc


# Classe que provê os métodos que implementam o serviço de carteiras
class Wallet(wallet_pb2_grpc.WalletServicer):
    def __init__(self, stop_event: threading.Event, wallets: dict[str, int]) -> None:
        """
        Construtor da classe que provê os procedimentos que implementam o
        serviço de carteira.

        Parâmetros:
            stop_event (threading.Event): evento usado para determinar quando
                                          o servidor deve parar de executar
            wallets (dict[str, int]): dicionário com as carteiras lidas da
                                      entrada padrão antes do servidor começar
                                      a executar
        """

        # Evento de término do servidor
        self._stop_event = stop_event

        # A representação de carteiras e ordens de pagamento segue a sugestão
        # dada pelo professor no enunciado do trabalho
        # Além disso, como as carteiras são identificadas pela String
        # identificadora e as ordens de pagamento pelo índice, o uso de
        # dicionários do Python facilitou bastante a busca por registros nessa
        # estrutura, o que simplificou bastante as verificações realizadas em
        # cada procedimento e o acesso aos valores que cada par guarda

        # Carteiras
        self.wallets = wallets
        print("wallets:", self.wallets)

        # Ordens de pagamento
        self.payment_orders: dict[int, int] = {}
        print("payment orders:", self.payment_orders)

        # Índice das ordens de pagamento
        self.payment_orders_index = 1

    def balance(self, request, context):
        """
        Retorna uma mensagem com o saldo em conta da carteira informada
        como parâmetro.

        Parâmetros:
            request.wallet (str): carteira do cliente

        Retorna:
            Uma mensagem de tipo BalanceReply contendo o saldo em conta da
            carteira informada ou -1, caso a carteira não exista.
        """

        # Verifica se a carteira informada existe
        if request.wallet in self.wallets:
            # Caso sim, retorna o saldo na carteira
            return wallet_pb2.BalanceReply(balance=self.wallets[request.wallet])
        else:
            # Caso não, retorna o código de erro -1
            return wallet_pb2.BalanceReply(balance=-1)

    def create_payment_order(self, request, context):
        """
        Cria uma ordem de pagamento a partir da carteira e do valor informado
        para essa ordem.

        Parâmetros:
            request.wallet (str): carteira em que o valor será debitado
            request.value (int): valor da ordem de pagamento

        Retorna:
            Uma mensagem de tipo CreatePaymentOrderReply contendo o número da
            ordem de pagamento criada ou os códigos de erro -1, caso a carteira
            informada não existe, ou -2, caso o saldo da carteira informada
            seja menor que o valor da ordem de pagamento criada.
        """

        # Verifica se a carteira informada existe, caso não retorna o status
        # de erro -1
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

        print("create payment order")
        print("wallets:", self.wallets)
        print("payment orders:", self.payment_orders)

        # Retorna o ID da ordem de pagamento criada
        return wallet_pb2.CreatePaymentOrderReply(retval=self.payment_orders_index - 1)

    def transfer(self, request, context):
        """
        Transfere o dinheiro de uma ordem de pagamento para uma carteira
        informada.

        Parâmetros:
            request.payment_order (int): número da ordem de pagamento
            request.recount (int): valor de conferência da ordem de pagamento
            request.wallet (str): carteira de destino do dinheiro da ordem de
                                  pagamento

        Retorna:
            Uma mensagem do tipo TransferReply contendo o valor 0, caso a
            operação seja feita com sucesso, ou os códigos de erro -1,
            caso a ordem de pagamento informada não exista, -2, caso o valor de
            conferência informado seja diferente do valor registrado na ordem
            de pagamento, ou -3, caso a carteira informada não existe, ou -2,
            caso a carteira informada não exista.
        """

        # Verifica se a ordem de pagamento informada existe, caso não
        # retorna o status de erro -1
        if request.payment_order not in self.payment_orders:
            return wallet_pb2.TransferReply(status=-1)

        # Verifica se o valor de conferência é igual ao valor da ordem de
        # pagamento, caso não retorna o status de erro -2
        if self.payment_orders[request.payment_order] != request.recount:
            return wallet_pb2.TransferReply(status=-2)

        # Verifica se a carteira informada existe, caso não retorna o
        # status de erro -3
        if request.wallet not in self.wallets:
            return wallet_pb2.TransferReply(status=-3)

        # Transfere o valor da ordem de pagamento para a carteira
        self.wallets[request.wallet] += self.payment_orders[request.payment_order]

        # Deleta a ordem de pagamento
        del self.payment_orders[request.payment_order]

        print("transfer")
        print("wallets:", self.wallets)
        print("payment orders:", self.payment_orders)

        # Retorna o status 0 (sucesso)
        return wallet_pb2.TransferReply(status=0)

    def end_execution(self, request, context):
        """
        Finaliza o servidor de carteiras. Exibe as carteiras registradas e o
        saldo corrente delas e envia o número de ordens de pagamento pendentes
        como resposta.

        Retorna:
            Uma mensagem do tipo EndExecutionReply contendo o número de ordens
            de pagamento pendentes e que serão perdidas com a terminação do
            servidor.
        """

        # Imprime na saída padrão as carteiras e os saldos
        for wallet, value in self.wallets.items():
            print(wallet, value)

        # Sinaliza o evento de encerramento do servidor
        self._stop_event.set()

        # Monta a resposta com o número de ordens de pagamento pendentes e
        # envia para o cliente
        return wallet_pb2.EndExecutionReply(pendencies=len(self.payment_orders))


def run(port, wallets):
    """
    Inicia o servidor de carteiras.

    Parâmetros:
        port (int): porta que o servidor de carteiras irá executar
        wallets (dict[str, int]): carteiras recebidas da entrada padrão
    """

    # Define o evento de parada do servidor
    stop_event = threading.Event()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Liga o servidor à classe que implementa os métodos disponibilizados
    # pelo servidor
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

    while True:
        # Lê uma linha da entrada e em caso de EOFError
        # (fim da leitura) sai do loop
        try:
            line = input()
        except EOFError:
            break

        if not line:
            continue

        id, value = line.split()
        wallets[id] = int(value)

        # Porta que o servidor irá usar
    port = int(sys.argv[1])

    # Chama a função que inicia o servidor
    run(port, wallets)
