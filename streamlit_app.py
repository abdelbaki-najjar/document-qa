import streamlit as st
import pypdf
import json
import io
import re

# استخدام الحزمة الرسمية المحدثة
try:
    from google import genai
    from google.genai import types
except ImportError:
    import google.generativeai as genai

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib import colors

# إعداد واجهة Streamlit
st.set_page_config(page_title="منظومة تشخيص الأخطاء وتوليد وضعيات العلاج", page_icon="🎓", layout="wide")

# تنسيق CSS احترافي لدعم العربية
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
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .remedial-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        border-right: 6px solid #2a5298;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h2 style="margin:0; font-weight: 800;">🎓 منظومة تشخيص الأخطاء وتوليد وضعيات الدعم والعلاج (إصدار نهائي)</h2>
    <p style="margin:8px 0 0 0; opacity: 0.9;">حلل أي ملف تقييم PDF واحصل على وضعيات علاجية فارقية ومصممة بيداغوجياً وملف PDF جاهز للطباعة فوراً.</p>
</div>
""", unsafe_allow_html=True)

# الشريط الجانبي
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
    # توجيه بيداغوجي عميق وعالي الجودة للمحاكاة المباشرة
    system_prompt = """
    أنت خبير بيداغوجي ومختص في الهندسة التعليمية وتحليل مكتسبات التلاميذ في المرحلة الابتدائية.
    قم بقراءة نص ملف التقييم المرفق بدقة عالية واستخراج المعايير وجداول الأخطاء.
    ثم صمم وضعيات دعم وعلاج فارقية متكاملة لكل معيار ثبت فيه تعثر لدى بعض التلاميذ.

    يجب أن تكون مخرجاتك بتنسيق JSON حصراً ونقي وبالمبنى الموضح أدناه:
    {
        "title": "تقرير وضعيات الدعم والعلاج الفارقية",
        "subtitle": "تقييم مكتسبات التلاميذ - مادة الرياضيات - السنة الرابعة",
        "situations": [
            {
                "criterion": "اسم المعيار (مثال: المعيار 1: التأويل الملائم)",
                "students": "أسماء التلاميذ المعنيين بالدعم (مثال: إيناس الحمروني)",
                "error_analysis": "مصدر الخطأ وتأويله البيداغوجي المستخرج من الملف",
                "activity_title": "عنوان الوضعية العلاجية",
                "context": "نص الوضعية وسياقها بأسلوب تعليمي متكامل",
                "tasks": [
                    "1. المطلب الأول والمتدرج (مثال: تفكيك المعطيات أو الاستعانة برسم)",
                    "2. المطلب الثاني (إعادة الصياغة أو اختيار العمليات)",
                    "3. المطلب الثالث (الحل المرحلي أو التحقق الذاتي)"
                ],
                "teacher_guidance": "التوجيهات البيداغوجية للمعلم (خطة العلاج والمقاربة المتبعة)"
            }
        ]
    }
    """

    # محاولة الاستدعاء بالحزمة الجديدة أو التقليدية
    try:
        client = genai.Client(api_key=key)
        response = client.models.generate_content(
            model='gemini-4-argon',
            contents=f"{system_prompt}\n\nنص ملف التقييم:\n{pdf_text}"
        )
        return json.loads(clean_json_response(response.text))
    except Exception:
        genai.configure(api_key=key)
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(f"{system_prompt}\n\nنص ملف التقييم:\n{pdf_text}")
        except Exception:
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(f"{system_prompt}\n\nنص ملف التقييم:\n{pdf_text}")
        return json.loads(clean_json_response(response.text))

def create_pdf(data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('MainTitle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor("#1e3c72"), alignment=1)
    sub_style = ParagraphStyle('SubTitle', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor("#64748b"), alignment=1)
    crit_style = ParagraphStyle('CritHeader', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor("#2a5298"))
    body_style = ParagraphStyle('BodyText', parent=styles['Normal'], fontSize=10, leading=14)

    story.append(Paragraph(data.get("title", "وضعيات الدعم والعلاج"), title_style))
    story.append(Paragraph(data.get("subtitle", ""), sub_style))
    story.append(Spacer(1, 15))

    for sit in data.get("situations", []):
        story.append(Paragraph(f"<b>📌 المعيار:</b> {sit['criterion']}", crit_style))
        story.append(Paragraph(f"<b>👥 التلاميذ المعنيون:</b> {sit['students']}", body_style))
        story.append(Paragraph(f"<b>🔍 مصدر الخطأ وتأويله:</b> {sit['error_analysis']}", body_style))
        story.append(Spacer(1, 6))

        story.append(Paragraph(f"<b>🎯 {sit['activity_title']}</b>", crit_style))
        story.append(Paragraph(f"<b>📜 السياق:</b> {sit['context']}", body_style))
        story.append(Paragraph("<b>📝 المهام والمطاليب المتدرجة:</b>", body_style))
        for t in sit.get("tasks", []):
            story.append(Paragraph(f"  • {t}", body_style))

        story.append(Spacer(1, 6))
        story.append(Paragraph(f"<b>💡 توجيهات للمعلم:</b> {sit['teacher_guidance']}", body_style))
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1")))
        story.append(Spacer(1, 10))

    doc.build(story)
    buffer.seek(0)
    return buffer

# التنفيذ الرئيسي
if uploaded_file and api_key:
    if st.button("🚀 تشخيص الملف وتوليد وضعيات العلاج والـ PDF"):
        with st.spinner("جاري تحليل ملف التقييم وتوليد الوضعيات بأسلوب بيداغوجي محترف..."):
            try:
                pdf_text = extract_pdf_text(uploaded_file)
                result_data = analyze_and_generate_with_gemini(pdf_text, api_key)

                st.success("✨ تم تحليل الملف وإنشاء خطة الدعم والعلاج بنجاح!")

                # عرض الأنشطة بشكل تفاعلي
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

                # إنتاج الـ PDF
                pdf_file = create_pdf(result_data)

                st.download_button(
                    label="📥 تحميل التقرير والوضعيات بصيغة PDF جاهزة للطباعة",
                    data=pdf_file,
                    file_name="وضعيات_الدعم_والعلاج_المفصلة.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"حدث خطأ أثناء المعالجة: {e}")
elif uploaded_file and not api_key:
    st.warning("⚠️ يرجى إدخال مفتاح Gemini API Key في القائمة الجانبية لتشغيل المعالجة.")
