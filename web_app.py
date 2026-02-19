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
    
    /* Terminal style for input/output */
    .stTextArea textarea {
        background-color: #0d1117;
        color: #00ff00;
        font-family: 'Courier New', monospace;
        border: 1px solid #30363d;
    }
</style>
""", unsafe_allow_html=True)

# --- AI ENGINE (Red Channel Detection for Stability) ---
def generate_complexity_mask(image_np):
    # Use ONLY Red Channel for detection to ensure map stability
    red_channel = image_np[:, :, 0] 
    edges = cv2.Canny(red_channel, 100, 200)
    kernel = np.ones((3,3), np.uint8)
    dilated_edges = cv2.dilate(edges, kernel, iterations=1)
    return dilated_edges

# --- ROBUST BINARY CONVERSION (UTF-8) ---
def text_to_bits(text):
    bits = bin(int.from_bytes(text.encode('utf-8', 'surrogatepass'), 'big'))[2:]
    return bits.zfill(8 * ((len(bits) + 7) // 8))

def text_from_bits(bits):
    n = int(bits, 2)
    return n.to_bytes((n.bit_length() + 7) // 8, 'big').decode('utf-8', 'surrogatepass') or '\0'

# --- ADAPTIVE HIDE (With Length Header) ---
def adaptive_hide(cover_image, message, password):
    img_np = np.array(cover_image.convert('RGB'))
    
    # 1. Prepare Payload: PasswordHash + Delimiter + Message
    pass_hash = hashlib.sha256(password.encode()).hexdigest()[:8]
    full_payload = pass_hash + "::" + message
    
    # 2. Convert to Binary
    binary_payload = text_to_bits(full_payload)
    payload_len = len(binary_payload)
    
    # 3. Create Header: Store length as 32-bit binary
    # This tells the decoder EXACTLY when to stop reading.
    length_header = format(payload_len, '032b') 
    
    final_bits = length_header + binary_payload
    required_bits = len(final_bits)
    
    # 4. Generate Mask
    complexity_mask = generate_complexity_mask(img_np)
    mask_visual = Image.fromarray(complexity_mask)
    max_capacity_bits = np.sum(complexity_mask == 255)
    
    if required_bits > max_capacity_bits:
        return "CAPACITY_ERROR", mask_visual, (max_capacity_bits, required_bits)

    # 5. Embed Data
    data_index = 0
    height, width, _ = img_np.shape
    stego_np = img_np.copy()
    
    for y in range(height):
        for x in range(width):
            if data_index >= required_bits: break
            
            if complexity_mask[y, x] == 255:
                r, g, b = stego_np[y, x]
                b_bin = list(format(b, '08b'))
                # Hide in Blue Channel
                b_bin[-1] = final_bits[data_index] 
                new_b = int("".join(b_bin), 2)
                stego_np[y, x] = (r, g, new_b)
                data_index += 1
                
    return "SUCCESS", Image.fromarray(stego_np), (max_capacity_bits, required_bits)

# --- ADAPTIVE REVEAL (Header Based) ---
def adaptive_reveal(stego_image, input_password):
    img_np = np.array(stego_image.convert('RGB'))
    complexity_mask = generate_complexity_mask(img_np)
    
    height, width, _ = img_np.shape
    extracted_bits = ""
    
    # 1. READ HEADER (First 32 bits)
    header_bits = ""
    header_found = False
    payload_length = 0
    
    bit_counter = 0
    
    for y in range(height):
        for x in range(width):
            if complexity_mask[y, x] == 255:
                _, _, b = img_np[y, x]
                bit = format(b, '08b')[-1]
                
                if not header_found:
                    header_bits += bit
                    if len(header_bits) == 32:
                        payload_length = int(header_bits, 2)
                        header_found = True
                        # Safety check for absurd lengths (corrupt image)
                        if payload_length > (height * width) or payload_length <= 0:
                            return "FAIL_CORRUPT", "Header corrupted (Invalid Length)."
                else:
                    extracted_bits += bit
                    bit_counter += 1
                    # STOP exactly when we have the full message
                    if bit_counter >= payload_length:
                        try:
                            full_msg = text_from_bits(extracted_bits)
                            
                            if "::" in full_msg:
                                stored_hash, actual_msg = full_msg.split("::", 1)
                                input_hash = hashlib.sha256(input_password.strip().encode()).hexdigest()[:8]
                                
                                if input_hash == stored_hash:
                                    return "SUCCESS", actual_msg
                                else:
                                    return "FAIL_PASSWORD", "Incorrect Password."
                            else:
                                return "FAIL_CORRUPT", "Password hash missing."
                        except:
                            return "FAIL_CORRUPT", "Binary decode failed."

    return "FAIL_EMPTY", "No hidden data stream detected."

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
        
        col1, col2 = st.columns([1, 1])
        with col1:
            uploaded_file = st.file_uploader("Upload Cover Image", type=["png", "jpg", "jpeg"])
            password = st.text_input("Encryption Password", type="password")
            
        with col2:
            secret_message = st.text_area(
                "Classified Intel", 
                height=150, 
                placeholder="Enter detailed intelligence report here... (Supports paragraphs & symbols)"
            )

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
                    efficiency = round((used/capacity)*100, 4) if capacity > 0 else 0
                    m3.markdown(f"<div class='metric-box'>Texture Usage<br><b>{efficiency}%</b></div>", unsafe_allow_html=True)
                    
                    st.markdown("---")
                    
                    buf = io.BytesIO()
                    stego_img.save(buf, format="PNG")
                    st.download_button("💾 DOWNLOAD STEGO-IMAGE", buf.getvalue(), "stegoshield_secure.png", "image/png")
                    
                elif status == "CAPACITY_ERROR":
                    mask = result
                    capacity, required = metrics
                    st.error(f"❌ IMAGE REJECTED: Too Smooth.")
                    st.warning(f"Required Bits: {required} | Available Texture Spots: {capacity}")
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
                    # Using code block for better copy-pasting of large paragraphs
                    st.markdown("### DECODED INTEL:")
                    st.code(result, language="text")
                    
                elif status == "FAIL_PASSWORD":
                    st.error(f"❌ ACCESS DENIED: {result}")
                elif status == "FAIL_CORRUPT":
                    st.error(f"⚠️ DATA CORRUPTION DETECTED: {result}")
                    st.info("Ensure you uploaded the correct PNG file directly downloaded from Phase 1.")
                else:
                    st.warning(f"⚠️ Scan Complete: {result}")

if __name__ == "__main__":
    main()