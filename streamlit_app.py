import streamlit as st
import cv2
import numpy as np
from PIL import Image
from datetime import datetime
import io
import os
import time

st.set_page_config(page_title="6-in-1 Smart Wrong-Book System", layout="centered")

# Standard English Helvetica font
FONT_NAME = 'Helvetica'
FONT_BOLD = 'Helvetica-Bold'

if 'wrong_questions' not in st.session_state:
    st.session_state.wrong_questions = []

if 'camera_key' not in st.session_state:
    st.session_state.camera_key = 0

if 'input_source' not in st.session_state:
    st.session_state.input_source = ""

st.title("📝 6-in-1 Smart Wrong-Book System")

# 1. Scope and Source Input
source = st.text_input(
    "Enter Exam Source / Scope:", 
    value=st.session_state.input_source,
    placeholder="例如：理化第三單元、115北模..."
)
st.session_state.input_source = source

# 2. Category Selection
st.subheader("🎯 Select Category:")
note_type = st.radio(
    "Choose one category:",
    ["Concept", "Steps", "Review"],
    index=0
)

# 3. Layout (Camera on left, Preview on right)
col_cam, col_prev = st.columns(2)

with col_cam:
    st.write("### 📸 Camera Window")
    uploaded_file = st.camera_input("Take a photo of the question:", key=f"my_camera_{st.session_state.camera_key}", label_visibility="collapsed")

# Process photo immediately when taken
if uploaded_file is not None:
    img_bytes = uploaded_file.read()
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    saved_source = st.session_state.input_source if st.session_state.input_source else "Mock Exam"
    
    # 終極修正：直接用秒數手工加上 28800 秒（8小時），100% 避開 timedelta 工具未引入的錯誤！
    current_timestamp = time.time() + (8 * 3600)
    saved_time = datetime.fromtimestamp(current_timestamp).strftime('%Y-%m-%d %H:%M:%S')
    
    # 建立純白標籤畫布
    label_img = np.ones((30, 480, 3), dtype=np.uint8) * 255
    # 使用絕對不會變框框的內建向量線條字體繪製時間與分類
    safe_text = f"Time: {saved_time} | Tag: {note_type}"
    cv2.putText(label_img, safe_text, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (50, 50, 50), 1, cv2.LINE_AA)
    
    q_id = len(st.session_state.wrong_questions) + 1
    st.session_state.wrong_questions.append({
        "id": q_id,
        "img": img,
        "label_img": label_img, 
        "source": saved_source,
        "date": saved_time,
        "type": note_type
    })
    
    st.session_state.camera_key += 1
    st.rerun()

with col_prev:
    st.write("### 🖼️ Latest Saved Photo")
    if st.session_state.wrong_questions:
        preview_img = cv2.cvtColor(st.session_state.wrong_questions[-1]['img'], cv2.COLOR_BGR2RGB)
        st.image(preview_img, caption="Color Preview", use_container_width=True)
    else:
        st.info("No photo saved yet.")

# 4. List Management
if st.session_state.wrong_questions:
    st.write("---")
    st.subheader(f"📋 Current List ({len(st.session_state.wrong_questions)} questions)")
    for q in st.session_state.wrong_questions:
        st.write(f"**Question #{q['id']}** | Time: {q['date']} | Source: {q['source']} | Tag: `{q['type']}`")

    st.write("---")
    if st.button("🚀 Pack and Export A4 Wrong-Book (PDF)"):
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        
        pdf_buffer = io.BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=A4)
        width, height = A4
        
        col_width = 240
        row_height = 240
        
        # 用安全乘法代碼鎖定坐標，防止數值被系統洗掉變空白
        start_x = [45, 310]
        start_y = [540, 290, 40]
        
        for idx, q in enumerate(st.session_state.wrong_questions):
            page_idx = idx % 6
            if idx > 0 and page_idx == 0:
                c.showPage()
                
            x_pos = start_x[page_idx % 2]
            y_pos = start_y[page_idx // 2]
            
            # Draw boundaries
            c.setStrokeColorRGB(0.7, 0.7, 0.7)
            c.setLineWidth(1)
            c.rect(x_pos, y_pos, col_width, row_height, stroke=1, fill=0)
            
            # Insert the safe vector label image (100% correct time & no boxes)
            temp_lbl_path = f"temp_lbl_{q['id']}.jpg"
            cv2.imwrite(temp_lbl_path, q['label_img'])
            c.drawImage(temp_lbl_path, x_pos + 4, y_pos + row_height - 16, width=col_width - 8, height=12, preserveAspectRatio=False)
            
            c.setStrokeColorRGB(0.85, 0.85, 0.85)
            c.line(x_pos, y_pos + row_height - 18, x_pos + col_width, y_pos + row_height - 18)
            
            # Insert question photo
            temp_path = f"temp_{q['id']}.jpg"
            cv2.imwrite(temp_path, q['img'], [int(cv2.IMWRITE_JPEG_QUALITY), 90])
            c.drawImage(temp_path, x_pos + 8, y_pos + 95, width=col_width - 16, height=120, preserveAspectRatio=True)
            
            # Hand-written notes block (100% clean and blank)
            c.setStrokeColorRGB(0.8, 0.8, 0.8)
            c.rect(x_pos + 8, y_pos + 8, col_width - 16, 75, stroke=1, fill=0)
            
            # Two light gray lines for notes
            c.setStrokeColorRGB(0.9, 0.9, 0.9)
            c.line(x_pos + 14, y_pos + 52, x_pos + col_width - 14, y_pos + 52)
            c.line(x_pos + 14, y_pos + 28, x_pos + col_width - 14, y_pos + 28)
            
            if os.path.exists(temp_path): os.remove(temp_path)
            if os.path.exists(temp_lbl_path): os.remove(temp_lbl_path)
                
        c.save()
        pdf_buffer.seek(0)
        
        st.download_button(
            label="💾 Download 6-in-1 A4 PDF",
            data=pdf_buffer,
            file_name=f"會考高效錯題本.pdf",
            mime="application/pdf"
        )
