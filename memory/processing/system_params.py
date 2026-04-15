from memory.storage.db import get_connection


class SystemParams:

    @staticmethod
    def get_param(key: str, default=None):
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT param_value FROM system_params WHERE param_key = ?",
            (key,)
        )
        row = cur.fetchone()
        conn.close()

        if row:
            return row[0]

        return default

    @staticmethod
    def set_param(key: str, value: str):
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO system_params (param_key, param_value)
            VALUES (?, ?)
            ON CONFLICT(param_key)
            DO UPDATE SET
                param_value = excluded.param_value,
                updated_at = CURRENT_TIMESTAMP
        """, (key, str(value)))

        conn.commit()
        conn.close()

    @staticmethod
    def get_audio_config():
        return {
            "input_name": SystemParams.get_param("audio_input_device_name"),
            "input_index": SystemParams.get_param("audio_input_device_index"),
            "output_mode": SystemParams.get_param("audio_output_mode", "system_default"),
            "output_name": SystemParams.get_param("audio_output_device_name"),
        }
