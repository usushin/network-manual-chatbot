import os
import time
from typing import List
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

from config import config
from src.logger import get_logger
from src.performance import measure_time

class DocumentProcessor:
    """ドキュメント処理クラス"""
    
    def __init__(self, persist_directory: str = None):
        self.persist_directory = persist_directory or config.PERSIST_DIRECTORY
        self.logger = get_logger()
        
        # 設定から値を取得
        self.chunk_size = config.CHUNK_SIZE
        self.chunk_overlap = config.CHUNK_OVERLAP
        
        # 埋め込みモデルの初期化
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'}
            )
            self.logger.info("埋め込みモデルの初期化完了")
        except Exception as e:
            self.logger.error(f"埋め込みモデル初期化エラー: {str(e)}")
            raise
        
        # テキスト分割器の初期化
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", "。", ".", " ", ""]
        )
        
        self.logger.info(
            f"ドキュメント処理初期化完了 - "
            f"チャンクサイズ: {self.chunk_size}, "
            f"オーバーラップ: {self.chunk_overlap}"
        )
    
    @measure_time(log_result=True)
    def load_pdf(self, pdf_path: str) -> List[Document]:
        """PDFファイルを読み込み、テキストを抽出"""
        try:
            self.logger.info(f"PDF読み込み開始: {pdf_path}")
            
            # PDFファイルの存在確認
            if not Path(pdf_path).exists():
                raise FileNotFoundError(f"PDFファイルが見つかりません: {pdf_path}")
            
            # ファイルサイズチェック
            file_size_mb = Path(pdf_path).stat().st_size / 1024 / 1024
            self.logger.info(f"PDFファイルサイズ: {file_size_mb:.2f}MB")
            
            if file_size_mb > 100:  # 100MB以上の場合は警告
                self.logger.warning(f"大きなファイルです ({file_size_mb:.2f}MB) - 処理に時間がかかる可能性があります")
            
            # PyPDFLoaderを使用してPDFを読み込み
            loader = PyPDFLoader(pdf_path)
            documents = loader.load()
            
            self.logger.info(f"PDF読み込み完了 - ページ数: {len(documents)}")
            
            # テキストのクリーニング
            cleaned_documents = []
            for i, doc in enumerate(documents):
                content = doc.page_content
                
                # 空のページをスキップ
                if not content.strip():
                    self.logger.debug(f"空のページをスキップ: ページ {i + 1}")
                    continue
                
                # テキストクリーニング
                content = self._clean_text(content)
                
                if content.strip():
                    doc.page_content = content
                    # メタデータにページ番号を追加
                    doc.metadata['page'] = i + 1
                    cleaned_documents.append(doc)
            
            self.logger.info(
                f"テキストクリーニング完了 - "
                f"有効ページ数: {len(cleaned_documents)}/{len(documents)}"
            )
            
            return cleaned_documents
            
        except Exception as e:
            self.logger.error(f"PDF読み込みエラー {pdf_path}: {str(e)}")
            return []
    
    def _clean_text(self, text: str) -> str:
        """テキストをクリーニング"""
        import re
        
        try:
            # 極端に短い行（1-2文字）が連続している場合を検出して修正
            lines = text.split('\n')
            cleaned_lines = []
            temp_chars = []
            
            for line in lines:
                line = line.strip()
                
                # 非常に短い行で英数字のみの場合
                if len(line) <= 2 and line.isalnum():
                    temp_chars.append(line)
                else:
                    # 蓄積された短い文字列を結合
                    if temp_chars:
                        if len(temp_chars) > 3:  # 3文字以上分離されている場合
                            combined = ''.join(temp_chars)
                            if len(combined) > 5:  # 意味のある長さの場合のみ追加
                                cleaned_lines.append(combined)
                        else:
                            # 短すぎる場合はそのまま追加
                            cleaned_lines.extend(temp_chars)
                        temp_chars = []
                    
                    if line:
                        cleaned_lines.append(line)
            
            # 残った短い文字列を処理
            if temp_chars and len(temp_chars) > 3:
                combined = ''.join(temp_chars)
                if len(combined) > 5:
                    cleaned_lines.append(combined)
            
            # 再結合
            cleaned_text = '\n'.join(cleaned_lines)
            
            # 余分な空白や改行を削除
            cleaned_text = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned_text)  # 3つ以上の改行を2つに
            cleaned_text = re.sub(r' +', ' ', cleaned_text)  # 複数のスペースを1つに
            cleaned_text = re.sub(r'\t+', ' ', cleaned_text)  # タブをスペースに
            
            return cleaned_text.strip()
            
        except Exception as e:
            self.logger.error(f"テキストクリーニングエラー: {str(e)}")
            return text  # エラー時は元のテキストを返す
    
    @measure_time(log_result=True)
    def process_documents(self, pdf_directory: str) -> Chroma:
        """ディレクトリ内のすべてのPDFを処理してベクトルストアに保存"""
        start_time = time.time()
        all_documents = []
        processed_files = []
        
        try:
            self.logger.info(f"ドキュメント処理開始 - ディレクトリ: {pdf_directory}")
            
            # PDFファイルを検索
            pdf_files = list(Path(pdf_directory).glob("*.pdf"))
            if not pdf_files:
                raise ValueError(f"PDFファイルが見つかりません: {pdf_directory}")
            
            self.logger.info(f"見つかったPDFファイル数: {len(pdf_files)}")
            
            # 各PDFファイルを処理
            for pdf_file in pdf_files:
                file_start_time = time.time()
                self.logger.info(f"処理中: {pdf_file.name}")
                
                documents = self.load_pdf(str(pdf_file))
                
                if documents:
                    # メタデータにファイル名を追加
                    for doc in documents:
                        doc.metadata['source'] = pdf_file.name
                        doc.metadata['file_name'] = pdf_file.name
                    
                    all_documents.extend(documents)
                    processed_files.append(pdf_file.name)
                    
                    file_processing_time = time.time() - file_start_time
                    self.logger.info(
                        f"ファイル処理完了: {pdf_file.name} - "
                        f"ページ数: {len(documents)}, "
                        f"処理時間: {file_processing_time:.2f}秒"
                    )
                else:
                    self.logger.warning(f"ファイル処理失敗: {pdf_file.name}")
            
            if not all_documents:
                raise ValueError("処理可能なドキュメントがありません")
            
            self.logger.info(f"全ドキュメント読み込み完了 - 総ページ数: {len(all_documents)}")
            
            # テキストを適切なサイズに分割
            self.logger.info("テキスト分割開始")
            split_docs = self.text_splitter.split_documents(all_documents)
            
            self.logger.info(f"テキスト分割完了 - 総チャンク数: {len(split_docs)}")
            
            # ベクトルストアディレクトリの作成
            Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
            
            # ベクトルストアを作成
            self.logger.info("ベクトルストア作成開始")
            vectorstore = Chroma.from_documents(
                documents=split_docs,
                embedding=self.embeddings,
                persist_directory=self.persist_directory
            )
            
            # 永続化
            vectorstore.persist()
            
            total_processing_time = time.time() - start_time
            self.logger.info(
                f"ドキュメント処理完了 - "
                f"処理ファイル数: {len(processed_files)}, "
                f"総チャンク数: {len(split_docs)}, "
                f"総処理時間: {total_processing_time:.2f}秒, "
                f"保存先: {self.persist_directory}"
            )
            
            return vectorstore
            
        except Exception as e:
            self.logger.error(f"ドキュメント処理エラー: {str(e)}")
            raise
    
    @measure_time(log_result=False)
    def load_vectorstore(self) -> Chroma:
        """保存されたベクトルストアを読み込み"""
        try:
            self.logger.info(f"ベクトルストア読み込み開始: {self.persist_directory}")
            
            # ベクトルストアディレクトリの存在確認
            if not Path(self.persist_directory).exists():
                raise FileNotFoundError(f"ベクトルストアが見つかりません: {self.persist_directory}")
            
            vectorstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
            
            # 簡単な動作確認
            collection = vectorstore._collection
            document_count = collection.count()
            
            self.logger.info(f"ベクトルストア読み込み完了 - ドキュメント数: {document_count}")
            
            return vectorstore
            
        except Exception as e:
            self.logger.error(f"ベクトルストア読み込みエラー: {str(e)}")
            raise
    
    def get_vectorstore_info(self) -> dict:
        """ベクトルストアの情報を取得"""
        try:
            if not Path(self.persist_directory).exists():
                return {"status": "not_found", "document_count": 0}
            
            vectorstore = self.load_vectorstore()
            collection = vectorstore._collection
            document_count = collection.count()
            
            # ディレクトリサイズを計算
            total_size = 0
            for file_path in Path(self.persist_directory).rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            
            size_mb = total_size / 1024 / 1024
            
            return {
                "status": "loaded",
                "document_count": document_count,
                "size_mb": size_mb,
                "directory": str(self.persist_directory)
            }
            
        except Exception as e:
            self.logger.error(f"ベクトルストア情報取得エラー: {str(e)}")
            return {"status": "error", "error": str(e)}

