from typing import List, Tuple
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain_core.retrievers import BaseRetriever
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory


class NetworkManualChatbot:
    def __init__(self, retriever: BaseRetriever, model_name: str = "llama3-70b-8192"):
        self.retriever = retriever
        # Groq APIを使用（無料）
        self.llm = ChatGroq(
            model_name=model_name,  # llama3-70b-8192 または mixtral-8x7b-32768
            temperature=0.3,
            max_tokens=2048
        )
        
        # プロンプトテンプレート（日本語強化）
        self.system_template = """あなたはCISCOなどのネットワーク機器の技術サポート専門家です。
製品マニュアルに基づいて、技術者からの質問に正確かつ簡潔に**日本語で**回答してください。

重要な指示：
1. **必ず日本語で回答してください**
2. 提供された文書の内容に基づいて回答する
3. 技術的に正確な用語を使用する
4. 不明な点は推測せず、マニュアルに記載がないことを明確に伝える
5. 必要に応じて、関連する設定例やコマンドを含める
6. 専門用語は日本語で説明し、英語の場合は括弧内に併記する

コンテキスト:
{context}

質問: {question}

回答（日本語で）:"""
        
        self.prompt = ChatPromptTemplate.from_template(self.system_template)
        
        # メモリの初期化
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )
        
        # 会話型検索チェーンの構築
        self.qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.retriever,
            memory=self.memory,
            combine_docs_chain_kwargs={"prompt": self.prompt},
            return_source_documents=True,
            verbose=False
        )
    
    def ask(self, question: str) -> Tuple[str, List[dict]]:
        """質問に対する回答を生成"""
        try:
            result = self.qa_chain({"question": question})
            
            # ソース情報を整理
            sources = []
            for doc in result.get("source_documents", []):
                source_info = {
                    "file": doc.metadata.get("file_name", "Unknown"),
                    "page": doc.metadata.get("page", "Unknown"),
                    "content": doc.page_content[:200] + "..."
                }
                sources.append(source_info)
            
            return result["answer"], sources
            
        except Exception as e:
            error_message = f"エラーが発生しました: {str(e)}"
            return error_message, []
    
    def clear_memory(self):
        """会話履歴をクリア"""
        self.memory.clear()
    
    def get_chat_history(self) -> List[Tuple[str, str]]:
        """会話履歴を取得"""
        messages = self.memory.chat_memory.messages
        history = []
        
        for i in range(0, len(messages), 2):
            if i + 1 < len(messages):
                user_msg = messages[i].content
                ai_msg = messages[i + 1].content
                history.append((user_msg, ai_msg))
        
        return history