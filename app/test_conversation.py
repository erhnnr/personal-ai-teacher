from conversation import ConversationContext


def test_conversation_context():

    context = ConversationContext()

    context.add_message(
        "student",
        "Limit çalışıyorum."
    )

    data = context.get_context()


    assert len(data["history"]) == 1

    assert data["history"][0]["content"] == "Limit çalışıyorum."