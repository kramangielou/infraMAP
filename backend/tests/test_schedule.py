from datetime import date,timedelta
from app.services.schedule import expected_progress,calculate_schedule_status

def test_expected_progress():
    assert expected_progress(date(2026,1,1),date(2026,7,1),date(2026,4,2))>49

def test_delayed():
    assert calculate_schedule_status(50,date(2026,1,1),date(2026,3,1),now=date(2026,4,1))=='Delayed'

def test_insufficient_data():
    assert calculate_schedule_status(50,None,date(2026,3,1))=='Insufficient Data'
