from study_log import (
    add_study_record,
    get_topic_history,
    calculate_total_time
)



def test_add_record():


    record = add_study_record(

        "Matematik",

        "Fonksiyonlar",

        45,

        80

    )


    assert record["duration"] == 45



def test_history():


    history = get_topic_history(
        "Fonksiyonlar"
    )


    assert len(history) >= 1



def test_total_time():


    total = calculate_total_time()


    assert total >= 45