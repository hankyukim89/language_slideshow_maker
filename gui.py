import tkinter
import customtkinter as ctk
from tkinter import filedialog, font
import threading
import os
import pygame
import utils
from config_manager import ConfigManager
from logic import SlideshowConfig, SlideshowGenerator
from PIL import Image, ImageTk

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent, config, callback_save):
        super().__init__(parent)
        self.config = config
        self.callback_save = callback_save
        self.title("Advanced Settings")
        self.geometry("900x700")
        
        # Initialize pygame mixer for audio preview
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Tab View
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.tabview.add("Visuals")
        self.tabview.add("Audio & TTS")
        
        self.setup_visuals_tab()
        self.setup_audio_tab()

        # Action Buttons
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        self.btn_save = ctk.CTkButton(self.btn_frame, text="Save Settings", command=self.save_settings, fg_color="green")
        self.btn_save.pack(side="right", padx=10)
        
        self.btn_cancel = ctk.CTkButton(self.btn_frame, text="Cancel", command=self.destroy, fg_color="red")
        self.btn_cancel.pack(side="right", padx=10)

    def setup_visuals_tab(self):
        tab = self.tabview.tab("Visuals")
        tab.grid_columnconfigure(1, weight=1)

        # Font Selection
        ctk.CTkLabel(tab, text="Font:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.fonts = sorted(font.families())
        self.var_font = ctk.StringVar(value=self.config.get("font_name", "Arial"))
        self.combo_font = ctk.CTkComboBox(tab, values=self.fonts, variable=self.var_font, command=self.update_font_preview)
        self.combo_font.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(tab, text="Size:").grid(row=0, column=2, padx=10, pady=10, sticky="w")
        self.var_font_size = ctk.IntVar(value=self.config.get("font_size", 60))
        self.slider_font_size = ctk.CTkSlider(tab, from_=20, to=150, variable=self.var_font_size, command=self.update_font_preview)
        self.slider_font_size.grid(row=0, column=3, padx=10, pady=10, sticky="ew")
        self.lbl_font_size = ctk.CTkLabel(tab, textvariable=self.var_font_size)
        self.lbl_font_size.grid(row=0, column=4, padx=5, pady=10)

        # Font Preview Area
        self.frame_font_preview = ctk.CTkFrame(tab, height=100)
        self.frame_font_preview.grid(row=1, column=0, columnspan=5, padx=10, pady=10, sticky="ew")
        self.lbl_font_preview = ctk.CTkLabel(self.frame_font_preview, text="The quick brown fox jumps over the lazy dog.")
        self.lbl_font_preview.pack(expand=True, fill="both", padx=10, pady=10)

        # Background & Opacity
        ctk.CTkLabel(tab, text="Background Image:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.var_bg_path = ctk.StringVar(value=self.config.get("bg_image_path", ""))
        self.entry_bg = ctk.CTkEntry(tab, textvariable=self.var_bg_path)
        self.entry_bg.grid(row=2, column=1, columnspan=3, padx=10, pady=10, sticky="ew")
        self.btn_bg = ctk.CTkButton(tab, text="Browse", command=self.select_bg, width=60)
        self.btn_bg.grid(row=2, column=4, padx=10, pady=10)

        ctk.CTkLabel(tab, text="Opacity (Overlay):").grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.var_opacity = ctk.DoubleVar(value=self.config.get("bg_opacity", 0.5))
        self.slider_opacity = ctk.CTkSlider(tab, from_=0.0, to=1.0, variable=self.var_opacity, command=self.update_visual_preview)
        self.slider_opacity.grid(row=3, column=1, columnspan=3, padx=10, pady=10, sticky="ew")

        # Visual Preview Canvas
        self.canvas_preview = ctk.CTkCanvas(tab, width=400, height=225, bg="black", highlightthickness=0)
        self.canvas_preview.grid(row=4, column=0, columnspan=5, padx=10, pady=10)
        
        # Trigger initial updates
        self.update_font_preview()
        self.update_visual_preview()

    def select_bg(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg")])
        if path:
            self.var_bg_path.set(path)
            self.update_visual_preview()

    def update_font_preview(self, event=None):
        try:
            # Tkinter font format: (family, size)
            f = (self.var_font.get(), 20) # Just for the label, scalled down
            self.lbl_font_preview.configure(font=f)
            self.update_visual_preview() # Update the canvas too
        except:
            pass

    def update_visual_preview(self, event=None):
        # Generate a small preview using logic generator logic (roughly)
        # We simulate it with PIL and convert to ImageTk
        
        # Mock config for generation
        temp_conf = SlideshowConfig()
        temp_conf.font_name = self.var_font.get()
        # Scale for preview
        scale_factor = 400 / 1920
        temp_conf.font_size = int(self.var_font_size.get() * scale_factor)
        temp_conf.bg_image_path = self.var_bg_path.get()
        temp_conf.bg_opacity = self.var_opacity.get()
        temp_conf.output_resolution = (400, 225)
        
        gen = SlideshowGenerator(temp_conf)
        
        try:
            pil_img = gen.generate_slide("Preview Top Text", "Preview Bottom Text")
            self.preview_image_tk = ImageTk.PhotoImage(pil_img)
            self.canvas_preview.create_image(0, 0, anchor="nw", image=self.preview_image_tk)
        except Exception as e:
            print(f"Preview error: {e}")

    def setup_audio_tab(self):
        tab = self.tabview.tab("Audio & TTS")
        tab.grid_columnconfigure(1, weight=1)

        # Provider
        ctk.CTkLabel(tab, text="Provider:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.var_provider = ctk.StringVar(value=self.config.get("tts_provider", "gTTS"))
        self.seg_provider = ctk.CTkSegmentedButton(tab, values=["gTTS", "google_cloud"], variable=self.var_provider, command=self.update_audio_ui)
        self.seg_provider.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        # API Key
        self.lbl_api = ctk.CTkLabel(tab, text="API Key:")
        self.var_api_key = ctk.StringVar(value=self.config.get("api_key", ""))
        self.entry_api_key = ctk.CTkEntry(tab, textvariable=self.var_api_key, show="*")
        
        # Speed
        ctk.CTkLabel(tab, text="Speed:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.var_speed = ctk.DoubleVar(value=self.config.get("tts_speed", 1.0))
        self.slider_speed = ctk.CTkSlider(tab, from_=0.5, to=2.0, variable=self.var_speed)
        self.slider_speed.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

        # Pauses
        ctk.CTkLabel(tab, text="Sentence Pause (s):").grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.var_sent_pause = ctk.StringVar(value=str(self.config.get("sentence_pause", 0.5)))
        ctk.CTkEntry(tab, textvariable=self.var_sent_pause, width=60).grid(row=3, column=1, sticky="w", padx=10)

        ctk.CTkLabel(tab, text="Slide Pause (s):").grid(row=3, column=1, padx=10, pady=10, sticky="e")
        self.var_slide_pause = ctk.StringVar(value=str(self.config.get("slide_pause", 0.5)))
        ctk.CTkLabel(tab, text=" s").grid(row=3, column=3, sticky="w")
        ctk.CTkEntry(tab, textvariable=self.var_slide_pause, width=60).grid(row=3, column=2, sticky="ew", padx=10)

        self.update_audio_ui(self.var_provider.get())

    def update_audio_ui(self, provider):
        if provider == "google_cloud":
            self.lbl_api.grid(row=1, column=0, padx=10, pady=10, sticky="w")
            self.entry_api_key.grid(row=1, column=1, columnspan=2, padx=10, pady=10, sticky="ew")
        else:
            self.lbl_api.grid_forget()
            self.entry_api_key.grid_forget()

    def save_settings(self):
        new_config = {
            "font_name": self.var_font.get(),
            "font_size": self.var_font_size.get(),
            "bg_image_path": self.var_bg_path.get(),
            "bg_opacity": self.var_opacity.get(),
            "tts_provider": self.var_provider.get(),
            "api_key": self.var_api_key.get(),
            "tts_speed": self.var_speed.get(),
            "sentence_pause": float(self.var_sent_pause.get()),
            "slide_pause": float(self.var_slide_pause.get())
        }
        self.callback_save(new_config)
        self.destroy()

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Language Slideshow Maker")
        self.geometry("700x650")
        
        # Load Config
        self.config_data = ConfigManager.load_config()
        # Initialize Voices Cache
        self.all_google_voices = [] 
        
        # Init audio for preview
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        self.excel_path = ctk.StringVar()
        self.lang1 = ctk.StringVar(value=self.config_data.get("lang1", "English"))
        self.lang2 = ctk.StringVar(value=self.config_data.get("lang2", "French"))
        self.voice1 = ctk.StringVar(value=self.config_data.get("tts_voice_id_1", ""))
        self.voice2 = ctk.StringVar(value=self.config_data.get("tts_voice_id_2", ""))

        # --- GUI ---
        
        # Header
        ctk.CTkLabel(self, text="Language Slideshow Maker", font=("Arial", 24, "bold")).grid(row=0, column=0, pady=10)

        # 1. File Selection
        frame_file = ctk.CTkFrame(self)
        frame_file.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
        ctk.CTkButton(frame_file, text="Select Excel File", command=self.select_excel).pack(side="left", padx=10, pady=10)
        self.lbl_file = ctk.CTkLabel(frame_file, textvariable=self.excel_path)
        self.lbl_file.pack(side="left", padx=10)

        # 2. Languages & Voices
        frame_lang = ctk.CTkFrame(self)
        frame_lang.grid(row=2, column=0, padx=20, pady=5, sticky="ew")
        frame_lang.grid_columnconfigure(1, weight=1)
        
        lang_values = list(utils.LANG_MAP.keys())

        # Top Language (1)
        ctk.CTkLabel(frame_lang, text="Top Language:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.opt_lang1 = ctk.CTkOptionMenu(frame_lang, values=lang_values, variable=self.lang1, command=self.on_lang1_change)
        self.opt_lang1.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(frame_lang, text="Voice (Top):").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.combo_voice1 = ctk.CTkComboBox(frame_lang, variable=self.voice1)
        self.combo_voice1.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        self.btn_prev1 = ctk.CTkButton(frame_lang, text="▶", width=30, command=lambda: self.play_preview(1))
        self.btn_prev1.grid(row=1, column=2, padx=5, pady=5)

        # Bottom Language (2)
        ctk.CTkLabel(frame_lang, text="Bottom Language:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.opt_lang2 = ctk.CTkOptionMenu(frame_lang, values=lang_values, variable=self.lang2, command=self.on_lang2_change)
        self.opt_lang2.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(frame_lang, text="Voice (Bottom):").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.combo_voice2 = ctk.CTkComboBox(frame_lang, variable=self.voice2)
        self.combo_voice2.grid(row=3, column=1, padx=10, pady=5, sticky="ew")

        self.btn_prev2 = ctk.CTkButton(frame_lang, text="▶", width=30, command=lambda: self.play_preview(2))
        self.btn_prev2.grid(row=3, column=2, padx=5, pady=5)
        
        # Refresh Voices Button
        self.btn_refresh = ctk.CTkButton(frame_lang, text="Refresh Google Voices", command=self.refresh_voices)
        self.btn_refresh.grid(row=4, column=0, columnspan=3, padx=10, pady=10)


        # 3. Actions
        frame_ctrl = ctk.CTkFrame(self)
        frame_ctrl.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        
        ctk.CTkButton(frame_ctrl, text="Advanced Settings", command=self.open_settings).pack(side="left", padx=20, pady=20)
        
        self.btn_gen = ctk.CTkButton(frame_ctrl, text="Generate Video", command=self.start_gen, fg_color="green", height=40)
        self.btn_gen.pack(side="right", padx=20, pady=20)

        # 4. Log
        self.log_box = ctk.CTkTextbox(self)
        self.log_box.grid(row=4, column=0, padx=20, pady=10, sticky="nsew")
        
        # Initial voice load if API key present
        if self.config_data.get("api_key"):
            self.refresh_voices(silent=True)

    def log(self, msg):
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")

    def select_excel(self):
        path = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx *.xls")])
        if path:
            self.excel_path.set(path)
            self.log(f"Selected: {path}")

    def open_settings(self):
        SettingsDialog(self, self.config_data, self.save_settings)

    def save_settings(self, new_conf):
        self.config_data.update(new_conf)
        ConfigManager.save_config(self.config_data)
        self.log("Settings saved.")
        self.update_voice_lists() # Update main UI if provider changed

    def refresh_voices(self, silent=False):
        api_key = self.config_data.get("api_key")
        if not api_key:
            if not silent: self.log("No API Key found in settings.")
            return

        conf = SlideshowConfig()
        conf.api_key = api_key
        gen = SlideshowGenerator(conf)
        
        if not silent: self.log("Fetching defined voices from Google Cloud...")
        voices = gen.get_google_voices()
        
        if voices:
            self.all_google_voices = voices
            if not silent: self.log(f"Fetched {len(voices)} voices.")
            self.update_voice_lists()
        else:
            if not silent: self.log("Failed to fetch voices or none found.")

    def update_voice_lists(self):
        provider = self.config_data.get("tts_provider", "gTTS")
        
        if provider == "gTTS":
            default_val = ["Default gTTS"]
            self.combo_voice1.configure(values=default_val)
            self.combo_voice1.set(default_val[0])
            self.combo_voice2.configure(values=default_val)
            self.combo_voice2.set(default_val[0])
            self.btn_refresh.configure(state="disabled")
            return

        self.btn_refresh.configure(state="normal")

        # Update Combo 1
        lang1_code = utils.get_language_code(self.lang1.get())
        voices1 = self.filter_voices(lang1_code)
        voices1_names = [v['name'] for v in voices1]
        self.combo_voice1.configure(values=voices1_names)
        if voices1_names:
            # If current selection not in list, select first
            if self.voice1.get() not in voices1_names:
                self.combo_voice1.set(voices1_names[0])
        else:
            self.combo_voice1.set("No voices found")
        
        # Update Combo 2
        lang2_code = utils.get_language_code(self.lang2.get())
        voices2 = self.filter_voices(lang2_code)
        voices2_names = [v['name'] for v in voices2]
        self.combo_voice2.configure(values=voices2_names)
        if voices2_names:
             if self.voice2.get() not in voices2_names:
                self.combo_voice2.set(voices2_names[0])
        else:
            self.combo_voice2.set("No voices found")

    def play_preview(self, slot):
        # 1 or 2
        try:
            conf = SlideshowConfig()
            # Copy basic config
            for k, v in self.config_data.items():
                if hasattr(conf, k):
                    setattr(conf, k, v)
            
            gen = SlideshowGenerator(conf)
            
            if slot == 1:
                lang = self.lang1.get()
                voice = self.voice1.get()
            else:
                lang = self.lang2.get()
                voice = self.voice2.get()
                
            if voice == "Default gTTS":
                voice = None
                
            self.log(f"Previewing... ({lang} - {voice})")
            
            # Text sample based on language?
            # Creating a simple map or just using English for now, 
            # ideally we translate usage, but "Hello" equivalent is fine.
            # Using lang name as text is simple enough test.
            text = f"This is a preview for {lang}"
            
            # Using generate_audio directly to bypass logic wrapping
            # wait, generate_audio needs text, lang_name, specific_voice_id
            
            path = gen.generate_audio(text, lang, specific_voice_id=voice)
            
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            
        except Exception as e:
            self.log(f"Preview Failed: {e}")

    def filter_voices(self, lang_code):
        # Google voices have list of lang codes e.g. ['en-US']
        # our lang_code is 'en', 'fr', etc.
        filtered = []
        for v in self.all_google_voices:
            # Check if any code starts with our lang code
            # e.g. 'en-US' starts with 'en'
            for c in v['language_codes']:
                if c.startswith(lang_code):
                    filtered.append(v)
                    break
        return filtered

    def on_lang1_change(self, value):
        self.update_voice_lists()
        
    def on_lang2_change(self, value):
        self.update_voice_lists()

    def start_gen(self):
        threading.Thread(target=self.run_gen, daemon=True).start()

    def run_gen(self):
        excel = self.excel_path.get()
        if not excel:
            self.log("No Excel file selected.")
            return

        self.btn_gen.configure(state="disabled")
        try:
            # Save selections
            self.config_data["lang1"] = self.lang1.get()
            self.config_data["lang2"] = self.lang2.get()
            self.config_data["tts_voice_id_1"] = self.voice1.get()
            self.config_data["tts_voice_id_2"] = self.voice2.get()
            ConfigManager.save_config(self.config_data)

            conf = SlideshowConfig()
            for k, v in self.config_data.items():
                if hasattr(conf, k):
                    setattr(conf, k, v)
            
            gen = SlideshowGenerator(conf)
            self.log("Loading data...")
            data = gen.load_excel(excel)
            
            cost = gen.estimate_cost(data)
            self.log(f"Estimated Cost: {cost}")
            
            output = os.path.splitext(excel)[0] + "_slideshow.mp4"
            gen.create_video(data, self.lang1.get(), self.lang2.get(), output, 
                             progress_callback=lambda p, m: self.log(f"{int(p*100)}%: {m}"))
            
            self.log("Done!")
        except Exception as e:
            self.log(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.btn_gen.configure(state="normal")
