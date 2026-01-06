from logic import SlideshowConfig, SlideshowGenerator
import os

def test_generation():
    print("Testing SlideshowGenerator...")
    
    # Setup Config
    config = SlideshowConfig()
    config.font_size = 40
    config.bg_opacity = 0.5
    # Use defaults for others
    
    generator = SlideshowGenerator(config)
    
    # Load Data
    data = generator.load_excel("sample.xlsx")
    print(f"Loaded {len(data)} rows.")
    assert len(data) == 3
    
    # Generate Video
    output_path = "test_output.mp4"
    if os.path.exists(output_path):
        os.remove(output_path)
        
    print("Generating video...")
    generator.create_video(data, "English", "French", output_path, progress_callback=lambda p, m: print(f"{p*100:.0f}%: {m}"))
    
    if os.path.exists(output_path):
        print(f"Success! Video created at {output_path}")
    else:
        print("Failed to create video.")

if __name__ == "__main__":
    test_generation()
