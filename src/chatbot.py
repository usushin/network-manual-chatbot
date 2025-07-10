import time
from typing import List, Tuple
from groq import RateLimitError, APIError
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain_core.retrievers import BaseRetriever
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory

from config import config
from src.logger import get_logger
from src.cache import SimpleCache
from src.performance import measure_time

class NetworkManualChatbot:
    """ネットワークマニュアル対応チャットボット"""
    
    def __init__(self, retriever: BaseRetriever, model_name: str = None):
        self.retriever = retriever
        self.logger = get_logger()
        
        # 設定から値を取得
        model_name = model_name or config.MODEL_NAME
        
        # Groq APIを使用
        self.llm = ChatGroq(
            model_name=model_name,
            temperature=config.TEMPERATURE,
            max_tokens=config.MAX_TOKENS
        )
        
        # 改善されたプロンプトテンプレート
        self.system_template = """あなたはCISCOなどのネットワーク機器の技術サポート専門家です。
以下のルールに従って回答してください：

【回答ルール】
1. **必ず日本語で回答**
2. **段階的で実践的な手順を提供**
3. **コマンド例は具体的に記載**
4. **注意点や前提条件を明確化**
5. **マニュアルに記載がない場合は明示**

【回答形式】
- 概要（1-2行）
- 手順（番号付きリスト）
- 注意点
- 関連コマンド（該当する場合）

提供された技術文書: {context}

質問: {question}

回答:"""
        
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
            verbose=config.DEBUG
        )
        
        # キャッシュの初期化
        if config.ENABLE_CACHE:
            self.cache = SimpleCache(cache_dir=config.CACHE_DIR)
            self.logger.info("キャッシュ機能が有効です")
        else:
            self.cache = None
            self.logger.info("キャッシュ機能が無効です")
        
        self.logger.info(f"チャットボット初期化完了 - モデル: {model_name}")
    
    @measure_time(log_result=True)
    def ask(self, question: str) -> Tuple[str, List[dict]]:
        """質問に対する回答を生成"""
        start_time = time.time()
        
        try:
            # キャッシュから確認
            if self.cache:
                cached_result = self.cache.get(question)
                if cached_result:
                    processing_time = time.time() - start_time
                    self.logger.info(f"キャッシュから回答取得 - 処理時間: {processing_time:.3f}秒")
                    return cached_result
            
            # 通常の処理（リトライ機能付き）
            max_retries = 3
            for attempt in range(max_retries):
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
                    
                    answer = result["answer"]
                    
                    # キャッシュに保存
                    if self.cache:
                        self.cache.set(question, answer, sources)
                    
                    # ログ記録
                    processing_time = time.time() - start_time
                    self.logger.info(
                        f"質問応答完了 - 処理時間: {processing_time:.3f}秒, "
                        f"参照元数: {len(sources)}"
                    )
                    
                    return answer, sources
                
                except RateLimitError as e:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # 指数バックオフ
                        self.logger.warning(
                            f"レート制限発生 - {wait_time}秒待機後に再試行 "
                            f"(試行回数: {attempt + 1}/{max_retries})"
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        error_message = (
                            "レート制限に達しました。少し待ってから再度お試しください。\n\n"
                            "Groqの無料プランでは1分間に30リクエストの制限があります。"
                        )
                        self.logger.error(f"レート制限エラー: {str(e)}")
                        return error_message, []
                
                except APIError as e:
                    error_message = f"API エラーが発生しました: {str(e)}"
                    self.logger.error(f"Groq API エラー: {str(e)}")
                    return error_message, []
                
                except Exception as e:
                    if attempt < max_retries - 1:
                        wait_time = 1
                        self.logger.warning(
                            f"予期しないエラー - {wait_time}秒待機後に再試行: {str(e)} "
                            f"(試行回数: {attempt + 1}/{max_retries})"
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        error_message = (
                            f"エラーが発生しました: {str(e)}\n\n"
                            "TROUBLESHOOTING.mdを確認するか、しばらく待ってから再度お試しください。"
                        )
                        self.logger.error(f"予期しないエラー: {str(e)}")
                        return error_message, []
            
        except Exception as e:
            error_message = f"システムエラーが発生しました: {str(e)}"
            self.logger.error(f"システムエラー: {str(e)}")
            return error_message, []
    
    def clear_memory(self):
        """会話履歴をクリア"""
        try:
            self.memory.clear()
            self.logger.info("会話履歴をクリアしました")
        except Exception as e:
            self.logger.error(f"会話履歴クリアエラー: {str(e)}")
    
    def get_chat_history(self) -> List[Tuple[str, str]]:
        """会話履歴を取得"""
        try:
            messages = self.memory.chat_memory.messages
            history = []
            
            for i in range(0, len(messages), 2):
                if i + 1 < len(messages):
                    user_msg = messages[i].content
                    ai_msg = messages[i + 1].content
                    history.append((user_msg, ai_msg))
            
            return history
        except Exception as e:
            self.logger.error(f"会話履歴取得エラー: {str(e)}")
            return []
    
    def get_cache_stats(self) -> dict:
        """キャッシュ統計を取得"""
        if self.cache:
            return self.cache.get_stats()
        return {}
    
    def clear_cache(self):
        """キャッシュをクリア"""
        if self.cache:
            self.cache.clear_cache()
            self.logger.info("キャッシュをクリアしました")
    
    def get_model_info(self) -> dict:
        """モデル情報を取得"""
        return {
            "model_name": config.MODEL_NAME,
            "temperature": config.TEMPERATURE,
            "max_tokens": config.MAX_TOKENS,
            "cache_enabled": config.ENABLE_CACHE
        }

