import streamlit as st
import pypdf
import json
import io
import re
import os

try:
    from google import genai
except ImportError:
    import google.generativeai as genai

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# تسجيل خط عربي يدعم اللغة العربية بشكل صحيح إن وجد في النظام، أو استخدام البدائل
try:
    # محاولة البحث عن خط Tajawal أو Amiri في نظام لينكس لتفادي مربعات الخطوط
    font_path = "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf"
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('ArabicFont', font_path))
        arabic_font_name = 'ArabicFont'
    else:
        arabic_font_name = 'Helvetica'
except:
    arabic_font_name = 'Helvetica'

# إعداد واجهة Streamlit
st.set_page_config(page_title="المساعد البيداغوجي - وضعيات الدعم والعلاج", page_icon="🎓", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');
    html, body, [class*="css"] {
        font-family: 'Tajawal', sans-serif;
        direction: rtl;
        text-align: right;
    }
    .stApp { background-color: #f8f9fa; }
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        padding: 25px;
        border-radius: 12px;
        margin-bottom: 25px;
    }
    .remedial-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        border-right: 6px solid #2a5298;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h2 style="margin:0; font-weight: 800;">🎓 المساعد البيداغوجي لتوليد وضعيات الدعم والعلاج</h2>
    <p style="margin:8px 0 0 0; opacity: 0.9;">حلل ملف التقييم واحصل على وضعيات علاجية دقيقة ومطابقة تماماً للمعايير التربوية.</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.header("⚙️ الإعدادات والملف")
api_key = st.sidebar.text_input("أدخل مفتاح Gemini API Key:", type="password")
uploaded_file = st.sidebar.file_uploader("📂 اختر ملف التقييم (PDF)", type=["pdf"])

def extract_pdf_text(file):
    reader = pypdf.PdfReader(file)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text

def clean_json_response(raw_text):
    clean = raw_text.strip()
    if clean.startswith("```"):
        clean = re.sub(r"^```[a-zA-Z]*\n?", "", clean)
        clean = re.sub(r"\n?```$", "", clean)
    return clean.strip()

def analyze_and_generate_with_gemini(pdf_text, key):
    system_prompt = """
    أنت خبير بيداغوجي ومختص في الهندسة التعليمية وتحليل مكتسبات التلاميذ في المرحلة الابتدائية (السنة الرابعة).
    قم بقراءة نص ملف التقييم المرفق بدقة متناهية، واستخرج المعايير والأخطاء المرصوحة وأسماء التلاميذ بدقة.
    صمم وضعيات دعم وعلاج فارقية وعميقة ومبتكرة بنفس الأسلوب الأكاديمي الاحترافي (سياق دقيق، مهام متدرجة، وتوجيهات بيداغوجية واضحة للمعلم).

    يجب أن تكون مخرجاتك بتنسيق JSON حصراً ونقي بالمبنى التالي دون أي إضافات خارجة عن الـ JSON:
    {
        "title": "تقرير وضعيات الدعم والعلاج الفارقية",
        "subtitle": "إصلاح الأخطاء وتثبيت المكتسبات - مادة الرياضيات",
        "situations": [
            {
                "criterion": "المعيار المستهدف (مثال: المعيار 1: التأويل الملائم)",
                "students": "أسماء التلاميذ المعنيين (مثال: إيناس الحمروني)",
                "error_analysis": "تأويل ومصدر الخطأ المرصود بدقة",
                "activity_title": "عنوان الوضعية العلاجية",
                "context": "نص الوضعية والسياق التعليمي المتكامل",
                "tasks": [
                    "1. المطلب الأول والمتدرج",
                    "2. المطلب الثاني",
                    "3. المطلب الثالث"
                ],
                "teacher_guidance": "التوجيهات البيداغوجية للمعلم ومعالجة الصعوبة"
            }
        ]
    }
    """

    try:
        client = genai.Client(api_key=key)
        response = client.models.generate_content(
            model='gemini-3.8-flash',
            contents=f"{system_prompt}\n\nنص ملف التقييم:\n{pdf_text}"
        )
        return json.loads(clean_json_response(response.text))
    except Exception:
        genai.configure(api_key=key)
        model = genai.GenerativeModel('gemini-3.8-flash')
        response = model.generate_content(f"{system_prompt}\n\nنص ملف التقييم:\n{pdf_text}")
        return json.loads(clean_json_response(response.text))

def create_pdf(data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []

    styles = getSampleStyleSheet()
    
    # ربط أنماط النصوص بالخط العربي لتفادي المربعات
    title_style = ParagraphStyle('MainTitle', parent=styles['Heading1'], fontName=arabic_font_name, fontSize=16, textColor=colors.HexColor("#1e3c72"), alignment=1)
    sub_style = ParagraphStyle('SubTitle', parent=styles['Normal'], fontName=arabic_font_name, fontSize=10, textColor=colors.HexColor("#64748b"), alignment=1)
    crit_style = ParagraphStyle('CritHeader', parent=styles['Heading2'], fontName=arabic_font_name, fontSize=11, textColor=colors.HexColor("#2a5298"))
    body_style = ParagraphStyle('BodyText', parent=styles['Normal'], fontName=arabic_font_name, fontSize=9, leading=14)

    story.append(Paragraph(data.get("title", "وضعيات الدعم والعلاج"), title_style))
    story.append(Paragraph(data.get("subtitle", ""), sub_style))
    story.append(Spacer(1, 12))

    for sit in data.get("situations", []):
        story.append(Paragraph(f"<b>📌 المعيار:</b> {sit['criterion']}", crit_style))
        story.append(Paragraph(f"<b>👥 التلاميذ المعنيون:</b> {sit['students']}", body_style))
        story.append(Paragraph(f"<b>🔍 تحليل الخطأ:</b> {sit['error_analysis']}", body_style))
        story.append(Spacer(1, 4))

        story.append(Paragraph(f"<b>🎯 {sit['activity_title']}</b>", crit_style))
        story.append(Paragraph(f"<b>📜 السياق:</b> {sit['context']}", body_style))
        story.append(Paragraph("<b>📝 المهام والمطاليب المتدرجة:</b>", body_style))
        for t in sit.get("tasks", []):
            story.append(Paragraph(f"  • {t}", body_style))

        story.append(Spacer(1, 4))
        story.append(Paragraph(f"<b>💡 توجيهات للمعلم:</b> {sit['teacher_guidance']}", body_style))
        story.append(Spacer(1, 8))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1")))
        story.append(Spacer(1, 8))

    doc.build(story)
    buffer.seek(0)
    return buffer

if uploaded_file and api_key:
    if st.button("🚀 تشخيص الملف وتوليد وضعيات العلاج والـ PDF"):
        with st.spinner("جاري تحليل ملف التقييم بذكاء بيداغوجي متقدم..."):
            try:
                pdf_text = extract_pdf_text(uploaded_file)
                result_data = analyze_and_generate_with_gemini(pdf_text, api_key)

                st.success("✨ تم إنشاء خطة الدعم والعلاج بنجاح!")

                for sit in result_data.get("situations", []):
                    st.markdown(f"""
                    <div class="remedial-card">
                        <h3 style="color:#1e3c72; margin-top:0;">{sit['activity_title']}</h3>
                        <p><strong>📌 المعيار:</strong> {sit['criterion']}</p>
                        <p><strong>👥 التلاميذ المعنيون:</strong> {sit['students']}</p>
                        <p><strong>🔍 تحليل الخطأ:</strong> {sit['error_analysis']}</p>
                        <hr>
                        <p><strong>📜 السياق:</strong> {sit['context']}</p>
                        <p><strong>📝 المهام المطلوبة:</strong></p>
                        <ul>{"".join([f"<li>{t}</li>" for t in sit.get('tasks', [])])}</ul>
                        <p style="color:#2a5298;"><strong>💡 التوجيهات البيداغوجية:</strong> {sit['teacher_guidance']}</p>
                    </div>
                    """, unsafe_allow_html=True)

                pdf_file = create_pdf(result_data)

                st.download_button(
                    label="📥 تحميل التقرير والوضعيات بصيغة PDF جاهزة للطباعة",
                    data=pdf_file,
                    file_name="وضعيات_الدعم_والعلاج_النهائية.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"حدث خطأ أثناء المعالجة: {e}")
elif uploaded_file and not api_key:
    st.warning("⚠️ يرجى إدخال مفتاح Gemini API Key في القائمة الجانبية.")
