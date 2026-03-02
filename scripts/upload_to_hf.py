import os
from huggingface_hub import HfApi, create_repo, whoami, login

# --- ログイン ---
print("Logging in to Hugging Face...")
try:
    login()
    user_info = whoami()
    username = user_info['name']
    print(f"Successfully logged in as: {username}")
except Exception as e:
    print(f"Error: {e}")
    exit(1)

api = HfApi()
repo_id = f"{username}/Dataset"
local_folder = "Data/FFHQ"

# 1. リポジトリの準備
print(f"Ensuring repository '{repo_id}' exists...")
create_repo(repo_id=repo_id, repo_type="dataset", private=False, exist_ok=True)

# 2. データのアップロード
print(f"\nStarting upload of '{local_folder}' to '{repo_id}'...")
print("Uploading... This may take several hours for 6.7GB.")

try:
    # 最も互換性の高いシンプルな引数のみを使用
    api.upload_folder(
        folder_path=local_folder,
        repo_id=repo_id,
        repo_type="dataset",
        path_in_repo="Data/FFHQ",
        commit_message="Upload FFHQ dataset",
    )
    print("\nUpload completed successfully!")
    print(f"View your dataset at: https://huggingface.co/datasets/{repo_id}")
except Exception as e:
    print(f"\nAn error occurred: {e}")
    print("\nIf the upload was interrupted, simply run this script again.")
    print("It will automatically resume by skipping files that are already uploaded.")