#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ingest_corpus.py

Amaç:
- Korpus klasörlerinden metinleri toplamak
- Otomatik chunk etmek
- Metadata üretmek
- Embedding alıp FAISS index oluşturmak
- Metadata'yı jsonl olarak kaydetmek

Örnek kullanım:
python ingest_corpus.py \
  --input_dirs data/meb_curriculum data/gemini_chunks data/study_guides \
  --output_index memory/faiss.index \
  --output_meta memory/faiss_meta.jsonl

Not:
- JSON dosyalarında ya tek obje, ya liste, ya da {"items":[...]} beklenir.
- JSON item içinde "content" veya "text" alanı aranır.
- "subject", "topic", "chunk_type", "keywords", "intent_tags", "embedding_priority"
  gibi alanlar varsa korunur.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


SUPPORTED_EXTENSIONS = {".txt", ".md", ".json", ".jsonl"}


@dataclass
class ChunkRecord:
    vector_id: int
    id: str
    source_file: str
    source_type: str
    subject: str
    grade: Optional[int]
    topic: str
    chunk_type: str
    title: str
    content: str
    keywords: List[str]
    difficulty: str
    audience: str
    intent_tags: List[str]
    embedding_priority: float


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def slugify(text: str) -> str:
    t = (text or "").strip().lower()
    t = (
        t.replace("ı", "i")
        .replace("ğ", "g")
        .replace("ş", "s")
        .replace("ç", "c")
        .replace("ö", "o")
        .replace("ü", "u")
    )
    t = re.sub(r"[^a-z0-9]+", "_", t)
    return t.strip("_") or "unknown"


def stable_id(*parts: str) -> str:
    raw = "||".join(parts)
    digest = hashlib.md5(raw.encode("utf-8")).hexdigest()[:10]
    return digest


def split_paragraphs(text: str) -> List[str]:
    parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return parts


def split_sentences(text: str) -> List[str]:
    text = normalize_text(text)
    if not text:
        return []
    # Türkçe için basit ama pratik bölme
    pieces = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in pieces if p.strip()]


def chunk_sentences(
    text: str,
    min_words: int = 40,
    max_words: int = 90,
) -> List[str]:
    sentences = split_sentences(text)
    if not sentences:
        return []

    chunks: List[str] = []
    current: List[str] = []
    current_words = 0

    for sent in sentences:
        sent_words = len(sent.split())

        # Çok uzun tek cümleyi doğrudan al
        if sent_words >= max_words:
            if current:
                chunks.append(" ".join(current).strip())
                current = []
                current_words = 0
            chunks.append(sent.strip())
            continue

        if current_words + sent_words <= max_words:
            current.append(sent)
            current_words += sent_words
        else:
            if current:
                chunks.append(" ".join(current).strip())
            current = [sent]
            current_words = sent_words

    if current:
        chunks.append(" ".join(current).strip())

    # Çok kısa chunk'ları birleştir
    merged: List[str] = []
    for chunk in chunks:
        if not merged:
            merged.append(chunk)
            continue

        if len(chunk.split()) < min_words and len((merged[-1] + " " + chunk).split()) <= max_words + 20:
            merged[-1] = (merged[-1] + " " + chunk).strip()
        else:
            merged.append(chunk)

    return [c for c in merged if c.strip()]


def infer_subject_from_path(path: Path) -> str:
    p = str(path).lower()
    if "mat" in p or "matematik" in p:
        return "Matematik"
    if "turkce" in p or "türkçe" in p:
        return "Türkçe"
    if "fen" in p:
        return "Fen Bilimleri"
    if "inkilap" in p or "inkılap" in p:
        return "T.C. İnkılap Tarihi ve Atatürkçülük"
    if "din" in p:
        return "Din Kültürü ve Ahlak Bilgisi"
    if "ingilizce" in p or "english" in p:
        return "İngilizce"
    return "Genel"


def infer_source_type(path: Path) -> str:
    p = str(path).lower()
    if "meb" in p:
        return "meb_aligned"
    if "gemini" in p:
        return "gemini_generated"
    return "local_corpus"


def infer_chunk_type(title: str, content: str) -> str:
    blob = f"{title} {content}".lower()
    if "yaygın hata" in blob or "common mistake" in blob:
        return "common_mistake"
    if "çalışma" in blob or "taktik" in blob or "öneri" in blob:
        return "study_tip"
    if "strateji" in blob:
        return "exam_strategy"
    if "örnek" in blob:
        return "example"
    if "tanım" in blob or "nedir" in blob:
        return "definition"
    if "ilişki" in blob:
        return "relation"
    if "sınav" in blob or "lgs" in blob:
        return "exam_guidance"
    return "simple_explanation"


