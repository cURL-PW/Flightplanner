# MSFS Flightplan Viewer

Microsoft Flight Simulator 2020のフライトプランを表示するアプリケーションです。
各種有名アドオン機体のフライトプランファイルを読み込み、地図上に経路とフィックス情報を表示します。

## 対応機体

- **MSFS標準機体** (B787, A320neo等) - `.pln`形式
- **PMDG** (737/777/747シリーズ) - `.pln`, `.rte`形式
- **Fenix** (A320シリーズ) - `.flp`, `.pln`形式
- **FlyByWire** (A32NX) - `.flp`, `.pln`形式
- **iniBuilds** (A300/A310/A380) - `.pln`, `.flp`形式
- **Aerosoft** (CRJシリーズ) - `.flp`, `.pln`形式
- **その他多数の機体**

## 対応フォーマット

| 形式 | 説明 |
|------|------|
| `.pln` | MSFS標準XML形式 |
| `.flp` | CFMS形式 (Fenix, FlyByWire, Aerosoft) |
| `.rte` | PMDG形式 |

## 機能

- **地図表示**: Leaflet.jsを使用したインタラクティブな地図上でフライトプランを表示
- **ウェイポイント一覧**: 全ウェイポイントの詳細情報をテーブル形式で表示
- **自動検出**: 各機体のフライトプランフォルダを自動的にスキャン
- **フィルター機能**: 機体別、検索ワードでフライトプランをフィルター
- **ダークテーマ**: 目に優しいダークテーマUI

## インストール

### 必要要件

- Python 3.10以上
- PyQt6
- PyQt6-WebEngine

### セットアップ

```bash
# リポジトリをクローン
git clone <repository-url>
cd Flightplanner

# 依存関係をインストール
pip install -r requirements.txt

# アプリケーションを起動
python main.py
```

## 使い方

1. アプリケーションを起動すると、自動的にMSFSのフライトプランフォルダをスキャンします
2. 左側のツリーからフライトプランをダブルクリックして読み込み
3. 「Open File...」ボタンから任意のファイルを開くことも可能
4. 「Add Folder...」でカスタムフォルダを追加可能

## スクリーンショット

### 地図表示
- 経路は青いラインで表示
- ウェイポイントは種類別に色分け
  - 緑: 空港 (APT)
  - 青: VOR
  - 紫: NDB
  - 黄: FIX/インターセクション

### ウェイポイント一覧
- ウェイポイント番号、識別子、種類
- 緯度/経度
- 高度 (フライトレベル)
- 使用エアウェイ

## フォルダ構成

```
Flightplanner/
├── main.py                 # アプリケーションエントリーポイント
├── requirements.txt        # 依存関係
├── README.md
├── samples/                # サンプルフライトプラン
│   ├── RJTT_RJOO.pln      # 羽田→伊丹
│   ├── KJFK_KLAX.pln      # JFK→LAX
│   ├── EGLL_LFPG.flp      # ロンドン→パリ
│   └── EDDF_EDDM.rte      # フランクフルト→ミュンヘン
└── src/
    ├── __init__.py
    ├── models.py           # データモデル
    ├── aircraft_config.py  # 機体設定・パス管理
    ├── map_widget.py       # 地図表示ウィジェット
    ├── main_window.py      # メインウィンドウ
    └── parsers/
        ├── __init__.py
        ├── base.py         # パーサー基底クラス
        ├── pln_parser.py   # PLN形式パーサー
        ├── flp_parser.py   # FLP形式パーサー
        └── rte_parser.py   # RTE形式パーサー
```

## ライセンス

MIT License
