from typing import List
import os

from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

app = FastAPI(root_path=os.getenv('API_ROOT_PATH'))
model = SentenceTransformer('distiluse-base-multilingual-cased-v2')


def get_model():
    return model


class EncodingInput(BaseModel):
    texts: List[str]


@app.post('/encode')
def predict(inp: EncodingInput, model=Depends(get_model)):
    return model.encode(inp.texts, show_progress_bar=False).tolist()
