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
│ │ Flask App    ├───────────────────►│ 1024x1024 FFHQ │ │
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

本アプリケーションで使用する画像データセットを準備します。現在は **FFHQ 1024x1024** データセットを使用しています。

1.  **ソースデータのダウンロード:**
    -   **画像:** NVIDIA公式の `download_ffhq.py` 等を使用して、**1024x1024** 解像度の画像をダウンロードします。
    -   **ラベル:** 性別情報が含まれる`ffhq_aging_labels.csv`等を準備します。

2.  **依存ライブラリのインストール:**
    画像分類スクリプトに必要なライブラリをインストールします。
    ```bash
    pip install pandas tqdm pillow
    ```

3.  **画像分類スクリプトの実行:**
    `scripts/prepare_ffhq.py` などを利用して、画像をフィルタリング・分類します。
    -   最終的な画像は、`Data/FFHQ/ffhq_sorted` 内に `性別/年齢/人種/ファイル名` の構造で配置されることを想定しています。

### ステップ2: クラウドストレージへの同期

1.  **R2にアップロード:**
    分類済みの画像フォルダを、Cloudflare R2バケットのルートにアップロードします。

2.  **マニフェストファイルの生成:**
    アップロードした画像のリストを記載した`manifest.txt`を作成します。
    - ファイル形式 (各行: `性別/年齢/人種/ファイル名`):
      ```
      female/15-19/asian/00001.png
      female/20-29/asian/00002.png
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
    -   **Build Command:** `pip install -r requirements.txt`
    -   **Start Command:** `gunicorn image_labeler.app:app`
    -   **環境変数:**
        -   `DATABASE_URL`: RenderのPostgreSQLから提供される接続文字列。
        -   `R2_BASE_URL`: Cloudflare R2の公開バケットURL。（例: `https://pub-xxxxxxxx.r2.dev`）

3.  **手動デプロイと初期化:**
    - データベースの初期化や更新が必要な場合は、別途初期化スクリプトを実行する手順が必要です（データ保護のため、デプロイごとの自動初期化は無効化されています）。

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