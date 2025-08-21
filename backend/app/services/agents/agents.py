from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
#from langchain_google_genai import GoogleGenerativeAI

from app.services.agents.memory import State
from app.services.agents.prompts import *
from langgraph.store.base import BaseStore

from app.services.agents.responses import InformationCollectorResponse
from app.utils.graph import generate_memory_from_db


load_dotenv()

llm = ChatOpenAI(model="gpt-4.1", temperature=0)

def information_collector(state: State, store: BaseStore) -> State:
    memory = store.get(namespace="user_trip_information", key=state.user_id)
    if not memory:
        # If no memory found, generate it from the database
        memory = generate_memory_from_db(state.user_id)
        store.put(namespace="user_trip_information", key=state.user_id, value=memory)
    else:
        memory = memory.value
    instructions = information_collector_prompt.format(
        memory=memory,
        user_query=state.user_query
    )

    structured_llm = llm.with_structured_output(InformationCollectorResponse)

    response = structured_llm(instructions)




    
    return state


if __name__ == "__main__":
    print("This module is not meant to be run directly. It provides the agent nodes.")
