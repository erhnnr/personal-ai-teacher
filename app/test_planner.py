from planner import create_plan


plan = create_plan(
    "Limit konusunu anlat."
)


print()

print("Allowed :", plan.allowed)

print("Reason  :", plan.reason)

print("Next    :", plan.next_topic)

print("Grade   :", plan.grade)

print("Subject :", plan.subject)

print()