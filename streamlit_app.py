import streamlit as st
import cv2
import numpy as np
from PIL import Image
from datetime import datetime
import io
import os
import time

st.set_page_config(page_title="會考高階精準錯題筆記系統", layout="centered")

# Standard English Helvetica font
FONT_NAME = 'Helvetica'
FONT_BOLD = 'Helvetica-Bold'

if 'wrong_questions' not in st.session_state:
    st.session_state.wrong_questions = []

st.title("📝 錯題本 (Advanced Exam Tracking Edition)")
st.write("精準衝刺流：結合科目、星級重要度、盲點原因分析與計畫追蹤，打造一頁 3 題黃金錯題講義！")

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
    
    # 科目選擇：1.Subject（預設）與其他會考必考核心學科
    subject_opt = st.selectbox(
        "Choose Subject:",
        ["Subject", "Chinese", "English", "Math", "History", "Geography", "Civics", "Biology", "Physics", "Chemistry", "Earth Science"]
    )
    subject_custom = st.text_input("Custom Subject Note (Optional Textbox):", placeholder="e.g., Unit 3, Chapter 2...")
    
    # 錯題三大分類標籤 (Concept / Steps / Review)
    note_type = st.radio(
        "Select Core Category:",
        ["Concept", "Steps", "Review"],
        index=0
    )
    
    # 閱讀區專屬延伸選項：粗心及原因（預設），以及其他常見痛點
    review_reason = st.selectbox(
        "If you chose 'Review', select the main reason:",
        ["Careless & Misread (粗心及原因)", "Time Pressure (時間不夠)", "Concept Confused (觀念模糊)", "Anxiety (緊張失常)"]
    )
    
    # 重要程度 1-5 星級設定
    importance_stars = st.slider("Select Importance Level (重要程度 1-5):", min_value=1, max_value=5, value=3)
    
    submit_button = st.form_submit_with_ui_button if hasattr(st, 'form_submit_with_ui_button') else st.form_submit_button
    submitted = submit_button("📥 Save Batch to High-Advanced Tracker List")

# 後台高階資料處理
if submitted and uploaded_files:
    for uploaded_file in uploaded_files:
        img_bytes = uploaded_file.read()
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # 精準鎖定台灣當下的錄入秒數
        current_timestamp = time.time() + (8 * 3600)
        saved_time = datetime.fromtimestamp(current_timestamp).strftime('%Y-%m-%d %H:%M:%S')
        
        # 整合科目名稱與自訂文字
        final_subject = f"{subject_opt}"
        if subject_custom:
            final_subject += f" ({subject_custom})"
            
        # 將重要度轉化為 PDF 專用的星星字串 (★)
        star_string = "X" * importance_stars
        
        # 利用絕對不變框框的內建向量字體繪製大數據精準頂部標籤貼紙
        label_img = np.ones((30, 480, 3), dtype=np.uint8) * 255
        # 標記：時間 | 科目 | 類別 | 星級
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

