import io
import json
import os
import re
import urllib.request
from fpdf import FPDF
import pypdf
import streamlit as st

try:
  from google import genai
except ImportError:
  import google.generativeai as genai

# إعداد واجهة التطبيق
st.set_page_config(
    page_title="منظومة توليد وضعيات الدعم والعلاج", page_icon="🎓", layout="wide"
)

# تنسيق الواجهة
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; direction: rtl; text-align: right; }
    .stApp { background-color: #f8f9fa; }
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white; padding: 25px; border-radius: 12px; margin-bottom: 25px;
    }
    .remedial-card {
        background-color: #ffffff; border: 1px solid #e2e8f0;
        border-radius: 10px; padding: 20px; margin-bottom: 20px; border-right: 6px solid #2a5298;
    }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="main-header">
    <h2 style="margin:0; font-weight: 800;">🎓 منظومة توليد وضعيات الدعم والعلاج الفارقية</h2>
    <p style="margin:8px 0 0 0; opacity: 0.9;">ارفع ملف تقييم التلاميذ (PDF) لتشخيص الأخطاء وإنتاج وثيقة علاجية جاهزة للطباعة فوراً.</p>
</div>
""",
    unsafe_allow_html=True,
)

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
  system_prompt = """
    أنت خبير بيداغوجي ومختص في الهندسة التعليمية وتحليل مكتسبات التلاميذ في المرحلة الابتدائية.
    قم بقراءة نص ملف التقييم المرفق بدقة متناهية، واستخرج المعايير والأخطاء المرصوحة وأسماء التلاميذ المعنيين.
    صمم وضعيات دعم وعلاج فارقية وعميقة ومبتكرة بنفس الأسلوب الأكاديمي الاحترافي (سياق دقيق، مهام متدرجة، وتوجيهات بيداغوجية واضحة للمعلم).

    أرجع النتيجة على شكل كود JSON حصراً ونقي بالمبنى التالي:
    {
        "title": "تقرير وضعيات الدعم والعلاج الفارقية",
        "subtitle": "إصلاح الأخطاء وتثبيت المكتسبات - مادة الرياضيات",
        "situations": [
            {
                "criterion": "المعيار المستهدف (مثال: المعيار 1: التأويل الملائم)",
                "students": "أسماء التلاميذ المعنيين",
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
        model="gemini-3.8-flash",
        contents=f"{system_prompt}\n\nنص ملف التقييم:\n{pdf_text}",
    )
    return json.loads(clean_json_response(response.text))
  except Exception:
    genai.configure(api_key=key)
    model = genai.GenerativeModel("gemini-3.8-flash")
    response = model.generate_content(
        f"{system_prompt}\n\nنص ملف التقييم:\n{pdf_text}"
    )
    return json.loads(clean_json_response(response.text))


# دالة توليد PDF مع تحميل الخط العربي بطريقة مضمونة تمنع الحظر
def generate_pdf_with_fpdf(data):
  font_path = "Amiri-Regular.ttf"
  if not os.path.exists(font_path):
    url = (
        "[https://raw.githubusercontent.com/google/fonts/main/ofl/amiri/Amiri-Regular.ttf](https://raw.githubusercontent.com/google/fonts/main/ofl/amiri/Amiri-Regular.ttf)"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as response, open(
        font_path, "wb"
    ) as out_file:
      out_file.write(response.read())

  pdf = FPDF()
  pdf.add_page()

  # تسجيل واستخدام الخط العربي
  pdf.add_font("Amiri", "", font_path)
  pdf.set_font("Amiri", size=14)

  # العنوان الرئيسي
  pdf.cell(0, 10, txt=data.get("title", "تقرير وضعيات الدعم والعلاج"), ln=True, align="C")
  if data.get("subtitle"):
    pdf.set_font("Amiri", size=10)
    pdf.cell(0, 8, txt=data.get("subtitle"), ln=True, align="C")

  pdf.ln(8)
  pdf.set_font("Amiri", size=11)

  for sit in data.get("situations", []):
    pdf.set_text_color(30, 60, 114)
    pdf.cell(0, 7, txt=f"المعيار: {sit.get('criterion', '')}", ln=True, align="R")
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, txt=f"التلاميذ المعنيون: {sit.get('students', '')}", ln=True, align="R")
    pdf.cell(0, 6, txt=f"تحليل الخطأ: {sit.get('error_analysis', '')}", ln=True, align="R")

    pdf.ln(3)
    pdf.set_text_color(42, 82, 152)
    pdf.cell(0, 7, txt=f"الوضعية: {sit.get('activity_title', '')}", ln=True, align="R")
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 6, txt=f"السياق: {sit.get('context', '')}", align="R")

    pdf.cell(0, 6, txt="المهام المطلوبة:", ln=True, align="R")
    for task in sit.get("tasks", []):
      pdf.cell(0, 6, txt=f"  - {task}", ln=True, align="R")

    pdf.ln(2)
    pdf.set_text_color(30, 64, 175)
    pdf.multi_cell(0, 6, txt=f"توجيهات المعلم: {sit.get('teacher_guidance', '')}", align="R")
    pdf.set_text_color(0, 0, 0)

    pdf.ln(5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

  return bytes(pdf.output())


# التشغيل والواجهة
if uploaded_file and api_key:
  if st.button("🚀 تشخيص الملف وتوليد الـ PDF الاحترافي"):
    with st.spinner("جاري تحليل ملف التقييم وتنسيق المستند البيداغوجي..."):
      try:
        pdf_text = extract_pdf_text(uploaded_file)
        result_data = analyze_and_generate_with_gemini(pdf_text, api_key)

        st.success("✨ تم إنشاء خطة الدعم والعلاج بنجاح!")

        for sit in result_data.get("situations", []):
          st.markdown(
              f"""
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
                    """,
              unsafe_allow_html=True,
          )

        pdf_bytes = generate_pdf_with_fpdf(result_data)

        st.download_button(
            label="📥 تحميل ملف الـ PDF الجاهز للطباعة (بدون أخطاء خطوط)",
            data=pdf_bytes,
            file_name="وضعيات_الدعم_والعلاج_المفصلة.pdf",
            mime="application/pdf",
        )
      except Exception as e:
        st.error(f"حدث خطأ أثناء المعالجة: {e}")
elif uploaded_file and not api_key:
  st.warning("⚠️ يرجى إدخال مفتاح Gemini API Key في القائمة الجانبية.")
