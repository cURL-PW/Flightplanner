# MSFS Flightplan Viewer

Microsoft Flight Simulator 2020のフライトプランを表示するPyQt6アプリケーションです。
各種有名アドオン機体のフライトプランファイルを読み込み、地図上に経路とフィックス情報を表示します。

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.4+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## 目次

- [機能](#機能)
- [対応機体](#対応機体)
- [対応フォーマット](#対応フォーマット)
- [インストール](#インストール)
- [使い方](#使い方)
- [キーボードショートカット](#キーボードショートカット)
- [フライトプランの保存場所](#フライトプランの保存場所)
- [フォルダ構成](#フォルダ構成)
- [技術詳細](#技術詳細)
- [トラブルシューティング](#トラブルシューティング)
- [ライセンス](#ライセンス)

---

## 機能

### 地図表示
- **Leaflet.js**を使用したインタラクティブな地図
- 3種類のマップスタイル（ダーク/ストリート/衛星）
- 経路を**大圏コース**（実際の飛行経路）で描画
- ウェイポイントを種類別に色分け表示
- クリックでウェイポイント詳細をポップアップ表示
- 自動ズーム・センタリング

### MSFSリアルタイム連携 (SimConnect)
- ツールバーの「✈ MSFS接続」でシミュレータに接続
- 自機位置を地図上にリアルタイム表示（機首方位に連動して回転）
- 実際に飛行した軌跡を赤いラインで記録・表示
- ステータスバーに「次のFIXまでの距離 / 目的地までの残距離 / ETE」を表示
- 「追従」ボタンで地図を自機に自動追従
- 別途 `pip install SimConnect` が必要（Windows + MSFS環境のみ）

### 気象情報 (METAR)
- 出発地・目的地のMETARを自動取得（aviationweather.gov、APIキー不要）
- フライトカテゴリ（VFR/MVFR/IFR/LIFR）を色付きバッジで表示
- 風向風速・気温・視程・QNHをデコード表示

### 形式間変換エクスポート
- File → Export As から読み込んだプランを任意の形式で保存
- MSFS PLN / Fenix・Aerosoft FLP / PMDG RTE の相互変換が可能
- 例: SimBriefから取得したプランをPMDG用RTEとして書き出し

### ウェイポイント表示
| 色 | 種類 | 説明 |
|----|------|------|
| 緑 | APT | 空港 |
| 青 | VOR | VOR航法援助施設 |
| 紫 | NDB | NDB航法援助施設 |
| 黄 | FIX | インターセクション/フィックス |
| オレンジ | USR | ユーザー定義ポイント |

### その他の機能
- **ウェイポイント一覧**: 全ウェイポイントの詳細情報をテーブル形式で表示
- **自動検出**: 各機体のフライトプランフォルダを自動的にスキャン
- **フィルター機能**: 機体別、検索ワードでフライトプランをフィルター
- **カスタムフォルダ**: 任意のフォルダを追加してスキャン
- **ダークテーマ**: 目に優しいダークテーマUI
- **設定の保存**: ウィンドウサイズ、カスタムフォルダ等を自動保存

---

## 対応機体

| メーカー | 機体 | 対応形式 | 自動検出パス |
|----------|------|----------|--------------|
| **Microsoft/Asobo** | B787, A320neo, CJ4等 | `.pln` | MSFS LocalState |
| **PMDG** | 737/777/747シリーズ | `.pln`, `.rte` | packages/pmdg-aircraft-*/work/Flightplans |
| **Fenix** | A319/A320/A321 | `.flp`, `.pln` | %LOCALAPPDATA%/Fenix/A3XX/Flightplans |
| **FlyByWire** | A32NX | `.flp`, `.pln` | Community/flybywire-aircraft-a320-neo |
| **iniBuilds** | A300/A310/A380 | `.pln`, `.flp` | Community/inibuilds-* |
| **Aerosoft** | CRJ 550/700/900/1000 | `.flp`, `.pln` | %LOCALAPPDATA%/Aerosoft/CRJ/Flightplans |
| **Leonardo** | MD-80シリーズ | `.pln`, `.rte` | %LOCALAPPDATA%/Leonardo/MD-80/Flightplans |
| **Headwind** | A330-900 | `.pln`, `.flp` | Community/headwind-aircraft-a330-900 |
| **LatinVFR** | A340シリーズ | `.pln` | Community/latinvfr-a340 |

---

## 対応フォーマット

### PLN形式 (MSFS標準)
- **拡張子**: `.pln`
- **形式**: XML
- **使用機体**: MSFS標準機、PMDG、iniBuilds等
- **特徴**: 最も一般的な形式。SimBriefからのエクスポートにも対応

```xml
<ATCWaypoint id="CLARK">
    <ATCWaypointType>Intersection</ATCWaypointType>
    <WorldPosition>N35° 28' 0.00",E139° 37' 0.00",+000000.00</WorldPosition>
    <ATCAirway>Y28</ATCAirway>
</ATCWaypoint>
```

### FLP形式 (CFMS)
- **拡張子**: `.flp`
- **形式**: テキスト（CoRte形式またはキー=値形式）
- **使用機体**: Fenix, FlyByWire, Aerosoft CRJ
- **特徴**: Airbusの実機に近いフォーマット

```
[CoRte]
EGLL
CPT VOR 51.2550 -0.9867 0 0 DIRECT
BOGNA INT 50.8500 -0.4500 0 0 L9
LFPG
```

### RTE形式 (PMDG)
- **拡張子**: `.rte`
- **形式**: テキスト
- **使用機体**: PMDG 737/777/747
- **特徴**: PMDGのFMC用フォーマット

```
EDDF RJ 50.0333 8.5706 APT 0 DIRECT
RID RJ 49.8667 8.1667 VOR 0 T104
EDDM RJ 48.3539 11.7861 APT 0 DIRECT
```

---

## インストール

### 必要要件

- **Python**: 3.10以上
- **OS**: Windows 10/11 (MSFS連携の自動検出)
- **ディスク**: 約50MB

### 依存パッケージ

| パッケージ | バージョン | 用途 |
|------------|------------|------|
| PyQt6 | >= 6.4.0 | GUIフレームワーク |
| PyQt6-WebEngine | >= 6.4.0 | 地図表示 (Leaflet.js) |
| lxml | >= 4.9.0 | XMLパース (PLN形式) |
| SimConnect | >= 0.4.24 | MSFSリアルタイム連携（オプション） |

### セットアップ

```bash
# 1. リポジトリをクローン
git clone https://github.com/your-username/Flightplanner.git
cd Flightplanner

# 2. 仮想環境を作成 (推奨)
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# 3. インストール（pyproject.tomlベース）
pip install -e .

# MSFSリアルタイム連携も使う場合
pip install -e ".[simconnect]"

# 4. アプリケーションを起動
python main.py
# または（pip install -e . 済みなら）
flightplanner
```

### 開発者向け

```bash
# 開発用依存（pytest, ruff）を含めてインストール
pip install -e ".[dev]"

# テスト実行
pytest

# Lint
ruff check src/ main.py tests/
```

### 実行ファイル化 (オプション)

```bash
# PyInstallerをインストール
pip install pyinstaller

# 実行ファイルを生成
pyinstaller --onefile --windowed --name "MSFS Flightplan Viewer" main.py
```

---

## 使い方

### 基本操作

1. **起動**: `python main.py` を実行
2. **自動スキャン**: 起動時に自動的にMSFSのフライトプランフォルダをスキャン
3. **フライトプラン選択**: 左側のツリーからダブルクリックで読み込み
4. **地図確認**: 右側の地図タブでルートを確認
5. **詳細確認**: ウェイポイントタブで詳細情報を確認

### ファイルを開く

- **メニュー**: File → Open Flightplan... (Ctrl+O)
- **ボタン**: 「Open File...」をクリック
- **対応形式**: `.pln`, `.flp`, `.rte`

### フォルダを追加

1. 「Add Folder...」をクリック
2. フライトプランが保存されているフォルダを選択
3. 自動的にスキャンされ、ツリーに追加

### フィルタリング

- **機体フィルター**: ドロップダウンから機体を選択
- **検索**: テキストボックスにファイル名の一部を入力

---

## キーボードショートカット

| ショートカット | 機能 |
|----------------|------|
| `Ctrl+O` | ファイルを開く |
| `Ctrl+M` | 地図タブを表示 |
| `Ctrl+W` | ウェイポイントタブを表示 |
| `Ctrl+A` | 高度プロファイルタブを表示 |
| `Ctrl+E` | 気象タブを表示 |
| `Ctrl+D` | お気に入りに追加/解除 |
| `Ctrl+H` | 履歴を表示 |
| `Ctrl+B` | SimBriefからOFPを取得 |
| `Ctrl+,` | 設定を開く |
| `F5` | フライトプランを再スキャン |
| `Alt+F4` | アプリケーションを終了 |

---

## フライトプランの保存場所

### MSFS (Windows Store版)
```
%LOCALAPPDATA%\Packages\Microsoft.FlightSimulator_8wekyb3d8bbwe\LocalState\
```

### MSFS (Steam版)
```
%APPDATA%\Microsoft Flight Simulator\
```

### PMDG
```
[MSFS Community]\pmdg-aircraft-737\work\Flightplans\
[MSFS Community]\pmdg-aircraft-777\work\Flightplans\
[MSFS Community]\pmdg-aircraft-747\work\Flightplans\
```

### Fenix
```
%LOCALAPPDATA%\Fenix\A320\Flightplans\
%LOCALAPPDATA%\Fenix\A319\Flightplans\
%LOCALAPPDATA%\Fenix\A321\Flightplans\
```

### SimBrief (ダウンロード先)
```
%USERPROFILE%\Documents\MSFS Flightplans\
%USERPROFILE%\Downloads\
```

---

## フォルダ構成

```
Flightplanner/
├── main.py                     # アプリケーションエントリーポイント
├── pyproject.toml              # パッケージ定義・ツール設定 (ruff/pytest)
├── requirements.txt            # 依存関係（pip install -e . を推奨）
├── README.md                   # このファイル
├── LICENSE                     # MITライセンス
│
├── .github/workflows/ci.yml   # CI (lint + テスト)
│
├── samples/                    # サンプルフライトプラン
│   ├── RJTT_RJOO.pln          # 羽田 → 伊丹 (PLN形式)
│   ├── KJFK_KLAX.pln          # ニューヨークJFK → ロサンゼルス (PLN形式)
│   ├── EGLL_LFPG.flp          # ロンドン・ヒースロー → パリCDG (FLP形式)
│   └── EDDF_EDDM.rte          # フランクフルト → ミュンヘン (RTE形式)
│
├── tests/                      # pytestテストスイート
│   ├── test_parsers.py
│   ├── test_exporters.py
│   ├── test_flight_calculator.py
│   ├── test_simbrief.py
│   └── test_weather.py
│
└── src/
    ├── __init__.py             # バージョン定義
    ├── theme.py                # モダンダークテーマ (デザイントークン + QSS)
    ├── models.py               # データモデル (Waypoint, Flightplan)
    ├── aircraft_config.py      # 機体設定・パス管理
    ├── map_widget.py           # Leaflet.js地図ウィジェット
    ├── main_window.py          # メインウィンドウUI
    ├── flight_calculator.py    # 距離・方位・大圏コース計算
    ├── altitude_profile_widget.py  # 高度プロファイルチャート
    ├── history_manager.py      # 履歴・お気に入り
    ├── navdata.py              # 内蔵ナビゲーションDB
    ├── simbrief.py             # SimBrief API連携
    ├── simconnect_client.py    # MSFSリアルタイム連携
    ├── weather.py              # METAR取得 (aviationweather.gov)
    ├── weather_widget.py       # 気象タブUI
    ├── settings_dialog.py      # 設定ダイアログ
    │
    ├── parsers/                # フライトプランパーサー
    │   ├── base.py             # パーサー基底クラス
    │   ├── pln_parser.py       # PLN形式 (XML)
    │   ├── flp_parser.py       # FLP形式 (CFMS)
    │   └── rte_parser.py       # RTE形式 (PMDG)
    │
    └── exporters/              # 形式間変換エクスポーター
        ├── pln_exporter.py
        ├── flp_exporter.py
        └── rte_exporter.py
```

---

## 技術詳細

### アーキテクチャ

```
┌─────────────────────────────────────────────────────────┐
│                    MainWindow (PyQt6)                    │
├─────────────────┬───────────────────────────────────────┤
│   FlightplanTree│              TabWidget                │
│   (QTreeWidget) │  ┌─────────────┬─────────────────┐   │
│                 │  │  MapWidget  │ WaypointTable   │   │
│   AircraftFilter│  │ (WebEngine) │  (QTableWidget) │   │
│   SearchBox     │  │             │                 │   │
│                 │  │ Leaflet.js  │                 │   │
│   Buttons       │  │             │                 │   │
└─────────────────┴──┴─────────────┴─────────────────┴───┘
                           │
                           ▼
              ┌────────────────────────┐
              │    Flightplan Parser   │
              ├────────────────────────┤
              │ PlnParser  (.pln/XML)  │
              │ FlpParser  (.flp/CFMS) │
              │ RteParser  (.rte/PMDG) │
              └────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │     Data Models        │
              ├────────────────────────┤
              │ Flightplan             │
              │ Waypoint               │
              │ AircraftConfig         │
              └────────────────────────┘
```

### 地図レンダリング

1. `Flightplan`オブジェクトからウェイポイント座標を抽出
2. JavaScriptコードを動的に生成
3. 一時HTMLファイルとして保存
4. `QWebEngineView`で表示

---

## トラブルシューティング

### 地図が表示されない

**原因**: PyQt6-WebEngineがインストールされていない

```bash
pip install PyQt6-WebEngine
```

### フライトプランが見つからない

**原因**: MSFSのインストールパスが自動検出できない

**対処**:
1. 「Add Folder...」で手動でフォルダを追加
2. 環境変数 `MSFS_PATH` を設定

```bash
# Windows
set MSFS_PATH=C:\Users\YourName\AppData\Local\Packages\Microsoft.FlightSimulator_8wekyb3d8bbwe\LocalState
```

### 日本語ファイル名が文字化け

**原因**: ファイルエンコーディングの問題

**対処**: ファイル名をASCII文字のみに変更

### アプリケーションが起動しない

**確認事項**:
1. Python 3.10以上がインストールされているか
2. すべての依存パッケージがインストールされているか

```bash
pip install -r requirements.txt --upgrade
```

---

## ライセンス

MIT License

Copyright (c) 2024

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

## 貢献

バグ報告や機能リクエストは[Issues](https://github.com/your-username/Flightplanner/issues)までお願いします。

プルリクエストも歓迎します。
