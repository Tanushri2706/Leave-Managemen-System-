def decide_leave(history, duration, last30, continuous, is_monday, is_friday):

    # ----------- REJECT RULES -----------
    if last30 > 4:
        return "Rejected", 0.90

    if continuous == 1 and duration > 3:
        return "Rejected", 0.92

    if (is_monday or is_friday) and history > 3:
        return "Rejected", 0.88

    if history > 5 and duration > 5:
        return "Rejected", 0.95


    # ----------- APPROVED RULE -----------
    # very safe leave
    if duration == 1 and history <= 2:
        return "Approved", 0.85


    # ----------- PENDING RULES -----------
    if duration <= 3 and history <= 3:
        return "Pending", 0.65

    if duration <= 2:
        return "Pending", 0.60

    if last30 <= 2 and duration <= 4:
        return "Pending", 0.70


    # default
    return "Approved", 0.75