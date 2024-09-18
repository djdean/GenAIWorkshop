from openai import AzureOpenAI
def main():
    #Go over the SDK and how to connect to AOAI programatically using the API. 
    #Simple prompting
    print("Connecting to Azure OpenAI...")
    endpoint = "<AOAI Endpoint>"
    openai_key = "<AOAI Key>"
    openai_api_version = "<AOAI API Version>"
    model = "<Model Deployment Name>"
    client = AzureOpenAI(
            azure_endpoint = endpoint, 
            api_key=openai_key,  
            api_version=openai_api_version
        )
    print("Done!\n\n")
    question = ""
    while True:
        question = input("\nEnter a question to ask "+model+ " or 'exit' to quit:\n")
        if question == "exit":
             exit(0)
        answer = answer_question(question,client,model)
        print(answer)
def answer_question(question,client, model):
        response = client.chat.completions.create(
            model=model, # model = "deployment_name".
            messages=[
                {"role": "system", "content": "You are an AI assistant extremely proficient in answering questions coming from different users. When possible, insert some humor into your responses."},
                {"role": "user", "content": "\n\nAnswer the following question:\n\n"+question},
            ]
        )
        return response.choices[0].message.content
           
if __name__ == "__main__":
    main()

