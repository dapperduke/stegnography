import os
import numpy as np
import time
from flask import Flask, render_template, request
from PIL import Image
from gtts import gTTS

app = Flask(__name__)
UPLOAD_FOLDER = 'static'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- STEP 1: DEFINE STEGANOGRAPHY FUNCTIONS FIRST ---

def encode_message(image, message):
    """Hides a message into the Least Significant Bit of image pixels."""
    # Add a delimiter so the decoder knows where the text ends
    message += "#####" 
    binary_msg = ''.join(format(ord(i), '08b') for i in message)
    
    # Convert image to grayscale and flatten
    pixels = np.array(image, dtype=np.uint8).flatten()
    
    if len(binary_msg) > len(pixels):
        raise ValueError("Image is too small for this message!")

    # Modify the LSB of each pixel (using 254 to avoid uint8 overflow)
    for i in range(len(binary_msg)):
        pixels[i] = (pixels[i] & 254) | int(binary_msg[i])
    
    # Reshape back to original dimensions
    new_pixels = pixels.reshape((image.height, image.width))
    return Image.fromarray(new_pixels, mode='L')

def decode_message(image):
    """Extracts bits from the LSB and converts them back to text."""
    pixels = np.array(image).flatten()
    binary_msg = "".join([str(p & 1) for p in pixels])
    
    # Group bits into 8-bit bytes
    all_bytes = [binary_msg[i:i+8] for i in range(0, len(binary_msg), 8)]
    decoded_text = ""
    for byte in all_bytes:
        try:
            char = chr(int(byte, 2))
            decoded_text += char
            # Stop if we hit our delimiter
            if "#####" in decoded_text:
                return decoded_text.replace("#####", "")
        except:
            break
    return "No hidden message found."

# --- STEP 2: DEFINE FLASK ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/encode', methods=['POST'])
def encode():
    file = request.files.get('file')
    msg = request.form.get('message')
    
    if not file or not msg:
        return "Please upload a file and enter a message."

    # Convert to Grayscale
    img = Image.open(file).convert('L')
    
    try:
        # This call now works because encode_message is defined above
        stego_img = encode_message(img, msg)
        path = os.path.join(UPLOAD_FOLDER, 'stego_image.png')
        stego_img.save(path)
        return render_template('index.html', encoded_img='/'+path, time=time.time())
    except ValueError as e:
        return str(e)

@app.route('/decode', methods=['POST'])
def decode():
    file = request.files.get('file')
    if not file:
        return "Please upload the stego-image."

    img = Image.open(file).convert('L')
    secret_text = decode_message(img)
    
    # Convert extracted text to MP3
    tts = gTTS(text=secret_text, lang='en')
    mp3_path = os.path.join(UPLOAD_FOLDER, 'output.mp3')
    tts.save(mp3_path)
    
    return render_template('index.html', mp3_path='/'+mp3_path, secret_text=secret_text, time=time.time())

if __name__ == '__main__':
    app.run(debug=True)