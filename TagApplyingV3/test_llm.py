import os
from dotenv import load_dotenv
from pyvegas.helpers.utils import set_proxy
set_proxy()
load_dotenv()


# os.environ["ENVIRONMENT"] = "test"
os.environ['VEGAS_API_KEY'] = os.getenv("VEGAS_API_KEY")
os.environ["ENVIRONMENT"] = "test"
context_name = os.getenv("context_name")
usecase_name = os.getenv("usecase_name")

print(f"Context: {context_name}")
print(f"Usecase: {usecase_name}")

from pyvegas.langx.llm import VegasChatLLM

def get_vegas_llm():
    """Get the Vegas LLM instance."""
    return VegasChatLLM(context_name=context_name, usecase_name=usecase_name)


from langchain_core.tools import tool
model = get_vegas_llm()
print(model.invoke("Hello, how are you?"))


# @tool
# def get_add_function(x:int,y:int):
#     """Get the addition function."""
#     return x + y
# llm_with_tools = model.bind_tools([get_add_function])
# print(llm_with_tools.invoke("What is 2 + 2?"))