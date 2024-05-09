import streamlit as st
from llama_index.llms.openai import OpenAI
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader


st.title('Chat App with LlamaIndex + Streamlit + langfuse')


# Initialize the chat history
if "messages" not in st.session_state.keys():
    st.session_state.messages = [
        {"role": "assistant", "content": "Ask me a question about Streamlit's open-source Python library!"}
    ]


@st.cache_resource(show_spinner=False)
def load_data():
    with st.spinner(text="Loading and indexing the Streamlit docs – hang tight! This should take 1-2 minutes."):
        docs = SimpleDirectoryReader(input_dir="./data", recursive=True).load_data()
        index = VectorStoreIndex.from_documents(docs)
        return index


index = load_data()


# Initialize the chat engine
if "chat_engine" not in st.session_state.keys():
    llm = OpenAI(model="gpt-3.5-turbo", temperature=0.5, system_prompt="You are an expert on the Streamlit Python library and your job is to answer technical questions. Assume that all questions are related to the Streamlit Python library. Keep your answers technical and based on facts – do not hallucinate features.")
    st.session_state.chat_engine = index.as_chat_engine(chat_mode="openai", llm=llm, verbose=True)


# Prompt for user input and save to chat history
if prompt := st.chat_input("Your question"):
    st.session_state.messages.append({"role": "user", "content": prompt})


# Display the prior chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# If last message is not from assistant, generate a new response
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = st.session_state.chat_engine.chat(prompt)
            st.write(response.response)
            message = {"role": "assistant", "content": response.response}
            st.session_state.messages.append(message)
