# 画像評価アンケートツール

## 1. 概要

本プロジェクトは、高品質な顔画像データセットを構築するため、主観的な評価を収集することを目的としたWebベースのアンケートツールです。

現在は **FFHQ (Flickr-Faces-HQ)** データセットをベースとし、参加者は一連の顔画像を5段階の星評価で評価します。収集されたデータは、将来の高品質な画像生成モデル（VAE, Latent Diffusion Modelsなど）の訓練データとして活用されます。

## 2. アーキテクチャ

このアプリケーションは、PaaSと外部クラウドストレージを組み合わせた、モダンでスケーラブルな構成を採用しています。

- **アプリケーションサーバー:** [Render](https://render.com/) (PaaS)
- **バックエンド:** Python / Flask
- **データベース:** PostgreSQL (on Render)
- **画像ストレージ:** Cloudflare R2 (or any S3-compatible object storage)
- **デプロイ:** GitHubへのpushをトリガーとした自動デプロイ

```
  ユーザー
     │
     ▼ (HTTPS)
┌──────────────────┐
│  ブラウザ         │
│  (React/JS/CSS)  │
└────────┬─────────┘
         │ ▲
         │ │ APIリクエスト (JSON)
         │ │
         ▼ │
┌──────────────────┐               ┌──────────────────┐
│ Render           │               │ Cloudflare R2      │
│ ┌──────────────┐ │ GET image     │ ┌────────────────┐ │
│ │ Flask App    ├───────────────────►│ 512x512 FFHQ   │ │
│ │ (Gunicorn)   │ │               │ │ 画像ファイル   │ │
│ └───────┬──────┘ │               │ └────────────────┘ │
│         │        │               └──────────────────┘
│         │ SQL
│         ▼
│ ┌──────────────┐
│ │ PostgreSQL   │
│ │ (DB on Render) │
│ └──────────────┘
└──────────────────┘
```

## 3. セットアップと実行フロー

### ステップ1: データセットの準備 (初回のみ)

本アプリケーションで使用する画像データセットを準備します。

1.  **ソースデータのダウンロード:**
    -   **画像:** 512x512ピクセルのFFHQデータセットをダウンロードします。（例: [Kaggle](https://www.kaggle.com/datasets/arnaud58/flickrfaceshq-dataset-ffhq)）
    -   **ラベル:** 性別情報が含まれる`ffhq_aging_labels.csv`を、[royorel/FFHQ-Aging-Dataset](https://github.com/royorel/FFHQ-Aging-Dataset)からダウンロードします。

2.  **依存ライブラリのインストール:**
    画像分類スクリプトに必要なライブラリをインストールします。
    ```bash
    pip install pandas tqdm pillow
    ```

3.  **画像分類スクリプトの実行:**
    ダウンロードした画像とラベルCSVを元に、画像を`male`と`female`フォルダに分類します。
    ```bash
    python scripts/prepare_ffhq.py \
        --csv_path "/path/to/your/ffhq_aging_labels.csv" \
        --source_dir "/path/to/your/ffhq-512px-images/" \
        --output_dir "./Data/FFHQ_512x512_sorted"
    ```
    -   実行後、`./Data/FFHQ_512x512_sorted`内に`male`と`female`フォルダが生成されます。

### ステップ2: クラウドストレージへの同期

1.  **R2にアップロード:**
    ステップ1で生成された`male`と`female`フォルダを、Cloudflare R2バケットのルートにアップロードします。

2.  **マニフェストファイルの生成:**
    アップロードした画像のリストを記載した`manifest.txt`を作成します。これはデータベースへの登録に必要です。R2のCLIツール(`rclone`など)を使うか、手動でファイルリストを生成してください。
    - ファイル形式 (各行: `性別/ファイル名`):
      ```
      female/00001.png
      female/00002.png
      male/00003.png
      ...
      ```
    - 生成した`manifest.txt`を`image_labeler/`ディレクトリに配置します。

### ステップ3: ローカルでの開発・実行

1.  **仮想環境の有効化:**
    ```bash
    source .venv/bin/activate
    ```

2.  **依存関係のインストール:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **環境変数の設定 (任意):**
    ローカルではデフォルトでSQLiteが使用されます。もし外部DBをテストしたい場合は、`DATABASE_URL`環境変数を設定してください。
    
4.  **アプリケーションの実行:**
    ```bash
    python image_labeler/app.py
    ```
    - サーバーが起動し、`instance/survey.db`というSQLiteデータベースが自動的に作成・初期化されます。

### ステップ4: 本番環境へのデプロイ (Render)

1.  **リポジトリの変更をPush:**
    - `image_labeler/manifest.txt` が最新の状態になっていることを確認し、変更をGitHubリポジトリにPushします。

2.  **Renderでの設定:**
    -   **Build Command:** `pip install -r requirements.txt && python image_labeler/init_db.py`
    -   **Start Command:** `gunicorn image_labeler.app:app`
    -   **環境変数:**
        -   `DATABASE_URL`: RenderのPostgreSQLから提供される接続文字列。
        -   `R2_BASE_URL`: Cloudflare R2の公開バケットURL。（例: `https://pub-xxxxxxxx.r2.dev`）

3.  **自動デプロイ:**
    - mainブランチへのPushをトリガーに、Renderが自動でビルドとデプロイを実行します。ビルドコマンドの一部として`init_db.py`が実行され、本番データベースのテーブル作成と画像情報の移入が行われます。

## 4. データベーススキーマ

| テーブル | カラム名 | データ型 | 説明 | 
| :--- | :--- | :--- | :--- |
| **Participant** | `id` | 整数 | 回答者ID (主キー) |
| | `created_at` | 日時 | セッション開始日時 |
| | `age` | 整数 | 回答者の年齢（任意） |
| | `gender` | 文字列 | 回答者の性別（任意） |
| **Image** | `id` | 整数 | 画像ID (主キー) |
| | `filename` | 文字列 | 画像のファイル名 |
| | `gender` | 文字列 | 画像の性別 (`male`/`female`) |
| | `url` | 文字列 | R2上の画像の完全な公開URL |
| **Label** | `id` | 整数 | 評価ID (主キー) |
| | `participant_id` | 整数 | `Participant`への外部キー |
| | `image_id` | 整数 | `Image`への外部キー |
| | `rating` | 整数 | 評価スコア (1-5) |
| | `created_at` | 日時 | 評価日時 |

---
*This tool was developed with the assistance of the Gemini CLI.*