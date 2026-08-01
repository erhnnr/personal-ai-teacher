from memory import *

clear_memory()

set_last_topic("Fonksiyonlar")

add_completed_topic("Sayılar")
add_completed_topic("Fonksiyonlar")

add_weak_topic("Problemler")

add_study_history({
    "topic": "Fonksiyonlar",
    "duration": 45
})

add_quiz_result({
    "topic": "Fonksiyonlar",
    "score": 80
})

print(load_memory())