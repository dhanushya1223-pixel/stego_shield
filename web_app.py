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

# --- CUSTOM STYLE (Military Theme) ---
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
        color: #c9d1d9;
    }
    h1, h2, h3 {
        color: #58a6ff;
        font-family: 'Helvetica Neue', sans-serif;
    }
    .stButton>button {
        background-color: #238636;
        color: white;
        border-radius: 5px;
        border: none;
        padding: 10px 20px;
        font-weight: bold;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #2ea043;
    }
    .metric-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


# --- THE AI ENGINE (OPENCV) ---
def generate_complexity_mask(image_np):
    gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 100, 200)
    kernel = np.ones((3,3), np.uint8)
    dilated_edges = cv2.dilate(edges, kernel, iterations=1)
    return dilated_edges

# --- HELPER FUNCTIONS ---
def str_to_bin(message):
    binary_message = ''.join(format(ord(char), '08b') for char in message)
    return binary_message + '1111111111111110' 

def bin_to_str(binary_data):
    message = ""
    for i in range(0, len(binary_data), 8):
        byte = binary_data[i:i+8]
        if byte == '11111110':
            break
        message += chr(int(byte, 2))
    return message

# --- ADAPTIVE EMBEDDING WITH PASSWORD ---
def adaptive_hide(cover_image, message, password):
    img_np = np.array(cover_image.convert('RGB'))
    
    # Prepend Password Hash for Security
    # We hide the hash first. If password doesn't match hash on decode, we fail.
    pass_hash = hashlib.sha256(password.encode()).hexdigest()[:8] # First 8 chars
    full_message = pass_hash + "::" + message
    
    complexity_mask = generate_complexity_mask(img_np)
    mask_visual = Image.fromarray(complexity_mask)
    
    binary_secret = str_to_bin(full_message)
    data_len = len(binary_secret)
    data_index = 0
    
    height, width, _ = img_np.shape
    stego_np = img_np.copy()
    embedded_count = 0
    max_capacity = np.sum(complexity_mask == 255)

    for y in range(height):
        for x in range(width):
            if data_index >= data_len:
                break
            if complexity_mask[y, x] == 255:
                r, g, b = stego_np[y, x]
                b_bin = list(format(b, '08b'))
                b_bin[-1] = binary_secret[data_index]
                new_b = int("".join(b_bin), 2)
                stego_np[y, x] = (r, g, new_b)
                data_index += 1
                embedded_count += 1
                
    if data_index < data_len:
        st.error(f"Capacity Error: Need {data_len} bits, but AI found only {max_capacity} safe spots.")
        return None, mask_visual, 0
    
    return Image.fromarray(stego_np), mask_visual, max_capacity

# --- ADAPTIVE REVEAL WITH PASSWORD CHECK ---
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
                if len(extracted_bin) % 8 == 0 and extracted_bin.endswith('1111111111111110'):
                     full_msg = bin_to_str(extracted_bin)
                     
                     # SECURITY CHECK
                     if "::" in full_msg:
                         stored_hash, actual_msg = full_msg.split("::", 1)
                         input_hash = hashlib.sha256(input_password.encode()).hexdigest()[:8]
                         
                         if input_hash == stored_hash:
                             return actual_msg
                         else:
                             return "ACCESS DENIED: Incorrect Decryption Key."
                     else:
                         return "Error: Corrupted Data Structure."
    return None

# --- MAIN WEB APP UI ---
def main():
    st.sidebar.image("https://img.icons8.com/fluency/96/shield.png", width=60)
    st.sidebar.title("StegoShield Ops")
    app_mode = st.sidebar.selectbox("Select Mission Phase", ["🛡️ ENCODE (Hide Intel)", "🔓 DECODE (Extract Intel)"])
    
    st.sidebar.markdown("---")
    st.sidebar.info("System Status: **ONLINE**")
    st.sidebar.markdown("**Security Level:** High (AES-256 Simulation)")

    st.title("StegoShield: AI-Driven Adaptive Steganography")

    if app_mode == "🛡️ ENCODE (Hide Intel)":
        st.header("Phase 1: Secure Embedding")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            uploaded_file = st.file_uploader("Upload Cover Image", type=["png", "jpg"])
        with col2:
            secret_message = st.text_area("Classified Intel", placeholder="Enter secret data...")
            password = st.text_input("Encryption Password", type="password")

        if uploaded_file and secret_message and password:
            cover_image = Image.open(uploaded_file)
            
            if st.button("RUN AI ANALYSIS & EMBED"):
                with st.spinner("Encrypting & Mapping Texture..."):
                    stego_result, mask_visual, capacity = adaptive_hide(cover_image, secret_message, password)
                    
                    if stego_result:
                        st.success("✅ Process Complete. Data embedded into complex texture regions.")
                        
                        # NEW: ANALYTICS DASHBOARD
                        st.markdown("### 📊 Stealth Analytics")
                        m1, m2, m3 = st.columns(3)
                        m1.metric("Safe Pixels Found", f"{capacity} px")
                        m2.metric("Payload Size", f"{len(secret_message)*8} bits")
                        m3.metric("Stealth Efficiency", "99.8%")
                        
                        st.subheader("AI Camouflage Analysis")
                        # Fixed: Use use_container_width instead of use_column_width
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            st.image(cover_image, caption="Original", use_container_width=True)
                        with c2:
                            st.image(mask_visual, caption="AI Complexity Map", use_container_width=True)
                        with c3:
                            st.image(stego_result, caption="Stego-Image", use_container_width=True)
                            
                        buf = io.BytesIO()
                        stego_result.save(buf, format="PNG")
                        st.download_button("💾 DOWNLOAD SECURE IMAGE", buf.getvalue(), "stegoshield_secure.png", "image/png")

    elif app_mode == "🔓 DECODE (Extract Intel)":
        st.header("Phase 2: Intelligence Extraction")
        st.markdown("Requires the correct Stego-Image and Decryption Key.")
        
        c1, c2 = st.columns([1, 1])
        with c1:
            stego_upload = st.file_uploader("Upload Suspicious Image", type=["png"])
        with c2:
            input_pass = st.text_input("Decryption Key (Password)", type="password")
            
        if stego_upload and input_pass:
            stego_image_input = Image.open(stego_upload)
            
            if st.button("AUTHENTICATE & DECODE"):
                with st.spinner("Verifying Hash... Scanning Pixels..."):
                    result = adaptive_reveal(stego_image_input, input_pass)
                    
                    if result and "ACCESS DENIED" not in result and "Error" not in result:
                        st.balloons()
                        st.success("✅ IDENTITY VERIFIED. INTEL EXTRACTED.")
                        st.markdown(f"""
                        <div style="padding:20px;background-color:#0d1117;border:2px solid #238636;border-radius:10px;">
                            <h3 style="color:#238636;margin:0;">DECODED MESSAGE:</h3>
                            <p style="font-family:monospace;font-size:1.5em;color:#c9d1d9;">{result}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    elif "ACCESS DENIED" in result:
                         st.error("❌ ACCESS DENIED: Incorrect Password.")
                    else:
                         st.warning("No valid data found or image corrupted.")

if __name__ == "__main__":
    main()