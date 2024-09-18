#Go through how to add context to the prompt. Specifically, read a PDF in, and use GPT to summarize the text.

from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
import tiktoken
def main():
    print("Connecting to Azure OpenAI...")
    endpoint = "<AOAI Endpoint>"
    openai_key = "<AOAI Key>"
    openai_api_version = "<AOAI API Version>"
    model = "<Model Deployment Name>"
    model_family = "<Model Family>"
    model_cost = "<Model Cost>(int)"
    document_intelligence_key = "<Document Intelligence Key>"
    document_intelligence_endpoint = "<Document Intelligence Endpoint>"
    filename = r"<Path To Sample Input>"
    filename_pretty = get_filename_pretty(filename)
    client = AzureOpenAI(
            azure_endpoint = endpoint, 
            api_key=openai_key,  
            api_version=openai_api_version
        )
    print("Done!\n\nConnecting to the Document Intelligence Service...")
    document_intelligence_client = DocumentIntelligenceClient(
        endpoint=document_intelligence_endpoint, credential=AzureKeyCredential(document_intelligence_key)
    )
    print("Done!\n\n")
    with open(filename,"rb") as input_file:
        document = input_file.read()
    content = parse_pdf(document, document_intelligence_client)
    paragraphs = content["paragraphs"]
    question = ""
    while True:
        question = input("\nEnter a question to ask "+model+ " about "+filename_pretty+" or 'exit' to quit:\n")
        numtokens_sent = get_num_tokens_from_string(question,model_family)
        if question == "exit":
             exit(0)
        answer = answer_question(question,client,model, paragraphs)
        numtokens_received = get_num_tokens_from_string(answer,model_family)
        print(answer)
        cost = ((numtokens_sent+numtokens_received)/1000) *model_cost
        print("Total cost was $"+str(cost)+".\n\n")

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
def answer_question(question,client, model,content):
        response = client.chat.completions.create(
            model=model, # model = "deployment_name".
            messages=[
                {"role": "system", "content": "You are an AI assistant extremely proficient in answering questions coming from different users based on input context. When possible, insert some humor into your responses."},
                {"role": "user", "content": "Based on the following context:"+content+"\n\nAnswer the following question:\n\n"+question},
            ]
        )
        return response.choices[0].message.content
           
if __name__ == "__main__":
    main()

