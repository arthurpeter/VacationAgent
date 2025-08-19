from dotenv import load_dotenv
from agents.utils import *
from langchain_openai import ChatOpenAI
#from langchain_google_genai import GoogleGenerativeAI


load_dotenv()

INPUT_FILE = "../io/input.txt"
OUTPUT_FILE = "../io/output.txt"



class Agent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)

    def template_function(self, input_data: str) -> str:
        # TODO change the prompt
        prompt = f"""
        Input data: {input_data}"
        """

        response = self.llm.invoke(prompt)
        return response.content.strip()
    
    def do_stuff(self):
        # TODO implement the logic for the data from the agent
        pass

if __name__ == "__main__":
    print("This module is not meant to be run directly. It provides the Agent class.")