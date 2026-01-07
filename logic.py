import os
import tempfile
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS
from google.cloud import texttospeech
from google.api_core import client_options
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip
import utils
from langdetect import detect

class SlideshowConfig:
    def __init__(self):
        self.font_path = "Arial.ttf" # Default, might need system path
        self.font_name = "Arial"
        self.font_size = 60
        self.bg_image_path = None
        self.bg_opacity = 0.5 # 0.0 to 1.0 (overlay opacity)
        self.slide_pause = 0.5 # seconds
        self.sentence_pause = 0.5 # seconds
        self.tts_provider = "gTTS" # or "google_cloud"
        self.api_key = ""
        self.tts_voice_id_1 = "" 
        self.tts_voice_id_2 = ""
        self.tts_speed = 1.0 # 0.5 to 4.0
        self.output_resolution = (1920, 1080)
        self.text_color = "white"

class SlideshowGenerator:
    def __init__(self, config: SlideshowConfig):
        self.config = config
        self.temp_dir = tempfile.mkdtemp()

    def load_excel(self, file_path):
        """Loads Excel. Assumes col 1 is lang1, col 2 is lang2."""
        df = pd.read_excel(file_path, header=None)
        # Drop rows with missing values
        df = df.dropna(subset=[0, 1])
        data = []
        for index, row in df.iterrows():
            data.append({
                'text1': str(row[0]),
                'text2': str(row[1])
            })
        return data

    def generate_slide(self, text1, text2):
        """Creates a PIL Image for the slide."""
        width, height = self.config.output_resolution
        
        # Background
        if self.config.bg_image_path and os.path.exists(self.config.bg_image_path):
            try:
                bg = Image.open(self.config.bg_image_path).convert('RGBA')
                # Resize to cover
                bg_ratio = bg.width / bg.height
                screen_ratio = width / height
                if bg_ratio > screen_ratio:
                    # wider than screen, crop sides
                    new_height = height
                    new_width = int(new_height * bg_ratio)
                else:
                    new_width = width
                    new_height = int(new_width / bg_ratio)
                
                bg = bg.resize((new_width, new_height), Image.LANCZOS)
                # Center crop
                left = (new_width - width) / 2
                top = (new_height - height) / 2
                bg = bg.crop((left, top, left + width, top + height))
            except Exception as e:
                print(f"Error loading background: {e}")
                bg = Image.new('RGBA', (width, height), 'black')
        else:
            bg = Image.new('RGBA', (width, height), 'black')

        # Opacity Overlay (Darken background)
        # If opacity is 100% (1.0), we see fully black overlay? 
        # Requirement: "set the opacity from 0-100%" for the background image.
        # usually means how visible the background is. 100% = fully visible. 0% = black.
        # Let's interpret config.bg_opacity as "Background Visibility".
        # So we overlay black with alpha = (1 - visibility).
        
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, int(255 * (1 - self.config.bg_opacity))))
        bg = Image.alpha_composite(bg, overlay)
        
        # Text Drawing
        draw = ImageDraw.Draw(bg)
        
        try:
            # Try to load font, fallback to default
            # If font_name is provided, try to find it. 
            # Pillow needs a path to a ttf file usually, or system font loading is platform specific.
            # For simplicity, if it's a path use it, otherwise try default.
            # In a real app we might map font family names to paths.
            # Just relying on font_path from config which should be updating with absolute path from GUI if possible?
            # Or if it's just a name "Arial", PIL might find it if installed.
            font = ImageFont.truetype(self.config.font_name, self.config.font_size)
        except:
            # Try appending .ttf
            try:
                font = ImageFont.truetype(f"{self.config.font_name}.ttf", self.config.font_size)
            except:
                font = ImageFont.load_default()
            # Default font size is fixed/small, so this is a bad fallback but prevents crash.

        margin = 100
        max_text_width = width - (2 * margin)
        
        lines1 = utils.wrap_text(text1, font, max_text_width)
        lines2 = utils.wrap_text(text2, font, max_text_width)
        
        # Calculate total height to center everything
        # We want text1 on top half, text2 on bottom half? 
        # Requirement: "sentence of language 1 on top, and language 2 on the bottom. Everything should be centered"
        # Let's put a gap between them.
        
        line_height = self.config.font_size * 1.2
        total_text_height = (len(lines1) + len(lines2)) * line_height + line_height # +1 line gap
        
        start_y = (height - total_text_height) / 2
        
        # Draw Text 1
        current_y = start_y
        for line in lines1:
            # Center horizontally
            bbox = font.getbbox(line)
            w = bbox[2] - bbox[0]
            x = (width - w) / 2
            draw.text((x, current_y), line, font=font, fill=self.config.text_color)
            current_y += line_height
            
        # Gap
        current_y += line_height
        
        # Draw Text 2
        for line in lines2:
            bbox = font.getbbox(line)
            w = bbox[2] - bbox[0]
            x = (width - w) / 2
            draw.text((x, current_y), line, font=font, fill=self.config.text_color)
            current_y += line_height
            
        return bg.convert('RGB')



    def generate_audio(self, text, lang_name, specific_voice_id=None):
        """Generates audio file for text. Returns path."""
        lang_code = utils.get_language_code(lang_name)
        
        if lang_code == 'auto':
            try:
                lang_code = detect(text)
                print(f"Detected language for '{text}': {lang_code}")
            except Exception as e:
                print(f"Language detection failed: {e}. Defaulting to 'en'.")
                lang_code = 'en'

        filename = f"tts_{hash(text)}_{lang_code}_{self.config.tts_provider}_{self.config.tts_speed}_{specific_voice_id}.mp3"
        filepath = os.path.join(self.temp_dir, filename)
        
        if os.path.exists(filepath):
            return filepath

        if self.config.tts_provider == 'google_cloud' and self.config.api_key:
            try:
                options = client_options.ClientOptions(api_key=self.config.api_key)
                client = texttospeech.TextToSpeechClient(client_options=options)
                input_text = texttospeech.SynthesisInput(text=text)
                # Voice selection
                voice_params = {"language_code": lang_code}
                
                # Use specific voice if provided, otherwise config, otherwise neutral
                vid = specific_voice_id
                
                if vid:
                    voice_params["name"] = vid
                    # Fix for Google Cloud strict matching: 'es' != 'es-ES'
                    # If we have a specific voice, we should trust its language code.
                    # Voice IDs are usually "lang-region-voice" (e.g. es-ES-Standard-A)
                    parts = vid.split('-')
                    if len(parts) >= 2:
                         voice_params["language_code"] = f"{parts[0]}-{parts[1]}"
                
                print(f"DEBUG: voice_params={voice_params}")
                
                # Check for gender in voice name if manual selection not present, or just default to Neutral
                # If tts_voice_id is present, it usually implies gender/type.
                
                voice = texttospeech.VoiceSelectionParams(**voice_params)

                audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.MP3,
                    speaking_rate=self.config.tts_speed
                )
                response = client.synthesize_speech(
                    input=input_text, voice=voice, audio_config=audio_config
                )
                with open(filepath, "wb") as out:
                    out.write(response.audio_content)
                return filepath
            except Exception as e:
                print(f"Google Cloud TTS failed: {e}. Falling back to gTTS.")
                # Fallback
        
        # gTTS
        # gTTS doesn't support fine-grained speed control natively easily without hacks or post-processing.
        # But we can assume standard speed for now.
        tts = gTTS(text=text, lang=lang_code, slow=False)
        tts.save(filepath)
        
        # If speed is not 1.0, we might want to use ffmpeg/moviepy to speed it up/slow down later?
        # For this iteration, let's keep gTTS speed fixed or implement a hack if critical.
        # User requested speed control for gTTS too.
        # We can do this by post-processing the audio file with moviepy/ffmpeg right now.
        
        if self.config.tts_speed != 1.0:
            # Rename original to 'raw'
            raw_path = filepath + "_raw.mp3"
            os.rename(filepath, raw_path)
            # Use moviepy to change speed? AudioFileClip doesn't have speed change easily.
            # Using ffmpeg via moviepy's ffmpeg_tools or just os.system
            # setpts filter is for video, atempo is for audio.
            # cmd: ffmpeg -i input -filter:a "atempo=SPEED" -vn output
            import subprocess
            cmd = [
                "ffmpeg", "-y", "-i", raw_path, 
                "-filter:a", f"atempo={self.config.tts_speed}", 
                "-vn", filepath
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
        return filepath

    def get_google_voices(self):
        """Returns a list of available voices from Google Cloud."""
        if not self.config.api_key:
            return []
        try:
            options = client_options.ClientOptions(api_key=self.config.api_key)
            client = texttospeech.TextToSpeechClient(client_options=options)
            response = client.list_voices()
            voices = []
            for voice in response.voices:
                # Filter by our supported languages slightly? Or just return all?
                # Returning all is safer, GUI can filter.
                voices.append({
                    "name": voice.name,
                    "language_codes": voice.language_codes,
                    "ssml_gender": texttospeech.SsmlVoiceGender(voice.ssml_gender).name
                })
            return voices
        except Exception as e:
            print(f"Error fetching voices: {e}")
            return []

    def estimate_cost(self, data):
        """Estimates cost for Google Cloud TTS."""
        if self.config.tts_provider != 'google_cloud':
            return "Free (gTTS)"
        
        char_count = 0
        for item in data:
            char_count += len(item.get('text1', ''))
            char_count += len(item.get('text2', ''))
        
        # Standard: $4.00 / 1M chars
        # WaveNet: $16.00 / 1M chars
        # Assuming WaveNet if using google cloud usually? Or check config.
        # Let's assume standard price avg or show both.
        
        cost_standard = (char_count / 1_000_000) * 4.00
        cost_wavenet = (char_count / 1_000_000) * 16.00
        
        return f"~${cost_standard:.4f} (Std) / ~${cost_wavenet:.4f} (WaveNet)"

    def preview_audio(self, text, lang_name):
        """Generates a preview audio file and returns the path."""
        # Force re-generation for preview to hear changes
        # We use a temp name
        path = self.generate_audio(text, lang_name)
        return path

    def create_video(self, data, lang1, lang2, output_path, progress_callback=None):
        """
        Main orchestration function.
        data: list of dicts {'text1': ..., 'text2': ...}
        """
        clips = []
        
        total_steps = len(data)
        
        for i, item in enumerate(data):
            if progress_callback:
                progress_callback(i / total_steps, f"Processing slide {i+1}/{total_steps}")

            text1 = item['text1']
            text2 = item['text2']
            
            # Generate Image
            img = self.generate_slide(text1, text2)
            img_path = os.path.join(self.temp_dir, f"slide_{i}.png")
            img.save(img_path)
            
            # Generate Audio
            # We need to map lang1/lang2 to voice1/voice2
            audio1_path = self.generate_audio(text1, lang1, specific_voice_id=self.config.tts_voice_id_1)
            audio2_path = self.generate_audio(text2, lang2, specific_voice_id=self.config.tts_voice_id_2)
            
            # Create Clips
            # Audio 1
            audio1_clip = AudioFileClip(audio1_path)
            # Audio 2
            audio2_clip = AudioFileClip(audio2_path)
            
            # Total duration calculation
            # Pattern: Read 1 -> Pause -> Read 2 -> Pause
            
            # We construct the audio track first
            # Silence clip
            pause_sentence = AudioFileClip(os.path.join(self.temp_dir, "silence.mp3")) if False else None 
            # Moviepy making silence is slightly annoying without a file, 
            # let's just use set_start for positioning.
            
            # Sequence:
            # 0s: Start Audio 1
            # audio1_end: Wait sentence_pause
            # audio1_end + sentence_pause: Start Audio 2
            # audio2_end: Wait slide_pause
            
            total_dur = audio1_clip.duration + self.config.sentence_pause + audio2_clip.duration + self.config.slide_pause
            
            # Create Composite Audio
            # audio1 starts at 0
            audio1_clip = audio1_clip.with_start(0)
            
            # audio2 starts at len(a1) + pause
            t_audio2 = audio1_clip.duration + self.config.sentence_pause
            audio2_clip = audio2_clip.with_start(t_audio2)
            
            combined_audio = CompositeAudioClip([audio1_clip, audio2_clip])
            combined_audio.duration = total_dur # Enforce duration including final pause
            
            # Video Clip (Static Image)
            video_clip = ImageClip(img_path).with_duration(total_dur)
            video_clip.audio = combined_audio
            
            clips.append(video_clip)
            
        final_video = concatenate_videoclips(clips)
        final_video.write_videofile(output_path, fps=24, codec='libx264', audio_codec='aac')
        
        if progress_callback:
            progress_callback(1.0, "Done!")

