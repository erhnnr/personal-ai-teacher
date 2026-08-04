"""
EIE-020 Learning Session Engine

Purpose:
Manage a complete learning session.
"""


from planner import create_plan
from quiz_generator import generate_quiz

from evaluator import evaluate_quiz
from progress import update_topic_progress

from memory import (
    set_last_topic,
    add_quiz_result,
    add_completed_topic,
    add_weak_topic
)

from conversation import ConversationContext



class LearningSession:


    def __init__(self, question):

        self.question = question

        self.plan = None

        self.quiz = None

        self.result = None

        self.answer = None

        self.context = ConversationContext()

        self.status = "created"



    def start(self):

        self.context.load()

        self.plan = create_plan(
            self.question
        )


        self.quiz = generate_quiz(
            self.plan
        )


        self.context.add_message(
            "student",
            self.question
        )


        self.status = "started"


        return self



    def teach(self):

        from teacher import ask_teacher


        self.answer = ask_teacher(
            self.question
        )


        self.context.add_message(
            "teacher",
            self.answer
        )


        self.status = "teaching"


        return self.answer



    def complete(self, answers):


        self.result = evaluate_quiz(
            self.quiz,
            answers
        )


        topic = self.quiz.topic



        update_topic_progress(
            topic,
            self.result.score
        )


        set_last_topic(
            topic
        )


        add_quiz_result({

            "topic": topic,

            "score": self.result.score

        })



        if self.result.score >= 80:

            add_completed_topic(
                topic
            )


        else:

            add_weak_topic(
                topic
            )


        self.status = "completed"


        return self.result