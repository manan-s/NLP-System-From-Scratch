from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace

class nn_generator:
    def __init__(self, repo_id="mistralai/Mistral-7B-Instruct-v0.3", max_new_tokens=512):
        self.llm = HuggingFaceEndpoint(
            repo_id=repo_id,
            task="text-generation",
            max_new_tokens=max_new_tokens,
            do_sample=False,
            repetition_penalty=1.03,
        )
        self.chat = ChatHuggingFace(llm=self.llm, verbose=True)

    def generate_answer(self, query, retrieved_docs):
        source_knowledge = "\n".join([doc if isinstance(doc, str) else doc.page_content for doc in retrieved_docs])
        augmented_prompt = f"""Using the information below, answer the query concisely:

        Information:
        {source_knowledge}

        Query: {query}

        Concise Answer:(answer the query in a single phrase or word or, at most, one line)"""
        
        response = self.chat.invoke([augmented_prompt])
        return response.content.replace("\n", " ")
