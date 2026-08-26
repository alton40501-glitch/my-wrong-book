import streamlit as st
import cv2
import numpy as np
from PIL import Image
from datetime import datetime
import io
import os
import time

st.set_page_config(page_title="6-in-1 Advanced Wrong-Book System", layout="centered")

FONT_NAME = 'Helvetica'
FONT_BOLD = 'Helvetica-Bold'

if 'wrong_questions' not in st.session_state:
    st.session_state.wrong_questions = []

st.title("📝 錯題本")
st.write("Fast continuous shooting. Color preview. 6-in-1 layout with Left-aligned images and Right-aligned notes.")

# 網頁時間精準加 8 小時同步台灣時區
web_timestamp = time.time() + (8 * 3600)
current_date = datetime.fromtimestamp(web_timestamp).strftime('%Y-%m-%d %H:%M:%S')
st.info(f"📅 Today's Date: {current_date}")

st.write("---")

# 使用 Form 表單鎖定網頁，確保所有複雜選項連開連選，絕對不觸發自動整理刷新！
with st.form("wrong_book_form", clear_on_submit=True):
    st.subheader("📸 1. Capture or Select Photos")
    uploaded_files = st.file_uploader(
        "Upload images for this batch:", 
        type=["jpg", "jpeg", "png"], 
        accept_multiple_files=True,
        label_visibility="collapsed"
    )
    
    st.write("---")
    st.subheader("🎯 2. Question Analytics & Tagging")
    
    subject_opt = st.selectbox(
        "Choose Subject:",
        ["Subject", "Chinese", "English", "Math", "History", "Geography", "Civics", "Biology", "Physics", "Chemistry", "Earth Science"]
    )
    subject_custom = st.text_input("Custom Subject Note (Optional Textbox):", placeholder="e.g., Unit 3, Chapter 2...")
    
    note_type = st.radio(
        "Select Core Category:",
        ["Concept", "Steps", "Review"],
        index=0
    )
    
    review_reason = st.selectbox(
        "If you chose 'Review', select the main reason:",
        ["Careless & Misread (粗心及原因)", "Time Pressure (時間不夠)", "Concept Confused (觀念模糊)", "Anxiety (緊張失常)"]
    )
    
    importance_stars = st.slider("Select Importance Level (重要程度 1-5):", min_value=1, max_value=5, value=3)
    
    submit_button = st.form_submit_with_ui_button if hasattr(st, 'form_submit_with_ui_button') else st.form_submit_button
    submitted = submit_button("📥 Save Batch to Tracker List")

