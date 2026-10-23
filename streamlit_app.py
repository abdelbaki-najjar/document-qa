import streamlit as st
import pypdf
import google.generativeai as genai
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib import colors
import io
import json

# ضبط إعدادات الصفحة
st.set_page_config(page_title="المساعد البيداغوجي الذكي - Gemini", page_icon="🪄", layout="wide")

# CSS لدعم اللغة العربية وتنسيق الواجهة
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; direction: rtl; text-align: right; }
    .stApp { background-color: #f8f9fa; }
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h2 style="margin:0;">🪄 المساعد البيداغوجي الذكي (مدعوم بـ Google Gemini)</h2>
    <p style="margin:5px 0 0 0;">قم برفع ملف التقييم (PDF)، وسيقوم Gemini بتحليله وإنشاء وضعيات علاجية وملف PDF جاهز للطباعة.</p>
</div>
""", unsafe_allow_html=True)

# إدخال المفتاح من الشريط الجانبي
st.sidebar.header("⚙️ الإعدادات")
api_key = st.sidebar.text_input("أدخل مفتاح Gemini API Key:", type="password")

uploaded_file = st.sidebar.file_uploader("📂 اختر ملف التقييم (PDF)", type=["pdf"])

# دالة قراءة الـ PDF
def extract_text_from_pdf(file):
    reader = pypdf.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

# دالة استدعاء Gemini API باستخدام أحدث نموذج مدعوم
def generate_remedial_with_gemini(pdf_text, api_key):
    genai.configure(api_key=api_key)
    # استخدام نموذج gemini-2.5-flash أو gemini-1.5-flash المعتمد حالياً
    model = genai.GenerativeModel('gemini-3.8-flash')
    
    prompt = f"""
    أنت خبير بيداغوجي ومختص في الهندسة التعليمية.
    بناءً على نص ملف التقييم المرفق أسفله:
    1. استخرج المعايير والأخطاء المرصوحة وأسماء التلاميذ المعنيين بالتثبيت/العلاج.
    2. صمم وضعيات دعم وعلاج فارقية ومبتكرة لكل معيار فيه تعثر.
    3. أرجع النتيجة على شكل كود JSON نقي حصراً بالهيكل التالي (بدون أي علامات تخريب أو markdown خارج النص إن أمكن، فقط JSON):
    {{
        "title": "عنوان التقرير",
        "eval_info": "معلومات التقييم (المادة، المستوى، التاريخ...)",
        "situations": [
            {{
                "criterion": "اسم المعيار",
                "students": "أسماء التلاميذ المعنيين",
                "error_source": "مصدر الخطأ وتأويله",
                "activity_title": "عنوان الوضعية العلاجية",
                "context": "نص الوضعية والسياق",
                "tasks": ["المطلب 1", "المطلب 2", "المطلب 3"],
                "guidance": "التوجيهات البيداغوجية للمعلم"
            }}
        ]
    }}

    نص ملف التقييم:
    {pdf_text}
    """
    
    response = model.generate_content(prompt)
    clean_text = response.text.strip()
    
    if clean_text.startswith("```json"):
        clean_text = clean_text[7:]
    if clean_text.endswith("```"):
        clean_text = clean_text[:-3]
        
    return json.loads(clean_text.strip())

# دالة إنشاء ملف الـ PDF الاحترافي
def build_pdf_document(ai_data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor("#1e3c72"), alignment=1)
    subtitle_style = ParagraphStyle('SubTitle', parent=styles['Normal'], fontSize=10, textColor=colors.gray, alignment=1)
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor("#2a5298"))
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, leading=14)
    
    story.append(Paragraph(ai_data.get("title", "ملف وضعيات الدعم والعلاج"), title_style))
    story.append(Paragraph(ai_data.get("eval_info", ""), subtitle_style))
    story.append(Spacer(1, 15))
    
    for sit in ai_data.get("situations", []):
        story.append(Paragraph(f"<b>المعيار المستهدف:</b> {sit['criterion']}", heading_style))
        story.append(Paragraph(f"<b>التلاميذ المعنيون:</b> {sit['students']}", body_style))
        story.append(Paragraph(f"<b>مصدر الخطأ:</b> {sit['error_source']}", body_style))
        story.append(Spacer(1, 5))
        
        story.append(Paragraph(f"<b>{sit['activity_title']}</b>", heading_style))
        story.append(Paragraph(f"<b>السياق:</b> {sit['context']}", body_style))
        story.append(Paragraph("<b>المهام والمطاليب:</b>", body_style))
        for t in sit.get("tasks", []):
            story.append(Paragraph(f"• {t}", body_style))
        
        story.append(Spacer(1, 5))
        story.append(Paragraph(f"<b>💡 توجيهات للمعلم:</b> {sit['guidance']}", body_style))
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1")))
        story.append(Spacer(1, 10))
        
    doc.build(story)
    buffer.seek(0)
    return buffer

# التنفيذ
if uploaded_file and api_key:
    if st.button("🚀 تحليل الملف بواسطة Gemini وتوليد الـ PDF"):
        with st.spinner("جاري قراءة الملف وتحليله عبر Gemini AI..."):
            try:
                text = extract_text_from_pdf(uploaded_file)
                ai_result = generate_remedial_with_gemini(text, api_key)
                
                st.success("✨ تم تحليل الملف وتوليد الوضعيات بنجاح!")
                
                for sit in ai_result.get("situations", []):
                    with st.expander(f"📌 {sit['criterion']} - {sit['students']}"):
                        st.write(f"**نص الوضعية:** {sit['context']}")
                        st.write("**المهام:**")
                        for task in sit['tasks']:
                            st.write(f"- {task}")
                        st.info(f"**توجيهات المعلم:** {sit['guidance']}")
                
                pdf_out = build_pdf_document(ai_result)
                
                st.download_button(
                    label="📥 تحميل ملف الـ PDF الاحترافي والجاهز للطباعة",
                    data=pdf_out,
                    file_name="وضعيات_الدعم_والعلاج_Gemini.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"حدث خطأ أثناء المعالجة: {e}")
elif uploaded_file and not api_key:
    st.warning("⚠️ يرجى إدخال مفتاح Google Gemini API Key في القائمة الجانبية.")
