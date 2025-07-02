# ネットワーク機器マニュアル チャットボット

CISCO等のネットワーク機器の技術マニュアルに基づいて質問に回答するRAGシステムです。

## 機能

- PDFマニュアルの自動処理とベクトル化
- 自然言語での質問応答
- 回答の参照元表示
- 会話履歴の保持
- 複数マニュアルの同時検索

## セットアップ

### 1. 環境構築

```bash
# リポジトリのクローン
cd network_manual_chatbot

# 仮想環境の作成（推奨）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係のインストール
pip install -r requirements.txt
```

### 2. OpenAI APIキーの設定

```bash
# .env.exampleをコピー
cp .env.example .env

# .envファイルを編集してAPIキーを設定
# OPENAI_API_KEY=your_actual_api_key_here
```

### 3. アプリケーションの起動

```bash
streamlit run app.py
```

ブラウザが自動的に開き、`http://localhost:8501`でアプリケーションが表示されます。

## 使い方

### 初回セットアップ

1. **APIキーの入力**
   - サイドバーにOpenAI APIキーを入力

2. **マニュアルのアップロード**
   - サイドバーの「マニュアルのアップロード」セクションでPDFファイルを選択
   - 「マニュアルを処理」ボタンをクリック
   - 処理には数分かかる場合があります

3. **質問の入力**
   - チャット入力欄に技術的な質問を入力
   - Enterキーで送信

### 2回目以降の利用

- 「保存済みデータを読み込む」ボタンで前回処理したマニュアルを再利用可能

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