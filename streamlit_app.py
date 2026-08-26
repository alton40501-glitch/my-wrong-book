import streamlit as st
import cv2
import numpy as np
from PIL import Image
from datetime import datetime
import io
import os
import easyocr # 新增：AI文字辨識工具
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

st.set_page_config(page_title="會考高效錯題本產生器", layout="centered")

FONT_NAME = 'Helvetica'
FONT_BOLD = 'Helvetica-Bold'

# 初始化 AI 文字辨識器 (快取儲存，避免重複下載模型)
@st.cache_resource
def load_ocr_reader():
    return easyocr.Reader(['ch_tra', 'en']) # 支援繁體中文與英文

if 'wrong_questions' not in st.session_state:
    st.session_state.wrong_questions = []

st.title("📝 會考專屬錯題本系統 (OCR 文字抓取版)")
st.write("直接拍照，原圖完整保留！下方自動提取題目文字與繪製訂正區。")

current_date = datetime.today().strftime('%Y-%m-%d')
st.info(f"📅 本次產出日期：{current_date}")

source = st.text_input("輸入範圍來源 (例如：115北模、理化第三單元)", placeholder="請輸入...")
source_note = st.text_input("其他備註提示", placeholder="例如：考前一週必看")

uploaded_file = st.camera_input("📸 請對準考卷題目拍照")

if uploaded_file is not None:
    img_bytes = uploaded_file.read()
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    clean_q = img  
    st.success("影像處理成功！正在為您提取圖片中的文字...")
    
    # --- 🤖 核心功能：開始抓取圖片文字 ---
    try:
        reader = load_ocr_reader()
        ocr_results = reader.readtext(img_bytes)
        # 將辨識出來的段落文字組合成完整文章
        extracted_text = "\n".join([res[1] for res in ocr_results])
    except Exception as e:
        extracted_text = f"文字提取失敗，原因：{e}"
    
    # 畫面上並排顯示預覽
    col1, col2 = st.columns(2)
    with col1:
        st.image(clean_q, caption="即將生成的彩色題目", use_container_width=True)
    with col2:
        st.image(img, caption="原始拍照記錄", use_container_width=True)
        
    # 顯示抓取到的文字區塊，方便會考生直接選取、複製
    st.subheader("🤖 AI 抓取到的題目文字：")
    text_area_content = st.text_area("您可以直接在這裡複製或修改這題的文字：", value=extracted_text, height=150)
        
    if st.button("📥 確認無誤，加入本次打包清單"):
        q_id = len(st.session_state.wrong_questions) + 1
        st.session_state.wrong_questions.append({
            "id": q_id,
            "q_img": clean_q,
            "original_img": img,
            "source": source,
            "status": "Review"
        })
        st.toast(f"第 {q_id} 題已成功加入清單！")

if st.session_state.wrong_questions:
    st.write("---")
    st.subheader("📋 本次累積錯題管理")
    
    for q in st.session_state.wrong_questions:
        col_q, col_btn = st.columns(2)
        with col_q:
            st.write(f"**題號 {q['id']}** | 來源：{q['source']} | 狀態：`{q['status']}`")
        with col_btn:
            if st.button(f"❌ 仍做錯 #{q['id']}", key=f"wrong_{q['id']}"):
                q['status'] = "Urgent"
                st.toast(f"題號 {q['id']} 已標記為重點加強題！")

    st.write("---")
    if st.button("🚀 一鍵打包輸出 A4 錯題本 (PDF)"):
        pdf_buffer = io.BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=A4)
        width, height = A4
        
        for q in st.session_state.wrong_questions:
            c.setFont(FONT_NAME, 10)
            c.drawString(50, height - 40, f"Date: {current_date} | Source: {q['source']} | Status: {q['status']}")
            c.setStrokeColorRGB(0.8, 0.8, 0.8)
            c.line(50, height - 45, width - 50, height - 45)
            
            c.setFont(FONT_BOLD, 12)
            c.drawString(50, height - 65, f"Question #{q['id']}:")
            
            temp_q_path = f"temp_q_{q['id']}.jpg"
            cv2.imwrite(temp_q_path, q['q_img'], [int(cv2.IMWRITE_JPEG_QUALITY), 90])
            c.drawImage(temp_q_path, 50, height - 300, width=width-100, height=220, preserveAspectRatio=True)
            
            c.setFont(FONT_BOLD, 11)
            c.setFillColorRGB(0.4, 0.4, 0.4)
            c.drawString(50, height - 340, "[ Notes & Corrections ]")
            
            c.setStrokeColorRGB(0.85, 0.85, 0.85)
            for i in range(8):
                y_pos = height - 370 - (i * 30)
                c.line(50, y_pos, width - 50, y_pos)
            c.showPage()
            
            if os.path.exists(temp_q_path):
                os.remove(temp_q_path)
            
        c.setFont(FONT_BOLD, 16)
        c.setFillColorRGB(0, 0, 0)
        c.drawString(50, height - 50, "【 Answer Keys & Original Records 】")
        c.line(50, height - 60, width - 50, height - 60)
        
        for q in st.session_state.wrong_questions:
            y_pos = height - 120 - ((q['id']-1) * 150)
            c.setFont(FONT_NAME, 12)
            c.drawString(50, y_pos + 110, f"Question #{q['id']} Original Record:")
            
            temp_a_path = f"temp_a_{q['id']}.png"
            cv2.imwrite(temp_a_path, q['original_img'], [int(cv2.IMWRITE_JPEG_QUALITY), 90])
            c.drawImage(temp_a_path, 50, y_pos, width=width-100, height=100, preserveAspectRatio=True)
            
            if os.path.exists(temp_a_path):
                os.remove(temp_a_path)
            
        c.save()
        pdf_buffer.seek(0)
        
        st.download_button(
            label="💾 Download A4 Wrong-Book PDF",
            data=pdf_buffer,
            file_name=f"會考錯題本_{current_date}.pdf",
            mime="application/pdf"
        )
