import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    """アプリケーション設定を管理するクラス"""
    
    # API設定
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "llama3-70b-8192")
    
    # ベクトルストア設定
    PERSIST_DIRECTORY: str = os.getenv("PERSIST_DIRECTORY", "./data/vectorstore")
    
    # チャンク設定
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))
    
    # 検索設定
    SEARCH_K: int = int(os.getenv("SEARCH_K", "4"))
    
    # LLM設定
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.3"))
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "2048"))
    
    # アプリケーション設定
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # キャッシュ設定
    ENABLE_CACHE: bool = os.getenv("ENABLE_CACHE", "true").lower() == "true"
    CACHE_DIR: str = os.getenv("CACHE_DIR", "./data/cache")
    
    # ログ設定
    LOG_DIR: str = os.getenv("LOG_DIR", "./logs")
    
    def validate(self) -> Optional[str]:
        """設定の妥当性をチェック"""
        if not self.GROQ_API_KEY:
            return "GROQ_API_KEY が設定されていません"
        
        if self.CHUNK_SIZE <= 0:
            return "CHUNK_SIZE は正の値である必要があります"
            
        if self.CHUNK_OVERLAP >= self.CHUNK_SIZE:
            return "CHUNK_OVERLAP は CHUNK_SIZE より小さい必要があります"
            
        if self.SEARCH_K <= 0:
            return "SEARCH_K は正の値である必要があります"
            
        if not (0.0 <= self.TEMPERATURE <= 1.0):
            return "TEMPERATURE は 0.0 から 1.0 の間である必要があります"
            
        return None

# グローバル設定インスタンス
config = Config()

