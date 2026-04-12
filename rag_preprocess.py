import json
import uuid

INPUT_FILE = "chunks_v1.json"
OUTPUT_FILE = "chunks_v2.json"


def shorten_text(text, max_words=60):
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words])


def build_semantic_id(item):
    topic = item["topic"].lower().replace(" ", "_")
    ctype = item["chunk_type"]
    return f"math.{topic}.{ctype}.{uuid.uuid4().hex[:6]}"


def enrich_chunk(item):
    item["id"] = build_semantic_id(item)

    item["content"] = shorten_text(item["content"])

    # intent tags
    type_map = {
        "definition": ["nedir", "tanım"],
        "simple_explanation": ["anlat", "açıkla"],
        "example": ["örnek", "nasıl çözülür"],
        "common_mistake": ["hata", "yanlış"],
        "study_tip": ["nasıl çalışılır", "taktik"],
        "relation": ["ilişki", "bağlantı"],
        "exam_guidance": ["sınav", "nasıl çıkar"],
        "exam_strategy": ["strateji", "nasıl çözülür"]
    }

    item["intent_tags"] = type_map.get(item["chunk_type"], [])

    # importance
    importance_map = {
        "definition": 1.0,
        "simple_explanation": 1.0,
        "example": 0.9,
        "common_mistake": 0.95,
        "study_tip": 0.8,
        "relation": 0.7,
        "exam_guidance": 0.9,
        "exam_strategy": 0.85
    }

    item["embedding_priority"] = importance_map.get(item["chunk_type"], 0.7)

    return item


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    processed = [enrich_chunk(item) for item in data]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(processed, f, ensure_ascii=False, indent=2)

    print("DONE →", OUTPUT_FILE)


if __name__ == "__main__":
    main()
