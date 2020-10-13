from typing import List
import os

import uvicorn
from fastapi import FastAPI, Depends
from pydantic import BaseModel

from model import TextPairClassificationModel, get_colibert

app = FastAPI(root_path=os.getenv('API_ROOT_PATH'))


class PredictionInput(BaseModel):
    queries: List[str]
    contexts: List[str]


@app.post('/predict')
def predict(inp: PredictionInput, model: TextPairClassificationModel = Depends(get_colibert)):
    return model.all_pairs(inp.queries, inp.contexts).tolist()


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8080)
