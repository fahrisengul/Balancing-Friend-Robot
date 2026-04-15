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

    # 1️⃣ İsim ile eşleştir
    index = find_device_by_name(devices, preferred_name)
    if index is not None:
        print(f">>> [MIC SELECT] İsim ile seçildi: #{index} {devices[index]}")
        return index

    # 2️⃣ Index fallback
    if preferred_index is not None:
        try:
            idx = int(preferred_index)
            if 0 <= idx < len(devices):
                print(f">>> [MIC SELECT] Index ile seçildi: #{idx} {devices[idx]}")
                return idx
        except Exception:
            pass

    # 3️⃣ Otomatik seçim (fallback)
    print(">>> [MIC SELECT] Otomatik seçim (fallback)")

    for i, d in enumerate(devices):
        if "macbook" in d.lower():
            print(f">>> [MIC AUTO] #{i} {d}")
            return i

    print(">>> [MIC AUTO] Default index 0")
    return 0
