from datetime import datetime
from typing import Optional

def time_diff_seconds(data: dict[str, str]) -> Optional[float]:
    """Calculate time difference between given datetime and now in seconds.
    
    Returns None if date/time data is invalid or missing.
    """
    date_str = data.get('date', '').strip()
    time_str = data.get('time', '').strip()
    
    if not date_str or not time_str:
        return None
    
    try:
        date_obj = datetime.strptime(date_str, '%d-%m-%Y').date()
        time_obj = datetime.strptime(time_str, '%H:%M:%S').time()
        target_datetime = datetime.combine(date_obj, time_obj)
        return (datetime.now() - target_datetime).total_seconds()
    except ValueError:
        return None