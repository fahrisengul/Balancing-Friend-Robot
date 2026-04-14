class MemoryWriter:
    def __init__(self, memory_manager):
        self.memory = memory_manager

    def process(self, text: str):
        # Burada filtre/kuralların varsa koru
        if not text or len(text.strip()) < 2:
            return
        # İstersen DB’ye “conversation raw” yazımı burada yapabilirsin
        pass
