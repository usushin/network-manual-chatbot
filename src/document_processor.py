import os
from typing import List
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
import chromadb


class DocumentProcessor:
    def __init__(self, persist_directory: str = "./data/vectorstore"):
        self.persist_directory = persist_directory
        # 無料の日本語対応埋め込みモデルを使用（より軽量で安定）
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", "。", ".", " ", ""]
        )
        
    def load_pdf(self, pdf_path: str) -> List[Document]:
        """PDFファイルを読み込み、テキストを抽出"""
        try:
            # PyPDFLoaderを使用してPDFを読み込み
            loader = PyPDFLoader(pdf_path)
            documents = loader.load()
            
            # テキストのクリーニング
            cleaned_documents = []
            for doc in documents:
                # 文字が分離されている場合の修正
                content = doc.page_content
                # 不適切な改行や文字分離を修正
                content = self._clean_text(content)
                if content.strip():  # 空でない場合のみ追加
                    doc.page_content = content
                    cleaned_documents.append(doc)
            
            return cleaned_documents
        except Exception as e:
            print(f"Error loading PDF {pdf_path}: {str(e)}")
            return []
    
    def _clean_text(self, text: str) -> str:
        """テキストをクリーニング"""
        import re
        
        # 極端に短い行（1-2文字）が連続している場合を検出して修正
        lines = text.split('\n')
        cleaned_lines = []
        temp_chars = []
        
        for line in lines:
            line = line.strip()
            if len(line) <= 2 and line.isalpha():
                # 短い行は一時的に保存
                temp_chars.append(line)
            else:
                # 蓄積された短い文字列を結合
                if temp_chars:
                    if len(temp_chars) > 3:  # 3文字以上分離されている場合
                        combined = ''.join(temp_chars)
                        if len(combined) > 5:  # 意味のある長さの場合のみ追加
                            cleaned_lines.append(combined)
                    else:
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
        cleaned_text = re.sub(r'\n\s*\n', '\n\n', cleaned_text)
        cleaned_text = re.sub(r' +', ' ', cleaned_text)
        
        return cleaned_text
    
    def process_documents(self, pdf_directory: str) -> Chroma:
        """ディレクトリ内のすべてのPDFを処理してベクトルストアに保存"""
        all_documents = []
        
        # PDFファイルを検索して読み込み
        for filename in os.listdir(pdf_directory):
            if filename.endswith('.pdf'):
                pdf_path = os.path.join(pdf_directory, filename)
                print(f"Processing: {filename}")
                documents = self.load_pdf(pdf_path)
                
                # メタデータにファイル名を追加
                for doc in documents:
                    doc.metadata['source'] = filename
                    doc.metadata['file_name'] = filename
                
                all_documents.extend(documents)
        
        # テキストを適切なサイズに分割
        split_docs = self.text_splitter.split_documents(all_documents)
        print(f"Total chunks created: {len(split_docs)}")
        
        # ベクトルストアを作成
        vectorstore = Chroma.from_documents(
            documents=split_docs,
            embedding=self.embeddings,
            persist_directory=self.persist_directory
        )
        
        # 永続化
        vectorstore.persist()
        print(f"Vectorstore saved to {self.persist_directory}")
        
        return vectorstore
    
    def load_vectorstore(self) -> Chroma:
        """保存されたベクトルストアを読み込み"""
        vectorstore = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings
        )
        return vectorstore