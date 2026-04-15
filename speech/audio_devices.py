import pvrecorder
from memory.processing.system_params import SystemParams


def list_audio_devices():
    devices = pvrecorder.PvRecorder.get_available_devices()

    print(">>> [MIC DEBUG] Cihaz Listesi:")
    for i, d in enumerate(devices):
        print(f"    #{i}: {d}")

    return devices


def find_device_by_name(devices, name):
    if not name:
        return None

    for i, d in enumerate(devices):
        if name.lower() in d.lower():
            return i

    return None


def select_input_device():
    devices = list_audio_devices()

    config = SystemParams.get_audio_config()

    preferred_name = config.get("input_name")
    preferred_index = config.get("input_index")

    # 1) isimle eşleştir
    index = find_device_by_name(devices, preferred_name)
    if index is not None:
        print(f">>> [MIC SELECT] İsim ile seçildi: #{index} {devices[index]}")
        return index

    # 2) index fallback
    if preferred_index is not None:
        try:
            idx = int(preferred_index)
            if 0 <= idx < len(devices):
                print(f">>> [MIC SELECT] Index ile seçildi: #{idx} {devices[idx]}")
                return idx
        except Exception:
            pass

    # 3) otomatik seçim
    print(">>> [MIC SELECT] Otomatik seçim (fallback)")

    for i, d in enumerate(devices):
        if "macbook" in d.lower():
            print(f">>> [MIC AUTO] #{i} {d}")
            return i

    print(">>> [MIC AUTO] Default index 0")
    return 0


# =========================================================
# Backward-compatible wrappers
# speech_engine.py eski isimleri kullanıyorsa bozulmasın
# =========================================================

def debug_list_input_devices(log_fn=None):
    devices = pvrecorder.PvRecorder.get_available_devices()

    if log_fn:
        log_fn(">>> [MIC DEBUG] Cihaz Listesi:")
    else:
        print(">>> [MIC DEBUG] Cihaz Listesi:")

    for i, d in enumerate(devices):
        print(f"    #{i}: {d}")

    return devices


def select_default_input_device(current_index=None, log_fn=None):
    devices = pvrecorder.PvRecorder.get_available_devices()
    config = SystemParams.get_audio_config()

    preferred_name = config.get("input_name")
    preferred_index = config.get("input_index")

    # 1) SQL'den isim
    index = find_device_by_name(devices, preferred_name)
    if index is not None:
        msg = f">>> [MIC ACTIVE] SQL isim ile seçim: #{index} {devices[index]}"
        if log_fn:
            log_fn(msg)
        else:
            print(msg)
        return index

    # 2) SQL'den index
    if preferred_index is not None:
        try:
            idx = int(preferred_index)
            if 0 <= idx < len(devices):
                msg = f">>> [MIC ACTIVE] SQL index ile seçim: #{idx} {devices[idx]}"
                if log_fn:
                    log_fn(msg)
                else:
                    print(msg)
                return idx
        except Exception:
            pass

    # 3) Manuel verilmiş index
    if current_index is not None and current_index >= 0:
        try:
            if current_index < len(devices):
                msg = f">>> [MIC ACTIVE] Manuel seçim: #{current_index} {devices[current_index]}"
                if log_fn:
                    log_fn(msg)
                else:
                    print(msg)
                return current_index
        except Exception:
            pass

    # 4) Otomatik fallback
    for i, d in enumerate(devices):
        if "macbook" in d.lower():
            msg = f">>> [MIC ACTIVE] Otomatik seçim: #{i} {d}"
            if log_fn:
                log_fn(msg)
            else:
                print(msg)
            return i

    msg = ">>> [MIC ACTIVE] Otomatik seçim: #0"
    if log_fn:
        log_fn(msg)
    else:
        print(msg)
    return 0
