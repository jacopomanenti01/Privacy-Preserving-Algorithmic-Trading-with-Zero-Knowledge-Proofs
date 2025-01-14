import web3
import web3.eth
import web3.providers 
from dotenv import load_dotenv
import os
import json
from web3 import Web3
import asyncio

# Internal imports

'''   
class Proof():

    
    def load_env_file(self):
        dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_path = os.path.join(dir_path, "zkproof_forge", ".env")

        load_dotenv(env_path)

    def connect_provider(self):
        RPC = os.getenv("RPC_URL")
        address = os.getenv("ADDRESS")
        private_key = os.getenv("PRIVATE_KEY")


        # connect to poligon
        provider = Web3(Web3.HTTPProvider(RPC))

        # Check connection
        if not provider.is_connected():
            raise ConnectionError("Failed to connect to Ethereum network")
        
        return provider,address,private_key

    def load_abi(self):
        # Get abi
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        abi_dir = os.path.join(current_dir, "zkproof_forge", "out", "verifier.sol", "Verifier.json")
        # load abi
        try:
            with open(abi_dir, 'r') as file:
                abi = json.load(file)
            return abi["abi"]
        except FileNotFoundError:
            raise FileNotFoundError(f"ABI file not found at: {abi_dir}")
        except KeyError:
            raise KeyError("ABI key not found in JSON file")


    def format_proof_for_ethereum(self, proof_dict):
        """
        Format proof according to the Solidity contract's Proof struct:
        struct Proof {
            Pairing.G1Point a;
            Pairing.G2Point b;
            Pairing.G1Point c;
        }
        """
        return [
            # G1Point a
            [
                int(proof_dict['a'][0], 16),
                int(proof_dict['a'][1], 16)
            ],
            # G2Point b (note the reverse order for G2 points)
            [
                [int(proof_dict['b'][0][1], 16), int(proof_dict['b'][0][0], 16)],  # X array reversed
                [int(proof_dict['b'][1][1], 16), int(proof_dict['b'][1][0], 16)]   # Y array reversed
            ],
            # G1Point c
            [
                int(proof_dict['c'][0], 16),
                int(proof_dict['c'][1], 16)
            ]
        ]

    # Format the inputs
    def format_inputs(self,input_array):
        return [int(x, 16) if isinstance(x, str) and x.startswith('0x') else int(x) for x in input_array]



   
    async def get_proof(self,proof_data):
            self.load_env_file()
            provider,address,private_key = self.connect_provider()
            # Format the proof exactly as the contract expects
            # Format according to the ABI specification
            # Extract proof data from JSON structure
            print(f"This is address:{address}")
            balance = provider.eth.get_balance(address)
            print(f"Balance:{balance}")

            abi = self.load_abi()
            contract_address = os.getenv("VERIFIER_ADDRES")

            print(f"This is contract address {contract_address}")

            if not contract_address:
                raise ValueError("CONTRACT_ADDRESS not found in environment variables")
            
            # create instance of the contract
            contract = provider.eth.contract(address=contract_address, abi=abi)
            chain_id = provider.eth.chain_id
            print(chain_id)

            proof= proof_data["proof"]
            inputs = proof_data["inputs"]

    

            # Debug check before sending
            
                
            print("Simulating call...")
            proof = self.format_proof_for_ethereum(proof)
            inputs = self.format_inputs(inputs)
            print(proof)
            print(inputs)
            result = contract.functions.verifyTx(proof, inputs).call({
                'from': address,
                'gas': 1000000
            })
            print("Simulation successful:", result)
                
                # If simulation works, send the transaction
                #signed_tx = provider.eth.account.sign_transaction(tx_params, private_key)
                #tx_hash = provider.eth.send_raw_transaction(signed_tx.raw_transaction)
                #print(f"Transaction sent: {tx_hash.hex()}")
           



     

     return proof

def hex_to_int(hex_str):
    # Remove '0x' prefix if present and convert to int
    return int(hex_str.replace('0x', ''), 16)


async def main():
     getter = Proof()
     proof = await getter.get_proof()

if __name__ =="__main__":
    # initialize the model
    hash = asyncio.run(main())
    print(hash)

'''  

    






