import sys
import os

sys.path.append(os.path.abspath(".."))


from retrievers.bm25_retriever import bm25_retriever
from generators.nn_generator import nn_generator
from huggingface_hub import interpreter_login
interpreter_login("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")

docs_path = '../crawling/scraped_data/'
questions_file = '../test_data/reference_questions.txt'
answers_output_file = './answers.txt'

retriever = bm25_retriever(source_folder=docs_path)
generator = nn_generator()

with open(questions_file, 'r') as file:
    questions = [line.strip() for line in file if line.strip()]

answers = []
for question in questions:
    retrieved_docs = retriever.retrieve(query=question, k=3)
    answer = generator.generate_answer(question, retrieved_docs)
    print(answer)
    answers.append(answer)

# Write answers to the output file
with open(answers_output_file, 'w') as file:
    for answer in answers:
        file.write(answer + '\n')

print("Answers generated and saved to:", answers_output_file)
