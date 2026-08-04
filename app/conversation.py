"""
EIE-038 Conversation Intelligence

Purpose:
Manage student conversation context.
"""


from memory import load_memory


class ConversationContext:


    def __init__(self):

        self.history = []

        self.last_topic = ""

        self.last_subject = ""



    def load(self):

        memory = load_memory()

        self.last_topic = memory.get(
            "last_topic",
            ""
        )

        return self



    def add_message(
        self,
        role,
        content
    ):

        self.history.append({

            "role": role,

            "content": content

        })



    def get_context(self):

        return {

            "last_topic": self.last_topic,

            "last_subject": self.last_subject,

            "history": self.history

        }