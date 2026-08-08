from curriculum_engine import (
    get_topic_info,
    load_curriculum_data,
)


def test_curriculum_intelligence():

    topic = get_topic_info(
        "AYT",
        "Matematik",
        "Limit"
    )

    assert topic is not None
    assert topic["topic"] == "Limit"
    assert "Türev" in topic["next_topics"]
    assert topic["priority"] == "critical"


def test_tyt_matematik_curriculum_loaded():

    curriculum = load_curriculum_data()

    topics = [
        item
        for item in curriculum
        if item.get("exam") == "TYT"
        and item.get("subject") == "Matematik"
    ]

    assert len(topics) == 15


def test_tyt_matematik_topic_metadata():

    topic = get_topic_info(
        "TYT",
        "Matematik",
        "Problemler"
    )

    assert topic is not None
    assert topic["topic"] == "Problemler"
    assert topic["priority"] == "critical"
    assert topic["difficulty"] == "hard"
    assert "Hareket problemleri" in topic["subtopics"]
    assert "Denklemler ve Eşitsizlikler" in topic["dependencies"]


def test_tyt_turkce_curriculum_loaded():

    curriculum = load_curriculum_data()

    topics = [
        item
        for item in curriculum
        if item.get("exam") == "TYT"
        and item.get("subject") == "Türkçe"
    ]

    assert len(topics) == 13


def test_tyt_turkce_paragraf_metadata():

    topic = get_topic_info(
        "TYT",
        "Türkçe",
        "Paragrafta Anlam"
    )

    assert topic is not None
    assert topic["priority"] == "critical"
    assert topic["difficulty"] == "hard"
    assert "Ana düşünce" in topic["subtopics"]
    assert "Cümlede Anlam" in topic["dependencies"]
    assert "Sözel Mantık ve Muhakeme" in topic["next_topics"]


def test_tyt_fizik_curriculum_loaded():

    curriculum = load_curriculum_data()

    topics = [
        item
        for item in curriculum
        if item.get("exam") == "TYT"
        and item.get("subject") == "Fizik"
    ]

    assert len(topics) == 10


def test_tyt_fizik_hareket_metadata():

    topic = get_topic_info(
        "TYT",
        "Fizik",
        "Hareket ve Kuvvet"
    )

    assert topic is not None
    assert topic["priority"] == "critical"
    assert topic["difficulty"] == "medium"
    assert "Newton'un hareket yasaları" in topic["subtopics"]
    assert "Fizik Bilimine Giriş" in topic["dependencies"]
    assert "İş Güç ve Enerji" in topic["next_topics"]


def test_tyt_kimya_curriculum_loaded():

    curriculum = load_curriculum_data()

    topics = [
        item
        for item in curriculum
        if item.get("exam") == "TYT"
        and item.get("subject") == "Kimya"
    ]

    assert len(topics) == 10


def test_tyt_kimya_mol_metadata():

    topic = get_topic_info(
        "TYT",
        "Kimya",
        "Mol ve Kimyasal Hesaplamalar"
    )

    assert topic is not None
    assert topic["priority"] == "critical"
    assert topic["difficulty"] == "hard"
    assert "Mol kavramı" in topic["subtopics"]
    assert "Kimyanın Temel Kanunları" in topic["dependencies"]
    assert "Karışımlar" in topic["next_topics"]


def test_tyt_biyoloji_curriculum_loaded():

    curriculum = load_curriculum_data()

    topics = [
        item
        for item in curriculum
        if item.get("exam") == "TYT"
        and item.get("subject") == "Biyoloji"
    ]

    assert len(topics) == 10


def test_tyt_biyoloji_hucre_metadata():

    topic = get_topic_info(
        "TYT",
        "Biyoloji",
        "Hücre"
    )

    assert topic is not None
    assert topic["priority"] == "critical"
    assert topic["difficulty"] == "medium"
    assert "Prokaryot hücre" in topic["subtopics"]
    assert "Osmoz" in topic["subtopics"]
    assert "Canlıların Temel Bileşenleri" in topic["dependencies"]
    assert "Canlıların Sınıflandırılması" in topic["next_topics"]


def test_tyt_tarih_curriculum_loaded():

    curriculum = load_curriculum_data()

    topics = [
        item
        for item in curriculum
        if item.get("exam") == "TYT"
        and item.get("subject") == "Tarih"
    ]

    assert len(topics) == 15


def test_tyt_tarih_milli_mucadele_metadata():

    topic = get_topic_info(
        "TYT",
        "Tarih",
        "Millî Mücadele"
    )

    assert topic is not None
    assert topic["priority"] == "critical"
    assert topic["difficulty"] == "hard"
    assert "Amasya Genelgesi" in topic["subtopics"]
    assert "TBMM'nin açılması" in topic["subtopics"]
    assert (
        "20. Yüzyıl Başlarında Osmanlı Devleti ve Dünya"
        in topic["dependencies"]
    )
    assert "Atatürkçülük ve Türk İnkılabı" in topic["next_topics"]


def test_tyt_cografya_curriculum_loaded():

    curriculum = load_curriculum_data()

    topics = [
        item
        for item in curriculum
        if item.get("exam") == "TYT"
        and item.get("subject") == "Coğrafya"
    ]

    assert len(topics) == 13


