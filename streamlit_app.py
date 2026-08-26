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
st.write("Fast continuous shooting. Color preview. 6-in-1 layout with Top images and Bottom notes.")

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
        ["Concept", "Steps", "Review", "Careless"],
        index=0
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
        
        # 核心優化：將標籤貼紙畫布高度與寬度微調，並將 FONT_HERSHEY_SIMPLEX 縮放比例由 0.33 大幅拉大加粗至 0.52 正常印刷大小！
        label_img = np.ones((35, 480, 3), dtype=np.uint8) * 255
        safe_text = f"{saved_time} | {final_subject}"
        cv2.putText(label_img, safe_text, (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (30, 30, 30), 2, cv2.LINE_AA)
        
        q_id = len(st.session_state.wrong_questions) + 1
        st.session_state.wrong_questions.append({
            "id": q_id,
            "img": img,
            "label_img": label_img, 
            "date": saved_time,
            "subject": final_subject,
            "type": note_type,
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
        start_y = [535, 290, 45]
        
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
            
            # 核心優化：將大字體標籤貼紙完美對齊格子最頂端（width=232, height=14），字體飽滿、清晰好讀！
            temp_lbl_path = f"temp_lbl_{q['id']}.jpg"
            cv2.imwrite(temp_lbl_path, q['label_img'])
            c.drawImage(temp_lbl_path, x_pos + 4, y_pos + row_height - 16, width=232, height=14, preserveAspectRatio=False)
            
            c.setStrokeColorRGB(0.85, 0.85, 0.85)
            c.line(x_pos, y_pos + row_height - 18, x_pos + col_width, y_pos + row_height - 18)
            
            # 題目圖檔改到格子的「上半部」，橫向拉滿（寬度 224），高度 110 留出完美正方形視野
            temp_path = f"temp_{q['id']}.jpg"
            cv2.imwrite(temp_path, q['img'], [int(cv2.IMWRITE_JPEG_QUALITY), 90])
            c.drawImage(temp_path, x_pos + 8, y_pos + 110, width=col_width - 16, height=110, preserveAspectRatio=True)
            
            # 繪製一道水平分割線，把上半部的圖片跟下半部的計畫資訊筆記欄隔開
            c.setStrokeColorRGB(0.85, 0.85, 0.85)
            c.line(x_pos, y_pos + 105, x_pos + col_width, y_pos + 105)
            
            # 【下半部第一層】：Review Tracker 追蹤進度
            c.setFont(FONT_BOLD, 7)
            c.setFillColorRGB(0.1, 0.1, 0.1)
            c.drawString(x_pos + 10, y_pos + 95, "Review Tracker:")
            c.setFont(FONT_NAME, 6)
            c.setFillColorRGB(0.4, 0.4, 0.4)
            c.drawString(x_pos + 85, y_pos + 95, "1st: __/__   2nd: __/__   3rd: __/__   4th: __/__")
            
            # 【下半部第二層】：Key Focus 錯題原因與優先度星星 
            c.setFont(FONT_BOLD, 7)
            c.setFillColorRGB(0.1, 0.1, 0.1)
            c.drawString(x_pos + 10, y_pos + 83, "Key Focus:")
            c.setFont(FONT_NAME, 6)
            c.setFillColorRGB(0.4, 0.4, 0.4)
            star_display = "★" * q['stars']
            c.drawString(x_pos + 58, y_pos + 83, f"Type: {q['type']}   |   Priority: {star_display}")
            
            # 【下半部第三層】：橫向大拉長的 3 行完全乾淨手寫格線線條
            c.setFont(FONT_BOLD, 7)
            c.setFillColorRGB(0.1, 0.1, 0.1)
            c.drawString(x_pos + 10, y_pos + 70, "Core Notes & Analysis:")
            
            c.setStrokeColorRGB(0.9, 0.9, 0.9)
            c.line(x_pos + 12, y_pos + 52, x_pos + col_width - 12, y_pos + 52) 
            c.line(x_pos + 12, y_pos + 34, x_pos + col_width - 12, y_pos + 34) 
            c.line(x_pos + 12, y_pos + 16, x_pos + col_width - 12, y_pos + 16) 
            
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
