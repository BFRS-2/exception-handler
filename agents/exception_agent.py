from langchain.agents import initialize_agent, Tool
from langchain.llms import OpenAI
from tools.shipment_tools import resolve_exception, recommend_action
import os

# Wrapper functions for LangChain tools

def resolve_exception_tool(input_str):
    # Simple parsing: expects input like "type:context"
    if ':' in input_str:
        exception_type, context = input_str.split(':', 1)
        return resolve_exception(exception_type.strip(), context.strip())
    else:
        return "Please provide input as 'exception_type: context'."

def recommend_action_tool(input_str):
    if ':' in input_str:
        exception_type, context = input_str.split(':', 1)
        return recommend_action(exception_type.strip(), context.strip())
    else:
        return "Please provide input as 'exception_type: context'."

# The OpenAI LLM will automatically use the OPENAI_API_KEY from the environment
llm = OpenAI(temperature=0)

tools = [
    Tool(
        name="ResolveException",
        func=resolve_exception_tool,
        description="Resolves shipment exceptions. Input as 'exception_type: context'."
    ),
    Tool(
        name="RecommendAction",
        func=recommend_action_tool,
        description="Recommends the best next action for a shipment exception. Input as 'exception_type: context'."
    ),
]

agent = initialize_agent(
    tools,
    llm,
    agent="zero-shot-react-description",
    verbose=True
) 