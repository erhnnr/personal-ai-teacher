from teacher import ask_teacher


print("AI TYT Öğretmen hazır.")
print("Çıkmak için: exit")


while True:

    question = input("\nÖğrenci: ")

    if question.lower() == "exit":
        break

    answer = ask_teacher(question)

    print("\nÖğretmen:")
    print(answer)