# Personal AI Teacher
## System Architecture v1.0

---

# 1. Project Vision

Personal AI Teacher is a local AI-powered education platform designed to teach students rather than simply answer questions.

The system adapts to each student's level, learning speed, strengths and weaknesses.

The long-term goal is to build a complete AI teacher capable of replacing traditional tutoring for many subjects.

---

# 2. Main Goals

The system should be able to:

- Teach concepts
- Explain difficult topics
- Give examples
- Produce exercises
- Ask questions
- Detect misunderstandings
- Evaluate answers
- Track learning progress
- Build long-term knowledge

---

# 3. Design Principles

- Local-first
- Modular architecture
- Explain before solving
- Student-centered
- Curriculum-driven
- Long-term memory
- Easy to extend
- Multi-subject support

---

# 4. High Level Architecture

Student

↓

User Interface

↓

Conversation Manager

↓

Teacher Engine

↓

Lesson Planner

↓

Curriculum Engine

↓

Student Model

↓

Memory System

↓

Local LLM (LM Studio)

---

# 5. Core Modules

## UI

Responsible for the Streamlit interface.

---

## Conversation Manager

Controls conversations.

Maintains context.

Routes requests.

---

## Teacher Engine

Explains topics.

Produces examples.

Answers questions.

Changes explanation difficulty.

---

## Lesson Planner

Determines what should be taught next.

Skips mastered topics.

Returns to weak areas.

---

## Curriculum Engine

Contains the complete curriculum.

Knows prerequisites.

Builds learning paths.

---

## Student Model

Stores:

- Grade
- Goals
- Current topic
- Weak topics
- Strong topics
- Learning style
- Progress

---

## Memory

Stores:

Conversation history

Learning history

Mistakes

Solved questions

Achievements

---

## Quiz Engine

Creates quizzes.

Adjusts difficulty.

Produces hints.

---

## Evaluator

Checks student answers.

Calculates success.

Produces feedback.

---

## Progress Tracker

Tracks

Daily progress

Weekly progress

Completed topics

Mastery scores

Learning statistics

---

# 6. Data Flow

Student

↓

Question

↓

Conversation Manager

↓

Teacher

↓

Planner

↓

Memory

↓

LLM

↓

Answer

↓

Evaluation

↓

Progress Update

---

# 7. Future Modules

Voice Tutor

Vision Module

PDF Reader

Notebook Mode

Homework Generator

Exam Simulator

Flashcards

RAG Knowledge Base

Multi-Agent Teaching

---

# 8. Technology Stack

Python

Streamlit

OpenAI SDK

LM Studio

Qwen2.5

JSON

Markdown

---

# 9. Long-Term Goal

Build a complete personal AI teacher capable of guiding a student from Grade 9 through university using local LLMs.
