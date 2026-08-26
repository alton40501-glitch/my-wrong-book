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
            
        star_string = "X" * importance_stars
        
        # 核心優化 1：標籤貼紙畫布寬度徹底內縮回最原始、最常態、完全沒拉長的大小尺寸（寬度200、高度12）
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
        start_y = [520, 265, 10]
        
        for idx, q in enumerate(st.session_state.wrong_questions):
            page_idx = idx % 3
            if idx > 0 and page_idx == 0:
                c.showPage()
                
            x_pos = 48 
            y_pos = start_y[page_idx]
            
            # 繪製精美大外框
            c.setStrokeColorRGB(0.6, 0.6, 0.6)
            c.setLineWidth(1)
            c.rect(x_pos, y_pos, col_width, row_height, stroke=1, fill=0)
            
            # 核心優化 1：貼紙完美縮回一開始的俐落尺寸（width=220, height=10），正常大小絕不拉長！
            temp_lbl_path = f"temp_lbl_{q['id']}.jpg"
            cv2.imwrite(temp_lbl_path, q['label_img'])
            c.drawImage(temp_lbl_path, x_pos + 4, y_pos + row_height - 15, width=220, height=10, preserveAspectRatio=False)
            
            c.setStrokeColorRGB(0.8, 0.8, 0.8)
            c.line(x_pos, y_pos + row_height - 18, x_pos + col_width, y_pos + row_height - 18)
            
            # 放入彩色原圖題目
            temp_path = f"temp_{q['id']}.jpg"
            cv2.imwrite(temp_path, q['img'], [int(cv2.IMWRITE_JPEG_QUALITY), 90])
            c.drawImage(temp_path, x_pos + 12, y_pos + 92, width=col_width - 24, height=130, preserveAspectRatio=True)
            
            # 底部完全留白大計畫框
            c.rect(x_pos + 12, y_pos + 8, col_width - 24, 75, stroke=1, fill=0)
            
            # 核心優化 2：將 Review Tracker 和 Key Focus 全部整合進「最左側的同一個直欄內（上下重疊疊放）」！
            
            # 【同一個左直欄 - 上半部】：Review Tracker
            c.setFont(FONT_BOLD, 7)
            c.setFillColorRGB(0.1, 0.1, 0.1)
            c.drawString(x_pos + 18, y_pos + 68, "Review Tracker:")
            c.setFont(FONT_NAME, 6.5)
            c.setFillColorRGB(0.4, 0.4, 0.4)
            c.drawString(x_pos + 20, y_pos + 58, "1st: ___/___  2nd: ___/___")
            c.drawString(x_pos + 20, y_pos + 48, "3rd: ___/___  4th: ___/___")
            
            # 【同一個左直欄 - 下半部】：Key Focus 直接在下方對齊長出來
            c.setFont(FONT_BOLD, 7)
            c.setFillColorRGB(0.1, 0.1, 0.1)
            c.drawString(x_pos + 18, y_pos + 36, "Key Focus & Reason:")
            c.setFont(FONT_NAME, 6.5)
            c.setFillColorRGB(0.4, 0.4, 0.4)
            c.drawString(x_pos + 20, y_pos + 26, f"Type: {q['type']} | Rs: {q['reason'][:12]}")
            
            c.setFont(FONT_BOLD, 7)
            c.setFillColorRGB(0, 0, 0)
            star_display = "★" * q['stars']
            c.drawString(x_pos + 20, y_pos + 15, f"Priority: {star_display}")
            
            # 繪製一道優雅的垂直切分線，將最左邊這個「複合直欄」與右邊的寫字區隔開
            c.setStrokeColorRGB(0.85, 0.85, 0.85)
            c.line(x_pos + 150, y_pos + 8, x_pos + 150, y_pos + 75)
            
            # 【右側完全大拉長欄位】：3行高質感橫格手寫線
            c.setFont(FONT_BOLD, 8.5)
            c.setFillColorRGB(0.1, 0.1, 0.1)
            c.drawString(x_pos + 160, y_pos + 68, "Core Notes & Analysis:")
            
            # 橫格線空間徹底橫向大拉長（起點160，一直拉到框框邊緣），超級好寫字！
            c.line(x_pos + 160, y_pos + 48, x_pos + col_width - 18, y_pos + 48)
            c.line(x_pos + 160, y_pos + 30, x_pos + col_width - 18, y_pos + 30)
            c.line(x_pos + 160, y_pos + 12, x_pos + col_width - 18, y_pos + 12)
            
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
