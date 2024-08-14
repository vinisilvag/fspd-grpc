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
        """
        Construtor da classe que provê os procedimentos que implementam o
        serviço de loja.

        Parâmetros:
            stop_event (threading.Event): evento usado para determinar quando
                                          o servidor deve parar de executar
            wallet_addr (tuple[str, int]): endereço do servidor de carteiras
            seller_wallet (str): identificador da carteira do vendedor
            price (int): preço do produto vendido
        """

        # Evento de término do servidor
        self._stop_event = stop_event

        # Carteira do vendedor
        self.seller_wallet = seller_wallet
        print("seller wallet:", self.seller_wallet)

        # Preço do produto
        self.price = price
        print("price:", self.price)

        # Saldo em conta do vendedor
        self.balance = 0

        # A abertura do canal e a geração dos stubs é feita no construtor da
        # classe para evitar que a comunicação tenha que ser estabelecida toda
        # vez que for preciso comunicar com o servidor de carteiras
        # Dessa forma, minimizamos o overhead de estabelecimento da conexão
        # entre as duas pontas, obtendo um ligeiro ganho de desempenho
        self.wallet_channel = grpc.insecure_channel(
            f"{wallet_addr[0]}:{wallet_addr[1]}"
        )
        self.wallet_stub = wallet_pb2_grpc.WalletStub(self.wallet_channel)

        self._fetch_balance()

    def _fetch_balance(self):
        """
        Função auxiliar que consulta o saldo na carteira do vendedor e armazena
        o resultado obtido no atributo `balance` da classe.
        """

        balance_response = self.wallet_stub.balance(
            wallet_pb2.BalanceRequest(wallet=self.seller_wallet)
        )

        # A especificação não determina se essa chamada pode falhar,
        # portanto, o código foi escrito considerando que uma carteira
        # válida sempre será informada
        # Dessa forma, é assumido que o valor presente em balance nesse
        # momento é um valor válido >= 0 e não um código de erro
        self.balance = balance_response.balance
        print("balance:", self.balance)

    def read_price(self, request, context):
        """
        Envia para o cliente o preço do produto vendido pelo servidor.

        Retorna:
            Uma mensagem de tipo ReadPriceReply contendo o preço do produto.
        """

        # Monta a resposta com o preço do produto recebido como parâmetro
        return store_pb2.ReadPriceReply(price=self.price)

    def sell(self, request, context):
        """
        Construtor da classe que provê os procedimentos que implementam o
        serviço de loja.

        Parâmetros:
            stop_event (threading.Event): evento usado para determinar quando
                                          o servidor deve parar de executar
            wallet_addr (tuple[str, int]): endereço do servidor de carteiras
            seller_wallet (str): identificador da carteira do vendedor
            price (int): preço do produto vendido

        Retorna:
            Uma mensagem de tipo SellReply com o status da operação realizada:
            0, caso a venda tenha sido feita com sucesso, -1, caso a ordem de
            pagamento informada não exista, -2, caso o valor de conferência seja
            diferente do valor contido na ordem de pagamento, -3, caso a
            carteira informada não exista, ou -9, caso haja erro de comunicação
            entre o servidor da loja e o servidor de carteiras.

        """

        # Try ... except para capturar algum erro de comunicação que ocorra
        # na chamada de `transfer`
        # Dessa forma, é possível capturar esse erro e retornar o código
        # de erro -9, assim como a especificação do trabalho sugere
        try:
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
            if transfer_status not in [-1, -2, -3]:
                self.balance += self.price
            print("updated balance:", self.balance)
            return store_pb2.SellReply(status=transfer_status)
        except:
            return store_pb2.SellReply(status=-9)

    def end_execution(self, request, context):
        """
        Finaliza o servidor da loja. Além disso, finaliza também o servidor de
        carteiras, enviando como resposta o saldo atual do vendedor e o número
        de ordens de pagamento pendentes (que serão perdidas).

        Retorna:
            Uma mensagem de tipo EndExecutionReply contendo o saldo do vendedor
            e o número de ordens de pagamento que serão perdidas com o fim da
            execução dos servidores.
        """

        # Assim como na busca do saldo no começo da execução do servidor da
        # loja, a especificação do trabalho não diz se essa chamada pode falhar
        # ou não, portanto, estou assumindo que sempre vou conseguir terminar
        # o servidor de carteiras normalmente e, com isso, receber o número
        # de ordens de pagamento existentes no momento do término dele

        # Chama o procedimento de término do servidor de carteiras
        end_execution_response = self.wallet_stub.end_execution(
            wallet_pb2.EndExecutionRequest()
        )
        # Recebe o número de ordens de pagamento pendentes
        pendencies = end_execution_response.pendencies

        # Fecha o canal de comunicação com o servidor de carteiras
        self.wallet_channel.close()

        # Sinaliza o evento de encerramento do servidor
        self._stop_event.set()

        # Monta a resposta com o saldo atual do vendedor e o número de ordens
        # de pagamento pendentes
        return store_pb2.EndExecutionReply(balance=self.balance, pendencies=pendencies)


def run(price, port, seller_wallet, wallet_addr):
    """
    Inicia o servidor da loja.

    Parâmetros:
        price (int): preço do produto vendido pelo servidor
        port (int): porta que o servidor da loja irá executar
        seller_wallet (str): identificador da carteira do vendedor
        wallet_addr (tuple[str, int]): endereço do servidor de carteiras
    """

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
