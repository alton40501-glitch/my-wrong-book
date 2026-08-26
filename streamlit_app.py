import streamlit as st
import cv2
import numpy as np
from PIL import Image
from datetime import datetime
import io
import os
import time

st.set_page_config(page_title="會考高階精準錯題筆記系統", layout="centered")

FONT_NAME = 'Helvetica'
FONT_BOLD = 'Helvetica-Bold'

if 'wrong_questions' not in st.session_state:
    st.session_state.wrong_questions = []

st.title("📝 錯題本")
st.write("Fast continuous shooting. Color preview. PDF strictly marks specific category.")

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
    submitted = submit_button("📥 Save Batch to High-Advanced Tracker List")

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
            
        # 核心優化 3：後台標籤改用最安全的實心大星號標記
        star_string = "X" * importance_stars
        
        label_img = np.ones((30, 480, 3), dtype=np.uint8) * 255
        safe_text = f"Time: {saved_time} | Sub: {final_subject} | Tag: {note_type} | Imp: {star_string}"
        cv2.putText(label_img, safe_text, (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (40, 40, 40), 1, cv2.LINE_AA)
        
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
    st.subheader(f"📋 Current High-Advanced List ({len(st.session_state.wrong_questions)} questions)")
    for q in st.session_state.wrong_questions:
        st.write(f"**Question #{q['id']}** | Subject: `{q['subject']}` | Type: `{q['type']}` | Importance: {'★' * q['stars']}")

    st.write("---")
    if st.button("🚀 Pack and Export Advanced A4 Wrong-Book (PDF)"):
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        
        pdf_buffer = io.BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=A4)
        width, height = A4
        
        col_width = 500  
        row_height = 245 
        
        # A4 1頁3題精準座標（後台全自動鎖定保護，防洗白寫死）
        start_y = [545, 290, 35]
        
        for idx, q in enumerate(st.session_state.wrong_questions):
            page_idx = idx % 3
            if idx > 0 and page_idx == 0:
                c.showPage()
                
            x_pos = 48 
            y_pos = start_y[page_idx]
            
            # 1. 繪製精美大外框
            c.setStrokeColorRGB(0.6, 0.6, 0.6)
            c.setLineWidth(1)
            c.rect(x_pos, y_pos, col_width, row_height, stroke=1, fill=0)
            
            # 2. 置入時間與科目頂部標籤貼紙
            temp_lbl_path = f"temp_lbl_{q['id']}.jpg"
            cv2.imwrite(temp_lbl_path, q['label_img'])
            c.drawImage(temp_lbl_path, x_pos + 4, y_pos + row_height - 16, width=col_width - 8, height=12, preserveAspectRatio=False)
            
            c.setStrokeColorRGB(0.8, 0.8, 0.8)
            c.line(x_pos, y_pos + row_height - 18, x_pos + col_width, y_pos + row_height - 18)
            
            # 核心優化 1：照片縮減寬度並「精準往左邊推過去」，留出右側與下方的黃金空白，絕對不再壓到文字！
            temp_path = f"temp_{q['id']}.jpg"
            cv2.imwrite(temp_path, q['img'], [int(cv2.IMWRITE_JPEG_QUALITY), 90])
            c.drawImage(temp_path, x_pos + 12, y_pos + 92, width=col_width - 35, height=130, preserveAspectRatio=True)
            
            # 4. 底部完全留白大計畫框
            c.rect(x_pos + 12, y_pos + 8, col_width - 24, 75, stroke=1, fill=0)
            
            # 核心優化 2：1st 到 4th 複習日期追蹤計畫表重新計算 Y 軸，完美對齊排列！
            c.setFont(FONT_BOLD, 8)
            c.setFillColorRGB(0.1, 0.1, 0.1)
            c.drawString(x_pos + 18, y_pos + 68, "Review Tracker:")
            
            c.setFont(FONT_NAME, 8)
            c.setFillColorRGB(0.3, 0.3, 0.3)
            # 均勻垂直分佈 4 次寫字線，字體絕不疊在一起
            c.drawString(x_pos + 20, y_pos + 52, "1st:  ____ / ____")
            c.drawString(x_pos + 20, y_pos + 39, "2nd:  ____ / ____")
            c.drawString(x_pos + 20, y_pos + 26, "3rd:  ____ / ____")
            c.drawString(x_pos + 20, y_pos + 13, "4th:  ____ / ____")
            
            # 第一道垂直垂直切分線
            c.setStrokeColorRGB(0.85, 0.85, 0.85)
            c.line(x_pos + 130, y_pos + 8, x_pos + 130, y_pos + 75)
            
            # 中間欄位：3行高質感手寫橫格線
            c.setFont(FONT_BOLD, 8)
            c.setFillColorRGB(0.1, 0.1, 0.1)
            c.drawString(x_pos + 138, y_pos + 68, "Core Notes & Analysis:")
            c.line(x_pos + 138, y_pos + 50, x_pos + 335, y_pos + 50)
            c.line(x_pos + 138, y_pos + 32, x_pos + 335, y_pos + 32)
            c.line(x_pos + 138, y_pos + 14, x_pos + 335, y_pos + 14)
            
            # 第二道垂直垂直切分線
            c.line(x_pos + 342, y_pos + 8, x_pos + 342, y_pos + 75)
            
            # 右側欄位：重點原因與重要度星星數
            c.drawString(x_pos + 350, y_pos + 68, "Key Focus & Reason:")
            c.setFont(FONT_NAME, 7.5)
            c.setFillColorRGB(0.4, 0.4, 0.4)
            c.drawString(x_pos + 350, y_pos + 53, f"Type: {q['type']}")
            c.drawString(x_pos + 350, y_pos + 40, f"Reason: {q['reason'][:22]}")
            
            # 核心優化 3：Priority 直接改用超級漂亮的實心粗體大黑星號「★」呈現，視覺感拉滿！
            c.setFont(FONT_BOLD, 8.5)
            c.setFillColorRGB(0, 0, 0)
            star_display = "★" * q['stars']
            c.drawString(x_pos + 350, y_pos + 16, f"Priority: {star_display}")
            
            if os.path.exists(temp_path): os.remove(temp_path)
            if os.path.exists(temp_lbl_path): os.remove(temp_lbl_path)
                
        c.setFont(FONT_NAME, 8)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.drawString(48, 18, f"Generated by High-Advanced 3-in-1 Exam Review Tracker System")
            
        c.save()
        pdf_buffer.seek(0)
        
        st.download_button(
            label="💾 Download Advanced 3-in-1 A4 PDF",
            data=pdf_buffer,
            file_name=f"會考高階精準複習錯題本.pdf",
            mime="application/pdf"
        )
