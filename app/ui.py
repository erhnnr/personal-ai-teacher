"""
EIE-033 Student Interface

Purpose:
Personal AI Teacher learning flow.
"""


import streamlit as st

from session import LearningSession


st.set_page_config(
    page_title="Personal AI Teacher",
    page_icon="🎓"
)


st.title("🎓 Personal AI Teacher")


if "session" not in st.session_state:

    st.session_state.session = None


if "lesson_answer" not in st.session_state:

    st.session_state.lesson_answer = ""



st.sidebar.title("📚 Çalışma")


topic = st.sidebar.text_input(
    "Bugün hangi konuyu çalışacaksın?"
)



if st.sidebar.button("Dersi Başlat"):

    if topic:

        session = LearningSession(
            topic + " konusunu anlat."
        )


        session.start()


        st.session_state.session = session


        with st.spinner(
            "Öğretmen hazırlanıyor..."
        ):

            st.session_state.lesson_answer = (
                session.teach()
            )


        st.success(
            f"{topic} hazır."
        )



if st.session_state.session:


    st.subheader("📖 Ders Anlatımı")


    st.write(
        st.session_state.lesson_answer
    )



    st.divider()


    st.subheader("📝 Quiz")


    quiz = st.session_state.session.quiz


    answers = []


    for index, question in enumerate(
        quiz.questions
    ):

        st.write(
            f"{index + 1}. {question}"
        )


        answer = st.text_input(
            f"Cevap {index + 1}",
            key=f"answer_{index}"
        )


        answers.append(answer)



    if st.button("Sonuçları Değerlendir"):


        result = st.session_state.session.complete(
            answers
        )


        st.success(
            f"Skorun: %{result.score}"
        )


        st.write(
            "Doğru:",
            result.correct_answers
        )


        st.write(
            "Yanlış:",
            result.wrong_answers
        )