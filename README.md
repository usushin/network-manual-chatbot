# ネットワーク機器マニュアル チャットボット

CISCO等のネットワーク機器の技術マニュアルに基づいて質問に回答するRAG（Retrieval-Augmented Generation）システムです。

## 🚀 主な機能

- 📄 **PDFマニュアルの自動処理**: 複数のPDFを一括でベクトル化
- 🤖 **自然言語での質問応答**: 日本語での技術的質問に対応
- 📍 **参照元表示**: 回答の根拠となったマニュアル箇所を表示
- 💬 **会話履歴保持**: 前の質問を考慮した連続的な対話
- 🔍 **横断検索**: 複数マニュアルから関連情報を検索
- 💰 **完全無料**: Groq APIとHuggingFace埋め込みモデルを使用
- 💾 **キャッシュ機能**: 高速回答のためのキャッシュシステム
- 📊 **パフォーマンス監視**: 実行時間とシステムリソース監視

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
# リポジトリのクローン
git clone https://github.com/yourusername/network_manual_chatbot.git
cd network_manual_chatbot

# 仮想環境の作成と有効化
python3 -m venv venv
source venv/bin/activate

# 依存関係のインストール
pip install -r requirements.txt

