import web3
import web3.providers 
from dotenv import load_dotenv
import os
import json
from web3 import Web3
import asyncio

# Internal imports

class Getter():

        
    def load_env_file(self):
        dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_path = os.path.join(dir_path, "zkproof_forge", ".env")

        load_dotenv(env_path)

    def connect_provider(self):
        RPC = os.getenv("RPC_URL")

        # connect to poligon
        provider = Web3(Web3.HTTPProvider(RPC))

        # Check connection
        if not provider.is_connected():
            raise ConnectionError("Failed to connect to Ethereum network")
        
        return provider

    def load_abi(self):
        # Get abi
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        abi_dir = os.path.join(current_dir, "zkproof_forge", "out", "model.sol", "ModelRegistry.json")
        # load abi
        try:
            with open(abi_dir, 'r') as file:
                abi = json.load(file)
            return abi["abi"]
        except FileNotFoundError:
            raise FileNotFoundError(f"ABI file not found at: {abi_dir}")
        except KeyError:
            raise KeyError("ABI key not found in JSON file")


   
    async def get_hash(self):
        try:
            self.load_env_file()
            provider = self.connect_provider()
            abi = self.load_abi()
            contract_address = os.getenv("CONTRACT_ADDRES")

            if not contract_address:
                raise ValueError("CONTRACT_ADDRESS not found in environment variables")
            
            # create instance of the contract
            contract = provider.eth.contract(address=contract_address, abi=abi)


            model_hash = contract.functions.modelHash().call()

            return model_hash
        except Exception as e:
            print(f"Error getting model hash: {e}")
            raise

async def main():
     getter = Getter()
     hash = await getter.get_hash()

     

     return hash

            
if __name__ =="__main__":
    # initialize the model
    hash = asyncio.run(main())
    print(hash)


    