def infer_intent_tags(chunk_type: str) -> List[str]:
    mapping = {
        "definition": ["nedir", "tanım"],
        "simple_explanation": ["anlat", "açıkla"],
        "example": ["örnek", "nasıl çözülür"],
        "common_mistake": ["hata", "yanlış"],
        "study_tip": ["nasıl çalışılır", "taktik"],
        "relation": ["ilişki", "bağlantı"],
        "exam_guidance": ["sınav", "nasıl çıkar"],
        "exam_strategy": ["strateji", "takti̇k"],
    }
    return mapping.get(chunk_type, [])


def infer_embedding_priority(chunk_type: str) -> float:
    mapping = {
        "definition": 1.0,
        "simple_explanation": 1.0,
        "example": 0.9,
        "common_mistake": 0.95,
        "study_tip": 0.85,
        "relation": 0.75,
        "exam_guidance": 0.9,
        "exam_strategy": 0.9,
    }
    return mapping.get(chunk_type, 0.7)


def extract_keywords(text: str, top_k: int = 6) -> List[str]:
    text = normalize_text(text).lower()
    text = (
        text.replace("ı", "i")
        .replace("ğ", "g")
        .replace("ş", "s")
        .replace("ç", "c")
        .replace("ö", "o")
        .replace("ü", "u")
    )
    tokens = re.findall(r"[a-z0-9]{3,}", text)
    stop = {
        "bir", "ile", "olan", "gibi", "icin", "ama", "daha", "sonra", "kadar",
        "olan", "gore", "veya", "bunu", "soru", "sayi", "sayilar", "konu",
        "cunku", "gerekir", "olur", "olarak", "yani", "icin", "gore", "hem",
        "her", "gibi", "olan", "eden", "ise", "ile", "ve", "bu", "da", "de",
    }
    freq: Dict[str, int] = {}
    for tok in tokens:
        if tok in stop:
            continue
        freq[tok] = freq.get(tok, 0) + 1

    ranked = sorted(freq.items(), key=lambda x: (-x[1], x[0]))
    return [k for k, _ in ranked[:top_k]]


def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def load_json_records(path: Path) -> List[Dict[str, Any]]:
    raw = path.read_text(encoding="utf-8", errors="ignore").strip()
    if not raw:
        return []

    # markdown temizliği
    raw = raw.replace("```json", "").replace("```", "").strip()

    if path.suffix.lower() == ".jsonl":
        rows = []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
        return rows

    data = json.loads(raw)

    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]

    if isinstance(data, dict):
        if isinstance(data.get("items"), list):
            return [x for x in data["items"] if isinstance(x, dict)]
        return [data]

    return []


def make_records_from_json(path: Path, vector_start: int) -> Tuple[List[ChunkRecord], int]:
    rows = load_json_records(path)
    records: List[ChunkRecord] = []
    vector_id = vector_start

    for row in rows:
        content = normalize_text(str(row.get("content") or row.get("text") or ""))
        if not content:
            continue

        subject = row.get("subject") or infer_subject_from_path(path)
        topic = row.get("topic") or path.stem
        title = row.get("title") or topic
        chunk_type = row.get("chunk_type") or infer_chunk_type(title, content)
        keywords = row.get("keywords") or extract_keywords(f"{title} {content}")
        intent_tags = row.get("intent_tags") or infer_intent_tags(chunk_type)
        difficulty = row.get("difficulty") or "medium"
        audience = row.get("audience") or "student"
        source_type = row.get("source_type") or infer_source_type(path)
        grade = row.get("grade")
        embedding_priority = float(row.get("embedding_priority", infer_embedding_priority(chunk_type)))

        rec_id = row.get("id") or f"{slugify(subject)}.{slugify(topic)}.{slugify(chunk_type)}.{stable_id(path.name, title, content)}"

        records.append(
            ChunkRecord(
                vector_id=vector_id,
                id=rec_id,
                source_file=str(path),
                source_type=source_type,
                subject=subject,
                grade=grade,
                topic=topic,
                chunk_type=chunk_type,
                title=title,
                content=content,
                keywords=keywords,
                difficulty=difficulty,
                audience=audience,
                intent_tags=intent_tags,
                embedding_priority=embedding_priority,
            )
        )
        vector_id += 1

    return records, vector_id


