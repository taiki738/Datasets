# FairFace データセット - 特定条件でのフィルタリング・ダウンロード手順

このガイドでは、FairFace データセットから特定の条件（人種・年齢・性別など）に合致する画像のみを抽出する方法を説明します。

## 前提条件

- Python 3.x がインストールされていること
- pandas ライブラリ（`pip install pandas`）
- 十分なストレージ容量（全データセットは数 GB）

## 📥 ステップ 1: ラベルファイルのダウンロード

FairFace のラベルファイル（CSV 形式）をダウンロードします。

- [Train Labels](https://drive.google.com/file/d/1i1L3Yqwaio7YSOCj7ftgk8ZZchPG7dmH/view)
- [Validation Labels](https://drive.google.com/file/d/1wOdja-ezstMEp81tX1a-EYkFebev4h7D/view)

ダウンロード後、適切なディレクトリに保存します。

```
fairface/
├── fairface_label_train.csv
└── fairface_label_val. csv
```

## 🔍 ステップ 2: CSV ファイルのフィルタリング

### ラベルファイルの構造

CSV ファイルには以下のカラムが含まれています：

| カラム名       | 説明               | 値の例                                                                                           |
| -------------- | ------------------ | ------------------------------------------------------------------------------------------------ |
| `file`         | 画像ファイルのパス | `train/12345.jpg`                                                                                |
| `age`          | 年齢層             | `0-2`, `3-9`, `10-19`, `20-29`, `30-39`, `40-49`, `50-59`, `60-69`, `70+`                        |
| `gender`       | 性別               | `Male`, `Female`                                                                                 |
| `race`         | 人種（7 分類）     | `White`, `Black`, `Latino_Hispanic`, `East Asian`, `Southeast Asian`, `Indian`, `Middle Eastern` |
| `service_test` | テストセット区分   | `True`, `False`                                                                                  |

### フィルタリングスクリプト

以下の Python スクリプトで条件に合致するデータをフィルタリングします。

```python
import pandas as pd
import os

# ===== フィルタリング条件の設定 =====
# 例: 18-25歳くらいの東アジア人
RACE_FILTER = ['East Asian', 'Southeast Asian']  # 対象の人種
AGE_FILTER = ['20-29']  # 18-25歳に最も近い年齢層
GENDER_FILTER = None  # None = 全性別、['Male'] or ['Female'] で指定可能

# ===== ラベルファイルの読み込み =====
train_df = pd.read_csv('fairface_label_train. csv')
val_df = pd.read_csv('fairface_label_val.csv')

# 両方を結合
df = pd.concat([train_df, val_df], ignore_index=True)

print(f"全データ数: {len(df)}")

# ===== フィルタリング処理 =====
filtered_df = df. copy()

# 人種でフィルタリング
if RACE_FILTER:
    filtered_df = filtered_df[filtered_df['race'].isin(RACE_FILTER)]
    print(f"人種フィルタ後: {len(filtered_df)}")

# 年齢でフィルタリング
if AGE_FILTER:
    filtered_df = filtered_df[filtered_df['age'].isin(AGE_FILTER)]
    print(f"年齢フィルタ後: {len(filtered_df)}")

# 性別でフィルタリング
if GENDER_FILTER:
    filtered_df = filtered_df[filtered_df['gender']. isin(GENDER_FILTER)]
    print(f"性別フィルタ後:  {len(filtered_df)}")

# ===== 結果の保存 =====
output_file = 'filtered_images.csv'
filtered_df.to_csv(output_file, index=False)

print(f"\n✅ フィルタリング完了!")
print(f"抽出された画像数: {len(filtered_df)}")
print(f"結果ファイル: {output_file}")

# ===== 統計情報の表示 =====
print("\n📊 抽出データの内訳:")
print("\n年齢分布:")
print(filtered_df['age'].value_counts())
print("\n性別分布:")
print(filtered_df['gender'].value_counts())
print("\n人種分布:")
print(filtered_df['race'].value_counts())
```

### スクリプトの実行

```bash
python filter_fairface. py
```

実行結果例：

```
全データ数: 108501
人種フィルタ後: 25000
年齢フィルタ後: 8500

✅ フィルタリング完了!
抽出された画像数: 8500
結果ファイル: filtered_images.csv
```

## 📥 ステップ 3: 画像データセットのダウンロード

フィルタリング結果を確認後、画像データセット全体をダウンロードします。

### 画像データセットのリンク

- **Padding=0.25 版（推奨）**: [ダウンロード](https://drive.google.com/file/d/1Z1RqRo0_JiavaZw2yzZG6WETdZQ8qX86/view)
  - 顔のマージンが少ない、メイン実験用
- **Padding=1.25 版**: [ダウンロード](https://drive.google.com/file/d/1g7qNOZz9wC7OfOhcPqH1EZ5bk1UKq5FU/view)
  - 顔のマージンが大きい、商用 API 評価用

### ダウンロード後の展開

```bash
# ダウンロードしたzipファイルを展開
unzip fairface-img-margin025-trainval.zip -d fairface_images/
```

ディレクトリ構造：

```
fairface_images/
├── train/
│   ├── 1. jpg
│   ├── 2.jpg
│   └── ...
└── val/
    ├── 1.jpg
    ├── 2.jpg
    └── ...
```

## 📁 ステップ 4: 必要な画像のみを抽出

フィルタリングした CSV に基づいて、必要な画像ファイルのみをコピーします。

### 画像抽出スクリプト

```python
import pandas as pd
import shutil
import os
from pathlib import Path

# ===== 設定 =====
FILTERED_CSV = 'filtered_images.csv'  # ステップ2で作成したCSV
SOURCE_DIR = 'fairface_images'  # 画像データセットのディレクトリ
OUTPUT_DIR = 'filtered_fairface_images'  # 抽出先ディレクトリ

# ===== ディレクトリ作成 =====
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ===== フィルタリング済みCSVの読み込み =====
df = pd.read_csv(FILTERED_CSV)

print(f"抽出対象の画像数: {len(df)}")

# ===== 画像のコピー =====
copied_count = 0
missing_count = 0

for idx, row in df.iterrows():
    # 元画像のパス
    source_path = os. path.join(SOURCE_DIR, row['file'])

    # コピー先のパス（ディレクトリ構造を保持）
    relative_path = row['file']
    dest_path = os.path.join(OUTPUT_DIR, relative_path)

    # コピー先のディレクトリを作成
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)

    # 画像ファイルが存在する場合のみコピー
    if os.path.exists(source_path):
        shutil.copy2(source_path, dest_path)
        copied_count += 1

        if (copied_count % 100) == 0:
            print(f"進行状況: {copied_count}/{len(df)} 画像をコピー済み")
    else:
        print(f"⚠️  ファイルが見つかりません: {source_path}")
        missing_count += 1

# ===== 完了メッセージ =====
print(f"\n✅ 画像抽出完了!")
print(f"コピーされた画像:  {copied_count}")
print(f"見つからなかった画像: {missing_count}")
print(f"出力ディレクトリ: {OUTPUT_DIR}")

# ===== フィルタ済みCSVもコピー =====
shutil.copy2(FILTERED_CSV, os.path.join(OUTPUT_DIR, 'labels.csv'))
print(f"ラベルファイルも保存しました: {os.path.join(OUTPUT_DIR, 'labels.csv')}")
```

### スクリプトの実行

```bash
python extract_images.py
```

実行結果例：

```
抽出対象の画像数:  8500
進行状況: 100/8500 画像をコピー済み
進行状況: 200/8500 画像をコピー済み
...
✅ 画像抽出完了!
コピーされた画像: 8500
見つからなかった画像: 0
出力ディレクトリ: filtered_fairface_images
```

## 📂 最終的なディレクトリ構造

```
filtered_fairface_images/
├── labels.csv           # フィルタリングされたラベル情報
├── train/
│   ├── 12345.jpg
│   ├── 23456.jpg
│   └── ...
└── val/
    ├── 34567.jpg
    ├── 45678.jpg
    └── ...
```

## 🎯 条件設定の例

### 例 1: 若年女性の東アジア人

```python
RACE_FILTER = ['East Asian', 'Southeast Asian']
AGE_FILTER = ['10-19', '20-29']
GENDER_FILTER = ['Female']
```

### 例 2: 中年男性の全人種

```python
RACE_FILTER = None  # 全人種
AGE_FILTER = ['30-39', '40-49']
GENDER_FILTER = ['Male']
```

### 例 3: 高齢者のみ

```python
RACE_FILTER = None
AGE_FILTER = ['60-69', '70+']
GENDER_FILTER = None
```

## ⚠️ 注意事項

### 年齢の精度について

FairFace の年齢分類は以下の範囲で提供されています：

- `0-2`, `3-9`, `10-19`, `20-29`, `30-39`, `40-49`, `50-59`, `60-69`, `70+`

例えば「18-25 歳」という正確な年齢指定はできず、`10-19` と `20-29` を選択することで近似する必要があります。

### ストレージ容量

- 全データセット: 約 5-10GB
- フィルタリング後: 条件によりますが、通常 1-3GB 程度

### ライセンス

FairFace データセットは **CC BY 4.0** ライセンスで提供されています。利用時は以下の論文を引用してください：

```bibtex
@inproceedings{karkkainenfairface,
  title={FairFace: Face Attribute Dataset for Balanced Race, Gender, and Age for Bias Measurement and Mitigation},
  author={Karkkainen, Kimmo and Joo, Jungseock},
  booktitle={Proceedings of the IEEE/CVF Winter Conference on Applications of Computer Vision},
  year={2021},
  pages={1548--1558}
}
```

## 📚 参考リンク

- [FairFace 公式リポジトリ](https://github.com/dchen236/FairFace)
- [論文 PDF](https://openaccess.thecvf. com/content/WACV2021/papers/Karkkainen_FairFace_Face_Attribute_Dataset_for_Balanced_Race_Gender_and_Age_WACV_2021_paper.pdf)

---

**作成日**: 2025-12-18  
**対象データセット**: FairFace v1.0
