from PIL import ImageFont

def wrap_text(text, font, max_width):
    """
    Wraps text to fit within a maximum width.
    Returns a list of lines.
    """
    lines = []
    # simplistic split by words
    words = text.split()
    current_line = []
    
    for word in words:
        current_line.append(word)
        # Check width of current line
        temp_line = ' '.join(current_line)
        bbox = font.getbbox(temp_line)
        # getbbox returns (left, top, right, bottom)
        width = bbox[2] - bbox[0]
        
        if width > max_width:
            if len(current_line) == 1:
                # If a single word is too long, we keep it (or could split chars)
                lines.append(temp_line)
                current_line = []
            else:
                # Pop the last word and add the line
                current_line.pop()
                lines.append(' '.join(current_line))
                current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
        
    return lines

LANG_MAP = {
    'Auto': 'auto',
    'English': 'en',
    'French': 'fr',
    'Spanish': 'es',
    'German': 'de',
    'Italian': 'it',
    'Portuguese': 'pt',
    'Russian': 'ru',
    'Japanese': 'ja',
    'Korean': 'ko',
    'Chinese': 'zh-cn'
}

def get_language_code(lang_name):
    return LANG_MAP.get(lang_name, 'en')
