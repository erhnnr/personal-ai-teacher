
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import build_official_curriculum_registry as registry


def test_theme_framework_can_follow_last_outcome():
    text = """
    BİY.10.1.1. Birinci çıktı
    a) işlem
    BİY.10.1.2. İkinci çıktı
    a) işlem
    BİY.10.1.10. Son çıktı
    a) işlem
    İÇERİK ÇERÇEVESİ Güneşten Besinlere
    Canlılık İçin Enerjinin Önemi, ATP
    Anahtar Kavramlar ATP, fotosentez
    ÖĞRENME KANITLARI
    çalışma yaprağı
    BİY.10.2.1. Sonraki tema
    a) işlem
    """
    result = registry.extract_theme_content_framework(text, 10, 1)
    assert "Güneşten Besinlere" in result
    assert "Canlılık İçin Enerjinin Önemi" in result


def test_individual_outcome_need_not_contain_framework():
    text = """
    BİY.9.1.2. Bilimsel araştırma süreçlerinde bilimin doğasını yorumlayabilme
    a) Bilimsel araştırma süreçlerinde bilimin doğasının özelliklerini inceler.
    BİY.9.1.3. Bilimsel araştırmaların bilim etiğine uygunluğu ile ilgili bilgi toplayabilme
    a) Bilgi toplar.
    """
    outcomes = registry.split_outcome_blocks(text)
    assert len(outcomes) == 2
    assert outcomes[0]["content_framework"] == ""


def test_theme_framework_stops_before_next_theme():
    text = """
    BİY.12.1.12. Çimlenmeyi etkileyen faktörleri gözlemleyebileceği deney yapabilme
    a) Deney tasarlar.
    İÇERİK ÇERÇEVESİ Üreme ve Canlılar İçin Önemi
    Hücre Bölünmeleri
    Anahtar Kavramlar mitoz
    ÖĞRENME KANITLARI
    görev
    BİY.12.2.1. Nükleik asitlerin yapısını sorgulayabilme
    a) Soru sorar.
    İÇERİK ÇERÇEVESİ Nükleik Asitler ve Gen İfadesi
    DNA ve RNA
    Anahtar Kavramlar DNA
    """
    result = registry.extract_theme_content_framework(text, 12, 1)
    assert "Üreme ve Canlılar İçin Önemi" in result
    assert "Nükleik Asitler" not in result
