# トラブルシューティングガイド

## 🚨 一般的な問題と解決方法

### 1. インストール・セットアップ関連

#### ❌ `python3-venv not available`
```bash
# エラー内容
The virtual environment was not created successfully because ensurepip is not available.

# 解決方法
sudo apt update
sudo apt install python3.10-venv python3-pip -y
```

#### ❌ パッケージの依存関係エラー
```bash
# エラー内容
ERROR: Cannot install -r requirements.txt ... conflicting dependencies

# 解決方法（段階的）
# 1. 仮想環境を削除して再作成
rm -rf venv
python3 -m venv venv
source venv/bin/activate

# 2. pipをアップグレード
pip install --upgrade pip

# 3. 基本パッケージから順次インストール
pip install langchain langchain-groq langchain-community
pip install chromadb streamlit
pip install pypdf sentence-transformers
```

#### ❌ `ModuleNotFoundError: No module named 'xxx'`
```bash
# 解決方法
# 仮想環境が有効化されているか確認
source venv/bin/activate

# パッケージを個別にインストール
pip install [不足パッケージ名]

# または全体を再インストール
pip install -r requirements.txt
```

### 2. Groq API関連

#### ❌ `GROQ_API_KEY not found`
```bash
# 確認項目
1. .envファイルが存在するか
   ls -la .env

2. .envファイルの内容確認
   cat .env
   # GROQ_API_KEY=gsk_xxxxxxxxxxxxx

3. APIキーの形式確認
   # gsk_ で始まる文字列であることを確認
```

#### ❌ `Rate limit exceeded`
```
エラー内容: 429 Too Many Requests

解決方法:
1. 1-2分待ってから再試行
2. Groqの無料制限: 1分間30リクエスト
3. 連続して質問する場合は間隔を空ける
```

#### ❌ `Invalid API Key`
```
確認項目:
1. APIキーが正しくコピーされているか
2. 余分なスペースが含まれていないか
3. Groqアカウントが有効かhttps://console.groq.com で確認
```

### 3. PDF処理関連

#### ❌ PDF処理でエラーが発生
```python
# エラー例
Error loading PDF xxx.pdf: yyy

# 対処法
1. PDFファイルサイズ確認（100MB以下推奨）
2. PDFが破損していないか確認
3. パスワード保護PDFは事前に解除
4. スキャンPDFの場合、OCR処理済みのものを使用
```

#### ❌ 文字化けした参照元が表示される
```
問題: { puts "server a x e n v ( S e r v e r H o s t ) ...

原因: PDFのテキスト抽出時の文字分離

解決方法:
1. 既存のベクトルストアを削除
   rm -rf data/vectorstore/*

2. アプリを再起動してPDFを再処理
   streamlit run app.py
```

#### ❌ `Total chunks created: 0`
```
原因: PDFからテキストが抽出できない

確認項目:
1. PDFが画像ベース（スキャン）ではないか
2. PDFにテキストが含まれているか
3. PDFファイルが破損していないか

解決方法:
1. OCR処理済みのPDFを使用
2. テキストベースのPDFに変換
```

### 4. Streamlit関連

#### ❌ `localhost:8501` にアクセスできない
```bash
# 確認項目
1. Streamlitが起動しているか
   ps aux | grep streamlit

2. ポートが使用されているか
   netstat -tlnp | grep 8501

3. 別ポートで起動
   streamlit run app.py --server.port 8502
```

#### ❌ 画面が真っ白または読み込み中のまま
```
解決方法:
1. ブラウザの再読み込み（Ctrl+F5）
2. ブラウザのキャッシュクリア
3. 別ブラウザで試行
4. Streamlitを再起動
   Ctrl+C → streamlit run app.py
```

#### ❌ ファイルアップロードができない
```
確認項目:
1. ファイルサイズ（200MB以下）
2. ファイル形式（.pdfのみ）
3. ファイル名に特殊文字が含まれていないか

解決方法:
1. ファイル名を英数字のみに変更
2. ファイルサイズを小さくする
```

