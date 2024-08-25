#!/usr/bin/env python
# pip install langchain langchain-openai "langserve[all]" fastapi uvicorn  pydantic==1.10.13
# export OPENAI_API_KEY='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'
# export LANGCHAIN_TRACING_V2="true"
# export LANGCHAIN_API_KEY='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'
# http://localhost:8000/docs
# http://localhost:8000/chain/playground/ 

from typing import List

from fastapi import FastAPI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langserve import add_routes

# 1. Create prompt template
system_template = "Translate the following into {language}:"
prompt_template = ChatPromptTemplate.from_messages([
    ('system', system_template),
    ('user', '{text}')
])

# 2. Create model
model = ChatOpenAI()

# 3. Create parser
parser = StrOutputParser()

# 4. Create chain
chain = prompt_template | model | parser


# 4. App definition
app = FastAPI(
  title="LangChain Server",
  version="1.0",
  description="A simple API server using LangChain's Runnable interfaces",
)

# 5. Adding chain route

add_routes(
    app,
    chain,
    path="/chain",
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)