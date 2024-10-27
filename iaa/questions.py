import random

questions_path = '../test_data/reference_questions.txt'

with open(questions_path, 'r') as f:
    questions = f.readlines()

selected_indices = random.sample(range(len(questions)), 30)
selected_questions = [questions[i] for i in selected_indices]

with open('./iaa_questions.txt', 'w') as fq:
    fq.writelines(selected_questions)

