from typing import Literal
from dotenv import load_dotenv
#from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

from app.services.agents.memory import State
from app.services.agents.prompts import *
from langgraph.store.base import BaseStore
from langgraph.graph import END

from app.services.agents.responses import InformationCollectorResponse
from app.utils.graph import generate_memory_from_db, update_memory


load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

def information_collector(state: State, store: BaseStore) -> State:
    memory = store.get(namespace="user_trip_information", key=state["user_id"])
    if not memory:
        # If no memory found, generate it from the database
        memory = generate_memory_from_db(state["user_id"], test_mode=True)
        store.put(namespace="user_trip_information", key=state["user_id"], value=memory)
    else:
        memory = memory.value
    instructions = information_collector_prompt.format(
        memory=memory,
        user_query=state["user_query"]
    )

    structured_llm = llm.with_structured_output(InformationCollectorResponse)

    response = structured_llm.invoke(instructions)

    if not update_memory(state["user_id"], store, response):
        state["need_information"] = True
        state["llm_query"] = response.follow_up_question

    return state

def should_get_more_info(state: State):
    if state["need_information"]:
        return END
    return "next_node"

if __name__ == "__main__":
    print("This module is not meant to be run directly. It provides the agent nodes.")
