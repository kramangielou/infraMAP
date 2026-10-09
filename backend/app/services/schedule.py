from datetime import date
from typing import Literal
Status=Literal['On Track','At Risk','Delayed','Insufficient Data']
def expected_progress(start:date|None,end:date|None,now:date|None=None):
    if not start or not end:return None
    now=now or date.today()
    total=(end-start).days
    if total<=0:return 100.0 if now>=end else 0.0
    return max(0,min(100,((now-start).days/total)*100))
def calculate_schedule_status(progress:float,start:date|None,end:date|None,threshold:float=15,now:date|None=None)->Status:
    now=now or date.today(); exp=expected_progress(start,end,now)
    if exp is None:return 'Insufficient Data'
    if now>end and progress<100:return 'Delayed'
    if progress+threshold<exp:return 'At Risk'
    return 'On Track'
