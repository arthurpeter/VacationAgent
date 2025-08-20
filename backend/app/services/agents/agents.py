from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from app.services.agents.memory import State
from app.services.agents.prompts import *
#from langchain_google_genai import GoogleGenerativeAI


load_dotenv()

llm = ChatOpenAI(model="gpt-4o", temperature=0)

def information_collector(state: State):
    instructions = information_collector_instructions
    

if __name__ == "__main__":
    print("This module is not meant to be run directly. It provides the Agent class.")