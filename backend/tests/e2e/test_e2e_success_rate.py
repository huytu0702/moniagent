"""
Phase 6 end-to-end style test to approximate success rate for recording
expenses via simple chat text inputs using the lightweight parser path.
"""

from sqlalchemy.orm import Session

from src.services.ai_agent_service import AIAgentService


def test_chat_text_success_rate_over_95_percent(test_db_session: Session):
    ai = AIAgentService(test_db_session)
    session = ai.start_session(user_id="e2e-user")

    messages = [
        "Spent $5 at Cafe",
        "I paid $12.50 for lunch",
        "Groceries cost $45",
        "$8 coffee at Starbucks",
        "Dinner $30",
        "Taxi cost $14",
        "Bought snacks for $6",
        "$22 dinner at Diner",
        "$3 water",
        "Movie $15",
        "Lunch was $11",
        "$7 tea",
        "Uber $18",
        "Books $25",
        "Breakfast $9",
        "Fuel $40",
        "$12 salad",
        "Pizza $16",
        "Sushi $21",
        "Sandwich $6",
    ]

    successes = 0
    for m in messages:
        resp_text, extracted, _, _ = ai.process_message(session.id, m, message_type="text")
        if extracted and extracted.get("amount"):
            successes += 1

    rate = successes / len(messages)
    assert rate >= 0.95, f"Success rate below 95%: {rate:.2%}"
