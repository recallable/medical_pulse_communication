import os

from langchain.chat_models import init_chat_model
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_postgres import PGVector

from core.config import settings

embeddings = DashScopeEmbeddings(
    model="text-embedding-v1",
    dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"))

vector_store = PGVector(
    embeddings=embeddings,
    collection_name=settings.collection_name,
    connection=settings.database_vector_url,
    use_jsonb=True,
    create_extension=True,
)
llm = init_chat_model(
    model='qwen-flash',
    model_provider='openai',
    api_key=os.getenv('OPENAI_API_KEY'),
)
