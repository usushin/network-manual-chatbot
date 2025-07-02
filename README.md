# ネットワーク機器マニュアル チャットボット

CISCO等のネットワーク機器の技術マニュアルに基づいて質問に回答するRAG（Retrieval-Augmented Generation）システムです。

## 🚀 主な機能

- 📄 **PDFマニュアルの自動処理**: 複数のPDFを一括でベクトル化
- 🤖 **自然言語での質問応答**: 日本語での技術的質問に対応
- 📍 **参照元表示**: 回答の根拠となったマニュアル箇所を表示
- 💬 **会話履歴保持**: 前の質問を考慮した連続的な対話
- 🔍 **横断検索**: 複数マニュアルから関連情報を検索
- 💰 **完全無料**: Groq APIとHuggingFace埋め込みモデルを使用

## 🛠️ 技術スタック

- **LLM**: Groq API (Llama 3 70B) - 無料
- **埋め込みモデル**: HuggingFace Sentence Transformers - 無料
- **ベクトルDB**: ChromaDB
- **フロントエンド**: Streamlit
- **PDF処理**: PyPDF + カスタムテキストクリーニング

## 📋 前提条件

- Python 3.8以上
- WSL2またはLinux環境（推奨）
- Groq APIキー（無料取得可能）

## ⚡ クイックスタート

### 1. 環境構築

```bash
# プロジェクトディレクトリに移動
cd ~/test_project/network_manual_chatbot

# 仮想環境の作成と有効化
python3 -m venv venv
source venv/bin/activate

# 必要なパッケージのインストール
sudo apt install python3.10-venv python3-pip  # WSLで初回のみ
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Groq APIキーの取得と設定

```bash
# 1. https://console.groq.com/keys でGoogleアカウントでサインイン
# 2. 「Create API Key」をクリックしてキーを取得
# 3. 環境変数ファイルを設定
cp .env.example .env
nano .env  # GROQ_API_KEY=gsk_xxxxx を設定
```

### 3. アプリケーションの起動

```bash
streamlit run app.py
```

ブラウザで `http://localhost:8501` が自動的に開きます。

## 📖 使用方法

### 初回セットアップ

1. **Groq APIキーの入力**
   - サイドバーで取得したAPIキーを入力

2. **マニュアルのアップロード**
   - 「PDFファイルを選択」でマニュアルをアップロード
   - 「マニュアルを処理」ボタンをクリック
   - 処理完了まで数分待機

3. **質問開始**
   - チャット入力欄が表示されたら質問を入力

### 使用例

```
質問例：
- "VRRPの設定手順を教えてください"
- "コマンドラインでインターフェースを設定する方法は？"
- "冗長化構成の注意点は何ですか？"
- "show コマンドの使い方を説明してください"
```

### 2回目以降の利用

- 「保存済みデータを読み込む」ボタンで前回処理したマニュアルを再利用可能
- 新しいマニュアルを追加する場合は再度アップロード

## プロジェクト構造

```
network_manual_chatbot/
├── app.py                  # Streamlitメインアプリ
├── src/
│   ├── document_processor.py  # PDF処理とベクトル化
│   └── chatbot.py            # チャットボットロジック
├── data/
│   ├── manuals/             # PDFマニュアル保存先
│   └── vectorstore/         # ベクトルDB保存先
├── requirements.txt         # 依存関係
├── .env.example            # 環境変数テンプレート
└── README.md               # このファイル
```

## カスタマイズ

### モデルの変更

`.env`ファイルでモデルを変更可能：
```
MODEL_NAME=gpt-4  # より高精度な回答
```

### チャンクサイズの調整

`.env`ファイルで調整：
```
CHUNK_SIZE=1500      # より大きなコンテキスト
CHUNK_OVERLAP=300    # より多くの重複
```

## トラブルシューティング

### APIキーエラー
- OpenAI APIキーが正しく設定されているか確認
- APIの利用上限に達していないか確認

### メモリ不足
- 大量のPDFを処理する場合は、バッチ処理を検討
- チャンクサイズを小さくする

### 回答精度が低い
- より多くの関連マニュアルをアップロード
- GPT-4モデルの使用を検討

## 今後の拡張案

- Azure OpenAI対応
- 多言語対応（英語マニュアル）
- ユーザー認証機能
- 回答の評価機能
- マニュアルの自動更新

## ライセンス

社内利用を前提としています。