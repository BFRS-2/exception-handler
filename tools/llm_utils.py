from langchain.llms import OpenAI

def get_llm_response(prompt):
    llm = OpenAI(temperature=0.2)
    return llm(prompt) 