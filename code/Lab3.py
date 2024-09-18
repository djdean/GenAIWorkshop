#Go through how to add context to the prompt. Specifically, read a PDF in, and use GPT to summarize the text.

from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
import tiktoken
import streamlit as st
def main():
    endpoint = "<AOAI Endpoint>"
    openai_key = "<AOAI Key>"
    openai_api_version = "<AOAI API Version>"
    model = "<Model Deployment Name>"
    model_family = "<Model Family>"
    model_cost = "<Model Cost>(int)"
    document_intelligence_key = "<Document Intelligence Key>"
    document_intelligence_endpoint = "<Document Intelligence Endpoint>"
    
    st.set_page_config(layout="wide")
    init_sidebar(model,openai_api_version,endpoint,openai_key)
    uploaded_file = st.file_uploader("Choose a file")
    if uploaded_file is not None:
        with st.spinner("Thinking..."):
            # To read file as bytes:
            if not "content" in st.session_state:
                document = uploaded_file.getvalue()
                content = parse_pdf(document, st.session_state["DI_client"])
                st.session_state["content"] = content
            else:
                 content = st.session_state["content"]
            paragraphs = content["paragraphs"]
            if not "messages" in st.session_state:
                 st.session_state["messages"] = []
            question = st.chat_input("Enter a question to ask "+model+ " about "+uploaded_file.name+":")
            messages = st.session_state["messages"]
            history = ""
            for message in messages:
                history += message['content']
                with st.chat_message(message['role']):
                    if message['role'] == "Assistant":
                        st.markdown(message['content'] + " Cost:"+message['cost'])
                    else:
                        st.markdown(message['content'])
            if question:
                handle_question(question,model,model_family,paragraphs,history,model_cost)

def handle_question(question,model,model_family,paragraphs,history,model_cost):
    numtokens_sent = get_num_tokens_from_string(question,model_family)
    answer = answer_question(question,st.session_state["AOAI_client"],model, paragraphs, history)
    numtokens_received = get_num_tokens_from_string(answer,model_family)
    user_message = {
        "role":"user",
        "content":question
    }
    st.session_state["messages"].append(user_message)
    cost = ((numtokens_sent+numtokens_received)/1000) * model_cost
    response_message = {
        "role":"Assistant",
        "content":answer,
        "cost":"$"+str(cost)
    }
    with st.chat_message(response_message["role"]):
        st.markdown(response_message['content'] + " (Cost:"+response_message['cost'] +")")
    st.session_state["messages"].append(response_message) 
def init_sidebar(model,openai_api_version,endpoint,openai_key, document_intelligence_endpoint,document_intelligence_key):
    with st.sidebar:
        st.header(':green[Azure OpenAI Configuration]')
        st.subheader(':orange[Model:] ' + model)
        st.subheader(':orange[API Version:] ' + openai_api_version)
        if not "AOAI_client" in st.session_state:
            st.markdown("Connecting to Azure...")
            client = AzureOpenAI(
                azure_endpoint = endpoint, 
                api_key=openai_key,  
                api_version=openai_api_version
            )
            document_intelligence_client = DocumentIntelligenceClient(
                endpoint=document_intelligence_endpoint, credential=AzureKeyCredential(document_intelligence_key)
            )
            st.session_state["DI_client"] = document_intelligence_client
            st.session_state["AOAI_client"] = client
            st.markdown("Done")
            
        else:
             st.markdown("Connected.")
        

def get_filename_pretty(path):
     path_split = path.split("\\")
     filename_only = path_split[len(path_split)-1]
     return filename_only
def get_num_tokens_from_string(string: str, encoding_name: str) -> int:
        encoding = tiktoken.encoding_for_model(encoding_name)
        num_tokens = len(encoding.encode(string))
        return num_tokens
def parse_pdf(doc,document_intelligence_client):
        poller_layout = document_intelligence_client.begin_analyze_document(
            "prebuilt-layout", AnalyzeDocumentRequest(bytes_source=bytes(doc)), locale="en-US"
        )
        layout: AnalyzeResult = poller_layout.result()
        paragraph_content = ""
        table_content = ""
        for p in layout.paragraphs:
            paragraph_content += f"{p.content}\n"
        for t in layout.tables:
            previous_cell_row=0
            rowcontent='| '
            tablecontent = ''
            for c in t.cells:
                if c.row_index == previous_cell_row:
                    rowcontent +=  c.content + " | "
                else:
                    tablecontent += rowcontent + "\n"
                    rowcontent='|'
                    rowcontent += c.content + " | "
                    previous_cell_row += 1
            table_content += f"{tablecontent}\n"
        return_content = {
            "paragraphs": paragraph_content,
            "tables": table_content
        }
        return return_content
def answer_question(question,client, model,content, history):
        response = client.chat.completions.create(
            model=model, # model = "deployment_name".
            messages=[
                {"role": "system", "content": "You are an AI assistant extremely proficient in answering questions coming from different users based on input context. When possible, insert some humor into your responses."},
                {"role": "user", "content": "Based on the following context:\n\n"+content+"\n\n Along with the user's chat history:\n\n"+history+"\n\nAnswer the following question:\n\n"+question},
            ]
        )
        return response.choices[0].message.content
           
if __name__ == "__main__":
    main()

