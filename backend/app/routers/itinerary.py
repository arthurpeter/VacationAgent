from app.core.database import get_checkpointer, get_db
from fastapi import APIRouter, Depends, HTTPException, Query
from app import schemas, models
from app.core.logger import get_logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, update
from authx import TokenPayload
from app.core.auth import access_token_header
from datetime import datetime
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, AIMessage
from app.services.agents.discovery_graph import generate_graph as generate_discovery_graph
from app.services.agents.itinerary_graph import generate_graph as generate_itinerary_graph
from app.services.agents.discovery_graph import stream_discovery_message
from app.services.agents.itinerary_graph import stream_itinerary_message


log = get_logger(__name__)

router = APIRouter(prefix="/itinerary", tags=["Itinerary"])

