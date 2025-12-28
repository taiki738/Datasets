# 環境設定の違い: ローカル開発 vs. 本番 (Render)

このドキュメントは、画像ラベリングアプリケーションのローカル開発環境と、本番環境（Render）における主要な設定の違いをまとめたものです。

アプリケーションのコードベースは各環境で同一に保たれますが、これらの設定値は環境の特性に合わせて外部から供給されます。

---

## 1. データベース接続 (`DATABASE_URL`)

### ローカル開発環境

-   **タイプ:** SQLite
-   **設定方法:**
    -   `DATABASE_URL` 環境変数を**設定しない**ことで、アプリケーションがデフォルト値を使用する。
    -   `app.py`内で、プロジェクトルートの`instance`ディレクトリに`survey.db`というファイルが自動生成されるように設定されている。
-   **例 (内部処理):** `sqlite:////home/tm/img-science/github/Datasets/instance/survey.db`

### 本番環境 (Render)

-   **タイプ:** PostgreSQL
-   **設定方法:**
    -   Renderのダッシュボード（`Environment`設定）で、Renderが提供するPostgreSQLデータベースの接続URLを`DATABASE_URL`として設定する。
-   **例:** `postgresql://your_db_user:your_db_password@your_db_host:5432/your_db_name`
    （`your_db_user`, `your_db_password`, `your_db_host`, `your_db_name` はRenderで発行される実際の値に置き換えてください。）

---

## 2. 画像アセットのベースURL (`R2_BASE_URL`)

### ローカル開発環境

-   **場所:** Cloudflare R2（外部サービス）
-   **設定方法:**
    -   ターミナルで `export R2_BASE_URL=<R2の公開URL>` のように環境変数を設定する。
    -   アプリケーションは、この環境変数からURLを読み込み、R2に保存された画像を直接参照する。
-   **例:** `export R2_BASE_URL=https://pub-25b74b125d8b4c2999f84b64b18ff6oe.r2.dev`

### 本番環境 (Render)

-   **場所:** Cloudflare R2（外部サービス）
-   **設定方法:**
    -   Renderのダッシュボード（`Environment`設定）で、R2の公開URLを`R2_BASE_URL`として設定する。
    -   本番環境もR2に保存された画像を直接参照する。
-   **例:** `R2_BASE_URL = https://pub-25b74b125d8b4c2999f84b64b18ff6oe.r2.dev`

---

## 3. アプリケーションサーバー

### ローカル開発環境

-   **サーバー:** Flaskのビルトイン開発サーバー
-   **起動コマンド:** `python image_labeler/app.py`
-   **特徴:** `debug=True` のため、コード変更時の自動リロードや、詳細なエラーメッセージが表示される。

### 本番環境 (Render)

-   **サーバー:** Gunicorn（WSGIサーバー）
-   **起動コマンド:** Renderの設定で `gunicorn image_labeler.app:app` などと指定。
-   **特徴:** `debug=False` で動作し、本番環境でのパフォーマンスとセキュリティが確保される。

---

## 4. データベースの初期化

### ローカル開発環境

-   **方法:** `if __name__ == '__main__':` ブロック内で `db.create_all()` と `_populate_images_from_manifest()` が実行される。
-   **タイミング:** `python image_labeler/app.py` を実行した際、データベースファイルが存在しない場合に自動的にテーブルが作成され、`manifest.txt`から画像データが投入される。

### 本番環境 (Render)

-   **方法:** デプロイ時にデータベースを初期化するための明示的な`Pre-Deploy Command`（例: `python init_db.py`）を使用するか、手動でマイグレーションツールを実行する。
-   **現在の運用:** データの意図しない損失を防ぐため、`Build Command`からはデータベース初期化コマンドが**削除されている**。データベースのスキーマ変更や初期データ投入は、別途安全な手段（例: Render CLIを使用した手動実行）で行うことが推奨される。