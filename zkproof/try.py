import subprocess

def compute_witness(rsi, prediction, oversold, overbought, container_name='zokrates'):
    """
    Compute the witness and generate proof using ZoKrates inside a Docker container.
    
    Args:
        rsi (int): Relative Strength Index value
        prediction (int): Prediction value (0 or 1)
        oversold (int): Oversold threshold
        overbought (int): Overbought threshold
        container_name (str): Name of the Docker container running ZoKrates
    """
    try:
        # Construct the Docker exec command to run ZoKrates commands in /code directory
        compute_witness_cmd = [
            'docker', 'exec', '-it', container_name, '/bin/bash', '-c',
            f'cd /code && zokrates compute-witness -a {rsi} {prediction} {oversold} {overbought}'
        ]
        
        # Run the compute-witness command
        compute_result = subprocess.run(
            compute_witness_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Check for any errors in computing witness
        if compute_result.returncode != 0:
            raise Exception(f"Error in compute-witness: {compute_result.stderr.strip()}")
        
        print("Witness computation successful.")
        print(compute_result.stdout.strip())
        
        # Construct the Docker exec command to generate proof in /code directory
        generate_proof_cmd = [
            'docker', 'exec', '-it', container_name, '/bin/bash', '-c',
            'cd /code && zokrates generate-proof'
        ]
        
        # Run the generate-proof command
        proof_result = subprocess.run(
            generate_proof_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Check for any errors in generating proof
        if proof_result.returncode != 0:
            raise Exception(f"Error in generate-proof: {proof_result.stderr.strip()}")
        
        print("Proof generation successful.")
        print(proof_result.stdout.strip())
    
    except Exception as e:
        print(f"Error during ZoKrates trading proof generation: {e}")

def main():
    # Example trading parameters
    rsi = 25
    prediction = 1
    oversold = 30
    overbought = 70
    
    # Generate trading proof inside the Docker container
    compute_witness(rsi, prediction, oversold, overbought)

if __name__ == "__main__":
    main()