import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

class AppLogger:
    """アプリケーション用ログ管理クラス"""
    
    def __init__(self, log_dir: str = "./logs", log_level: str = "INFO"):
        self.log_dir = Path(log_dir)
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        self.logger: Optional[logging.Logger] = None
        self._setup_logger()
    
    def _setup_logger(self):
        """ロガーのセットアップ"""
        # ログディレクトリの作成
        self.log_dir.mkdir(exist_ok=True)
        
        # ログファイル名（日付付き）
        log_filename = f"chatbot_{datetime.now().strftime('%Y%m%d')}.log"
        log_path = self.log_dir / log_filename
        
        # ロガーの作成
        self.logger = logging.getLogger("NetworkManualChatbot")
        self.logger.setLevel(self.log_level)
        
        # 既存のハンドラーをクリア
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # フォーマッターの定義
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # ファイルハンドラー
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # コンソールハンドラー
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # 初期ログ
        self.logger.info("=== アプリケーション開始 ===")
        self.logger.info(f"ログレベル: {logging.getLevelName(self.log_level)}")
        self.logger.info(f"ログファイル: {log_path}")
    
    def get_logger(self) -> logging.Logger:
        """ロガーインスタンスを取得"""
        return self.logger
    
    def log_pdf_processing(self, filename: str, chunks_count: int, processing_time: float):
        """PDF処理のログ"""
        self.logger.info(
            f"PDF処理完了 - ファイル: {filename}, "
            f"チャンク数: {chunks_count}, 処理時間: {processing_time:.2f}秒"
        )
    
    def log_question_answer(self, question: str, answer_length: int, processing_time: float):
        """質問応答のログ"""
        self.logger.info(
            f"質問応答 - 質問長: {len(question)}文字, "
            f"回答長: {answer_length}文字, 処理時間: {processing_time:.2f}秒"
        )
        self.logger.debug(f"質問内容: {question}")
    
    def log_error(self, error_type: str, error_message: str, context: str = ""):
        """エラーログ"""
        if context:
            self.logger.error(f"エラー発生 [{error_type}] - {error_message} (コンテキスト: {context})")
        else:
            self.logger.error(f"エラー発生 [{error_type}] - {error_message}")
    
    def log_cache_hit(self, question_hash: str):
        """キャッシュヒットのログ"""
        self.logger.debug(f"キャッシュヒット - ハッシュ: {question_hash}")
    
    def log_cache_miss(self, question_hash: str):
        """キャッシュミスのログ"""
        self.logger.debug(f"キャッシュミス - ハッシュ: {question_hash}")

# グローバルロガーインスタンス
_logger_instance: Optional[AppLogger] = None

def setup_logger(log_dir: str = "./logs", log_level: str = "INFO") -> logging.Logger:
    """ロガーを初期化して返す"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = AppLogger(log_dir, log_level)
    return _logger_instance.get_logger()

def get_logger() -> logging.Logger:
    """既存のロガーを取得"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = AppLogger()
    return _logger_instance.get_logger()