def test_tyt_cografya_harita_metadata():

    topic = get_topic_info(
        "TYT",
        "Coğrafya",
        "Harita Bilgisi"
    )

    assert topic is not None
    assert topic["priority"] == "critical"
    assert topic["difficulty"] == "hard"
    assert "Ölçek" in topic["subtopics"]
    assert "İzohips" in topic["subtopics"]
    assert "Coğrafi Konum" in topic["dependencies"]
    assert "Atmosfer ve İklim" in topic["next_topics"]


def test_tyt_felsefe_curriculum_loaded():

    curriculum = load_curriculum_data()

    topics = [
        item
        for item in curriculum
        if item.get("exam") == "TYT"
        and item.get("subject") == "Felsefe"
    ]

    assert len(topics) == 9


def test_tyt_felsefe_bilgi_metadata():

    topic = get_topic_info(
        "TYT",
        "Felsefe",
        "Bilgi Felsefesi"
    )

    assert topic is not None
    assert topic["priority"] == "critical"
    assert topic["difficulty"] == "medium"
    assert "Rasyonalizm" in topic["subtopics"]
    assert "Empirizm" in topic["subtopics"]
    assert "Varlık Felsefesi" in topic["dependencies"]
    assert "Ahlak Felsefesi" in topic["next_topics"]


def test_tyt_din_curriculum_loaded():

    curriculum = load_curriculum_data()

    topics = [
        item
        for item in curriculum
        if item.get("exam") == "TYT"
        and item.get("subject") == "Din Kültürü"
    ]

    assert len(topics) == 10


def test_tyt_din_ibadet_metadata():

    topic = get_topic_info(
        "TYT",
        "Din Kültürü",
        "İslam ve İbadet"
    )

    assert topic is not None
    assert topic["priority"] == "critical"
    assert topic["difficulty"] == "medium"
    assert "Namaz" in topic["subtopics"]
    assert "Oruç" in topic["subtopics"]
    assert "Din ve İslam" in topic["dependencies"]
    assert "Gençlik ve Değerler" in topic["next_topics"]


def test_ayt_matematik_curriculum_loaded():

    curriculum = load_curriculum_data()

    topics = [
        item
        for item in curriculum
        if item.get("exam") == "AYT"
        and item.get("subject") == "Matematik"
    ]

    assert len(topics) == 17


def test_ayt_matematik_turev_metadata():

    topic = get_topic_info(
        "AYT",
        "Matematik",
        "Türev"
    )

    assert topic is not None
    assert topic["priority"] == "critical"
    assert topic["difficulty"] == "hard"
    assert "Türev alma kuralları" in topic["subtopics"]
    assert "Limit" in topic["dependencies"]
    assert "İntegral" in topic["next_topics"]


def test_ayt_fizik_curriculum_loaded():

    curriculum = load_curriculum_data()

    topics = [
        item
        for item in curriculum
        if item.get("exam") == "AYT"
        and item.get("subject") == "Fizik"
    ]

    assert len(topics) == 15


def test_ayt_fizik_modern_metadata():

    topic = get_topic_info(
        "AYT",
        "Fizik",
        "Modern Fizik"
    )

    assert topic is not None
    assert topic["priority"] == "critical"
    assert topic["difficulty"] == "hard"
    assert "Fotoelektrik olay" in topic["subtopics"]
    assert "Dalga Mekaniği" in topic["dependencies"]
    assert (
        "Modern Fiziğin Teknolojideki Uygulamaları"
        in topic["next_topics"]
    )


def test_ayt_kimya_curriculum_loaded():

    curriculum = load_curriculum_data()

    topics = [
        item
        for item in curriculum
        if item.get("exam") == "AYT"
        and item.get("subject") == "Kimya"
    ]

    assert len(topics) == 12


def test_ayt_kimya_denge_metadata():

    topic = get_topic_info(
        "AYT",
        "Kimya",
        "Kimyasal Denge"
    )

    assert topic is not None
    assert topic["priority"] == "critical"
    assert topic["difficulty"] == "hard"
    assert "Le Chatelier ilkesi" in topic["subtopics"]
    assert "Kimyasal Tepkimelerde Hız" in topic["dependencies"]
    assert "Asit Baz Dengesi" in topic["next_topics"]


def test_ayt_biyoloji_curriculum_loaded():

    curriculum = load_curriculum_data()

    topics = [
        item
        for item in curriculum
        if item.get("exam") == "AYT"
        and item.get("subject") == "Biyoloji"
    ]

    assert len(topics) == 16


def test_ayt_biyoloji_gen_metadata():

    topic = get_topic_info(
        "AYT",
        "Biyoloji",
        "Genden Proteine"
    )

    assert topic is not None
    assert topic["priority"] == "critical"
    assert topic["difficulty"] == "hard"
    assert "DNA replikasyonu" in topic["subtopics"]
    assert "Transkripsiyon" in topic["subtopics"]
    assert "TYT Kalıtım" in topic["dependencies"]
    assert (
        "Biyoteknoloji ve Genetik Mühendisliği"
        in topic["next_topics"]
    )