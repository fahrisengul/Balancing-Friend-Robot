from memory.storage.db import get_connection

class SystemParams:

    @staticmethod
    def get_param(key: str, default=None):
        try:
            from memory.storage.db import get_connection

            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT param_value FROM system_params
                    WHERE param_key = ?
                """, (key,))
                row = cur.fetchone()

                if row and row[0] is not None:
                    return row[0]

                return default

        except Exception as e:
            print(f">>> [PARAM ERROR] {e}")
            return default

    @staticmethod
    def get_audio_config():
        return {
            "output_mode": SystemParams.get_param("audio_output_mode", "system_default"),
            "output_name": SystemParams.get_param("audio_output_device_name", None),
            "input_name": SystemParams.get_param("audio_input_device_name", None),
        }
