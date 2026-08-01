CURRICULUM = {

    "Matematik": {

        "9": [

            "Sayılar",

            "Bölme ve Bölünebilme",

            "EBOB-EKOK",

            "Rasyonel Sayılar",

            "Üslü Sayılar",

            "Köklü Sayılar",

            "Denklemler",

            "Eşitsizlikler",

            "Fonksiyonlar"

        ],

        "10": [

            "Polinomlar",

            "İkinci Derece Denklemler",

            "Permütasyon",

            "Kombinasyon",

            "Olasılık"

        ],

        "11": [

            "Trigonometri",

            "Logaritma",

            "Diziler"

        ],

        "12": [

            "Limit",

            "Türev",

            "İntegral"

        ]

    }

}


def get_subjects():

    return list(CURRICULUM.keys())


def get_grades(subject):

    return list(CURRICULUM[subject].keys())


def get_topics(subject, grade):

    return CURRICULUM[subject][grade]