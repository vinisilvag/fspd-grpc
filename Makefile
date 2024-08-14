stubs:
	[ -f "wallet_pb2.py" ] || python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. wallet.proto
	[ -f "store_pb2.py" ] || python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. store.proto

run_serv_banco:
	stubs
	python3 wallet-server.py $(arg1)

run_cli_banco:
	stubs
	python3 wallet-client.py $(arg1) $(arg2)

run_serv_loja:
	stubs
	python3 store-server.py $(arg1) $(arg2) $(arg3) $(arg4)

run_cli_loja:
	stubs
	python3 store-client.py $(arg1) $(arg2) $(arg3)

clean:
	rm -f *_pb2*.py
	rm -rf __pycache__
