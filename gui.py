import tkinter
import customtkinter as ctk
from tkinter import filedialog
import threading
import os
import utils
from logic import SlideshowConfig, SlideshowGenerator

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Language Slideshow Maker")
        self.geometry("800x700")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1) # Log area expands

        # Variables
        self.excel_path = ctk.StringVar()
        self.bg_path = ctk.StringVar()
        self.tts_provider = ctk.StringVar(value="gTTS")
        self.lang1 = ctk.StringVar(value="English")
        self.lang2 = ctk.StringVar(value="French")

        # --- Frames ---

        # 1. File Selection
        self.file_frame = ctk.CTkFrame(self)
        self.file_frame.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        
        self.btn_file = ctk.CTkButton(self.file_frame, text="Import Excel File", command=self.select_excel)
        self.btn_file.pack(side="left", padx=10, pady=10)
        
        self.lbl_file = ctk.CTkLabel(self.file_frame, textvariable=self.excel_path, fg_color="transparent")
        self.lbl_file.pack(side="left", padx=10, pady=10)

        # 2. Main Settings
        self.settings_frame = ctk.CTkFrame(self)
        self.settings_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.settings_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Font Size
        ctk.CTkLabel(self.settings_frame, text="Font Size:").grid(row=0, column=0, padx=10, pady=5)
        self.entry_font_size = ctk.CTkEntry(self.settings_frame, width=60)
        self.entry_font_size.insert(0, "60")
        self.entry_font_size.grid(row=0, column=1, padx=10, pady=5)

        # BG Opacity
        ctk.CTkLabel(self.settings_frame, text="BG Opacity (0-1):").grid(row=0, column=2, padx=10, pady=5)
        self.slider_opacity = ctk.CTkSlider(self.settings_frame, from_=0, to=100, number_of_steps=100)
        self.slider_opacity.set(50) # 50%
        self.slider_opacity.grid(row=0, column=3, padx=10, pady=5)

        # Pauses
        ctk.CTkLabel(self.settings_frame, text="Sentence Pause (s):").grid(row=1, column=0, padx=10, pady=5)
        self.entry_pause_sent = ctk.CTkEntry(self.settings_frame, width=60)
        self.entry_pause_sent.insert(0, "0.5")
        self.entry_pause_sent.grid(row=1, column=1, padx=10, pady=5)

        ctk.CTkLabel(self.settings_frame, text="Slide Pause (s):").grid(row=1, column=2, padx=10, pady=5)
        self.entry_pause_slide = ctk.CTkEntry(self.settings_frame, width=60)
        self.entry_pause_slide.insert(0, "0.5")
        self.entry_pause_slide.grid(row=1, column=3, padx=10, pady=5)

        # Background Image
        self.btn_bg = ctk.CTkButton(self.settings_frame, text="Select Background Image", command=self.select_bg)
        self.btn_bg.grid(row=2, column=0, columnspan=2, padx=10, pady=10)
        
        self.lbl_bg = ctk.CTkLabel(self.settings_frame, textvariable=self.bg_path, fg_color="transparent")
        self.lbl_bg.grid(row=2, column=2, columnspan=2, padx=10, pady=10)

        # 3. TTS Settings
        self.tts_frame = ctk.CTkFrame(self)
        self.tts_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        
        ctk.CTkLabel(self.tts_frame, text="TTS Provider:").pack(side="left", padx=10)
        self.seg_tts = ctk.CTkSegmentedButton(self.tts_frame, values=["gTTS", "Google Cloud"], command=self.toggle_tts)
        self.seg_tts.set("gTTS")
        self.seg_tts.pack(side="left", padx=10)

        self.entry_api_key = ctk.CTkEntry(self.tts_frame, placeholder_text="Enter Google Cloud API Key", width=300)
        # Initially hidden or disabled? Just keeping it visible but disabled might be cleaner, or show/hide.
        # Let's show/hide.
        
        # 4. Action Frame
        self.action_frame = ctk.CTkFrame(self)
        self.action_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        
        lang_values = list(utils.LANG_MAP.keys())
        
        ctk.CTkLabel(self.action_frame, text="Language 1 (Top):").pack(side="left", padx=10)
        self.opt_lang1 = ctk.CTkOptionMenu(self.action_frame, values=lang_values, variable=self.lang1)
        self.opt_lang1.pack(side="left", padx=10)

        ctk.CTkLabel(self.action_frame, text="Language 2 (Bottom):").pack(side="left", padx=10)
        self.opt_lang2 = ctk.CTkOptionMenu(self.action_frame, values=lang_values, variable=self.lang2)
        self.opt_lang2.pack(side="left", padx=10)

        self.btn_generate = ctk.CTkButton(self.action_frame, text="GENERATE VIDEO", command=self.start_generation_thread, fg_color="green")
        self.btn_generate.pack(side="right", padx=20, pady=10)

        # 5. Progress
        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        self.progress_bar.set(0)

        # 6. Logs
        self.log_box = ctk.CTkTextbox(self, height=150)
        self.log_box.grid(row=5, column=0, padx=20, pady=10, sticky="nsew")

    def log(self, message):
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")

    def select_excel(self):
        path = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx *.xls")])
        if path:
            self.excel_path.set(path)
            self.log(f"Selected Excel: {path}")

    def select_bg(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg")])
        if path:
            self.bg_path.set(path)
            self.log(f"Selected Background: {path}")

    def toggle_tts(self, value):
        if value == "Google Cloud":
            self.entry_api_key.pack(side="left", padx=10)
        else:
            self.entry_api_key.pack_forget()

    def start_generation_thread(self):
        threading.Thread(target=self.run_generation, daemon=True).start()

    def run_generation(self):
        excel = self.excel_path.get()
        if not excel:
            self.log("Error: No Excel file selected.")
            return

        self.btn_generate.configure(state="disabled")
        self.log("Starting generation...")
        self.progress_bar.set(0)

        try:
            config = SlideshowConfig()
            config.font_size = int(self.entry_font_size.get())
            config.bg_opacity = self.slider_opacity.get() / 100.0
            config.sentence_pause = float(self.entry_pause_sent.get())
            config.slide_pause = float(self.entry_pause_slide.get())
            config.bg_image_path = self.bg_path.get()
            config.tts_provider = self.tts_provider.get() # "gTTS" or "Google Cloud"
            
            if config.tts_provider == "Google Cloud":
                # The segmented button value is 'Google Cloud' but logic expects 'google_cloud'
                config.tts_provider = 'google_cloud'
                config.api_key = self.entry_api_key.get().strip()

            generator = SlideshowGenerator(config)
            
            self.log("Loading Excel...")
            data = generator.load_excel(excel)
            if not data:
                self.log("Error: Excel file is empty or invalid.")
                self.btn_generate.configure(state="normal")
                return

            self.log(f"Found {len(data)} rows.")
            
            output_file = os.path.splitext(excel)[0] + "_slideshow.mp4"
            
            def progress(p, msg):
                self.progress_bar.set(p)
                self.log(msg)

            lang1 = self.lang1.get()
            lang2 = self.lang2.get()
            
            generator.create_video(data, lang1, lang2, output_file, progress_callback=progress)
            
            self.log(f"SUCCESS! Video saved to: {output_file}")

        except Exception as e:
            self.log(f"ERROR: {str(e)}")
            import traceback
            traceback.print_exc()

        finally:
            self.btn_generate.configure(state="normal")
