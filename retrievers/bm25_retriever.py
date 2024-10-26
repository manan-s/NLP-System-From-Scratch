from rank_bm25 import BM25Okapi
from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader, MergedDataLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

class bm25_retriever:
    def __init__(self, source_folder: str, chunk_size=1000, chunk_overlap=100):
        self.documents = self.load_documents(source_folder, chunk_size, chunk_overlap)
        self.tokenized_corpus = [doc.split() for doc in self.documents]  # Tokenize documents for BM25
        self.bm25 = BM25Okapi(self.tokenized_corpus)

    def load_documents(self, source_folder, chunk_size, chunk_overlap):
        text_loader = DirectoryLoader(source_folder, glob="**/*.txt", loader_cls=TextLoader)
        pdf_loader = DirectoryLoader(source_folder, glob="**/*.pdf", loader_cls=PyPDFLoader)
        docs = MergedDataLoader(loaders=[text_loader, pdf_loader]).load()

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        chunks = text_splitter.split_documents(docs)
        
        return [chunk.page_content for chunk in chunks]

    def retrieve(self, query, k=3):
        tokenized_query = query.split()
        scores = self.bm25.get_scores(tokenized_query)

        top_k_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        return [self.documents[i] for i in top_k_indices]