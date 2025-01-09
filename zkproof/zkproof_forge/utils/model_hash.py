import hashlib
import os

def compute_model_hash():
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    repo_root = os.path.dirname(os.path.dirname(current_dir))
    model_path = os.path.join(repo_root, "Test", "mlModel", "best_model_xboost.joblib")
    
    print(f"Looking for model at: {model_path}")
    with open(model_path, "rb") as f:
        model_data = f.read()
    hash_value = hashlib.sha256(model_data).hexdigest()
    return hash_value

def update_env_file(hash_value, env_file_path):
    if not os.path.exists(env_file_path):
        print(f".env file not found at {env_file_path}. Fail")
        return

    with open(env_file_path, "r") as f:
        lines = f.readlines()

    updated = False
    with open(env_file_path, "w") as f:
        for line in lines:
            if line.startswith("MODEL_HASH="):
                f.write(f"MODEL_HASH={hash_value}\n")
                updated = True
            else:
                f.write(line)
        
        if not updated:
            f.write(f"MODEL_HASH={hash_value}\n")

if __name__ == "__main__":
    hash_value = compute_model_hash()
    print(f"MODEL_HASH={hash_value}")

    # Set environment variable
    os.environ['HASH_MODEL'] = hash_value
    print(f"HASH_MODEL set to: {os.environ['HASH_MODEL']}")

    # Specify the path to your .env file
    env_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    print(env_file_path)
    update_env_file(hash_value, env_file_path)
    print(f"Updated MODEL_HASH in {env_file_path}")