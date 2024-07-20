import os
from dotenv import load_dotenv

from langchain.text_splitter import CharacterTextSplitter
from langchain.schema import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain_community.llms.octoai_endpoint import OctoAIEndpoint
from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

file_path = "CustomerData.txt"

# Read the content of the file
with open(file_path, 'r') as f:
    file_text = f.read()

# Initialize the text splitter
text_splitter = CharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=512, chunk_overlap=64
)

# Split the text into chunks
texts = text_splitter.split_text(file_text)

# Create a list of Document objects for the split texts
file_texts = [
    Document(page_content=chunked_text, 
             metadata={"doc_title": os.path.basename(file_path).split(".")[0], 
                       "chunk_num": i})
    for i, chunked_text in enumerate(texts)
]

embeddings = HuggingFaceEmbeddings()

vector_store = FAISS.from_documents(
    file_texts,
    embedding=embeddings
)

llm = OctoAIEndpoint(
        model="meta-llama-3-8b-instruct",
        max_tokens=1024,
        presence_penalty=0,
        temperature=0.1,
        top_p=0.9,
)

retriever = vector_store.as_retriever()

template="""You are an assistant for helping us make sales for our tires. Use the following pieces of retrieved context to give us the best response to our customers to ensure we can sell them new tires.
Question: {question} 
Context: {context} 
Answer:"""
prompt = ChatPromptTemplate.from_template(template)

chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

chain.invoke("I just got new tires. Why do I need new tires?")

# template="""You are a literary critic. You are given some context and asked to answer questions based on only that context.
# Question: {question} 
# Context: {context} 
# Answer:"""
# lit_crit_prompt = ChatPromptTemplate.from_template(template)

# lcchain = (
#     {"context": retriever, "question": RunnablePassthrough()}
#     | lit_crit_prompt
#     | llm
#     | StrOutputParser()
# )

# pprint(lcchain.invoke("What is the best thing about Luke's Father's story line?"))
