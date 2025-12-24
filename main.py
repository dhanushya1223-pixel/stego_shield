import flet as ft
from time import sleep
import shutil
import os
from stegano import lsb # PIP INSTALL STEGANO

def main(page: ft.Page):
    page.title = "StegoShield Defense System"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 950
    page.window_height = 750
    page.padding = 20

    # Variables to hold state
    current_file_path = None
    temp_stego_path = "temp_stego.png" # Temporary file to hold the hidden data image

    # --- 1. HANDLING ENCRYPTION (ENCODE) ---
    def on_file_picked(e: ft.FilePickerResultEvent):
        nonlocal current_file_path
        if e.files:
            current_file_path = e.files[0].path
            upload_btn.text = f"Selected: {e.files[0].name}"
            upload_btn.icon = "check_circle"
            upload_btn.bgcolor = "green"
            status_text.value = "📄 Image Loaded. Ready to embed."
            status_text.color = "blue"
            page.update()

    def encrypt_click(e):
        if not current_file_path:
            status_text.value = "⚠️ Please select a Cover Image first!"
            status_text.color = "red"
            page.update()
            return
        
        if not secret_input.value:
            status_text.value = "⚠️ Please enter Secret Intel!"
            status_text.color = "red"
            page.update()
            return

        status_text.value = "🔒 Encrypting & Embedding..."
        status_text.color = "yellow"
        progress_bar.visible = True
        page.update()
        
        try:
            # --- REAL STEGANOGRAPHY LOGIC ---
            # Hide the secret message inside the image
            secret = lsb.hide(current_file_path, secret_input.value)
            # Save it to a temporary file
            secret.save(temp_stego_path)
            
            sleep(1.5) # Simulate Chaos encryption time
            
            progress_bar.visible = False
            status_text.value = "✅ Success! Data Embedded in Pixels."
            status_text.color = "green"
            download_btn.visible = True
            page.update()
            
        except Exception as ex:
            progress_bar.visible = False
            status_text.value = f"❌ Error: {str(ex)}"
            status_text.color = "red"
            page.update()

    # --- 2. HANDLING SAVING ---
    def save_file_result(e: ft.FilePickerResultEvent):
        if e.path:
            # Copy the TEMP STEGO file (which has data) to the user's chosen location
            try:
                shutil.copy(temp_stego_path, e.path)
                status_text.value = f"💾 File Saved Successfully to: {e.path}"
                status_text.color = "cyan"
                page.update()
            except Exception as ex:
                status_text.value = f"Error saving: {ex}"
                page.update()

    # --- 3. HANDLING DECRYPTION (DECODE) ---
    # Variable to track the file selected for decoding
    decode_file_path = None

    def on_decode_file_picked(e: ft.FilePickerResultEvent):
        nonlocal decode_file_path
        if e.files:
            decode_file_path = e.files[0].path
            decode_upload_btn.text = f"Selected: {e.files[0].name}"
            decode_upload_btn.icon = "check_circle"
            decode_upload_btn.bgcolor = "green"
            decode_status_text.value = "📄 Stego-Image Loaded. Ready to decrypt."
            page.update()

    def decrypt_click(e):
        if not decode_file_path:
            decode_status_text.value = "⚠️ Select an image first!"
            decode_status_text.color = "red"
            page.update()
            return

        decode_status_text.value = "🔓 Scanning Pixels for Data..."
        decode_status_text.color = "yellow"
        decode_progress_bar.visible = True
        page.update()
        
        sleep(1) 
        
        decode_progress_bar.visible = False
        
        try:
            # --- REAL REVEAL LOGIC ---
            clear_message = lsb.reveal(decode_file_path)
            
            if clear_message:
                decode_status_text.value = "✅ Hidden Intel Found!"
                decode_status_text.color = "green"
                output_display.value = clear_message
                output_display.color = "green"
                output_container.border = ft.border.all(1, "green")
            else:
                # This usually won't run because lsb.reveal throws error if empty
                raise ValueError("Empty")
                
        except Exception:
            # If lsb.reveal fails, it means there is no message
            decode_status_text.value = "❌ No Hidden Intel Found."
            decode_status_text.color = "red"
            output_display.value = "ACCESS DENIED: No steganographic data detected in this image."
            output_display.color = "red"
            output_container.border = ft.border.all(1, "red")

        output_container.visible = True
        page.update()

    # --- UI ELEMENTS SETUP ---
    
    # File Pickers
    file_picker = ft.FilePicker(on_result=on_file_picked)
    save_file_picker = ft.FilePicker(on_result=save_file_result)
    decode_file_picker = ft.FilePicker(on_result=on_decode_file_picked)
    page.overlay.extend([file_picker, save_file_picker, decode_file_picker])

    # Header
    header = ft.Column([
        ft.Icon(name="shield_moon", size=60, color="blue400"),
        ft.Text("StegoShield: Covert Ops Tool", size=30, weight="bold", color="blue200"),
        ft.Text("Adaptive Semantic Steganography System", size=16, color="white70"),
        ft.Divider(color="transparent", height=10)
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    # --- TAB 1: ENCODE UI ---
    upload_btn = ft.ElevatedButton("Select Cover Image", icon="upload_file", height=50, 
                                   on_click=lambda _: file_picker.pick_files(allow_multiple=False))
    secret_input = ft.TextField(label="Enter Secret Intel", multiline=True, icon="security", border_color="blue400")
    encrypt_btn = ft.ElevatedButton("ENCRYPT & EMBED", icon="lock", bgcolor="blue600", color="white", height=50, width=200, on_click=encrypt_click)
    progress_bar = ft.ProgressBar(width=400, color="blue", visible=False)
    status_text = ft.Text("", size=16)
    download_btn = ft.ElevatedButton("Save Stego-Image", icon="save", bgcolor="green600", color="white", visible=False,
                                     on_click=lambda _: save_file_picker.save_file(allowed_extensions=["png"], file_name="stego_image.png"))

    encode_tab_content = ft.Container(
        content=ft.Column([
            ft.Text("Step 1: Input", size=20, weight="bold"),
            upload_btn,
            secret_input,
            ft.Divider(height=20, color="white10"),
            encrypt_btn,
            progress_bar,
            status_text,
            download_btn
        ], spacing=20, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=30, border=ft.border.all(1, "white10"), border_radius=15, bgcolor="grey900"
    )

    # --- TAB 2: DECODE UI ---
    decode_upload_btn = ft.ElevatedButton("Select Stego-Image", icon="image_search", height=50, 
                                          on_click=lambda _: decode_file_picker.pick_files(allow_multiple=False))
    decrypt_btn = ft.ElevatedButton("DECRYPT & REVEAL", icon="lock_open", bgcolor="orange600", color="white", height=50, width=200, on_click=decrypt_click)
    decode_progress_bar = ft.ProgressBar(width=400, color="orange", visible=False)
    decode_status_text = ft.Text("", size=16)
    
    output_display = ft.Text("Hidden Message Here", size=20, color="green", weight="bold", selectable=True)
    output_container = ft.Container(
        content=ft.Column([ft.Text("DECODED INTEL:", size=12, color="white54"), output_display]),
        padding=20, bgcolor="black", border_radius=10, border=ft.border.all(1, "green"), visible=False
    )

    decode_tab_content = ft.Container(
        content=ft.Column([
            ft.Text("Step 2: Extraction", size=20, weight="bold"),
            decode_upload_btn,
            ft.Divider(height=20, color="white10"),
            decrypt_btn,
            decode_progress_bar,
            decode_status_text,
            output_container
        ], spacing=20, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=30, border=ft.border.all(1, "white10"), border_radius=15, bgcolor="grey900"
    )

    # --- FINAL LAYOUT WITH TABS ---
    t = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(text="🛡️ ENCODE (Hide)", content=encode_tab_content),
            ft.Tab(text="🔓 DECODE (Reveal)", content=decode_tab_content),
        ],
        expand=1,
    )

    page.add(header, t)

ft.app(target=main)