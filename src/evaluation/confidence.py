def classify_confidence(avg_score):
    if avg_score <= 0.30:
        return "HIGH"
    
    if avg_score <= 0.80:
        return "MEDIUM"
    return "LOW"