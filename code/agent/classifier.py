def classify_ticket(issue, subject, company):
    text = f"{issue} {subject}".lower()

    # domain detection
    if "visa" in str(company).lower():
        domain = "visa"
    elif "claude" in str(company).lower():
        domain = "claude"
    elif "hackerrank" in str(company).lower():
        domain = "hackerrank"
    else:
        domain = "unknown"

    # safety rules
    if any(word in text for word in ["fraud", "stolen", "identity theft"]):
        return {
            "domain": domain,
            "request_type": "product_issue",
            "urgency": "high",
            "product_area": "security",
            "is_malicious": False,
            "reasoning": "Sensitive financial/security issue"
        }

    if any(word in text for word in ["not working", "down", "error", "failed"]):
        return {
            "domain": domain,
            "request_type": "bug",
            "urgency": "high",
            "product_area": "system",
            "is_malicious": False,
            "reasoning": "System issue detected"
        }

    if any(word in text for word in ["delete all", "hack", "exploit"]):
        return {
            "domain": domain,
            "request_type": "invalid",
            "urgency": "high",
            "product_area": "security",
            "is_malicious": True,
            "reasoning": "Potential malicious request"
        }

    return {
        "domain": domain,
        "request_type": "product_issue",
        "urgency": "medium",
        "product_area": "general",
        "is_malicious": False,
        "reasoning": "General support query"
    }