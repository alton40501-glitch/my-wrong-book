import streamlit as st
import cv2
import numpy as np
from PIL import Image
from datetime import datetime
import io
import os
import time

st.set_page_config(page_title="6-in-1 Smart Wrong-Book System", layout="centered")

# Standard English Helvetica font to prevent any block rendering issue
FONT_NAME = 'Helvetica'
FONT_BOLD = 'Helvetica-Bold'

if 'wrong_questions' not in st.session_state:
    st.session_state.wrong_questions = []

st.title("📝 錯題本 (Continuous batch version)")
st.write("零阻礙流：一次選取多張考卷照片，批量分類，一鍵打包 A4 六合一複習卷！")

# 網頁時間精準加 8 小時同步台灣時區
web_timestamp = time.time() + (8 * 3600)
current_date = datetime.fromtimestamp(web_timestamp).strftime('%Y-%m-%d %H:%M:%S')
st.info(f"📅 Today's Date: {current_date}")

st.write("---")

# 【核心大升級】使用 Form 表單鎖定網頁，讓你怎麼選、怎麼拍都絕對不會觸發自動刷新！
with st.form("wrong_book_form", clear_on_submit=True):
    st.subheader("📸 1. Select or Capture Multiple Photos")
    # 支援一次打包複數上傳，你可以用平板相機連續拍好幾張，再一次丟進來！
    uploaded_files = st.file_uploader(
        "Capture/Upload multiple images at once:", 
        type=["jpg", "jpeg", "png"], 
        accept_multiple_files=True,
        label_visibility="collapsed"
    )
    
    st.subheader("🎯 2. Select Category for this Batch")
    note_type = st.radio(
        "All uploaded questions in this batch will be tagged as:",
        ["Concept", "Steps", "Review"],
        index=0
    )
    
    # 按下這個按鈕，才會一口氣把所有照片收進清單，徹底解決「不能連開連選」的痛點！
    submit_button = st.form_submit_with_ui_button if hasattr(st, 'form_submit_with_ui_button') else st.form_submit_button
    submitted = submit_button("📥 Save All Captured Questions to List")

# 後台處理批量照片
if submitted and uploaded_files:
    for uploaded_file in uploaded_files:
        img_bytes = uploaded_file.read()
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # 每題拍照存檔時，精準戳記台灣當下的秒數
        current_timestamp = time.time() + (8 * 3600)
        saved_time = datetime.fromtimestamp(current_timestamp).strftime('%Y-%m-%d %H:%M:%S')
        
        # 用內建向量 Hershey 字體繪製時間與標籤，100% 絕不變框框
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
    st.toast(f"🎉 Successfully added {len(uploaded_files)} questions to your list!")

st.write("---")

# 獨立排在下方的彩色預覽區
st.subheader("🖼️ Latest Saved Photo Preview")
if st.session_state.wrong_questions:
    preview_img = cv2.cvtColor(st.session_state.wrong_questions[-1]['img'], cv2.COLOR_BGR2RGB)
    st.image(preview_img, caption=f"Latest Question #{len(st.session_state.wrong_questions)} Color Preview", use_container_width=True)
else:
    st.info("No photo saved yet. Add questions via the form above!")

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
        
        # 網格座標後台安全保護寫死 (1頁6題)
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
            
            # 置入 100% 絕不變框框、時間精準加8的向量標籤貼紙
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
