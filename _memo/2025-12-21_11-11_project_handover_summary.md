# プロジェクト引き継ぎ・作業再開ガイド (2025-12-21)

## 1. 使用したツール & サービス一覧

### サービス
-   **GitHub:**
    -   **役割:** ソースコードのバージョン管理。
    -   **URL:** `https://github.com/taiki738/Datasets`
-   **Cloudflare R2:**
    -   **役割:** 全ての画像アセットのホスティング。
    -   **バケット名:** `fairface`
    -   **公開URL:** `https://pub-8a092c33fb2543a78b50eceac30fa75d.r2.dev`
-   **Render:**
    -   **役割:** アプリケーションとデータベースの本番ホスティング環境。
    -   **Webサービス:** `image-labeler-app`
    -   **データベースサービス:** `image-labeler-db` (PostgreSQL)

### ツール
-   **`git`:**
    -   **役割:** GitHubへのコードのプッシュとバージョン管理。
-   **`rclone`:**
    -   **役割:** ローカルPCからCloudflare R2へ画像ファイルをアップロードする。
    -   **設定:** ローカルPCに設定済み。
-   **DBeaver (Community Edition):**
    -   **役割:** Render上の本番PostgreSQLデータベースに接続し、内容を確認するためのGUIツール。
    -   **インストール:** Windows版をローカルPCにインストール済み。

## 2. プロジェクトの構成と重要な設定

-   **`image_labeler/app.py`:** アプリケーションのメインファイル。
-   **`image_labeler/init_db.py`:** データベースのテーブル作成と、画像リストの初期投入を行うスクリプト。
-   **`image_labeler/manifest.txt`:** R2にアップロードした全画像ファイルのパス一覧。`init_db.py`がこれを読み込む。
-   **`requirements.txt`:** 本番環境で必要なPythonパッケージ。
-   **Renderのビルドコマンド:**
    -   **コマンド:** `pip install -r ../requirements.txt && python init_db.py`
    -   **役割:** 依存関係のインストール後、データベースの初期化スクリプトを実行する。無料プランで`Pre-Deploy Command`を代替するための重要な設定。

## 3. 作業再開・運用手順

### ローカルでの開発

1.  Pythonの仮想環境を有効化します (`source .venv/bin/activate`)。
2.  `requirements.txt` に変更があれば、`pip install -r requirements.txt` を実行します。
3.  `python image_labeler/app.py` を実行して、ローカルサーバーを起動します。
    *   ローカル環境では、プロジェクトルートの`instance/survey.db`（SQLite）がデータベースとして使用されます。

### 本番環境（Render）への変更反映

1.  ローカルでコードの変更や機能追加を行います。
2.  変更内容を`git`でコミットし、`master`ブランチにプッシュします。
    ```bash
    git add .
    git commit -m "ここにコミットメッセージ"
    git push origin master
    ```
3.  プッシュ後、Renderが自動でデプロイを開始します。もし5分以上経っても始まらない場合は、Renderのダッシュボードから手動デプロイ（Manual Deploy）を実行してください。

### 画像アセットの追加・更新

1.  ローカルの画像フォルダに新しい画像を追加します。
2.  **`rclone`** を使って、ローカルの画像フォルダとR2の`fairface`バケットを同期させます。
    ```bash
    # 例: /path/to/local/images の内容をR2のfairfaceバケットにコピー
    rclone copy /path/to/local/images r2:fairface --progress
    ```
3.  **`image_labeler/manifest.txt`** を更新し、追加した画像のファイルパスを追記します。
4.  更新した`manifest.txt`をGitHubにプッシュします。次回のデプロイ時に、`init_db.py`が実行され、新しい画像がデータベースに追加されます。

### 本番データベースの確認

1.  **DBeaver**を起動します。
2.  保存済みのRenderデータベースへの接続設定を使います。
3.  接続できない場合、Renderの`image-labeler-db`の「Connect」タブから`External Database URL`を確認し、DBeaverの接続情報を更新してください（パスワードは定期的に変更される可能性があります）。
4.  接続後、「Database Navigator」からテーブルを選択し、「View Data」で内容を確認します。
