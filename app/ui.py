"""
EIE-033 Student Interface

Purpose:
Professional student-facing interface for
Personal AI Teacher MODEL-1.

Architecture:
Curriculum -> LearningSession -> Teacher Engine
-> Quiz -> Evaluator -> Progress / Memory
"""

import streamlit as st

from curriculum_engine import load_curriculum_data
from session import LearningSession
from teacher import ask_teacher, TeacherError


st.set_page_config(
    page_title="Personal AI Teacher",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
        .block-container {
            max-width: 1100px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        .main-title {
            font-size: 2.1rem;
            font-weight: 700;
            margin-bottom: 0.2rem;
        }

        .subtitle {
            opacity: 0.72;
            margin-bottom: 1.5rem;
        }

        .status-card {
            border: 1px solid rgba(128, 128, 128, 0.20);
            border-radius: 12px;
            padding: 14px;
            margin-top: 10px;
        }

        div[data-testid="stChatMessage"] {
            border-radius: 14px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_curriculum():
    try:
        return load_curriculum_data()
    except Exception:
        return []


def get_exams(records):
    return sorted(
        {
            record["exam"]
            for record in records
            if record.get("exam")
        }
    )


def get_subjects(records, exam):
    return sorted(
        {
            record["subject"]
            for record in records
            if (
                record.get("exam") == exam
                and record.get("subject")
            )
        }
    )


def get_topics(records, exam, subject):
    return [
        record["topic"]
        for record in records
        if (
            record.get("exam") == exam
            and record.get("subject") == subject
            and record.get("topic")
        )
    ]


def get_topic_record(
    records,
    exam,
    subject,
    topic,
):
    for record in records:
        if (
            record.get("exam") == exam
            and record.get("subject") == subject
            and record.get("topic") == topic
        ):
            return record
    return None


def initialize_state():
    defaults = {
        "selected_exam": None,
        "selected_subject": None,
        "selected_topic": None,
        "lesson_started": False,
        "lesson_content": "",
        "messages": [],
        "learning_session": None,
        "quiz_submitted": False,
        "quiz_result": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_lesson():
    st.session_state.lesson_started = False
    st.session_state.lesson_content = ""
    st.session_state.messages = []
    st.session_state.learning_session = None
    st.session_state.quiz_submitted = False
    st.session_state.quiz_result = None


def quiz_is_placeholder(quiz):
    """
    Prevent known development-placeholder quiz content
    from being presented as real student assessment.
    """
    if quiz is None:
        return True

    questions = getattr(
        quiz,
        "questions",
        [],
    )

    answers = getattr(
        quiz,
        "answers",
        [],
    )

    if not questions or not answers:
        return True

    placeholder_question = any(
        "temel soru" in str(question).casefold()
        for question in questions
    )

    placeholder_answer = any(
        str(answer).casefold().startswith("cevap")
        for answer in answers
    )

    return (
        placeholder_question
        or placeholder_answer
    )


initialize_state()
curriculum = get_curriculum()


st.markdown(
    '<div class="main-title">📘 Personal AI Teacher</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="subtitle">
    TYT ve AYT için kişisel çalışma alanın.
    Konunu seç, dersi başlat ve öğretmeninle çalış.
    </div>
    """,
    unsafe_allow_html=True,
)


if not curriculum:
    st.error(
        "Müfredat verileri yüklenemedi."
    )
    st.stop()


exams = get_exams(curriculum)


with st.sidebar:
    st.header(
        "📚 Ders Seçimi"
    )

    exam = st.selectbox(
        "Sınav",
        exams,
        index=0,
    )

    subjects = get_subjects(
        curriculum,
        exam,
    )

    subject = st.selectbox(
        "Ders",
        subjects,
        index=0,
    )

    topics = get_topics(
        curriculum,
        exam,
        subject,
    )

    topic = st.selectbox(
        "Konu",
        topics,
        index=0,
    )

    topic_record = get_topic_record(
        curriculum,
        exam,
        subject,
        topic,
    )

    st.divider()

    if st.button(
        "▶ Dersi Başlat",
        use_container_width=True,
        type="primary",
    ):
        st.session_state.selected_exam = exam
        st.session_state.selected_subject = subject
        st.session_state.selected_topic = topic

        reset_lesson()

        question = (
            f"{topic} konusunu anlat. "
            "Önce mantığını açıkla, sonra anlaşılır "
            "bir örnek ver."
        )

        with st.spinner(
            "Öğretmenin dersi hazırlıyor..."
        ):
            try:
                session = LearningSession(
                    question
                )

                session.start()
                answer = session.teach()

                st.session_state.learning_session = (
                    session
                )
                st.session_state.lesson_content = (
                    answer
                )
                st.session_state.lesson_started = (
                    True
                )
                st.session_state.messages = [
                    {
                        "role": "assistant",
                        "content": answer,
                    }
                ]

            except TeacherError as exc:
                st.error(
                    f"Öğretmen başlatılamadı: {exc}"
                )

            except Exception as exc:
                st.error(
                    "Ders başlatılırken beklenmeyen "
                    f"bir hata oluştu: {exc}"
                )

    if st.button(
        "↻ Yeni Ders",
        use_container_width=True,
    ):
        reset_lesson()
        st.rerun()

    st.divider()

    st.caption(
        "MODEL-1 Student Release"
    )


left_column, right_column = st.columns(
    [2.2, 1]
)


with left_column:
    if not st.session_state.lesson_started:
        st.subheader(
            "Bugün ne çalışacağız?"
        )

        st.write(
            "Sol menüden sınav, ders ve konu seçerek "
            "çalışmaya başlayabilirsin."
        )

        st.info(
            "Dersi başlattığında öğretmenin konuyu "
            "senin için hazırlayacak."
        )

        st.markdown(
            """
            ### Çalışma düzeni

            1. Konunu seç.
            2. Öğretmenin anlatımını oku.
            3. Anlamadığın yeri hemen sor.
            4. Örnek iste.
            5. Hazır olduğunda alıştırmaya geç.
            """
        )

    else:
        selected_topic = (
            st.session_state.selected_topic
        )

        selected_subject = (
            st.session_state.selected_subject
        )

        st.subheader(
            f"📖 {selected_subject} · {selected_topic}"
        )

        lesson_tab, quiz_tab = st.tabs(
            [
                "Ders ve Öğretmen",
                "Alıştırma",
            ]
        )

        with lesson_tab:
            for message in (
                st.session_state.messages
            ):
                with st.chat_message(
                    message["role"]
                ):
                    st.markdown(
                        message["content"]
                    )

            student_question = st.chat_input(
                "Öğretmenine bir şey sor..."
            )

            if student_question:
                st.session_state.messages.append(
                    {
                        "role": "user",
                        "content": student_question,
                    }
                )

                with st.chat_message(
                    "user"
                ):
                    st.markdown(
                        student_question
                    )

                contextual_question = (
                    f"{selected_topic} konusu çalışılıyor. "
                    f"Öğrencinin sorusu: "
                    f"{student_question}"
                )

                with st.chat_message(
                    "assistant"
                ):
                    with st.spinner(
                        "Düşünüyorum..."
                    ):
                        try:
                            answer = ask_teacher(
                                contextual_question
                            )

                            st.markdown(
                                answer
                            )

                            st.session_state.messages.append(
                                {
                                    "role": "assistant",
                                    "content": answer,
                                }
                            )

                        except TeacherError as exc:
                            st.error(
                                "Öğretmen yanıt "
                                f"veremedi: {exc}"
                            )

        with quiz_tab:
            session = (
                st.session_state.learning_session
            )

            quiz = (
                session.quiz
                if session is not None
                else None
            )

            if quiz_is_placeholder(
                quiz
            ):
                st.warning(
                    "Bu konu için öğrenciye sunulabilir "
                    "doğrulanmış alıştırma henüz hazır değil."
                )

                st.caption(
                    "Ders anlatımı ve öğretmene soru sorma "
                    "kullanılabilir. Geliştirme amaçlı "
                    "placeholder quiz öğrenciye gösterilmez."
                )

            elif st.session_state.quiz_submitted:
                result = (
                    st.session_state.quiz_result
                )

                st.subheader(
                    "📊 Çalışma Sonucu"
                )

                metric_1, metric_2, metric_3 = (
                    st.columns(3)
                )

                metric_1.metric(
                    "Puan",
                    f"{result.score:.0f}",
                )

                metric_2.metric(
                    "Doğru",
                    result.correct_answers,
                )

                metric_3.metric(
                    "Yanlış",
                    result.wrong_answers,
                )

                if result.score >= 80:
                    st.success(
                        result.recommendation
                    )
                elif result.score >= 50:
                    st.warning(
                        result.recommendation
                    )
                else:
                    st.error(
                        result.recommendation
                    )

                st.caption(
                    "Sonuç öğrenci progress ve memory "
                    "kayıtlarına işlendi."
                )

            else:
                st.subheader(
                    "📝 Konu Alıştırması"
                )

                st.write(
                    "Soruları cevapla ve sonuçlarını gör."
                )

                with st.form(
                    "lesson_quiz_form"
                ):
                    student_answers = []

                    for index, question in enumerate(
                        quiz.questions,
                        start=1,
                    ):
                        st.markdown(
                            f"**{index}. {question}**"
                        )

                        answer = st.text_input(
                            "Cevabın",
                            key=(
                                f"quiz_answer_"
                                f"{selected_topic}_"
                                f"{index}"
                            ),
                        )

                        student_answers.append(
                            answer.strip()
                        )

                    submitted = st.form_submit_button(
                        "Cevapları Gönder",
                        type="primary",
                        use_container_width=True,
                    )

                if submitted:
                    if any(
                        not answer
                        for answer in student_answers
                    ):
                        st.warning(
                            "Lütfen bütün soruları cevapla."
                        )

                    else:
                        try:
                            result = session.complete(
                                student_answers
                            )

                            st.session_state.quiz_result = (
                                result
                            )

                            st.session_state.quiz_submitted = (
                                True
                            )

                            st.rerun()

                        except Exception as exc:
                            st.error(
                                "Alıştırma değerlendirilemedi: "
                                f"{exc}"
                            )


with right_column:
    st.subheader(
        "📌 Konu Bilgisi"
    )

    if topic_record:
        st.markdown(
            f"""
            <div class="status-card">
            <b>Sınav:</b> {exam}<br>
            <b>Ders:</b> {subject}<br>
            <b>Konu:</b> {topic}<br>
            <b>Zorluk:</b> {topic_record.get("difficulty", "-")}<br>
            <b>Öncelik:</b> {topic_record.get("priority", "-")}<br>
            <b>Tahmini süre:</b> {topic_record.get("estimated_hours", "-")} saat
            </div>
            """,
            unsafe_allow_html=True,
        )

        subtopics = topic_record.get(
            "subtopics",
            [],
        )

        if subtopics:
            st.markdown(
                "#### Alt başlıklar"
            )

            for subtopic in subtopics:
                st.write(
                    f"• {subtopic}"
                )

        dependencies = topic_record.get(
            "dependencies",
            [],
        )

        if dependencies:
            st.markdown(
                "#### Ön koşullar"
            )

            for dependency in dependencies:
                st.write(
                    f"• {dependency}"
                )

    st.divider()

    st.markdown(
        "#### Sistem durumu"
    )

    st.success(
        "Yerel AI öğretmeni hazır"
    )

    st.caption(
        "Yanıtlar LM Studio üzerinde çalışan "
        "yerel model tarafından üretilir."
    )