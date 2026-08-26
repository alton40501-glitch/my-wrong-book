import streamlit as st
import cv2
import numpy as np
from PIL import Image
from datetime import datetime
import io
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

st.set_page_config(page_title="會考高效錯題本產生器", layout="centered")

# 使用標準英文 Helvetica 字型，確保 100% 繞過亂碼黑方塊
FONT_NAME = 'Helvetica'
FONT_BOLD = 'Helvetica-Bold'

if 'wrong_questions' not in st.session_state:
    st.session_state.wrong_questions = []

st.title("📝 會考專屬錯題本系統")
st.write("極簡彩色記錄版：拍照直接存檔，一鍵打包 A4 複習卷。")

current_date = datetime.today().strftime('%Y-%m-%d')
st.info(f"📅 Date: {current_date}")

source = st.text_input("輸入範圍來源 (例如：115北模、理化第三單元)", placeholder="請輸入...")

uploaded_file = st.camera_input("📸 請對準考卷題目拍照")

if uploaded_file is not None:
    img_bytes = uploaded_file.read()
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    st.success("照片已成功存檔記錄！")
    st.image(img, caption="照片存檔預覽", use_container_width=True)
        
    if st.button("📥 確認無誤，加入本次打包清單"):
        q_id = len(st.session_state.wrong_questions) + 1
        st.session_state.wrong_questions.append({
            "id": q_id,
            "img": img,
            "source": source if source else "Mock Exam"
        })
        st.toast(f"第 {q_id} 題已成功加入清單！")

if st.session_state.wrong_questions:
    st.write("---")
    st.subheader("📋 本次累積錯題管理")
    
    for q in st.session_state.wrong_questions:
        st.write(f"**Question #{q['id']}** | Source: {q['source']}")

    st.write("---")
    if st.button("🚀 一鍵打包輸出 A4 錯題本 (PDF)"):
        pdf_buffer = io.BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=A4)
        width, height = A4
        
        for q in st.session_state.wrong_questions:
            # 頂部資訊欄（全英文避開亂碼）
            c.setFont(FONT_NAME, 10)
            c.drawString(50, height - 40, f"Date: {current_date} | Source: {q['source']}")
            c.setStrokeColorRGB(0.8, 0.8, 0.8)
            c.line(50, height - 45, width - 50, height - 45)
            
            c.setFont(FONT_BOLD, 12)
            c.drawString(50, height - 65, f"Question #{q['id']}:")
            
            # 彩色照片原圖直出（JPG高壓縮，確保生成與下載速度極快）
            temp_path = f"temp_{q['id']}.jpg"
            cv2.imwrite(temp_path, q['img'], [int(cv2.IMWRITE_JPEG_QUALITY), 90])
            c.drawImage(temp_path, 50, height - 300, width=width-100, height=220, preserveAspectRatio=True)
            
            # 下方手寫訂正欄位
            c.setFont(FONT_BOLD, 11)
            c.setFillColorRGB(0.4, 0.4, 0.4)
            c.drawString(50, height - 340, "[ Notes & Corrections ]")
            
            c.setStrokeColorRGB(0.85, 0.85, 0.85)
            for i in range(8):
                y_pos = height - 370 - (i * 30)
                c.line(50, y_pos, width - 50, y_pos)
            c.showPage()
            
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
        c.save()
        pdf_buffer.seek(0)
        
        st.download_button(
            label="💾 Download A4 Wrong-Book PDF",
            data=pdf_buffer,
            file_name=f"會考錯題本_{current_date}.pdf",
            mime="application/pdf"
        )
