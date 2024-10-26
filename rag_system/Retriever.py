from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader, TextLoader, MergedDataLoader
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
import torch

class Retriever:
    def __init__(self, source_folder: str, chunk_size=1000, chunk_overlap=100, embed_model_name="sentence-transformers/sentence-t5-large", collection_name="hf_embed_flan_t5_large"):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embed_model_name,
            model_kwargs={'device': self.device},
            encode_kwargs={'normalize_embeddings': False}
        )
        self.vectorstore = self.initialize_vectorstore(self.load_documents(source_folder, chunk_size, chunk_overlap), collection_name)
        

    def load_documents(self, source_folder, chunk_size, chunk_overlap):
        # Load text files from source folder
        text_loader = DirectoryLoader(source_folder, glob="**/*.txt", loader_cls=TextLoader)
        pdf_loader = DirectoryLoader(source_folder, glob="**/*.pdf", loader_cls=PyPDFLoader)
        docs = MergedDataLoader(loaders=[text_loader, pdf_loader]).load()

        # Split documents for vector storage
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        return text_splitter.split_documents(docs)

    def initialize_vectorstore(self, docs, collection_name):
        # Initialize vector store with split documents
        return Chroma.from_documents(
            documents=docs,
            embedding=self.embeddings,
            collection_name=collection_name
        )

    def retrieve(self, query, k=3):
        return self.vectorstore.similarity_search(query, k=k)