data/
  meb_curriculum/
  gemini_chunks/
  study_guides/



  python ingest_corpus.py \
  --input_dirs data/meb_curriculum data/gemini_chunks data/study_guides \
  --output_index memory/faiss.index \
  --output_meta memory/faiss_meta.jsonl


  Bu sürüm ne sağlar?
	•	Elle tek tek chunk yazma işini büyük ölçüde kaldırır
	•	JSON chunk’larını doğrudan içeri alır
	•	Düz metinleri otomatik parçalar
	•	Metadata üretir
	•	Deduplicate yapar
	•	FAISS + jsonl çıktısı üretir

Sonraki en doğru adım

Bu script’i çalıştırdıktan sonra memory/faiss.index ve memory/faiss_meta.jsonl oluşacak.
Sonra retriever tarafında:
	•	metadata filter
	•	topic-aware rerank
	•	subject filter
	•	confidence tuning

ince ayarına geçeriz.
