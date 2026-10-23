import streamlit as st
import pypdf
import json
import re
import weasyprint

try:
    from google import genai
except ImportError:
    import google.generativeai as genai

# إعداد واجهة التطبيق
st.set_page_config(page_title="منظومة توليد وضعيات الدعم والعلاج", page_icon="🎓", layout="wide")

# تنسيق الواجهة
st.markdown("""
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
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h2 style="margin:0; font-weight: 800;">🎓 منظومة توليد وضعيات الدعم والعلاج الفارقية</h2>
    <p style="margin:8px 0 0 0; opacity: 0.9;">ارفع ملف تقييم التلاميذ (PDF) لتشخيص الأخطاء وإنتاج وثيقة علاجية جاهزة للطباعة فوراً.</p>
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
            model='gemini-3.8-flash',
            contents=f"{system_prompt}\n\nنص ملف التقييم:\n{pdf_text}"
        )
        return json.loads(clean_json_response(response.text))
    except Exception:
        genai.configure(api_key=key)
        model = genai.GenerativeModel('gemini-3.8-flash')
        response = model.generate_content(f"{system_prompt}\n\nنص ملف التقييم:\n{pdf_text}")
        return json.loads(clean_json_response(response.text))

# دالة تحويل الـ HTML المصمم إلى PDF احترافي عبر WeasyPrint
def generate_pdf_from_html(data):
    situations_html = ""
    for sit in data.get("situations", []):
        tasks_list = "".join([f"<li>{task}</li>" for task in sit.get("tasks", [])])
        situations_html += f"""
        <div class="card">
            <div class="card-header">
                <h3>📌 {sit['criterion']}</h3>
                <p><strong>👥 التلاميذ المعنيون:</strong> {sit['students']}</p>
                <p><strong>🔍 مصدر الخطأ وتأويله:</strong> {sit['error_analysis']}</p>
            </div>
            <div class="card-body">
                <h4>🎯 {sit['activity_title']}</h4>
                <p><strong>📜 السياق:</strong> {sit['context']}</p>
                <p><strong>📝 المهام والمطاليب المتدرجة:</strong></p>
                <ul>{tasks_list}</ul>
                <div class="guidance">
                    <strong>💡 توجيهات للمعلم:</strong> {sit['teacher_guidance']}
                </div>
            </div>
        </div>
        """

    full_html = f"""
    <!DOCTYPE html>
    <html dir="rtl" lang="ar">
    <head>
        <meta charset="UTF-8">
        <style>
            @import url('[https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap](https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap)');
            @page {{ size: A4; margin: 15mm; }}
            body {{
                font-family: 'Tajawal', sans-serif;
                direction: rtl;
                color: #1e293b;
                line-height: 1.6;
            }}
            .header {{
                text-align: center;
                border-bottom: 3px solid #1e3c72;
                padding-bottom: 12px;
                margin-bottom: 20px;
            }}
            .header h1 {{ color: #1e3c72; margin: 0; font-size: 22px; }}
            .header p {{ color: #64748b; margin: 5px 0 0 0; font-size: 13px; }}
            .card {{
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                margin-bottom: 18px;
                page-break-inside: avoid;
            }}
            .card-header {{
                background-color: #f1f5f9;
                padding: 12px 15px;
                border-bottom: 1px solid #cbd5e1;
                border-radius: 8px 8px 0 0;
            }}
            .card-header h3 {{ margin: 0 0 6px 0; color: #1e3c72; font-size: 15px; }}
            .card-header p {{ margin: 3px 0; font-size: 12px; color: #334155; }}
            .card-body {{ padding: 15px; }}
            .card-body h4 {{ margin: 0 0 10px 0; color: #2a5298; font-size: 14px; }}
            .card-body p {{ font-size: 12px; margin: 6px 0; }}
            ul {{ margin: 6px 0; padding-right: 20px; font-size: 12px; }}
            li {{ margin-bottom: 4px; }}
            .guidance {{
                background-color: #eff6ff;
                border-right: 4px solid #2563eb;
                padding: 10px;
                margin-top: 10px;
                font-size: 11px;
                color: #1e40af;
                border-radius: 4px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{data.get("title", "تقرير وضعيات الدعم والعلاج")}</h1>
            <p>{data.get("subtitle", "")}</p>
        </div>
        {situations_html}
    </body>
    </html>
    """
    return weasyprint.HTML(string=full_html).write_pdf()

# التشغيل والواجهة
if uploaded_file and api_key:
    if st.button("🚀 تشخيص الملف وتوليد الـ PDF الاحترافي"):
        with st.spinner("جاري تحليل ملف التقييم وتنسيق المستند البيداغوجي..."):
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

                pdf_bytes = generate_pdf_from_html(result_data)

                st.download_button(
                    label="📥 تحميل ملف الـ PDF الجاهز للطباعة (بدون أخطاء خطوط)",
                    data=pdf_bytes,
                    file_name="وضعيات_الدعم_والعلاج_المفصلة.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"حدث خطأ أثناء المعالجة: {e}")
elif uploaded_file and not api_key:
    st.warning("⚠️ يرجى إدخال مفتاح Gemini API Key في القائمة الجانبية.")
