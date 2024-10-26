import Retriever  
import Generator  

docs_path = '/path/to/documents'
questions_file = '/path/to/questions.txt'
answers_output_file = '/path/to/answers_output.txt'

retriever = Retriever(source_folder=docs_path)
generator = Generator()

with open(questions_file, 'r') as file:
    questions = [line.strip() for line in file if line.strip()]

# Generate answers for each question
answers = []
for question in questions:
    retrieved_docs = retriever.retrieve(query=question, k=3)
    answer = generator.generate_answer(question, retrieved_docs)
    answers.append(answer)

# Write answers to the output file
with open(answers_output_file, 'w') as file:
    for answer in answers:
        file.write(answer + '\n')

print("Answers generated and saved to:", answers_output_file)
