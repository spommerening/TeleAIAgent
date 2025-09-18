"""
Monitoring Utilities (AsyncIO)
Helper functions for system monitoring using AsyncIO
"""

import logging
import psutil
import asyncio
from config import Config

logger = logging.getLogger(__name__)

class SystemMonitor:
    def __init__(self):
        self.heartbeat_interval = Config.WORKER_HEARTBEAT_INTERVAL
        self.monitoring_active = False
        self.monitor_task = None
        
    async def log_resource_usage(self):
        """Logs current resource usage"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            cpu_percent = process.cpu_percent(interval=0.1)  # Non-blocking
            
            return {
                'memory_mb': memory_info.rss / 1024 / 1024,
                'cpu_percent': cpu_percent,
                'timestamp': asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            logger.error(f"Error during monitoring: {e}")
            return None
    
    async def heartbeat(self):
        """Continuous heartbeat for monitoring"""
        while self.monitoring_active:
            # logger.info("System Heartbeat")
            await self.log_resource_usage()
            await asyncio.sleep(self.heartbeat_interval)
    
    async def start_monitoring(self):
        """Starts continuous monitoring"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitor_task = asyncio.create_task(self.heartbeat())
            logger.info("Async system monitoring started")
    
    async def stop_monitoring(self):
        """Stops continuous monitoring"""
        self.monitoring_active = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Async system monitoring stopped")
    
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
