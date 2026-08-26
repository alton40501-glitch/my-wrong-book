import streamlit as st
import cv2
import numpy as np
from PIL import Image
from datetime import datetime
import io
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

st.set_page_config(page_title="會考高效 1頁6題 智慧錯題本", layout="centered")

# 全面改用標準英文 Helvetica 字型，100% 徹底根除黑方塊亂碼問題
FONT_NAME = 'Helvetica'
FONT_BOLD = 'Helvetica-Bold'

if 'wrong_questions' not in st.session_state:
    st.session_state.wrong_questions = []

st.title("📝 6-in-1 Smart Wrong-Book System")
st.write("零阻礙極速流：相機隨拍隨加免清除，原圖彩色直出，PDF 精準標記錯題類別！")

current_date = datetime.today().strftime('%Y-%m-%d')
st.info(f"📅 Today's Date: {current_date}")

# 1. 基礎資訊輸入 (範圍來源)
source = st.text_input("輸入範圍來源 (例如：115北模、理化第三單元)", placeholder="請輸入考卷來源...")

# 2. 選擇分類鈕（Concept / Steps / Review）
st.subheader("🎯 Select Note Type for this question:")
note_type = st.radio(
    "Choose one category:",
    ["Concept", "Steps", "Review"],
    index=0
)

# 3. 手機相機上傳
uploaded_file = st.camera_input("📸 請對準考卷題目拍照")

# 核心升級：只要一拍照，自動塞進清單，且不卡住、免按 Clear photo 即可直接拍下一張
if uploaded_file is not None:
    img_bytes = uploaded_file.read()
    
    # 利用 file_id 來當作唯一的拍照標記，避免重複觸發新增
    if 'last_processed_file' not in st.session_state or st.session_state.last_processed_file != uploaded_file.file_id:
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        q_id = len(st.session_state.wrong_questions) + 1
        st.session_state.wrong_questions.append({
            "id": q_id,
            "img": img,
            "source": source if source else "Mock Exam",
            "date": current_date,
            "type": note_type  # 確實記錄這題是 Review, Concept 還是 Steps
        })
        st.session_state.last_processed_file = uploaded_file.file_id
        st.toast(f"🎉 Question #{q_id} 已自動加入清單！ (Type: {note_type})")

    # 修正：預覽圖片強制以最清晰、百分之百原汁原味的彩色呈現
    st.success(f"📸 圖片已成功記錄！可直接點選上方分類並按相機「繼續拍下一張」，免點 Clear Photo。")
    # 將 BGR 轉回 RGB 確保 Streamlit 網頁顯示色彩正常
    preview_img = cv2.cvtColor(st.session_state.wrong_questions[-1]['img'], cv2.COLOR_BGR2RGB)
    st.image(preview_img, caption=f"Latest Question #{len(st.session_state.wrong_questions)} 彩色原圖預覽", use_container_width=True)

if st.session_state.wrong_questions:
    st.write("---")
    st.subheader(f"📋 Current List ({len(st.session_state.wrong_questions)} questions)")
    
    for q in st.session_state.wrong_questions:
        st.write(f"**Question #{q['id']}** | Source: {q['source']} | Type: `{q['type']}`")

    st.write("---")
    if st.button("🚀 一鍵打包輸出 A4 錯題本 (PDF)"):
        pdf_buffer = io.BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=A4)
        width, height = A4  # A4 標準寬 595.27, 高 841.89
        
        # 定義 1頁 6 題的網格參數 (2排 3列)
        col_width = 240
        row_height = 240
        
        start_x = [45, 310]          # 左欄起點 45, 右欄起點 310
        start_y = [550, 300, 50]     # 上、中、下三排的起點 y 座標
        
        for idx, q in enumerate(st.session_state.wrong_questions):
            page_idx = idx % 6
            if idx > 0 and page_idx == 0:
                c.showPage() # 滿 6 題自動跳下一頁
                
            # 計算目前這題應該放在 A4 頁面的哪個格子
            x_pos = start_x[page_idx % 2]
            y_pos = start_y[page_idx // 2]
            
            # 1. 繪製每題的外框
            c.setStrokeColorRGB(0.7, 0.7, 0.7)
            c.setLineWidth(1)
            c.rect(x_pos, y_pos, col_width, row_height, stroke=1, fill=0)
            
            # 2. 核心修正：頂部標籤明確標註 Date, Source 還有你是勾選的 Review 還是什麼標籤！
            c.setFont(FONT_NAME, 7.5)
            c.setFillColorRGB(0.3, 0.3, 0.3)
            c.drawString(x_pos + 6, y_pos + row_height - 13, f"Dt: {q['date']} | Src: {q['source']} | Type: {q['type']}")
            c.setStrokeColorRGB(0.85, 0.85, 0.85)
            c.line(x_pos, y_pos + row_height - 18, x_pos + col_width, y_pos + row_height - 18)
            
            # 3. 置入高清彩色原圖題目（維持精緻彩色）
            temp_path = f"temp_{q['id']}.jpg"
            cv2.imwrite(temp_path, q['img'], [int(cv2.IMWRITE_JPEG_QUALITY), 90])
            c.drawImage(temp_path, x_pos + 8, y_pos + 95, width=col_width - 16, height=120, preserveAspectRatio=True)
            
            # 4. 繪製專用分類空白手寫格
            c.setStrokeColorRGB(0.8, 0.8, 0.8)
            c.rect(x_pos + 8, y_pos + 8, col_width - 16, 75, stroke=1, fill=0)
            
            # 標題字：動態印出專用的全英文分類標籤
            c.setFont(FONT_BOLD, 9)
            c.setFillColorRGB(0.2, 0.2, 0.2)
            c.drawString(x_pos + 14, y_pos + 68, f"[ Hand-written Notes for {q['type']} ]")
            
            # 在格子內畫出 2 條橫格線方便手寫
            c.setStrokeColorRGB(0.9, 0.9, 0.9)
            c.line(x_pos + 14, y_pos + 46, x_pos + col_width - 14, y_pos + 46)
            c.line(x_pos + 14, y_pos + 24, x_pos + col_width - 14, y_pos + 24)
            
            c.setFillColorRGB(0, 0, 0)
            
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
        c.setFont(FONT_NAME, 8)
        c.setFillColorRGB(0.6, 0.6, 0.6)
        c.drawString(45, 20, f"Generated by 6-in-1 Smart Wrong-Book System")
            
        c.save()
        pdf_buffer.seek(0)
        
        st.download_button(
            label="💾 Download 6-in-1 A4 PDF",
            data=pdf_buffer,
            file_name=f"會考高效六合一錯題本_{current_date}.pdf",
            mime="application/pdf"
        )
