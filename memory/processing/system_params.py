from memory.storage.db import get_connection


class SystemParams:

    @staticmethod
    def get_param(key: str, default=None):
        try:
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
    def set_param(key: str, value: str):
        try:
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO system_params (param_key, param_value)
                    VALUES (?, ?)
                    ON CONFLICT(param_key) DO UPDATE SET
                        param_value = excluded.param_value,
                        updated_at = CURRENT_TIMESTAMP
                """, (key, value))
                conn.commit()
        except Exception as e:
            print(f">>> [SET PARAM ERROR] {e}")

    @staticmethod
    def get_audio_config():
        return {
            "input_name": SystemParams.get_param("audio_input_device_name", None),
            "output_mode": SystemParams.get_param("audio_output_mode", "system_default"),
            "output_name": SystemParams.get_param("audio_output_device_name", None),
        }
