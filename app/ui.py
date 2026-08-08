"""
EIE-033 Student Interface

Purpose:
Professional student-facing interface for
Personal AI Teacher MODEL-1.

Architecture:
Curriculum -> Teacher Engine -> Knowledge First -> Local LLM
"""

import streamlit as st

from curriculum_engine import load_curriculum_data
from teacher import ask_teacher, TeacherError


st.set_page_config(
    page_title="Personal AI Teacher",
    page_icon="🎓",
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

        .lesson-card {
            border: 1px solid rgba(128, 128, 128, 0.25);
            border-radius: 14px;
            padding: 18px;
            margin-bottom: 16px;
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
    """
    Load curriculum records.
    """

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


def get_subjects(
    records,
    exam
):
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


def get_topics(
    records,
    exam,
    subject
):
    topics = [
        record["topic"]
        for record in records
        if (
            record.get("exam") == exam
            and record.get("subject") == subject
            and record.get("topic")
        )
    ]

    return topics


def get_topic_record(
    records,
    exam,
    subject,
    topic
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
    }

    for key, value in defaults.items():

        if key not in st.session_state:
            st.session_state[key] = value


def reset_lesson():

    st.session_state.lesson_started = False
    st.session_state.lesson_content = ""
    st.session_state.messages = []


initialize_state()

curriculum = get_curriculum()


st.markdown(
    '<div class="main-title">🎓 Personal AI Teacher</div>',
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


exams = get_exams(
    curriculum
)


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
        exam
    )

    subject = st.selectbox(
        "Ders",
        subjects,
        index=0,
    )

    topics = get_topics(
        curriculum,
        exam,
        subject
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
        topic
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

                answer = ask_teacher(
                    question
                )

                st.session_state.lesson_content = answer

                st.session_state.lesson_started = True

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
            5. Hazır olduğunda soru çözmeye geç.
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

        for message in st.session_state.messages:

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
                f"Şu anda {selected_topic} konusu "
                f"çalışılıyor. Öğrencinin sorusu: "
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
                            f"Öğretmen yanıt veremedi: {exc}"
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
            []
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
            []
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