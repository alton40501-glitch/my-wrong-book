import streamlit as st
import cv2
import numpy as np
from PIL import Image
from datetime import datetime
import io
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

st.set_page_config(page_title="會考高效單選錯題本", layout="centered")

# 使用標準英文 Helvetica 字型，確保 100% 繞過亂碼黑方塊
FONT_NAME = 'Helvetica'
FONT_BOLD = 'Helvetica-Bold'

if 'wrong_questions' not in st.session_state:
    st.session_state.wrong_questions = []

st.title("📝 智慧化會考錯題筆記系統")
st.write("手機拍照並「點選」筆記分類，自動生成帶有專用筆記欄的 A4 複習卷！")

current_date = datetime.today().strftime('%Y-%m-%d')
st.info(f"📅 Today's Date: {current_date}")

# 1. 基礎資訊輸入 (範圍來源)
source = st.text_input("輸入範圍來源 (例如：115北模、理化第三單元)", placeholder="請輸入考卷來源...")

# 2. 手機相機上傳
uploaded_file = st.camera_input("📸 請對準考卷題目拍照")

# 3. 核心升級：加入 3 個單選按鈕選項，讓使用者用點選的
st.subheader("💡 請選擇此題需要的筆記欄格式：")
note_type = st.radio(
    "選擇分類：",
    ["Concept (觀念)", "Steps (解題)", "Review (閱讀/盲點)"],
    index=0
)

if uploaded_file is not None:
    img_bytes = uploaded_file.read()
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    st.success(f"照片已成功捕捉！已選定筆記格式：{note_type}")
    st.image(img, caption="照片預覽", use_container_width=True)
        
    if st.button("📥 確認無誤，加入本次打包清單"):
        q_id = len(st.session_state.wrong_questions) + 1
        st.session_state.wrong_questions.append({
            "id": q_id,
            "img": img,
            "source": source if source else "Mock Exam",
            "date": current_date,
            "type": note_type  # 記錄使用者點選了哪一個選項
        })
        st.toast(f"第 {q_id} 題已加入清單！")

if st.session_state.wrong_questions:
    st.write("---")
    st.subheader(f"📋 目前累積的錯題清單 ({len(st.session_state.wrong_questions)} 題)")
    
    for q in st.session_state.wrong_questions:
        st.write(f"**Question #{q['id']}** | 來源: {q['source']} | 欄位格式: {q['type']}")

    st.write("---")
    if st.button("🚀 一鍵打包輸出 A4 錯題本 (PDF)"):
        pdf_buffer = io.BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=A4)
        width, height = A4
        
        # 每一頁排 2 題，上方放彩色原圖題目，下方放點選的專用筆記欄與格子
        for i, q in enumerate(st.session_state.wrong_questions):
            if i > 0 and i % 2 == 0:
                c.showPage()
                
            is_top = (i % 2 == 0)
            y_offset = 0 if is_top else -390
            
            # 1. 頂部標示加入時間跟範圍來源 (全英文避開亂碼)
            c.setFont(FONT_NAME, 9)
            c.setFillColorRGB(0.3, 0.3, 0.3)
            c.drawString(50, height - 35 + y_offset, f"Date: {q['date']} | Source: {q['source']}")
            c.setStrokeColorRGB(0.8, 0.8, 0.8)
            c.line(50, height - 40 + y_offset, width - 50, height - 40 + y_offset)
            
            c.setFont(FONT_BOLD, 12)
            c.setFillColorRGB(0, 0, 0)
            c.drawString(50, height - 55 + y_offset, f"Question #{q['id']}:")
            
            # 2. 放入高清彩色考卷原圖
            temp_path = f"temp_{q['id']}.jpg"
            cv2.imwrite(temp_path, q['img'], [int(cv2.IMWRITE_JPEG_QUALITY), 90])
            c.drawImage(temp_path, 50, height - 210 + y_offset, width=width-100, height=150, preserveAspectRatio=True)
            
            # 3. 根據使用者在手機上「點選」的項目，動態印出專用的手寫筆記欄標題
            c.setFont(FONT_BOLD, 11)
            c.setFillColorRGB(0.1, 0.1, 0.1)
            
            if "Concept" in q['type']:
                display_label = "[ Notes & Core Concept / 觀念筆記欄 ]"
            elif "Steps" in q['type']:
                display_label = "[ Solving Steps & Math / 解題步驟欄 ]"
            else:
                display_label = "[ Review & Mistakes / 閱讀與盲點複習欄 ]"
                
            c.drawString(50, height - 235 + y_offset, display_label)
            
            # 4. 繪製手寫格線（留空讓你在印出來之後手寫詳解）
            c.setStrokeColorRGB(0.85, 0.85, 0.85)
            for j in range(4):
                line_y = height - 260 - (j * 25) + y_offset
                c.line(50, line_y, width - 50, line_y)
            
            # 題與題之間的裝飾虛線
            if is_top:
                c.setStrokeColorRGB(0.85, 0.85, 0.85)
                c.setDash(2, 2)
                c.line(50, height - 370, width - 50, height - 370)
                c.setDash(1, 0)
            
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
        c.save()
        pdf_buffer.seek(0)
        
        st.download_button(
            label="💾 Download Smart A4 Wrong-Book PDF",
            data=pdf_buffer,
            file_name=f"會考智慧選擇錯題本_{current_date}.pdf",
            mime="application/pdf"
        )
