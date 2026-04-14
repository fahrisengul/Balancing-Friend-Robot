from pvrecorder import PvRecorder


def debug_list_input_devices(log_fn):
    try:
        devices = PvRecorder.get_available_devices()
        log_fn(">>> [MIC DEBUG] Cihaz Listesi:")
        for i, name in enumerate(devices):
            print(f"    #{i}: {name}")
    except Exception as e:
        log_fn(f">>> [MIC DEBUG ERROR] {type(e).__name__}: {e}")


def select_default_input_device(current_index, log_fn):
    try:
        devices = PvRecorder.get_available_devices()

        if current_index is not None and current_index >= 0:
            if current_index < len(devices):
                log_fn(f">>> [MIC ACTIVE] Manuel seçim: #{current_index} {devices[current_index]}")
                return current_index

        if not devices:
            log_fn(">>> [MIC ACTIVE] Kayıt cihazı bulunamadı, default (-1) kullanılacak.")
            return -1

        preferred_idx = None
        preferred_keywords = [
            "mikrofon",
            "microphone",
            "macbook pro mikrofonu",
            "internal",
            "built-in",
        ]
        avoid_keywords = [
            "speaker",
            "hoparlor",
            "hoparlör",
            "output",
            "kulaklik cikisi",
            "kulaklık çıkışı",
        ]

        for i, name in enumerate(devices):
            low = name.lower()

            if any(bad in low for bad in avoid_keywords):
                continue

            if any(key in low for key in preferred_keywords):
                preferred_idx = i
                break

        if preferred_idx is None:
            preferred_idx = 0

        log_fn(f">>> [MIC ACTIVE] Otomatik seçim: #{preferred_idx} {devices[preferred_idx]}")
        return preferred_idx

    except Exception as e:
        log_fn(f">>> [MIC SELECT ERROR] {type(e).__name__}: {e}")
        return -1
