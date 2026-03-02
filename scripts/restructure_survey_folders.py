import os
import shutil
from pathlib import Path

# 設定
BASE_DIR = Path("Data/FFHQ/ffhq_for_survey")
TARGET_CATEGORIES = ["OK_4.0", "not-OK_2.0"]

def reorganize_links():
    if not BASE_DIR.exists():
        print(f"Error: Base directory {BASE_DIR} does not exist.")
        return

    print(f"Starting reorganization in {BASE_DIR}...")

    for category in TARGET_CATEGORIES:
        source_dir = BASE_DIR / category
        
        if not source_dir.exists():
            print(f"Skipping {category}: Directory not found.")
            continue

        print(f"Processing {category}...")
        
        # ディレクトリ内のすべてのファイルを走査
        files = list(source_dir.iterdir())
        if not files:
            print(f"  No files found in {category}.")
            continue

        for file_path in files:
            # シンボリックリンクであることを確認
            if not file_path.is_symlink():
                print(f"  Skipping {file_path.name}: Not a symbolic link.")
                continue

            try:
                # リンク先を取得して解決
                target_path = file_path.resolve()
                target_path_str = str(target_path)

                # パスから性別を判定
                gender = None
                if "/male/" in target_path_str:
                    gender = "male"
                elif "/female/" in target_path_str:
                    gender = "female"
                
                if gender:
                    # 新しい移動先パス: .../ffhq_for_survey/{gender}/{category}/
                    new_dir = BASE_DIR / gender / category
                    new_file_path = new_dir / file_path.name

                    # 移動先ディレクトリを作成
                    new_dir.mkdir(parents=True, exist_ok=True)

                    # リンクを移動
                    shutil.move(str(file_path), str(new_file_path))
                    # print(f"  Moved {file_path.name} -> {new_dir}")
                else:
                    print(f"  Warning: Could not determine gender for {file_path.name} (Target: {target_path})")

            except Exception as e:
                print(f"  Error processing {file_path.name}: {e}")

        # 元のディレクトリが空になったら削除
        if not any(source_dir.iterdir()):
            source_dir.rmdir()
            print(f"Removed empty directory: {source_dir}")
        else:
            print(f"Directory {source_dir} is not empty, keeping it.")

    print("Reorganization complete.")

if __name__ == "__main__":
    reorganize_links()
