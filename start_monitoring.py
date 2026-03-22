import time
import logging
from health_monitor import HealthMonitor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("HealthService")

if __name__ == "__main__":
    monitor = HealthMonitor()
    logger.info("Starting Background Health Monitoring Service...")
    try:
        while True:
            monitor.generate_report()
            time.sleep(60) # Generate report every minute
    except KeyboardInterrupt:
        logger.info("Health monitoring stopped.")
