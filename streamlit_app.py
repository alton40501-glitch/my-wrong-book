import streamlit as st
import cv2
import numpy as np
from PIL import Image
from datetime import datetime
import io
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

st.set_page_config(page_title="6-in-1 Smart Wrong-Book System", layout="centered")

# Standard English Helvetica font to 100% avoid character rendering issues
FONT_NAME = 'Helvetica'
FONT_BOLD = 'Helvetica-Bold'

if 'wrong_questions' not in st.session_state:
    st.session_state.wrong_questions = []

if 'camera_key' not in st.session_state:
    st.session_state.camera_key = 0

st.title("📝 6-in-1 Smart Wrong-Book System")
st.write("Fast continuous shooting. Color preview. PDF strictly marks specific category.")

current_date = datetime.today().strftime('%Y-%m-%d')
st.info(f"📅 Today's Date: {current_date}")

# 1. Scope and Source Input
source = st.text_input("Enter Exam Source / Scope:", placeholder="e.g., Mock Exam, Unit 3...")

# 2. Category Selection
st.subheader("🎯 Select Category for this question:")
note_type = st.radio(
    "Choose one category:",
    ["Concept", "Steps", "Review"],
    index=0
)

# 3. Camera Input with Dynamic Key for Auto-Reset
uploaded_file = st.camera_input("📸 Take a photo of the question:", key=f"my_camera_{st.session_state.camera_key}")

# Process photo immediately when taken
if uploaded_file is not None:
    img_bytes = uploaded_file.read()
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    q_id = len(st.session_state.wrong_questions) + 1
    st.session_state.wrong_questions.append({
        "id": q_id,
        "img": img,
        "source": source if source else "Mock Exam",
        "date": current_date,
        "type": note_type
    })
    
    st.toast(f"🎉 Question #{q_id} added! (Type: {note_type})")
    
    # Auto-reset camera by changing the session key
    st.session_state.camera_key += 1
    st.rerun()

# 4. Color Preview of the Latest Question Added
if st.session_state.wrong_questions:
    st.success(f"📸 Latest photo saved successfully! Camera re-activated automatically.")
    preview_img = cv2.cvtColor(st.session_state.wrong_questions[-1]['img'], cv2.COLOR_BGR2RGB)
    st.image(preview_img, caption=f"Latest Question #{len(st.session_state.wrong_questions)} Color Preview", use_container_width=True)

# 5. List Management
if st.session_state.wrong_questions:
    st.write("---")
    st.subheader(f"📋 Current List ({len(st.session_state.wrong_questions)} questions)")
    
    for q in st.session_state.wrong_questions:
        st.write(f"**Question #{q['id']}** | Source: {q['source']} | Type: `{q['type']}`")

    st.write("---")
    # 6. PDF Packager
    if st.button("🚀 Pack and Export A4 Wrong-Book (PDF)"):
        pdf_buffer = io.BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=A4)
        width, height = A4
        
        # 6-in-1 layout configuration (2 columns x 3 rows)
        col_width = 240
        row_height = 240
        
        start_x = [45, 310]
        start_y = [540, 290, 40]
        
        for idx, q in enumerate(st.session_state.wrong_questions):
            page_idx = idx % 6
            if idx > 0 and page_idx == 0:
                c.showPage()
                
            x_pos = start_x[page_idx % 2]
            y_pos = start_y[page_idx // 2]
            
            # Draw borders
            c.setStrokeColorRGB(0.7, 0.7, 0.7)
            c.setLineWidth(1)
            c.rect(x_pos, y_pos, col_width, row_height, stroke=1, fill=0)
            
            # Header info
            c.setFont(FONT_NAME, 7.5)
            c.setFillColorRGB(0.3, 0.3, 0.3)
            c.drawString(x_pos + 6, y_pos + row_height - 13, f"Dt: {q['date']} | Src: {q['source']} | Type: {q['type']}")
            c.setStrokeColorRGB(0.85, 0.85, 0.85)
            c.line(x_pos, y_pos + row_height - 18, x_pos + col_width, y_pos + row_height - 18)
            
            # Color Image output
            temp_path = f"temp_{q['id']}.jpg"
            cv2.imwrite(temp_path, q['img'], [int(cv2.IMWRITE_JPEG_QUALITY), 90])
            c.drawImage(temp_path, x_pos + 8, y_pos + 95, width=col_width - 16, height=120, preserveAspectRatio=True)
            
            # Hand-written notes section
            c.setStrokeColorRGB(0.8, 0.8, 0.8)
            c.rect(x_pos + 8, y_pos + 8, col_width - 16, 75, stroke=1, fill=0)
            
            c.setFont(FONT_BOLD, 9)
            c.setFillColorRGB(0.2, 0.2, 0.2)
            c.drawString(x_pos + 14, y_pos + 68, f"[ Hand-written Notes for {q['type']} ]")
            
            c.setStrokeColorRGB(0.9, 0.9, 0.9)
            c.line(x_pos + 14, y_pos + 46, x_pos + col_width - 14, y_pos + 46)
            c.line(x_pos + 14, y_pos + 24, x_pos + col_width - 14, y_pos + 24)
            
            c.setFillColorRGB(0, 0, 0)
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
        c.setFont(FONT_NAME, 8)
        c.setFillColorRGB(0.6, 0.6, 0.6)
        c.drawString(45, 20, f"Generated by 6-in-1 Smart Wrong-Book System")
            
        c.save()
        pdf_buffer.seek(0)
        
        st.download_button(
            label="💾 Download 6-in-1 A4 PDF",
            data=pdf_buffer,
            file_name=f"WrongBook_{current_date}.pdf",
            mime="application/pdf"
        )
