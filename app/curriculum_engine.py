"""
EIE-010 Curriculum Engine

Purpose:
Manage TYT and AYT curriculum structure.
"""


YKS_CURRICULUM = {


    "TYT": {

        "Matematik": [

            "Sayılar",

            "Bölme ve Bölünebilme",

            "EBOB-EKOK",

            "Rasyonel Sayılar",

            "Üslü Sayılar",

            "Köklü Sayılar",

            "Denklemler",

            "Eşitsizlikler",

            "Fonksiyonlar",

            "Problemler"

        ],


        "Türkçe": [

            "Sözcükte Anlam",

            "Cümlede Anlam",

            "Paragraf",

            "Dil Bilgisi"

        ],


        "Fizik": [

            "Fizik Bilimine Giriş",

            "Madde ve Özellikleri",

            "Hareket"

        ],


        "Kimya": [

            "Kimya Bilimi",

            "Atom ve Periyodik Sistem",

            "Kimyasal Türler"

        ],


        "Biyoloji": [

            "Canlıların Ortak Özellikleri",

            "Hücre",

            "Kalıtım"

        ]

    },



    "AYT": {


        "Matematik": [

            "Fonksiyonlar",

            "Polinomlar",

            "İkinci Derece Denklemler",

            "Permütasyon",

            "Kombinasyon",

            "Olasılık",

            "Trigonometri",

            "Logaritma",

            "Diziler",

            "Limit",

            "Türev",

            "İntegral"

        ],


        "Fizik": [

            "Elektrik",

            "Manyetizma",

            "Dalgalar",

            "Modern Fizik"

        ],


        "Kimya": [

            "Gazlar",

            "Kimyasal Denge",

            "Organik Kimya"

        ],


        "Biyoloji": [

            "Sistemler",

            "Genetik",

            "Ekoloji"

        ]

    }

}





def get_subject_topics(subject, grade):

    """
    Eski API korunuyor.

    Örnek:
    get_subject_topics("Matematik",9)
    """

    grade = int(grade)


    if grade <= 10:

        exam = "TYT"

    else:

        exam = "AYT"


    return (
        YKS_CURRICULUM
        .get(exam, {})
        .get(subject, [])
    )





def is_topic_available(
    subject,
    grade,
    topic
):

    return topic in get_subject_topics(
        subject,
        grade
    )





def get_next_topic(
    subject,
    grade,
    current_topic
):

    topics = get_subject_topics(
        subject,
        grade
    )


    if current_topic in topics:

        index = topics.index(
            current_topic
        )


        if index + 1 < len(topics):

            return topics[index + 1]


    return None





def get_previous_topics(
    subject,
    grade,
    current_topic
):

    topics = get_subject_topics(
        subject,
        grade
    )


    if current_topic in topics:

        index = topics.index(
            current_topic
        )


        return topics[:index]


    return []