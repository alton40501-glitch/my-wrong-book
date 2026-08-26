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

# 核心修正 1：網頁大標題精簡改為「錯題本」
st.title("📝 錯題本")
st.write("Fast continuous shooting. Color preview. PDF strictly marks specific category.")

current_date = datetime.today().strftime('%Y-%m-%d')
st.info(f"📅 Today's Date: {current_date}")

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
    
    # 核心修正 2：時間自動加上 8 小時（28800秒）補回台灣當下精準時區
    current_timestamp = time.time() + (8 * 3600)
    saved_time = datetime.fromtimestamp(current_timestamp).strftime('%Y-%m-%d %H:%M:%S')
    
    # 建立純白標籤畫布，使用絕對不變框框的 Hershey 純英文向量線條字體繪製時間與標籤
    label_img = np.ones((30, 480, 3), dtype=np.uint8) * 255
    safe_text = f"Time: {saved_time} | Tag: {note_type}"
    cv2.putText(label_img, safe_text, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (50, 50, 50), 1, cv2.LINE_AA)
    
    q_id = len(st.session_state.wrong_questions) + 1
    st.session_state.wrong_questions.append({
        "id": q_id,
        "img": img,
        "label_img": label_img, 
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
        st.write(f"**Question #{q['id']}** | Time: {q['date']} | Tag: `{q['type']}`")

    st.write("---")
    if st.button("🚀 Pack and Export A4 Wrong-Book (PDF)"):
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        
        pdf_buffer = io.BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=A4)
        width, height = A4
        
        col_width = 240
        row_height = 240
        
        # 1頁6題網格座標參數（防系統洗版安全包裝）
        start_x =
        start_y =
        
        for idx, q in enumerate(st.session_state.wrong_questions):
            page_idx = idx % 6
            if idx > 0 and page_idx == 0:
                c.showPage()
                
            x_pos = start_x[page_idx % 2]
            y_pos = start_y[page_idx // 2]
            
            # 繪製題目的灰色外框
            c.setStrokeColorRGB(0.7, 0.7, 0.7)
            c.setLineWidth(1)
            c.rect(x_pos, y_pos, col_width, row_height, stroke=1, fill=0)
            
            # 置入 100% 絕不變框框、時間精準加8的標籤貼紙
            temp_lbl_path = f"temp_lbl_{q['id']}.jpg"
            cv2.imwrite(temp_lbl_path, q['label_img'])
            c.drawImage(temp_lbl_path, x_pos + 4, y_pos + row_height - 16, width=col_width - 8, height=12, preserveAspectRatio=False)
            
            c.setStrokeColorRGB(0.85, 0.85, 0.85)
            c.line(x_pos, y_pos + row_height - 18, x_pos + col_width, y_pos + row_height - 18)
            
            # 置入彩色題目原圖
            temp_path = f"temp_{q['id']}.jpg"
            cv2.imwrite(temp_path, q['img'], [int(cv2.IMWRITE_JPEG_QUALITY), 90])
            c.drawImage(temp_path, x_pos + 8, y_pos + 95, width=col_width - 16, height=120, preserveAspectRatio=True)
            
            # 繪製完全空白的手寫大框框
            c.setStrokeColorRGB(0.8, 0.8, 0.8)
            c.rect(x_pos + 8, y_pos + 8, col_width - 16, 75, stroke=1, fill=0)
            
            # 核心修正 3：在大框框內精準均勻畫出 3 條淡淡的淺灰色橫格線（剛好可以工整地寫滿 3 行筆記欄！）
            c.setStrokeColorRGB(0.9, 0.9, 0.9)
            c.line(x_pos + 14, y_pos + 58, x_pos + col_width - 14, y_pos + 58) # 第 1 條線
            c.line(x_pos + 14, y_pos + 40, x_pos + col_width - 14, y_pos + 40) # 第 2 條線
            c.line(x_pos + 14, y_pos + 22, x_pos + col_width - 14, y_pos + 22) # 第 3 條線
            
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
