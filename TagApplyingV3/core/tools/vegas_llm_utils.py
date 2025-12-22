import os
from dotenv import load_dotenv
from pyvegas.helpers.utils import set_proxy
from pyvegas.langx.llm import VegasChatLLM

set_proxy()
load_dotenv()

context_name = os.getenv("context_name")
usecase_name = os.getenv("usecase_name")

class VegasLLMWrapper:
    def __init__(self, context_name=context_name, usecase_name=usecase_name):
        self.context_name = context_name
        self.usecase_name = usecase_name
        self.llm = VegasChatLLM(context_name=context_name, usecase_name=usecase_name,max_output_tokens=8000)

    # def invoke(self, prompt: str,json_schema):
    #     structured_llm = self.llm.with_structured_output(json_schema)
    #     result = structured_llm.invoke(prompt)
    #     with open("debug_llm_output.json", "w", encoding="utf-8") as f:
    #         f.write(str(result)+ str(type(result)))
    #     # If result is an object (e.g., AIMessage), extract .content, else return as is
    #     if hasattr(result, 'content'):
    #         return result.content
    #     return str(result)
    
    def invoke(self, prompt: str):
        result = self.llm.invoke(prompt)
        # If result is an object (e.g., AIMessage), extract .content, else return as is
        if hasattr(result, 'content'):
            return result.content
        return str(result)
    

