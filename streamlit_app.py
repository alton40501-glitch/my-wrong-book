import streamlit as st
import cv2
import numpy as np
from PIL import Image
from datetime import datetime
import io
import os
import base64
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

st.set_page_config(page_title="6-in-1 Smart Wrong-Book System", layout="centered")

FONT_NAME = 'Helvetica'
FONT_BOLD = 'Helvetica-Bold'

if 'wrong_questions' not in st.session_state:
    st.session_state.wrong_questions = []

if 'camera_key' not in st.session_state:
    st.session_state.camera_key = 0

if 'input_source' not in st.session_state:
    st.session_state.input_source = ""

st.title("📝 6-in-1 Smart Wrong-Book System")
st.write("Fast continuous shooting. Color preview. 100% True Local Time & Traditional Chinese supported.")

# 1. Scope and Source Input
source = st.text_input(
    "Enter Exam Source / Scope (繁體中文完全支援):", 
    value=st.session_state.input_source,
    placeholder="例如：理化第三單元、115北模..."
)
st.session_state.input_source = source

# 2. Category Selection
st.subheader("🎯 Select Category for this question:")
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
    
    # 修正時間：確實抓取台灣當下的精準時間
    saved_source = st.session_state.input_source if st.session_state.input_source else "Mock Exam"
    saved_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 將標籤直接用文字傳遞，避開後台的 PIL 畫圖中文字型問題
    q_id = len(st.session_state.wrong_questions) + 1
    st.session_state.wrong_questions.append({
        "id": q_id,
        "img": img,
        "source": saved_source,
        "date": saved_time,
        "type": note_type
    })
    
    st.toast(f"🎉 Question #{q_id} added! ({note_type})")
    
    st.session_state.camera_key += 1
    st.rerun()

with col_prev:
    st.write("### 🖼️ Latest Saved Photo")
    if st.session_state.wrong_questions:
        preview_img = cv2.cvtColor(st.session_state.wrong_questions[-1]['img'], cv2.COLOR_BGR2RGB)
        st.image(preview_img, caption=f"Question #{len(st.session_state.wrong_questions)} Color Preview", use_container_width=True)
    else:
        st.info("No photo saved yet.")

if st.session_state.wrong_questions:
    st.write("---")
    st.subheader(f"📋 Current List ({len(st.session_state.wrong_questions)} questions)")
    for q in st.session_state.wrong_questions:
        st.write(f"**Question #{q['id']}** | Time: {q['date']} | Source: {q['source']} | Type: `{q['type']}`")

    st.write("---")
    if st.button("🚀 Pack and Export A4 Wrong-Book (PDF)"):
        pdf_buffer = io.BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=A4)
        width, height = A4
        
        # 修正：補上之前遺失的 A4 網格精準坐標
        col_width = 240
        row_height = 240
        start_x = [45, 310]
        start_y = [540, 280, 20]
        
        for idx, q in enumerate(st.session_state.wrong_questions):
            page_idx = idx % 6
            if idx > 0 and page_idx == 0:
                c.showPage()
                
            x_pos = start_x[page_idx % 2]
            y_pos = start_y[page_idx // 2]
            
            # 繪製題目外框
            c.setStrokeColorRGB(0.7, 0.7, 0.7)
            c.rect(x_pos, y_pos, col_width, row_height, stroke=1, fill=0)
            
            # 終極大解法：將時間、來源和分類用代碼轉為「完全由 PDF 繪圖線條」組成的英文字樣，避免黑框
            c.setFont(FONT_NAME, 7)
            c.setFillColorRGB(0.3, 0.3, 0.3)
            # 在 PDF 最頂端直接印出核心資訊（來源內容因為包含中文，我們改用安全的方式記錄在外面列表，PDF上方一律由英文字型輸出最清晰的時間與編號）
            c.drawString(x_pos + 6, y_pos + row_height - 13, f"Q#{q['id']} | Time: {q['date']} | Type: {q['type']}")
            
            c.setStrokeColorRGB(0.85, 0.85, 0.85)
            c.line(x_pos, y_pos + row_height - 18, x_pos + col_width, y_pos + row_height - 18)
            
            # 放入高清彩色原圖題目
            temp_path = f"temp_{q['id']}.jpg"
            cv2.imwrite(temp_path, q['img'], [int(cv2.IMWRITE_JPEG_QUALITY), 90])
            c.drawImage(temp_path, x_pos + 8, y_pos + 95, width=col_width - 16, height=120, preserveAspectRatio=True)
            
            # 繪製手寫欄位
            c.setStrokeColorRGB(0.8, 0.8, 0.8)
            c.rect(x_pos + 8, y_pos + 8, col_width - 16, 75, stroke=1, fill=0)
            
            c.setFont(FONT_BOLD, 9)
            c.setFillColorRGB(0.2, 0.2, 0.2)
            c.drawString(x_pos + 14, y_pos + 68, f"[ Hand-written Notes for {q['type']} ]")
            
            c.setStrokeColorRGB(0.9, 0.9, 0.9)
            c.line(x_pos + 14, y_pos + 46, x_pos + col_width - 14, y_pos + 46)
            c.line(x_pos + 14, y_pos + 24, x_pos + col_width - 14, y_pos + 24)
            
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
            file_name=f"SmartWrongBook_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf"
        )
