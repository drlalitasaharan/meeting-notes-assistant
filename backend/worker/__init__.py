# Re-export processing task for RQ string path
from .tasks_processing import process_meeting as process_meeting

__all__ = ["process_meeting"]
