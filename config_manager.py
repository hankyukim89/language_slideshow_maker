import json
import os

CONFIG_FILE = "config.json"

class ConfigManager:
    @staticmethod
    def load_config():
        default_config = {
            "font_size": 60,
            "font_name": "Arial",
            "bg_opacity": 0.5,
            "sentence_pause": 0.5,
            "slide_pause": 0.5,
            "tts_provider": "gTTS",
            "api_key": "",
            "tts_voice_id_1": "",
            "tts_voice_id_2": "",
            "tts_speed": 1.0,
            "bg_image_path": "",
            "lang1": "English",
            "lang2": "French"
        }
        
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    saved_config = json.load(f)
                    default_config.update(saved_config)
            except Exception as e:
                print(f"Error loading config: {e}")
        
        return default_config

    @staticmethod
    def save_config(config_data):
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(config_data, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")