# 清單精準管理
if st.session_state.wrong_questions:
    st.write("---")
    st.subheader(f"📋 Current High-Advanced List ({len(st.session_state.wrong_questions)} questions)")
    for q in st.session_state.wrong_questions:
        st.write(f"**Question #{q['id']}** | Subject: `{q['subject']}` | Type: `{q['type']}` | Reason: `{q['reason']}` | Importance: {'★' * q['stars']}")

    st.write("---")
    if st.button("🚀 Pack and Export Advanced A4 Wrong-Book (PDF)"):
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        
        pdf_buffer = io.BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=A4)
        width, height = A4 # 595.27 x 841.89
        
        # 核心修正：1頁改為 3 題，直向超大網格排列參數
        col_width = 500  # 橫跨整張 A4 寬度
        row_height = 245 # 每題高度，騰出海量空間放置大筆記與計畫表
        
        # 3題直向排列的固定 y 軸起點座標（後台完全雙重加密防洗白寫死保護）
        start_y =
        
        for idx, q in enumerate(st.session_state.wrong_questions):
            page_idx = idx % 3
            if idx > 0 and page_idx == 0:
                c.showPage() # 滿 3 題自動換下一頁
                
            x_pos = 48 # 左右居中起點
            y_pos = start_y[page_idx]
            
            # 1. 繪製精美題目大外框
            c.setStrokeColorRGB(0.6, 0.6, 0.6)
            c.setLineWidth(1)
            c.rect(x_pos, y_pos, col_width, row_height, stroke=1, fill=0)
            
            # 2. 置入 100% 絕不變框框、時間科目星級全包的高清標籤貼紙
            temp_lbl_path = f"temp_lbl_{q['id']}.jpg"
            cv2.imwrite(temp_lbl_path, q['label_img'])
            c.drawImage(temp_lbl_path, x_pos + 4, y_pos + row_height - 16, width=col_width - 8, height=12, preserveAspectRatio=False)
            
            c.setStrokeColorRGB(0.8, 0.8, 0.8)
            c.line(x_pos, y_pos + row_height - 18, x_pos + col_width, y_pos + row_height - 18)
            
            # 3. 置入彩色原圖題目
            temp_path = f"temp_{q['id']}.jpg"
            cv2.imwrite(temp_path, q['img'], [int(cv2.IMWRITE_JPEG_QUALITY), 90])
            c.drawImage(temp_path, x_pos + 12, y_pos + 92, width=col_width - 24, height=130, preserveAspectRatio=True)
            
            # 4. 繪製底部完全留白大筆記框架
            c.rect(x_pos + 12, y_pos + 8, col_width - 24, 75, stroke=1, fill=0)
            
            # 5. 精準切分三大進階計畫區（手寫線條）
            # 左側：[ Tracking & Dates ] 複習次數與日期紀錄表（包含4次計畫格）
            c.setFont(FONT_BOLD, 7.5)
            c.setFillColorRGB(0.2, 0.2, 0.2)
            c.drawString(x_pos + 18, y_pos + 70, "Review Tracker (Times / Dates):")
            
            c.setStrokeColorRGB(0.85, 0.85, 0.85)
            c.drawString(x_pos + 22, y_pos + 52, "1st: ____ / ____")
            c.drawString(x_pos + 22, y_pos + 38, "2nd: ____ / ____")
            c.drawString(x_pos + 22, y_pos + 24, "3rd: ____ / ____")
            c.drawString(x_pos + 22, y_pos + 10, "4th: ____ / ____")
            
            # 繪製第一道垂直垂直分割線
            c.line(x_pos + 140, y_pos + 8, x_pos + 140, y_pos + 75)
            
            # 中間：[ Core Notes ] 3行極簡手寫筆記訂正線
            c.drawString(x_pos + 148, y_pos + 70, "Core Notes & Analysis:")
            c.line(x_pos + 148, y_pos + 50, x_pos + 340, y_pos + 50) # 第 1 條線
            c.line(x_pos + 148, y_pos + 32, x_pos + 340, y_pos + 32) # 第 2 條線
            c.line(x_pos + 148, y_pos + 14, x_pos + 340, y_pos + 14) # 第 3 條線
            
            # 繪製第二道垂直垂直分割線
            c.line(x_pos + 348, y_pos + 8, x_pos + 348, y_pos + 75)
            
            # 右側：[ Key Focus ] 錯題原因標記與重點提示專區
            c.drawString(x_pos + 356, y_pos + 70, "Key Focus & Reason:")
            c.setFont(FONT_NAME, 7)
            c.setFillColorRGB(0.4, 0.4, 0.4)
            c.drawString(x_pos + 356, y_pos + 55, f"Type: {q['type']}")
            c.drawString(x_pos + 356, y_pos + 42, f"Reason: {q['reason'][:22]}") # 避免溢出
            
            # 留下一塊小空白格，印出重要度星星數
            c.setFont(FONT_BOLD, 7.5)
            c.setFillColorRGB(0.1, 0.1, 0.1)
            c.drawString(x_pos + 356, y_pos + 20, f"Priority: " + ("X" * q['stars']))
            
            if os.path.exists(temp_path): os.remove(temp_path)
            if os.path.exists(temp_lbl_path): os.remove(temp_lbl_path)
                
        c.setFont(FONT_NAME, 8)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.drawString(48, 20, f"Generated by High-Advanced 3-in-1 Exam Review Tracker System")
            
        c.save()
        pdf_buffer.seek(0)
        
        st.download_button(
            label="💾 Download Advanced 3-in-1 A4 PDF",
            data=pdf_buffer,
            file_name=f"會考高階精準複習錯題本.pdf",
            mime="application/pdf"
        )
