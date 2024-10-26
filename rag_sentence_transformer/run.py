import retrievers.nn_embedding_retriever as nn_embedding_retriever  
import generators.nn_generator as nn_generator  

docs_path = '../crawling/scraped_data'
questions_file = '../test_data/reference_questions.txt'
answers_output_file = './answers.txt'

retriever = nn_embedding_retriever(source_folder=docs_path)
generator = nn_generator()

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
