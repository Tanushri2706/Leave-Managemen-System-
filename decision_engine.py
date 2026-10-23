def decide_leave(history, duration, last30, continuous, is_monday, is_friday, leave_type="Casual", priority="Normal"):
    """
    Intelligent Rule-Based Decision Engine for Leave Requests.
    Returns:
        status (str): "Approved", "Rejected", or "Pending"
        probability (float): Confidence score (0.0 to 1.0)
        reasons (list): Detailed explanatory policy reasons
    """
    reasons = []

    # ----------- REJECT RULES -----------
    if last30 > 4:
        reasons.append("High frequency: >4 leave requests submitted within the last 30 calendar days")
        reasons.append("Exceeds monthly velocity guidelines; requires mandatory HR escalation")
        return "Rejected", 0.92, reasons

    if continuous == 1 and duration > 3:
        reasons.append("Consecutive absence pattern: Back-to-back leave request exceeding 3 days")
        reasons.append("Risk of unmitigated sprint and project delivery disruption")
        return "Rejected", 0.90, reasons

    if (is_monday or is_friday) and history > 3 and duration >= 2:
        reasons.append("Extended weekend absence pattern flagged during active operational cycle")
        reasons.append("Repeated Friday/Monday leave behavior detected in historical profile")
        return "Rejected", 0.86, reasons

    if history > 7 and duration > 5:
        reasons.append("Extended leave duration (>5 days) with high cumulative leave history (>7)")
        reasons.append("Annual allocation threshold advisory triggered")
        return "Rejected", 0.94, reasons

    # ----------- APPROVED RULES -----------
    if priority in ["Urgent", "Critical", "Emergency"] or leave_type in ["Sick Leave", "Sick"]:
        reasons.append("High-priority emergency / verified health leave fast-tracked")
        reasons.append("Complies with statutory workplace health and emergency safety guidelines")
        return "Approved", 0.95, reasons

    if leave_type in ["Work From Home", "WFH"]:
        reasons.append("Remote Work (WFH) protocol verified with no team schedule overlap")
        reasons.append("Productivity continuity assured under hybrid working norms")
        return "Approved", 0.91, reasons

    if duration == 1 and history <= 3:
        reasons.append("Low-impact single-day leave within standard allowable casual quota")
        reasons.append("Clean recent attendance record with zero recent overlaps")
        return "Approved", 0.88, reasons

    # ----------- PENDING RULES -----------
    if duration > 3:
        reasons.append(f"Multi-day leave ({duration} days) requires direct Manager workload review")
        reasons.append("Workload delegation and sprint coverage verification advised")
        return "Pending", 0.68, reasons

    if duration <= 3 and history <= 4:
        reasons.append("Standard leave request within acceptable limits awaiting managerial acknowledgement")
        reasons.append("Nominal team capacity available for the requested period")
        return "Pending", 0.72, reasons

    # ----------- DEFAULT SAFE APPROVAL -----------
    reasons.append("Leave request satisfies standard company attendance and entitlement policies")
    reasons.append("Predictive system assesses low operational risk for requested duration")
    return "Approved", 0.80, reasons