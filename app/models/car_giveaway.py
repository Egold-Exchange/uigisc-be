def car_giveaway_submission_helper(submission: dict) -> dict:
    """Convert MongoDB car giveaway submission document to dict."""
    return {
        "id": str(submission["_id"]),
        "first_name": submission.get("first_name", ""),
        "last_name": submission.get("last_name", ""),
        "phone": submission.get("phone", ""),
        "email": submission.get("email", ""),
        "agreed_to_rules": submission.get("agreed_to_rules", False),
        "created_at": submission.get("created_at"),
    }
