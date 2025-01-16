import subprocess
from utils.get_proof import Proof
import asyncio
import shutil
import os

import subprocess
from utils.get_proof import Proof
import asyncio
import json

class ZoKratesProof:
    def __init__(self, container_name='zokrates'):
        self.container_name = container_name

    def execute_in_container(self, rsi, 
                             prediction, 
                             oversold, 
                             overbought,
                             haspos,
                             ret,
                             thresh):

        print(f"Current working directory: {os.getcwd()}")
        commands = f"""
        cd code && \
        zokrates compute-witness -a {rsi} {prediction} {oversold} {overbought} {haspos} {ret} {thresh} && \
        zokrates generate-proof && \
        zokrates verify &&\
        zokrates export-verifier 
        """
        print(f"Executing command in container: {commands}")
        
        try:
            # Execute commands in container
            result = subprocess.run(
                ['docker', 'exec', self.container_name, '/bin/bash', '-c', commands],
                capture_output=True,
                text=True,
                check=True
            )
            print("Container execution output:", result.stdout)
        
        
            # Copy the verifier.sol using local file operations
            # First, copy from container to current directory
            # Try using the full paths and ensure correct syntax
            copy_from_container = subprocess.run(
                ['docker', 'exec', self.container_name, '/bin/bash', '-c', 'cp ./code/verifier.sol /tmp/verifier.sol'],
                capture_output=True,
                text=True,
                check=True
            )
            final_destination = "./Privacy-Preserving-Algorithmic-Trading-with-Zero-Knowledge-Proofs/zkproof/zkproof_forge/src/verifier.sol"

            # Then copy from container to host
            try:
                
            
                docker_cp_command = subprocess.run(
                    ['docker', 'cp', f'{self.container_name}:/tmp/verifier.sol', final_destination],
                    capture_output=True,
                    text=True,
                    check=True
                )
                print(f"Successfully copied verifier.sol to {final_destination}")
            except FileNotFoundError:
                print(f"Source file not found at")
                print("Current directory:", os.getcwd())
                print("Files in current directory:", os.listdir())
            except Exception as e:
                print(f"Error copying file: {e}")

            target_directory = "./Privacy-Preserving-Algorithmic-Trading-with-Zero-Knowledge-Proofs/zkproof/zkproof_forge"
            os.chdir(target_directory)
            # Load environment variables from .env file
            env = os.environ.copy()
            with open('.env', 'r') as f:
                for line in f:
                    # Skip comments and empty lines
                    if line.strip() and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        env[key] = value.strip().strip('"').strip("'")
            
            try:
                forge_script_command = subprocess.run(
                    [
                        'forge', 'script', 
                        'script/Deploy_verifier.sol:CounterScript', 
                        '--fork-url', env['SEPOLIA_RPC_URL'], 
                        '--private-key', env['PRIVATE_KEY'], 
                        '--broadcast'
                    ],
                    env=env,
                    capture_output=True,
                    text=True,
                    check=True
                )

                # Print output for debugging
                print("Standard Output:", forge_script_command.stdout)
                print("Standard Error:", forge_script_command.stderr)

            except subprocess.CalledProcessError as e:
                print("Command failed with error:")
                print("Return Code:", e.returncode)
                print("Standard Output:", e.stdout)
                print("Standard Error:", e.stderr)
            except Exception as e:
                print("An error occurred:", str(e))

            json_path = "./broadcast/Deploy_verifier.sol/11155111/run-latest.json"
            # Read the JSON file
            try:
                with open(json_path, 'r') as f:
                    data = json.load(f)
            except FileNotFoundError:
                print(f"Error: JSON file not found at {json_path}")
                raise
            except json.JSONDecodeError:
                print(f"Error: Invalid JSON format in {json_path}")
                raise
            except Exception as e:
                print(f"Unexpected error reading JSON file: {e}")
                raise

            # Extract the contract address
            try:
                sepolia_address = data['receipts'][0]['contractAddress']
            except (KeyError, IndexError) as e:
                print("Error: Unable to extract contract address from JSON")
                print(f"JSON structure: {json.dumps(data, indent=2)}")
                raise

            print(f"Sepolia_address set to: {sepolia_address}")
            
            # Get proof.json content
            cat_command = "cd code && cat proof.json"
            proof_result = subprocess.run(
                ['docker', 'exec', self.container_name, '/bin/bash', '-c', cat_command],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse the JSON content
            proof_data = json.loads(proof_result.stdout)
            
            # Extract proof and inputs
            return {
                'proof': proof_data['proof'],
                'inputs': proof_data['inputs'],
                'contract_address': sepolia_address
            }
            
        except subprocess.CalledProcessError as e:
            print(f"Error executing commands in container: {e.stderr}")
            return False
        except json.JSONDecodeError as e:
            print(f"Error parsing proof.json: {e}")
            return False


async def prove(rsi,
                prediction,
                oversold_threshold,
                overbought_threshold,
                haspos,
                ret,
                thresh):
            proover = ZoKratesProof()
            data = proover.execute_in_container(rsi,
                                             prediction,
                                             oversold_threshold,
                                             overbought_threshold,
                                             haspos,
                                             ret,
                                             thresh)
            print(f"Proof generation {'successful' if data else 'failed'}")
            getter = Proof()
            proof = await getter.get_proof(data)


            return proof



