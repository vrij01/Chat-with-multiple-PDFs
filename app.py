import streamlit as st
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import HuggingFaceInstructEmbeddings, OpenAIEmbeddings
from langchain.vectorstores import FAISS  
from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np  
from langchain.memory import ConversationBufferMemory  
from langchain.chains import ConversationalRetrievalChain
# from langchain.llms import ChatOpenAI
from langchain.llms import HuggingFaceHub
from htmlTemplates import css, bot_template, user_template

# llm = HuggingFaceHub(repo_id="google/flan-t5-large")

def get_pdf_text(pdf_docs):
    raw_text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            raw_text += page.extract_text()
    return raw_text


def get_text_chunks(text):
    text_splitter = CharacterTextSplitter(
        separator = '/n',
        chunk_size=1000,
        chunk_overlap=100,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks


# # Load the model and tokenizer
# model_name = "meta-llama/Meta-Llama-3.1-8B-Instruct"
# tokenizer = AutoTokenizer.from_pretrained(model_name)
# model = AutoModel.from_pretrained(model_name)

# def get_embeddings(texts):
#     inputs = tokenizer(texts, return_tensors='pt', padding=True, truncation=True)
#     with torch.no_grad():
#         outputs = model(**inputs)
#     embeddings = outputs.last_hidden_state[:, 0, :]
#     return embeddings.cpu().numpy()

def get_vectorstore(text_chunks):
    # embeddings = OpenAIEmbeddings()
    
    # embeddings = get_embeddings(text_chunks)
    embeddings = HuggingFaceInstructEmbeddings(model_name="hkunlp/instructor-xl")
    vectorstore = FAISS.from_texts(texts = text_chunks, embedding = embeddings)
    return vectorstore

def get_conversation_chain(vectorstore):
    # llm = ChatOpenAI()
    llm = HuggingFaceHub(repo_id="google/flan-t5-xxl", model_kwargs={"temperature":0, "max_length":512})
    memory = ConversationBufferMemory(memory_key = 'chat_history', return_messages = True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm = llm,
        retriever = vectorstore.as_retriever(),
        memory = memory
    )
    return conversation_chain

def handle_userinput(user_question):
    response = st.session_state.conversation({"question": user_question})
    st.session_state.chat_history = response['chat_history']
    
    for i, message in enumerate(st.session_state.chat_history):
        if i % 2 == 0:
            st.write(user_template.replace(
                "{{MSG}}", message.content), unsafe_allow_html=True)
        else:
            st.write(bot_template.replace(
                "{{MSG}}", message.content), unsafe_allow_html=True)
    

    
def main():
    load_dotenv()
    st.set_page_config(page_title="Chat with multiple pdf", page_icon=":books:")
    
    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None
    
    st.write(css, unsafe_allow_html = True)
    
    st.header("Chat with multiple pdf :books:")
    user_question = st.text_input("Ask a question about your document and I will try to answer it!")
    if user_question:
        handle_userinput(user_question)
    
    st.write(user_template.replace("{{MSG}}", "Hello Vrinda"), unsafe_allow_html = True)
    st.write(bot_template.replace("{{MSG}}", "Hello Human"), unsafe_allow_html = True) 
    
    
    with st.sidebar:
        st.subheader("Upload your PDF")
        pdf_docs = st.file_uploader("Upload your PDF file and click on 'Process", accept_multiple_files=True) 
        if st.button("Process"):
            with st.spinner("Processing..."):
                
                # get the pdf text
                raw_text = get_pdf_text(pdf_docs)
                # st.write(raw_text)
                
                # get the text chunks
                text_chunks = get_text_chunks(raw_text)
                st.write(text_chunks)
                
                # create vector store
                vectorstore = get_vectorstore(text_chunks) 
                
                # conversation chain
                st.session_state.conversation = get_conversation_chain(vectorstore)
                
    st.session_state.conversation

if __name__ == '__main__':
    main()


