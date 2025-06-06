import logging
import os
from http.client import HTTPResponse
from typing import Dict

from dotenv import load_dotenv
from fastapi import HTTPException, APIRouter, Request,Body
from fastapi.responses import JSONResponse
from langchain_community.chat_models import ChatDeepInfra
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_together import ChatTogether
from langchain_mistralai import ChatMistralAI
from pydantic import BaseModel

logger = logging.getLogger("basic_router")
load_dotenv()
router = APIRouter()
llm_instances = {}

llm_providers = {
    "ollama": ChatOllama,
    "groq": ChatGroq,
    "mistral":ChatMistralAI,
    "deepinfra":ChatDeepInfra,
    "together":ChatTogether,

}


api_providers = {
    "GROQ",
    "OPENAI",
    "GROK",
    "TOGETHER",
    "DEEPSEEK",
    "DEEPINFRA"
    "OPENROUTER"

}

class API_KEY_REQUEST(BaseModel):
    api_providers:str
    api_key : str



@router.post("/api/{api_provider}/{api_key}")
def set_api_provider(api_provider: str, api_key: str):
    if api_provider not in api_providers:
        raise HTTPException(status_code=404, detail="API Provider is Not Valid")
    else:
        os.environ[f"${api_provider}_API_KEY"] = api_key
        logger.info("API KEY SET")
        return HTTPException(status_code=200, detail="API KEY IS SET OK RESPONSE")


@router.get("/providers")
def get_llm_providers():
    logger.info("LLM providers requested")
    return JSONResponse(
        content={"providers": list(llm_providers.keys())},
        status_code=200
    )


from typing import Dict
from fastapi import Body, Request, HTTPException

@router.post("/providers", response_model=None)
async def choose_llm_provider(request: Request, body: Dict = Body(...)):
    llm_prov = body.get("llm_class")
    logger.info(f"Setting LLM provider: {llm_prov}")
    if llm_prov not in llm_providers:
        logger.warning(f"Invalid LLM provider requested: {llm_prov}")
        raise HTTPException(status_code=404, detail=f"LLM provider '{llm_prov}' not found")

    request.app.state.llm_class = llm_providers[llm_prov]
    logger.info(f"LLM provider '{llm_prov}' set successfully")

    return JSONResponse(
        content={"message": f"LLM provider '{llm_prov}' selected successfully"},
        status_code=200
    )


@router.post("/models", response_model=None)
async def choose_model(request: Request, body: Dict = Body(...)):
    model = body.get("model")
    logger.info(f"Setting model: {model}")

    llm_class = getattr(request.app.state, "llm_class", None)
    if llm_class is None:
        logger.warning("No LLM provider selected before requesting model")
        raise HTTPException(status_code=400, detail="No LLM provider selected")

    try:
        instance_key = f"{llm_class.__name__}_{model}"
        if instance_key not in llm_instances:
            llm_instances[instance_key] = llm_class(model=model)
            logger.info(f"Created new instance for {instance_key}")
        else:
            logger.info(f"Using existing instance for {instance_key}")
        request.app.state.llm_instance = llm_instances[instance_key]
        request.app.state.current_model = llm_instances[instance_key]
    except Exception as e:
        logger.error(f"Failed to instantiate model {model}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to instantiate model: {str(e)}")

    return JSONResponse(
        content={"message": f"Model '{model}' instantiated successfully"},
        status_code=200
    )
