import hashlib
import json
import os
import time
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
from src.logger import get_logger

class SimpleCache:
    """質問応答結果のキャッシュ管理クラス"""
    
    def __init__(self, cache_dir: str = "./data/cache", max_cache_size: int = 1000):
        self.cache_dir = Path(cache_dir)
        self.max_cache_size = max_cache_size
        self.logger = get_logger()
        
        # キャッシュディレクトリの作成
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # キャッシュ統計
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "total_requests": 0
        }
        
        self.logger.info(f"キャッシュ初期化 - ディレクトリ: {self.cache_dir}")
    
    def _get_cache_key(self, question: str) -> str:
        """質問文からキャッシュキーを生成"""
        # 質問文を正規化（小文字化、空白除去）
        normalized_question = question.strip().lower()
        return hashlib.md5(normalized_question.encode('utf-8')).hexdigest()
    
    def _get_cache_file_path(self, cache_key: str) -> Path:
        """キャッシュファイルのパスを取得"""
        return self.cache_dir / f"{cache_key}.json"
    
    def get(self, question: str) -> Optional[Tuple[str, List[Dict[str, Any]]]]:
        """キャッシュから回答を取得"""
        self.cache_stats["total_requests"] += 1
        
        cache_key = self._get_cache_key(question)
        cache_file = self._get_cache_file_path(cache_key)
        
        if not cache_file.exists():
            self.cache_stats["misses"] += 1
            self.logger.debug(f"キャッシュミス - 質問: {question[:50]}...")
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
            
            # キャッシュの有効期限チェック（24時間）
            cache_age = time.time() - cached_data.get('timestamp', 0)
            if cache_age > 86400:  # 24時間
                self.logger.debug(f"キャッシュ期限切れ - 質問: {question[:50]}...")
                cache_file.unlink()  # 期限切れキャッシュを削除
                self.cache_stats["misses"] += 1
                return None
            
            self.cache_stats["hits"] += 1
            self.logger.debug(f"キャッシュヒット - 質問: {question[:50]}...")
            
            return cached_data['answer'], cached_data['sources']
            
        except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
            self.logger.error(f"キャッシュ読み込みエラー: {str(e)}")
            # 破損したキャッシュファイルを削除
            if cache_file.exists():
                cache_file.unlink()
            self.cache_stats["misses"] += 1
            return None
    
    def set(self, question: str, answer: str, sources: List[Dict[str, Any]]):
        """回答をキャッシュに保存"""
        cache_key = self._get_cache_key(question)
        cache_file = self._get_cache_file_path(cache_key)
        
        cache_data = {
            'question': question,
            'answer': answer,
            'sources': sources,
            'timestamp': time.time(),
            'cache_key': cache_key
        }
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            self.logger.debug(f"キャッシュ保存 - 質問: {question[:50]}...")
            
            # キャッシュサイズの管理
            self._cleanup_old_cache()
            
        except Exception as e:
            self.logger.error(f"キャッシュ保存エラー: {str(e)}")
    
    def _cleanup_old_cache(self):
        """古いキャッシュファイルを削除"""
        try:
            cache_files = list(self.cache_dir.glob("*.json"))
            
            if len(cache_files) <= self.max_cache_size:
                return
            
            # ファイルを更新日時でソート（古い順）
            cache_files.sort(key=lambda f: f.stat().st_mtime)
            
            # 古いファイルを削除
            files_to_delete = len(cache_files) - self.max_cache_size
            for i in range(files_to_delete):
                cache_files[i].unlink()
                self.logger.debug(f"古いキャッシュファイルを削除: {cache_files[i].name}")
                
        except Exception as e:
            self.logger.error(f"キャッシュクリーンアップエラー: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """キャッシュ統計を取得"""
        hit_rate = 0.0
        if self.cache_stats["total_requests"] > 0:
            hit_rate = (self.cache_stats["hits"] / self.cache_stats["total_requests"]) * 100
        
        return {
            "total_requests": self.cache_stats["total_requests"],
            "hits": self.cache_stats["hits"],
            "misses": self.cache_stats["misses"],
            "hit_rate": hit_rate,
            "cache_files": len(list(self.cache_dir.glob("*.json")))
        }
    
    def clear_cache(self):
        """すべてのキャッシュを削除"""
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            
            # 統計をリセット
            self.cache_stats = {
                "hits": 0,
                "misses": 0,
                "total_requests": 0
            }
            
            self.logger.info("キャッシュをクリアしました")
            
        except Exception as e:
            self.logger.error(f"キャッシュクリアエラー: {str(e)}")
    
    def get_cache_size_mb(self) -> float:
        """キャッシュディレクトリのサイズをMBで取得"""
        total_size = 0
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                total_size += cache_file.stat().st_size
            return total_size / (1024 * 1024)  # MB
        except Exception:
            return 0.0

