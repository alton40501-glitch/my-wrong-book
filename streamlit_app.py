import streamlit as st
import cv2
import numpy as np
from PIL import Image
from datetime import datetime
import io
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

st.set_page_config(page_title="會考高效客製錯題本", layout="centered")

# 使用標準英文 Helvetica 字型，確保 100% 繞過亂碼黑方塊
FONT_NAME = 'Helvetica'
FONT_BOLD = 'Helvetica-Bold'

if 'wrong_questions' not in st.session_state:
    st.session_state.wrong_questions = []

st.title("📝 智慧化會考錯題筆記系統")
st.write("手機拍照並即時輸入：觀念、解題與閱讀筆記，自動排版產出 A4 詳解本！")

current_date = datetime.today().strftime('%Y-%m-%d')
st.info(f"📅 Today's Date: {current_date}")

# 1. 基礎資訊輸入 (範圍來源)
source = st.text_input("輸入範圍來源 (例如：115北模、理化第三單元)", placeholder="請輸入考卷來源...")

# 2. 手機相機上傳 (鎖定後置視訊鏡頭)
uploaded_file = st.camera_input("📸 請對準考卷題目拍照")

# 3. 核心功能：直接在網頁上加入「觀念、解題、閱讀」的輸入選項
st.subheader("💡 錯題即時筆記欄位 (可留空，有輸入會自動印在 PDF 上)")
note_concept = st.text_area("🧠 觀念分析 (這題考了什麼核心觀念？公式？)", placeholder="例如：透鏡折射規律、物體在兩倍焦距外成像...")
note_steps = st.text_area("🛠️ 解題步驟 (這題要怎麼算？怎麼推導？)", placeholder="例如：1. 畫出光線折射路徑 2. 套用公式 3. 刪除法選B...")
note_review = st.text_area("📖 閱讀與盲點複習 (當時為什麼錯？)", placeholder="例如：題目看太快，粗心把凸透鏡看成凹透鏡...")

if uploaded_file is not None:
    img_bytes = uploaded_file.read()
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    st.success("照片已成功捕捉！")
    st.image(img, caption="照片預覽", use_container_width=True)
        
    if st.button("📥 確認無誤，將照片與筆記加入打包清單"):
        q_id = len(st.session_state.wrong_questions) + 1
        st.session_state.wrong_questions.append({
            "id": q_id,
            "img": img,
            "source": source if source else "Mock Exam",
            "date": current_date,
            "concept": note_concept if note_concept else "None",
            "steps": note_steps if note_steps else "None",
            "review": note_review if note_review else "None"
        })
        st.toast(f"第 {q_id} 題與筆記已成功同步加入清單！")

if st.session_state.wrong_questions:
    st.write("---")
    st.subheader(f"📋 目前累積的錯題清單 ({len(st.session_state.wrong_questions)} 題)")
    
    for q in st.session_state.wrong_questions:
        st.write(f"**Question #{q['id']}** | 來源: {q['source']} | 筆記已同步記錄")

    st.write("---")
    if st.button("🚀 一鍵打包輸出 A4 錯題本 (PDF)"):
        pdf_buffer = io.BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=A4)
        width, height = A4
        
        # 每一頁排 2 題，上方放彩色原圖題目，下方放完美的筆記對齊欄
        for i, q in enumerate(st.session_state.wrong_questions):
            # 每 2 題自動切換下一頁
            if i > 0 and i % 2 == 0:
                c.showPage()
                
            # 判斷是目前頁面的上半部 (第1題) 還是下半部 (第2題)
            is_top = (i % 2 == 0)
            y_offset = 0 if is_top else -390
            
            # 1. 標示加入時間跟範圍來源與編號 (全英文避開亂碼)
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
            
            # 3. 繪製精美的筆記欄位（自動帶入你在手機上寫的文字）
            c.setFont(FONT_BOLD, 10)
            c.setFillColorRGB(0.1, 0.1, 0.1)
            
            # 觀念區 (Concept)
            c.drawString(50, height - 230 + y_offset, "[ Concept ]")
            c.setFont(FONT_NAME, 9)
            c.setFillColorRGB(0.4, 0.4, 0.4)
            c.drawString(60, height - 245 + y_offset, f"{q['concept']}")
            
            # 解題區 (Steps)
            c.setFont(FONT_BOLD, 10)
            c.setFillColorRGB(0.1, 0.1, 0.1)
            c.drawString(50, height - 270 + y_offset, "[ Steps ]")
            c.setFont(FONT_NAME, 9)
            c.setFillColorRGB(0.4, 0.4, 0.4)
            c.drawString(60, height - 285 + y_offset, f"{q['steps']}")
            
            # 閱讀區 (Review)
            c.setFont(FONT_BOLD, 10)
            c.setFillColorRGB(0.1, 0.1, 0.1)
            c.drawString(50, height - 310 + y_offset, "[ Review ]")
            c.setFont(FONT_NAME, 9)
            c.setFillColorRGB(0.4, 0.4, 0.4)
            c.drawString(60, height - 325 + y_offset, f"{q['review']}")
            
            # 題與題之間的裝飾虛線
            if is_top:
                c.setStrokeColorRGB(0.85, 0.85, 0.85)
                c.setDash(2, 2)
                c.line(50, height - 370, width - 50, height - 370)
                c.setDash(1, 0) # 恢復實線
            
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
        c.save()
        pdf_buffer.seek(0)
        
        st.download_button(
            label="💾 Download Smart A4 Wrong-Book PDF",
            data=pdf_buffer,
            file_name=f"會考智慧錯題本_{current_date}.pdf",
            mime="application/pdf"
        )
