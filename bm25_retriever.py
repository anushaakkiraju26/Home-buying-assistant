import re

from rank_bm25 import BM25Okapi


def tokenize(text: str) -> list[str]:
    return re.findall(r"\b[a-z0-9'-]+\b", text.lower())


class KeywordRetriever:
    def __init__(self, documents):
        self.documents = documents
        tokenized_documents = [
            tokenize(document.page_content)
            for document in documents
        ]
        self.index = BM25Okapi(tokenized_documents)

    def search(self, query: str, k: int = 20):
        query_tokens = tokenize(query)
        scores = self.index.get_scores(query_tokens)

        ranked_indexes = sorted(
            range(len(scores)),
            key=lambda index: scores[index],
            reverse=True,
        )[:k]

        return [
            (self.documents[index], float(scores[index]))
            for index in ranked_indexes
        ]