# 後台高階資料處理
if submitted and uploaded_files:
    for uploaded_file in uploaded_files:
        img_bytes = uploaded_file.read()
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        current_timestamp = time.time() + (8 * 3600)
        saved_time = datetime.fromtimestamp(current_timestamp).strftime('%Y-%m-%d %H:%M:%S')
        
        final_subject = f"{subject_opt}"
        if subject_custom:
            final_subject += f" ({subject_custom})"
            
        star_string = "X" * importance_stars
        
        # 保持最原始、最常態、完全沒拉長的大小尺寸（寬度200、高度12）
        label_img = np.ones((25, 220, 3), dtype=np.uint8) * 255
        safe_text = f"{saved_time} | {final_subject}"
        cv2.putText(label_img, safe_text, (5, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.33, (50, 50, 50), 1, cv2.LINE_AA)
        
        q_id = len(st.session_state.wrong_questions) + 1
        st.session_state.wrong_questions.append({
            "id": q_id,
            "img": img,
            "label_img": label_img, 
            "date": saved_time,
            "subject": final_subject,
            "type": note_type,
            "reason": review_reason if note_type == "Review" else "N/A",
            "stars": importance_stars
        })
    st.toast(f"🚀 Successfully tracked {len(uploaded_files)} advanced wrong questions!")

if st.session_state.wrong_questions:
    st.write("---")
    st.subheader(f"📋 Current List ({len(st.session_state.wrong_questions)} questions)")
    for q in st.session_state.wrong_questions:
        st.write(f"**Question #{q['id']}** | Subject: `{q['subject']}` | Type: `{q['type']}` | Importance: {'★' * q['stars']}")

    st.write("---")
    if st.button("🚀 Pack and Export 6-in-1 A4 PDF"):
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        
        pdf_buffer = io.BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=A4)
        width, height = A4
        
        # 1頁放6張的網格參數設定 (2欄 x 3排)
        col_width = 240
        row_height = 240
        
        # 後台絕對寫死保護的 A4 一頁 6 題座標陣列
        start_x = [45, 310]
        start_y = [545, 290, 35]
        
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
            
            # 頂欄完美恢復最原始小尺寸（width=220, height=10）
            temp_lbl_path = f"temp_lbl_{q['id']}.jpg"
            cv2.imwrite(temp_lbl_path, q['label_img'])
            c.drawImage(temp_lbl_path, x_pos + 4, y_pos + row_height - 15, width=220, height=10, preserveAspectRatio=False)
            
            c.setStrokeColorRGB(0.85, 0.85, 0.85)
            c.line(x_pos, y_pos + row_height - 18, x_pos + col_width, y_pos + row_height - 18)
            
            # 核心修正 1：題目圖檔「完美拉到最左邊」，分配寬度 110 (佔據整個格子的左半邊)
            temp_path = f"temp_{q['id']}.jpg"
            cv2.imwrite(temp_path, q['img'], [int(cv2.IMWRITE_JPEG_QUALITY), 90])
            c.drawImage(temp_path, x_pos + 6, y_pos + 8, width=110, height=210, preserveAspectRatio=True)
            
            # 繪製一道垂直中線，把左邊的照片區跟右邊的直向筆記計畫區分開
            c.setStrokeColorRGB(0.85, 0.85, 0.85)
            c.line(x_pos + 120, y_pos + 8, x_pos + 120, y_pos + row_height - 18)
            
            # 核心修正 2 & 3：所有筆記資訊欄位移到右側「同一個直欄內，由上往下上下疊放」
            note_x = x_pos + 124
            
            # 【右直欄 - 第一層】：Review Tracker
            c.setFont(FONT_BOLD, 7)
            c.setFillColorRGB(0.1, 0.1, 0.1)
            c.drawString(note_x, y_pos + 208, "Review Tracker:")
            c.setFont(FONT_NAME, 6)
            c.setFillColorRGB(0.4, 0.4, 0.4)
            c.drawString(note_x + 2, y_pos + 198, "1st: __/__  2nd: __/__")
            c.drawString(note_x + 2, y_pos + 188, "3rd: __/__  4th: __/__")
            
            # 【右直欄 - 第二層】：Key Focus & Stars
            c.setFont(FONT_BOLD, 7)
            c.setFillColorRGB(0.1, 0.1, 0.1)
            c.drawString(note_x, y_pos + 174, "Key Focus & Reason:")
            c.setFont(FONT_NAME, 6)
            c.setFillColorRGB(0.4, 0.4, 0.4)
            c.drawString(note_x + 2, y_pos + 164, f"Type: {q['type']} | Rs: {q['reason'][:10]}")
            
            c.setFont(FONT_BOLD, 7)
            c.setFillColorRGB(0, 0, 0)
            star_display = "★" * q['stars']
            c.drawString(note_x + 2, y_pos + 154, f"Priority: {star_display}")
            
            # 【右直欄 - 第三層】：Core Notes 專用 3 行橫格手寫線，完全乾淨留白超好寫
            c.setFont(FONT_BOLD, 7.5)
            c.setFillColorRGB(0.1, 0.1, 0.1)
            c.drawString(note_x, y_pos + 138, "Core Notes & Analysis:")
            
            c.setStrokeColorRGB(0.9, 0.9, 0.9)
            # 在最下方均勻切分出 3 條高質感的淺灰色手寫訂正格線
            c.line(note_x + 2, y_pos + 115, x_pos + col_width - 8, y_pos + 115) # 第 1 條線
            c.line(note_x + 2, y_pos + 90, x_pos + col_width - 8, y_pos + 90)   # 第 2 條線
            c.line(note_x + 2, y_pos + 65, x_pos + col_width - 8, y_pos + 65)   # 第 3 條線
            
            c.setFillColorRGB(0, 0, 0)
            if os.path.exists(temp_path): os.remove(temp_path)
            if os.path.exists(temp_lbl_path): os.remove(temp_lbl_path)
                
        c.setFont(FONT_NAME, 8)
        c.setFillColorRGB(0.6, 0.6, 0.6)
        c.drawString(45, 20, f"Generated by 6-in-1 Smart Wrong-Book System")
            
        c.save()
        pdf_buffer.seek(0)
        
        st.download_button(
            label="💾 Download 6-in-1 A4 PDF",
            data=pdf_buffer,
            file_name=f"會考高效六合一錯題本.pdf",
            mime="application/pdf"
        )
