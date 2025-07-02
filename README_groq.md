# Groq APIを使用したセットアップガイド

## 1. Groq APIキーの取得（無料）

1. https://console.groq.com にアクセス
2. Googleアカウントでサインイン
3. 左メニューの「API Keys」をクリック
4. 「Create API Key」をクリック
5. APIキーが表示されるのでコピー

## 2. 環境セットアップ

```bash
# WSL上で実行
cd ~/test_project/network_manual_chatbot

# 仮想環境を有効化
source venv/bin/activate

# 依存関係をインストール
pip install -r requirements.txt

# 環境変数を設定
cp .env.example .env
nano .env
```

`.env`ファイルを編集：
```
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxx  # 取得したAPIキーを貼り付け
```

## 3. アプリケーション起動

```bash
streamlit run app.py
```

## 主な変更点

- **無料**: Groq APIは完全無料
- **高速**: Groqのハードウェア最適化により高速応答
- **日本語対応**: Llama 3 70Bモデルは日本語に対応
- **埋め込みモデル**: HuggingFaceの無料モデルを使用

## レート制限

- 1分あたり30リクエスト程度
- プロトタイプには十分な制限

## トラブルシューティング

### エラー: "GROQ_API_KEY not found"
→ .envファイルにAPIキーが正しく設定されているか確認

### エラー: "Rate limit exceeded"
→ 少し待ってから再度実行してください