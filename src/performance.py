import time
import psutil
import threading
from functools import wraps
from typing import Dict, Any, Callable
from dataclasses import dataclass, field
from src.logger import get_logger

@dataclass
class PerformanceMetrics:
    """パフォーマンス指標を保存するクラス"""
    function_name: str
    execution_time: float
    memory_usage_mb: float
    cpu_percent: float
    timestamp: float = field(default_factory=time.time)

class PerformanceMonitor:
    """パフォーマンス監視クラス"""
    
    def __init__(self):
        self.metrics: Dict[str, list] = {}
        self.logger = get_logger()
        self._lock = threading.Lock()
    
    def record_metric(self, metric: PerformanceMetrics):
        """メトリクスを記録"""
        with self._lock:
            if metric.function_name not in self.metrics:
                self.metrics[metric.function_name] = []
            
            self.metrics[metric.function_name].append(metric)
            
            # 最新100件のみ保持
            if len(self.metrics[metric.function_name]) > 100:
                self.metrics[metric.function_name] = self.metrics[metric.function_name][-100:]
    
    def get_stats(self, function_name: str) -> Dict[str, Any]:
        """指定した関数の統計を取得"""
        with self._lock:
            if function_name not in self.metrics or not self.metrics[function_name]:
                return {}
            
            execution_times = [m.execution_time for m in self.metrics[function_name]]
            memory_usages = [m.memory_usage_mb for m in self.metrics[function_name]]
            cpu_percents = [m.cpu_percent for m in self.metrics[function_name]]
            
            return {
                "call_count": len(execution_times),
                "avg_execution_time": sum(execution_times) / len(execution_times),
                "min_execution_time": min(execution_times),
                "max_execution_time": max(execution_times),
                "avg_memory_usage_mb": sum(memory_usages) / len(memory_usages),
                "avg_cpu_percent": sum(cpu_percents) / len(cpu_percents),
                "last_execution_time": execution_times[-1],
                "last_memory_usage_mb": memory_usages[-1]
            }
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """すべての関数の統計を取得"""
        stats = {}
        for function_name in self.metrics.keys():
            stats[function_name] = self.get_stats(function_name)
        return stats
    
    def log_stats(self, function_name: str):
        """統計をログに出力"""
        stats = self.get_stats(function_name)
        if stats:
            self.logger.info(
                f"パフォーマンス統計 [{function_name}] - "
                f"実行回数: {stats['call_count']}, "
                f"平均実行時間: {stats['avg_execution_time']:.3f}秒, "
                f"平均メモリ使用量: {stats['avg_memory_usage_mb']:.1f}MB"
            )

# グローバルパフォーマンスモニター
_performance_monitor = PerformanceMonitor()

def measure_time(log_result: bool = True):
    """実行時間とシステムリソース使用量を測定するデコレータ"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 開始時のメトリクス取得
            start_time = time.time()
            process = psutil.Process()
            start_memory = process.memory_info().rss / 1024 / 1024  # MB
            start_cpu = process.cpu_percent()
            
            try:
                # 関数実行
                result = func(*args, **kwargs)
                
                # 終了時のメトリクス取得
                end_time = time.time()
                execution_time = end_time - start_time
                end_memory = process.memory_info().rss / 1024 / 1024  # MB
                end_cpu = process.cpu_percent()
                
                # メトリクス記録
                metric = PerformanceMetrics(
                    function_name=func.__name__,
                    execution_time=execution_time,
                    memory_usage_mb=end_memory,
                    cpu_percent=end_cpu
                )
                _performance_monitor.record_metric(metric)
                
                # ログ出力
                if log_result:
                    logger = get_logger()
                    logger.info(
                        f"実行完了 [{func.__name__}] - "
                        f"実行時間: {execution_time:.3f}秒, "
                        f"メモリ使用量: {end_memory:.1f}MB, "
                        f"CPU使用率: {end_cpu:.1f}%"
                    )
                
                return result
                
            except Exception as e:
                # エラー時のメトリクス取得
                end_time = time.time()
                execution_time = end_time - start_time
                end_memory = process.memory_info().rss / 1024 / 1024  # MB
                
                logger = get_logger()
                logger.error(
                    f"実行エラー [{func.__name__}] - "
                    f"実行時間: {execution_time:.3f}秒, "
                    f"エラー: {str(e)}"
                )
                raise
        
        return wrapper
    return decorator

def get_system_info() -> Dict[str, Any]:
    """システム情報を取得"""
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_total_gb": memory.total / 1024 / 1024 / 1024,
            "memory_available_gb": memory.available / 1024 / 1024 / 1024,
            "memory_percent": memory.percent,
            "disk_total_gb": disk.total / 1024 / 1024 / 1024,
            "disk_free_gb": disk.free / 1024 / 1024 / 1024,
            "disk_percent": (disk.used / disk.total) * 100
        }
    except Exception as e:
        logger = get_logger()
        logger.error(f"システム情報取得エラー: {str(e)}")
        return {}

def get_performance_monitor() -> PerformanceMonitor:
    """パフォーマンスモニターのインスタンスを取得"""
    return _performance_monitor

def log_system_status():
    """システム状態をログに出力"""
    logger = get_logger()
    system_info = get_system_info()
    
    if system_info:
        logger.info(
            f"システム状態 - "
            f"CPU: {system_info['cpu_percent']:.1f}%, "
            f"メモリ: {system_info['memory_percent']:.1f}%, "
            f"ディスク: {system_info['disk_percent']:.1f}%"
        )

