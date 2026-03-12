from typing import Literal
from dotenv import load_dotenv

from app.services.agents.memory import State
from app.services.agents.prompts import *
from langgraph.store.base import BaseStore
from langgraph.graph import END

from app.services.agents.responses import ExtractionResult
from app.core.config import settings


load_dotenv()

llm = settings.llm

def information_collector(state: State) -> State:
    instructions = information_collector_prompt.format(
        memory="",
        user_query=state["messages"][-1]
    )

    structured_llm = llm.with_structured_output(ExtractionResult)

    response = structured_llm.invoke(instructions)
    extracted_data = response.value.model_dump()

    state["extracted_data"] = extracted_data
    return state

def should_get_more_info(state: State):
    if state["need_information"]:
        return END
    return "next_node"

if __name__ == "__main__":
    print("This module is not meant to be run directly. It provides the agent nodes.")
