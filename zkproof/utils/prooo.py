from eth_utils import to_bytes
from web3 import Web3

# Convert array to bytes
inputs = [30, 70, 0, 30, 1]
inputs_bytes = b''.join([Web3.to_bytes(x) for x in inputs])

print(inputs_bytes)