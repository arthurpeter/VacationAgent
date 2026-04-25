from datetime import datetime

def calculate_age(date_of_birth):
    if not date_of_birth:
        return None
    today = datetime.today()
    age = today.year - date_of_birth.year - (
        (today.month, today.day) < (date_of_birth.month, date_of_birth.day)
    )
    return age