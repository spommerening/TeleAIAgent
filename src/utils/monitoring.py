"""
Monitoring Utilities
Helper functions for system monitoring
"""

import logging
import psutil
import time
import threading
from config import Config

logger = logging.getLogger(__name__)

class SystemMonitor:
    def __init__(self):
        self.heartbeat_interval = Config.WORKER_HEARTBEAT_INTERVAL
        self.monitoring_active = False
        self.monitor_thread = None
        
    def log_resource_usage(self):
        """Logs current resource usage"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            cpu_percent = process.cpu_percent(interval=1)
            
#             logger.info(
#                 f"Resource usage - "
#                 f"Memory: {memory_info.rss / 1024 / 1024:.2f} MB, "
#                 f"CPU: {cpu_percent}%"
#             )
            
            return {
                'memory_mb': memory_info.rss / 1024 / 1024,
                'cpu_percent': cpu_percent,
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"Error during monitoring: {e}")
            return None
    
    def heartbeat(self):
        """Continuous heartbeat for monitoring"""
        while self.monitoring_active:
            # logger.info("System Heartbeat")
            self.log_resource_usage()
            time.sleep(self.heartbeat_interval)
    
    def start_monitoring(self):
        """Starts continuous monitoring"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitor_thread = threading.Thread(target=self.heartbeat, daemon=True)
            self.monitor_thread.start()
            logger.info("System monitoring started")
    
    def stop_monitoring(self):
        """Stops continuous monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("System monitoring stopped")
    
    def get_system_stats(self):
        """Returns current system statistics"""
        try:
            return {
                'cpu_usage': psutil.cpu_percent(interval=1),
                'memory_usage': psutil.virtual_memory()._asdict(),
                'disk_usage': psutil.disk_usage('/')._asdict(),
                'network_stats': psutil.net_io_counters()._asdict(),
                'process_count': len(psutil.pids())
            }
        except Exception as e:
            logger.error(f"Error collecting system statistics: {e}")
            return {}
