import subprocess
from utils.get_proof import Proof
import asyncio


import subprocess
from utils.get_proof import Proof
import asyncio
import json

class ZoKratesProof:
    def __init__(self, container_name='zokrates'):
        self.container_name = container_name

    def execute_in_container(self, rsi, prediction, oversold, overbought):
        # Create the command that will be executed inside the container
        commands = f"""
        cd code && \
        zokrates compute-witness -a {rsi} {prediction} {oversold} {overbought} && \
        zokrates generate-proof && \
        zokrates verify
        """
        
        try:
            # Execute commands in container
            result = subprocess.run(
                ['docker', 'exec', self.container_name, '/bin/bash', '-c', commands],
                capture_output=True,
                text=True,
                check=True
            )
            print(result.stdout)
            
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
                'inputs': proof_data['inputs']
            }
            
        except subprocess.CalledProcessError as e:
            print(f"Error executing commands in container: {e.stderr}")
            return False
        except json.JSONDecodeError as e:
            print(f"Error parsing proof.json: {e}")
            return False


async def main():
    prover = ZoKratesProof()
    data = prover.execute_in_container(101, 1, 30, 70)
    print(f"Proof generation {'successful' if data else 'failed'}")
    getter = Proof()
    proof = await getter.get_proof(data)

     

    return proof


if __name__ == "__main__":
    #hash = main()
    hash = asyncio.run(main())
    print(hash)