### 5. メモリ・パフォーマンス関連

#### ❌ `Out of Memory` エラー
```
原因: 大量のPDFまたは大きなPDFファイルの処理

解決方法:
1. PDFファイルを分割
2. チャンクサイズを小さくする
   # document_processor.py
   chunk_size=500  # デフォルト: 1000

3. 一度に処理するPDF数を制限
4. システムメモリを増やす
```

#### ❌ 動作が遅い
```
改善方法:
1. 埋め込みモデルをより軽量なものに変更
   # より軽量: "all-MiniLM-L12-v2"
   # 現在: "all-MiniLM-L6-v2"

2. チャンク数を制限
3. 検索結果数を減らす
   search_kwargs={"k": 2}  # デフォルト: 4
```

### 6. ChromaDB関連

#### ❌ `Failed to send telemetry event`
```
エラー内容: Failed to send telemetry event ClientStartEvent

対処: 
このエラーは無視して構いません。
ChromaDBの内部テレメトリー送信エラーで、
機能には影響しません。
```

#### ❌ ベクトルストアが見つからない
```bash
# エラー内容
No data found in vectorstore

# 解決方法
1. データの再処理
   rm -rf data/vectorstore/*
   # アプリでPDFを再アップロード

2. パスの確認
   ls -la data/vectorstore/
```

## 🔧 詳細診断方法

### ログの確認
```bash
# Streamlitのログを詳細表示
streamlit run app.py --logger.level debug

# Pythonの詳細エラー表示
export PYTHONPATH=$PYTHONPATH:$(pwd)
python -c "from src.document_processor import DocumentProcessor; dp = DocumentProcessor()"
```

### 環境の検証
```bash
# Python環境の確認
python --version
pip list | grep -E "(langchain|groq|streamlit|chromadb)"

# 仮想環境の確認
which python
echo $VIRTUAL_ENV
```

### 設定ファイルの検証
```bash
# .envファイルの確認
cat .env | grep -v "^#"

# 権限の確認
ls -la .env
chmod 600 .env  # 必要に応じて
```

## 📞 サポート情報

### 1. ログ収集方法
問題が解決しない場合、以下の情報を収集してください：

```bash
# システム情報
uname -a
python --version
pip --version

# パッケージ情報
pip freeze > package_versions.txt

# エラーログ
streamlit run app.py 2>&1 | tee streamlit.log
```

### 2. よくある質問

#### Q: Groq APIは本当に無料ですか？
A: はい、2024年7月現在、Groq APIは無料です。ただし、レート制限があります。

#### Q: 日本語の回答品質を向上させるには？
A: プロンプトの調整や、より高性能なモデル（OpenAI GPT-4等）の利用を検討してください。

#### Q: 複数のPDFを同時に処理できますか？
A: はい、可能です。ただし、メモリ使用量とPDF処理時間が増加します。

#### Q: オフラインで使用できますか？
A: 埋め込みモデルはローカルで動作しますが、Groq APIにはインターネット接続が必要です。

### 3. 既知の制限事項

- **PDF形式**: 画像ベース（スキャン）PDFは直接対応不可
- **ファイルサイズ**: 100MB以上のPDFは処理に時間がかかる
- **同時接続**: Groqの制限により、同時に利用できるユーザー数に制限あり
- **言語**: 主に日本語と英語に最適化、他言語は品質が劣る場合あり

### 4. パフォーマンス最適化のヒント

```python
# 1. チャンクサイズの調整
chunk_size=800  # より小さく
chunk_overlap=150  # より少なく

# 2. 検索結果数の調整
search_kwargs={"k": 3}  # より少なく

# 3. モデルの変更
model_name="llama3-8b-8192"  # より軽量なモデル
```

問題が解決しない場合は、GitHubのIssueページまたは開発チームにご連絡ください。