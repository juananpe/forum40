import itertools
from typing import List

from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification, \
    AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F
import numpy as np


class TextPairClassificationModel:
    def __init__(self, model_name: str):
        self.tokenizer: DistilBertTokenizerFast = AutoTokenizer.from_pretrained(model_name, use_fast=True)
        self.model: DistilBertForSequenceClassification = AutoModelForSequenceClassification.from_pretrained(model_name)

    def all_pairs(self, texts_a: List[str], texts_b: List[str]) -> np.ndarray:
        text_pairs = itertools.product(texts_a, texts_b)
        tokens = self.tokenizer(*list(zip(*text_pairs)), padding=True, truncation='longest_first', max_length=128, return_tensors='pt')
        outputs, = self.model(**tokens)
        preds = F.softmax(outputs, dim=-1)
        return torch.reshape(preds[:, 1], (len(texts_a), len(texts_b))).detach().numpy()


colibert = TextPairClassificationModel('ietz/comment-linking-distilbert-base-german-cased')


def get_colibert():
    return colibert
