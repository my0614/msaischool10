"""
sentence-transformers 없이 transformers 직접 사용하는 임베딩 클래스.
huggingface-hub 버전 충돌 없이 동작.
"""

import torch
import numpy as np
from typing import List
from langchain_core.embeddings import Embeddings
from transformers import AutoTokenizer, AutoModel

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def _mean_pool(token_embeddings: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
    mask = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * mask, 1) / torch.clamp(mask.sum(1), min=1e-9)


class LocalEmbeddings(Embeddings):
    def __init__(self, model_name: str = MODEL_NAME):
        print(f"임베딩 모델 로딩: {model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.model.eval()

    def _encode(self, texts: List[str]) -> List[List[float]]:
        encoded = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt",
        )
        with torch.no_grad():
            output = self.model(**encoded)
        vectors = _mean_pool(output.last_hidden_state, encoded["attention_mask"])
        # L2 정규화
        vectors = torch.nn.functional.normalize(vectors, p=2, dim=1)
        return vectors.numpy().tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._encode(texts)

    def embed_query(self, text: str) -> List[float]:
        return self._encode([text])[0]
