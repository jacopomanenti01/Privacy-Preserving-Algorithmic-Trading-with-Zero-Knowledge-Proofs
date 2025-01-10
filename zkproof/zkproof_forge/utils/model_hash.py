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


if __name__ == "__main__":
    hash_value = compute_model_hash()
    print(f"HASH_MODEL={hash_value}")

   