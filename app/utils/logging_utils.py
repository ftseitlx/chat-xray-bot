import json
import logging
from datetime import datetime

from app.config import settings

# Configure JSON logger for cost tracking
json_logger = logging.getLogger("cost_tracker")
json_handler = logging.StreamHandler()
json_handler.setFormatter(logging.Formatter("%(message)s"))
json_logger.addHandler(json_handler)
json_logger.propagate = False

async def log_cost(user_id, chunks, cost):
    """Log cost information in JSON format"""
    if settings.ENABLE_COST_TRACKING:
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "chunks": chunks,
            "cost_$": cost,
        }
        json_logger.info(json.dumps(log_data)) 