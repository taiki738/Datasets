# Data Storage Information

この `Data/` ディレクトリには、研究で使用する画像データセットが配置されます。
画像データは容量が大きいため（約8GB）、Gitでは管理せず **Hugging Face Dataset** 上でホストしています。

## データセットの場所

以下のリンクからデータセットをダウンロードし、このディレクトリ（`Data/`）直下に展開してください。

- **Hugging Face Repository:** [higtr/Dataset](https://huggingface.co/datasets/higtr/Dataset)

## ディレクトリ内容
FFHQ/　内には以下のフォルダとファイルがあります。

- `ffhq_for_furvey/`: 最終的に研究に使用した、被験者の印象ラベルが付与されたデータセット

- `ffhq_sorted/`: FFHQを後述するメタデータでフィルタしたデータセット

- csvファイル: メタデータ。年齢、性別、人種

- `ffhq_survey_fixed.tar.gz`: ffhq_for_survey/ をgoogle colab用で使うために圧縮したもの


## アップロード用スクリプト

ローカルのデータを再度 Hugging Face に同期（アップロード）する場合は、ルートディレクトリにある以下のスクリプトを使用します。

```bash
python3 scripts/upload_to_hf.py
```