def make_records_from_text(path: Path, vector_start: int) -> Tuple[List[ChunkRecord], int]:
    text = normalize_text(read_text_file(path))
    if not text:
        return [], vector_start

    subject = infer_subject_from_path(path)
    source_type = infer_source_type(path)

    paragraphs = split_paragraphs(text)
    records: List[ChunkRecord] = []
    vector_id = vector_start

    for i, para in enumerate(paragraphs, start=1):
        chunks = chunk_sentences(para, min_words=35, max_words=85)

        for j, chunk in enumerate(chunks, start=1):
            title = f"{path.stem} bölüm {i}"
            chunk_type = infer_chunk_type(title, chunk)
            keywords = extract_keywords(f"{title} {chunk}")
            intent_tags = infer_intent_tags(chunk_type)
            topic = path.stem.replace("_", " ").replace("-", " ").strip()

            rec_id = f"{slugify(subject)}.{slugify(topic)}.{slugify(chunk_type)}.{stable_id(path.name, str(i), str(j), chunk)}"

            records.append(
                ChunkRecord(
                    vector_id=vector_id,
                    id=rec_id,
                    source_file=str(path),
                    source_type=source_type,
                    subject=subject,
                    grade=8 if subject != "Genel" else None,
                    topic=topic,
                    chunk_type=chunk_type,
                    title=title,
                    content=chunk,
                    keywords=keywords,
                    difficulty="medium",
                    audience="lgs_student" if subject != "Genel" else "general_user",
                    intent_tags=intent_tags,
                    embedding_priority=infer_embedding_priority(chunk_type),
                )
            )
            vector_id += 1

    return records, vector_id


def iter_supported_files(input_dirs: List[str]) -> Iterable[Path]:
    for input_dir in input_dirs:
        root = Path(input_dir)
        if not root.exists():
            print(f"[WARN] Klasör bulunamadı: {root}")
            continue

        for path in root.rglob("*"):
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
                yield path


def build_records(input_dirs: List[str]) -> List[ChunkRecord]:
    records: List[ChunkRecord] = []
    vector_id = 0

    for path in iter_supported_files(input_dirs):
        try:
            if path.suffix.lower() in {".json", ".jsonl"}:
                new_records, vector_id = make_records_from_json(path, vector_id)
            else:
                new_records, vector_id = make_records_from_text(path, vector_id)

            if new_records:
                print(f"[OK] {path} -> {len(new_records)} chunk")
                records.extend(new_records)
            else:
                print(f"[SKIP] {path} -> içerik bulunamadı")
        except Exception as e:
            print(f"[ERROR] {path}: {e}")

    return deduplicate_records(records)


def deduplicate_records(records: List[ChunkRecord]) -> List[ChunkRecord]:
    seen = set()
    clean: List[ChunkRecord] = []

    for rec in records:
        key = normalize_text(rec.content)
        if not key:
            continue
        if key in seen:
            continue
        seen.add(key)
        clean.append(rec)

    # vector_id'leri baştan düzenle
    for idx, rec in enumerate(clean):
        rec.vector_id = idx

    return clean


def build_embeddings(records: List[ChunkRecord], model_name: str) -> np.ndarray:
    if not records:
        raise ValueError("Embedding için kayıt bulunamadı.")

    model = SentenceTransformer(model_name)

    texts = [rec.content for rec in records]
    vectors = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True,
    ).astype("float32")

    return vectors


def write_outputs(
    records: List[ChunkRecord],
    vectors: np.ndarray,
    output_index: str,
    output_meta: str,
):
    dim = vectors.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(vectors)

    output_index_path = Path(output_index)
    output_meta_path = Path(output_meta)

    output_index_path.parent.mkdir(parents=True, exist_ok=True)
    output_meta_path.parent.mkdir(parents=True, exist_ok=True)

    faiss.write_index(index, str(output_index_path))

    with open(output_meta_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(asdict(rec), ensure_ascii=False) + "\n")

    print(f"[DONE] FAISS index: {output_index_path}")
    print(f"[DONE] Metadata:    {output_meta_path}")
    print(f"[DONE] Toplam chunk: {len(records)}")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input_dirs",
        nargs="+",
        required=True,
        help="Korpus klasörleri",
    )
    parser.add_argument(
        "--output_index",
        default="memory/faiss.index",
        help="FAISS index çıktı yolu",
    )
    parser.add_argument(
        "--output_meta",
        default="memory/faiss_meta.jsonl",
        help="Metadata jsonl çıktı yolu",
    )
    parser.add_argument(
        "--embedding_model",
        default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        help="Embedding modeli",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    print("[INFO] Kayıtlar oluşturuluyor...")
    records = build_records(args.input_dirs)

    if not records:
        print("[FATAL] Hiç kayıt üretilemedi.")
        sys.exit(1)

    print(f"[INFO] Deduplicate sonrası chunk sayısı: {len(records)}")
    print("[INFO] Embedding oluşturuluyor...")
    vectors = build_embeddings(records, args.embedding_model)

    print("[INFO] FAISS çıktıları yazılıyor...")
    write_outputs(
        records=records,
        vectors=vectors,
        output_index=args.output_index,
        output_meta=args.output_meta,
    )


if __name__ == "__main__":
    main()
