import streamlit as st
import cv2
import numpy as np
from PIL import Image
import io
import hashlib

# --- CONFIGURATION ---
st.set_page_config(
    page_title="StegoShield AI Defense",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM STYLE ---
st.markdown("""
<style>
    .main { background-color: #0e1117; color: #c9d1d9; }
    h1, h2, h3 { color: #58a6ff; font-family: 'Helvetica Neue', sans-serif; }
    .stButton>button { background-color: #238636; color: white; border-radius: 5px; width: 100%; font-weight: bold; }
    .stButton>button:hover { background-color: #2ea043; }
    .metric-box { background-color: #161b22; border: 1px solid #30363d; padding: 10px; border-radius: 5px; text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- AI ENGINE (STABILITY FIX - Unchanged) ---
def generate_complexity_mask(image_np):
    # Use ONLY Red Channel for detection to ensure map stability
    red_channel = image_np[:, :, 0] 
    
    # Use Canny Edge Detection
    edges = cv2.Canny(red_channel, 100, 200)
    
    # Dilate edges to create safe zones
    kernel = np.ones((3,3), np.uint8)
    dilated_edges = cv2.dilate(edges, kernel, iterations=1)
    return dilated_edges

# --- HELPER FUNCTIONS ---
def str_to_bin(message):
    binary_message = ''.join(format(ord(char), '08b') for char in message)
    return binary_message + '1111111111111110' # 16-bit Delimiter

def bin_to_str(binary_data):
    message = ""
    for i in range(0, len(binary_data), 8):
        byte = binary_data[i:i+8]
        message += chr(int(byte, 2))
    return message

# --- ADAPTIVE HIDE (UNCHANGED) ---
def adaptive_hide(cover_image, message, password):
    img_np = np.array(cover_image.convert('RGB'))
    
    pass_hash = hashlib.sha256(password.encode()).hexdigest()[:8]
    full_message = pass_hash + "::" + message
    
    complexity_mask = generate_complexity_mask(img_np)
    mask_visual = Image.fromarray(complexity_mask)
    
    # Capacity Check
    max_capacity_bits = np.sum(complexity_mask == 255)
    binary_secret = str_to_bin(full_message)
    required_bits = len(binary_secret)
    
    if required_bits > max_capacity_bits:
        return "CAPACITY_ERROR", mask_visual, (max_capacity_bits, required_bits)

    data_index = 0
    height, width, _ = img_np.shape
    stego_np = img_np.copy()
    
    for y in range(height):
        for x in range(width):
            if data_index >= required_bits: break
            
            if complexity_mask[y, x] == 255:
                r, g, b = stego_np[y, x]
                b_bin = list(format(b, '08b'))
                # Embed in BLUE channel (index 2)
                b_bin[-1] = binary_secret[data_index] 
                new_b = int("".join(b_bin), 2)
                stego_np[y, x] = (r, g, new_b)
                data_index += 1
                
    return "SUCCESS", Image.fromarray(stego_np), (max_capacity_bits, required_bits)

# --- ADAPTIVE REVEAL (FIXED "y" BUG) ---
def adaptive_reveal(stego_image, input_password):
    img_np = np.array(stego_image.convert('RGB'))
    complexity_mask = generate_complexity_mask(img_np)
    
    height, width, _ = img_np.shape
    extracted_bin = ""
    
    for y in range(height):
        for x in range(width):
            if complexity_mask[y, x] == 255:
                _, _, b = img_np[y, x]
                extracted_bin += format(b, '08b')[-1]
                
                # Check for 16-bit delimiter
                if len(extracted_bin) >= 16 and extracted_bin.endswith('1111111111111110'):
                     # FIX: Slice off the last 16 bits (delimiter) so it doesn't become 'ÿ'
                     clean_bin = extracted_bin[:-16]
                     full_msg = bin_to_str(clean_bin)
                     
                     if "::" in full_msg:
                         stored_hash, actual_msg = full_msg.split("::", 1)
                         input_hash = hashlib.sha256(input_password.strip().encode()).hexdigest()[:8]
                         
                         if input_hash == stored_hash:
                             return "SUCCESS", actual_msg
                         else:
                             return "FAIL_PASSWORD", "Incorrect Password."
                     else:
                         return "FAIL_CORRUPT", "Header mismatch."
    
    return "FAIL_EMPTY", "No Hidden Data Found."

# --- MAIN APP ---
def main():
    st.sidebar.image("https://img.icons8.com/fluency/96/shield.png", width=60)
    st.sidebar.title("StegoShield Ops")
    app_mode = st.sidebar.selectbox("Select Mission Phase", ["🛡️ ENCODE (Hide Intel)", "🔓 DECODE (Extract Intel)"])
    
    st.sidebar.markdown("---")
    st.sidebar.info("System Status: **ONLINE**")
    
    st.title("StegoShield: AI-Driven Defense Tool")

    # --- ENCODE SECTION ---
    if app_mode == "🛡️ ENCODE (Hide Intel)":
        st.header("Phase 1: Secure Embedding")
        
        col1, col2 = st.columns(2)
        with col1:
            uploaded_file = st.file_uploader("Upload Cover Image", type=["png", "jpg", "jpeg"])
        with col2:
            secret_message = st.text_input("Classified Intel")
            password = st.text_input("Encryption Password", type="password")

        if uploaded_file and secret_message and password:
            if st.button("RUN AI ANALYSIS & EMBED"):
                cover = Image.open(uploaded_file)
                
                with st.spinner("AI Engine Analyzing Textures..."):
                    status, result, metrics = adaptive_hide(cover, secret_message, password)
                
                if status == "SUCCESS":
                    stego_img = result
                    capacity, used = metrics
                    
                    st.success("✅ Operation Successful: Data Hidden in Complex Regions")
                    
                    # --- STEALTH ANALYTICS ---
                    st.markdown("### 📊 Stealth Analytics")
                    m1, m2, m3 = st.columns(3)
                    m1.markdown(f"<div class='metric-box'>Safe Pixels Found<br><b>{capacity} px</b></div>", unsafe_allow_html=True)
                    m2.markdown(f"<div class='metric-box'>Payload Size<br><b>{used} bits</b></div>", unsafe_allow_html=True)
                    efficiency = round((used/capacity)*100, 2) if capacity > 0 else 0
                    m3.markdown(f"<div class='metric-box'>Texture Usage<br><b>{efficiency}%</b></div>", unsafe_allow_html=True)
                    
                    st.markdown("---")
                    
                    # Buffer for download
                    buf = io.BytesIO()
                    stego_img.save(buf, format="PNG")
                    st.download_button("💾 DOWNLOAD STEGO-IMAGE", buf.getvalue(), "stegoshield_secure.png", "image/png")
                    
                elif status == "CAPACITY_ERROR":
                    mask = result
                    capacity, required = metrics
                    st.error(f"❌ IMAGE REJECTED: Too Smooth.")
                    st.warning(f"Required Bits: {required} | Available Texture Spots: {capacity}")
                    st.info("💡 Recommendation: Use an image with high texture (Grass, Rocks, Crowd). Avoid Skies/Cartoons.")
                    st.image(mask, caption="AI Complexity Map (Too Dark = No Hiding Spots)", width=300)

    # --- DECODE SECTION ---
    elif app_mode == "🔓 DECODE (Extract Intel)":
        st.header("Phase 2: Intelligence Extraction")
        
        stego_upload = st.file_uploader("Upload Suspicious Image", type=["png"])
        input_pass = st.text_input("Decryption Key", type="password")
        
        if stego_upload and input_pass:
            if st.button("AUTHENTICATE & DECODE"):
                stego_img = Image.open(stego_upload)
                
                status, result = adaptive_reveal(stego_img, input_pass)
                
                if status == "SUCCESS":
                    st.balloons()
                    st.success("✅ IDENTITY VERIFIED.")
                    st.markdown(f"""
                    <div style="padding:15px; border:2px solid #2ea043; border-radius:10px; background-color:#0d1117;">
                        <h3 style="color:#2ea043; margin:0;">DECODED INTEL:</h3>
                        <p style="font-family:monospace; font-size:18px; color:#ffffff;">{result}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                elif status == "FAIL_PASSWORD":
                    st.error(f"❌ ACCESS DENIED: {result}")
                    
                else:
                    st.warning(f"⚠️ Scan Complete: {result}")

if __name__ == "__main__":
    main()