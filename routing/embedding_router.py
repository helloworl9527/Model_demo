import json
from pathlib import Path
from typing import Dict, List, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from schema import StructuredAuditTask


def _build_text(parsed: StructuredAuditTask) -> str:
    """将结构化审计内容展开为向量检索输入文本。"""
    chunks = []
    chunks.extend(parsed.objective)
    chunks.extend(parsed.focus_areas)
    chunks.extend(parsed.audit_objects)
    chunks.extend(parsed.scope.org_units)
    chunks.extend(parsed.scope.datasets)
    if parsed.scope.period:
        chunks.append(parsed.scope.period)
    return " ".join(chunks)


class EmbeddingRouter:
    """使用 TF-IDF 向量相似度进行任务类型匹配。"""

    def __init__(self, profiles_path: str):
        """加载任务画像并构建向量化索引。"""
        data = json.loads(Path(profiles_path).read_text(encoding="utf-8"))
        self.task_types = [x["task_type"] for x in data]
        corpus = [x["profile"] for x in data]
        self.vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(2, 4))
        self.profile_matrix = self.vectorizer.fit_transform(corpus)

    def route(self, parsed: StructuredAuditTask, threshold: float = 0.18) -> Dict[str, float]:
        """返回超过阈值的任务类型及相似度分数。"""
        query = _build_text(parsed)
        qv = self.vectorizer.transform([query])
        sims = cosine_similarity(qv, self.profile_matrix)[0]
        result: Dict[str, float] = {}
        for i, s in enumerate(sims):
            if s >= threshold:
                result[self.task_types[i]] = float(s)
        return result