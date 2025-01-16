import web3
import web3.eth
import web3.providers 
from dotenv import load_dotenv
import os
import json
from web3 import Web3
import asyncio

# Internal imports

class Proof():
    def __init__(self):
        self.abi = None
        self.provider = None
        self.contract = None
        self.address = None
        self.isProofSet = True

    
    def load_env_file(self):
        dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_path = os.path.join(dir_path, "zkproof_forge", ".env")

        load_dotenv(env_path)

    def connect_provider(self):
        RPC = os.getenv("SEPOLIA_RPC_URL")
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
            # G1Point ax
            int(proof_dict['a'][0], 16),
            # G1Point ay   
            int(proof_dict['a'][1], 16),
            # G2Point b1 x 
            int(proof_dict['b'][0][1], 16), 
            # G2Point b1 y 
            int(proof_dict['b'][0][0], 16),  
            # G2Point b2 x 
            int(proof_dict['b'][1][1], 16), 
            # G2Point b2 y 
            int(proof_dict['b'][1][0], 16),
            # G1Point c x
            int(proof_dict['c'][0], 16),
            # G1Point c y
            int(proof_dict['c'][1], 16)
        ]

    # Format the inputs
    def format_inputs(self,input_array):
        return [int(x, 16) if isinstance(x, str) and x.startswith('0x') else int(x) for x in input_array]


    async def set_proof(self, proof_data):
        self.load_env_file()
        self.provider,self.address,private_key = self.connect_provider()
        print(f"This is address:{self.address}")
        balance = self.provider.eth.get_balance(self.address)
        print(f"Balance:{balance}")
        self.abi = self.load_abi()

        contract_address = os.getenv("SEPOLIA_VERIFIER_ADDRES")

        print(f"This is contract address {contract_address}")

        if not contract_address:
            raise ValueError("CONTRACT_ADDRESS not found in environment variables")
        # create instance of the contract
        self.contract = self.provider.eth.contract(address=contract_address, abi=self.abi)
        chain_id = self.provider.eth.chain_id
        print(chain_id)

        
        proof= proof_data["proof"]

        print("formatting the proof")
        proof = self.format_proof_for_ethereum(proof)
        print(proof)



        print("Simulating call...")
        try:
            # Get the current nonce
            nonce = self.provider.eth.get_transaction_count(self.address)
            
            # Estimate gas
            gas_estimate = self.contract.functions.setProof(*proof).estimate_gas({'from': self.address})
            
            # Get current gas price
            gas_price = self.provider.eth.gas_price

            print(f"THis is the estimated gas price: {gas_price}")

            # Prepare transaction parameters
            tx_params = {
                'nonce': nonce,
                'gasPrice': gas_price,
                'gas': int(gas_estimate * 1.2),  # Add 20% buffer to gas estimate
                'to': contract_address,
                'from': self.address,
                'data': self.contract.encode_abi('setProof', args=[*proof]),
                'chainId': chain_id
            }

            print("Simulating call...")
            
            # Sign transaction
            signed_tx = self.provider.eth.account.sign_transaction(tx_params, private_key)
            
            # Send transaction
            tx_hash = self.provider.eth.send_raw_transaction(signed_tx.raw_transaction)
            print(f"Transaction sent: {tx_hash.hex()}")
            
            # Wait for transaction receipt
            receipt = self.provider.eth.wait_for_transaction_receipt(tx_hash)
            print(f"Transaction confirmed in block {receipt['blockNumber']}")
            # Verify the proof was actually set
            await asyncio.sleep(4)

            try:
                self.isProofSet =  self.contract.functions.isProofSet().call({'from': self.address})
                print(f"Proof set verification: {self.isProofSet}")
            except Exception as verify_e:
                print(f"Could not verify if proof was set: {verify_e}")

            
            return {
                'success': True,
                'tx_hash': tx_hash.hex(),
                'receipt': dict(receipt)
            }
        
        except Exception as e:
            print(f"Error setting proof: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'proof': proof
            }

    def to_uint256(self,hex_str):
        # Remove '0x' prefix and convert hex to int
        return int(hex_str, 16)

    def transform_proof(self,input_proof):
        return [
            # Convert 'a' values
            [self.to_uint256(input_proof['a'][0]), self.to_uint256(input_proof['a'][1])],
            
            # Convert 'b' values (nested arrays)
            [
                [self.to_uint256(input_proof['b'][0][0]), self.to_uint256(input_proof['b'][0][1])],
                [self.to_uint256(input_proof['b'][1][0]), self.to_uint256(input_proof['b'][1][1])]
            ],
            
            # Convert 'c' values
            [self.to_uint256(input_proof['c'][0]), self.to_uint256(input_proof['c'][1])]
        ]



   
    async def get_proof(self,proof_data):    
        try:
            # Format and validate inputs
            inputs = proof_data["inputs"]
            print("Formatting inputs...")
            inputs = self.format_inputs(inputs)
            proof = self.transform_proof(proof_data["proof"])
            print("Formatted inputs:", inputs)   
            print("This is proof:", proof)   


            # Cancel 
            self.load_env_file()
            self.provider,self.address,private_key = self.connect_provider()
            print(f"This is address:{self.address}")
            balance = self.provider.eth.get_balance(self.address)
            print(f"Balance:{balance}")
            self.abi = self.load_abi()

            contract_address = proof_data['contract_address']
            print(f"Contract address before check{contract_address}")
            contract_address=Web3.to_checksum_address(contract_address)
            print(f"This is contract address {contract_address}")

            if not contract_address:
                raise ValueError("CONTRACT_ADDRESS not found in environment variables")
            # create instance of the contract
            self.contract = self.provider.eth.contract(address=contract_address, abi=self.abi)
            chain_id = self.provider.eth.chain_id
            print(f"Chain ID: {chain_id}")
           

            try:
                
                if self.isProofSet:
                    verify_resutl =  self.contract.functions.verifyTx(proof,inputs).call()
                    return verify_resutl

                '''        
                    if not self.isProofSet:
                        return {
                            'success': False,
                            'error': 'Proof was not properly set before verification'
                        }

                    print("Calling verifyTx...")
                    verify_data = self.contract.encode_abi(
                'verifyTx',
                args=[*inputs]
            )
                    result = self.provider.eth.call({
                'to': self.contract.address,
                'from': self.address,
                'data': verify_data
            })

                    # Decode the result
                    decoded_result = self.contract.decode_function_result('verifyTx', result)
                    print(f"Verification result: {decoded_result}")

                    
                    return {
                        'success': True,
                        'verified': decoded_result
                    }
                '''
            except Exception as verify_error:
                    error_msg = str(verify_error)
                    print(f"Verification error: {error_msg}")
                    
                    if "invalid opcode" in error_msg:
                        return {
                            'success': False,
                            'error': 'Invalid operation during verification. Please check input values and proof format.',
                            'inputs': inputs
                        }
                    
                    return {
                        'success': False,
                        'error': error_msg,
                        'inputs': inputs
                    }

        except Exception as e:
            print(f"Error in get_proof: {str(e)}")
            return {
                    'success': False,
                    'error': str(e)
                }

 




async def main():
     getter = Proof()
     proof = await getter.set_proof()

if __name__ =="__main__":
    # initialize the model
    hash = asyncio.run(main())
    print(hash)



    






