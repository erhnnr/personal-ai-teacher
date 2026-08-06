# EID-008 Learning Loop

## Amaç

Öğrencinin soru çözme sürecini öğrenme döngüsüne çevirmek.

Sistem sadece soru sormayacak;
öğrencinin hatasını anlayacak ve sonraki çalışma kararını verecek.

---

# Öğrenme Döngüsü

Student

↓

Question

↓

Answer

↓

Evaluation

↓

Mistake Analysis

↓

Learning Decision

↓

Next Action


---

# Girdi

Öğrenci cevabı:

- question_id
- student_answer
- correct_answer
- timestamp


---

# Evaluation

Sistem belirler:

- doğru / yanlış
- hata tipi
- konu
- zorluk seviyesi


---

# Mistake Analysis

Bağlantılar:

Question
 |
 misconception_target
 |
 Mistake Knowledge


Örnek:

Limit sorusu yanlış

↓

LIMIT-M001

↓

Fonksiyon değeri ve limit karıştırılıyor


---

# Learning Decision

Çıktı:

Örnek:

{
 "action": "review",
 "topic": "Limit",
 "reason": "Aynı hata tekrarlandı",
 "recommended_time": 15
}


---

# Model-1 Kapsamı

Dahil:

- cevap değerlendirme
- hata tespiti
- basit öneri sistemi
- öğrenci hafızasına kayıt

Hariç:

- gelişmiş AI karar sistemi
- otomatik müfredat optimizasyonu
- ileri tahmin modelleri

Bunlar Model-2 kapsamındadır.