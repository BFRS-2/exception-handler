import pandas as pd
import json

def resolve_exception(exception_type, context):
    # Placeholder: Implement logic to resolve exception (e.g., call API, update DB)
    return f"Resolved {exception_type} with context: {context}"

def recommend_action(exception_type, context):
    # Placeholder: Implement logic to recommend action
    if exception_type == "address_issue":
        return "Request updated address from customer."
    elif exception_type == "delivery_failed":
        return "Schedule a re-delivery attempt."
    else:
        return "Escalate to human agent."

def get_exception_details(shipment_id):
    df = pd.read_csv("data/shipment_logs.csv")
    row = df[df["shipment_id"] == int(shipment_id)]
    if not row.empty:
        exception_type = row.iloc[0]["exception_type"]
        details = row.iloc[0]["details"]
        return exception_type, details
    return None, None

def get_conversation_history(shipment_id):
    with open("data/conversations.json", "r") as f:
        conversations = json.load(f)
    for conv in conversations:
        if conv["shipment_id"] == str(shipment_id):
            return conv["conversation"]
    return [] 