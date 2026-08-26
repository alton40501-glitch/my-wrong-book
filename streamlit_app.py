import streamlit as st
import cv2
import numpy as np
from PIL import Image
from datetime import datetime
import io
import os
import time

st.set_page_config(page_title="6-in-1 Smart Wrong-Book System", layout="centered")

FONT_NAME = 'Helvetica'
FONT_BOLD = 'Helvetica-Bold'

if 'wrong_questions' not in st.session_state:
    st.session_state.wrong_questions = []

st.title("📝 錯題本")
st.write("Fast continuous shooting. Color preview. PDF strictly marks specific category.")

# 網頁時間精準加 8 小時同步
web_timestamp = time.time() + (8 * 3600)
current_date = datetime.fromtimestamp(web_timestamp).strftime('%Y-%m-%d %H:%M:%S')
st.info(f"📅 Today's Date: {current_date}")

# 1. 分類標籤選擇
st.subheader("🎯 Select Category:")
note_type = st.radio(
    "Choose one category:",
    ["Concept", "Steps", "Review"],
    index=0
)

st.write("---")

# 2. 核心大升級：改用 st.file_uploader！在 iPad/手機上點擊會直接拉起精準的「背面原生大相機」
st.subheader("📸 Upload or Take a Photo")
uploaded_file = st.file_uploader("Tap here to take a photo using back camera or upload an image:", type=["jpg", "jpeg", "png"], label_visibility="collapsed")

# 只要拍好或選好照片，一秒鐘後台自動新增，完全不需要按任何清除或確認按鈕！
if uploaded_file is not None:
    img_bytes = uploaded_file.read()
    
    if 'last_processed_file' not in st.session_state or st.session_state.last_processed_file != uploaded_file.name:
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # 時間手工自動精準加 8 小時（28800秒）
        current_timestamp = time.time() + (8 * 3600)
        saved_time = datetime.fromtimestamp(current_timestamp).strftime('%Y-%m-%d %H:%M:%S')
        
        # 建立純白標籤畫布，用 Hershey 向量字體繪製時間與標籤，100% 永不變框框
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
        st.session_state.last_processed_file = uploaded_file.name
        st.toast(f"🎉 Question #{q_id} added successfully!")

st.write("---")

# 3. 獨立排在下方的彩色預覽區
st.subheader("🖼️ Latest Saved Photo")
if st.session_state.wrong_questions:
    preview_img = cv2.cvtColor(st.session_state.wrong_questions[-1]['img'], cv2.COLOR_BGR2RGB)
    st.image(preview_img, caption="Color Preview", use_container_width=True)
else:
    st.info("No photo saved yet. Tap the button above to capture your first question!")

# 4. 累積清單管理
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
        
        # 網格座標後台多重保險防洗白寫死
        start_x = [45, 310]
        start_y = [540, 280, 20]
        
        for idx, q in enumerate(st.session_state.wrong_questions):
            page_idx = idx % 6
            if idx > 0 and page_idx == 0:
                c.showPage()
                
            x_pos = start_x[page_idx % 2]
            y_pos = start_y[page_idx // 2]
            
            c.setStrokeColorRGB(0.7, 0.7, 0.7)
            c.setLineWidth(1)
            c.rect(x_pos, y_pos, col_width, row_height, stroke=1, fill=0)
            
            temp_lbl_path = f"temp_lbl_{q['id']}.jpg"
            cv2.imwrite(temp_lbl_path, q['label_img'])
            c.drawImage(temp_lbl_path, x_pos + 4, y_pos + row_height - 16, width=col_width - 8, height=12, preserveAspectRatio=False)
            
            c.setStrokeColorRGB(0.85, 0.85, 0.85)
            c.line(x_pos, y_pos + row_height - 18, x_pos + col_width, y_pos + row_height - 18)
            
            temp_path = f"temp_{q['id']}.jpg"
            cv2.imwrite(temp_path, q['img'], [int(cv2.IMWRITE_JPEG_QUALITY), 90])
            c.drawImage(temp_path, x_pos + 8, y_pos + 95, width=col_width - 16, height=120, preserveAspectRatio=True)
            
            c.setStrokeColorRGB(0.8, 0.8, 0.8)
            c.rect(x_pos + 8, y_pos + 8, col_width - 16, 75, stroke=1, fill=0)
            
            # 每題下方精準畫出 3 條手寫訂正格線
            c.setStrokeColorRGB(0.9, 0.9, 0.9)
            c.line(x_pos + 14, y_pos + 58, x_pos + col_width - 14, y_pos + 58)
            c.line(x_pos + 14, y_pos + 40, x_pos + col_width - 14, y_pos + 40)
            c.line(x_pos + 14, y_pos + 22, x_pos + col_width - 14, y_pos + 22)
            
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
