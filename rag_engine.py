import re
from pathlib import Path


class RAGEngine:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.chunks = self._load_chunks()

    def _load_chunks(self):
        if not self.file_path.exists():
            return []

        text = self.file_path.read_text(encoding="utf-8")
        raw_blocks = re.split(r"\n\s*\n", text)

        chunks = []
        for block in raw_blocks:
            cleaned = block.strip()
            if cleaned:
                chunks.append(cleaned)

        return chunks

    def _tokenize(self, text: str):
        text = (text or "").lower()
        words = re.findall(r"[ก-๙a-zA-Z0-9]+", text)
        return [w for w in words if len(w) >= 2]

    def search(self, query: str, top_k: int = 5):
        if not self.chunks:
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return self.chunks[:top_k]

        scored = []

        for chunk in self.chunks:
            chunk_lower = chunk.lower()
            score = 0

            for token in query_tokens:
                if token in chunk_lower:
                    score += 3

            # boost ถ้าคำถามตรงกับชื่อเมนู/โปร/ราคา
            if "เมนู" in query and "เมนู" in chunk:
                score += 2
            if "ราคา" in query and "ราคา" in chunk:
                score += 2
                score += 4
            if "ไพ่" in query and ("ไพ่" in chunk or "Tarot" in chunk):
                score += 4

            if score > 0:
                scored.append((score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)

        if not scored:
            return self.chunks[:top_k]

        return [chunk for _, chunk in scored[:top_k]]
