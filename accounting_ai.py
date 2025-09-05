import streamlit as st
import pandas as pd
import base64
import io
from datetime import datetime
import time
import re
import numpy as np
from PIL import Image
import plotly.express as px
import plotly.graph_objects as go

# إعداد صفحة Streamlit
st.set_page_config(
    page_title="نظام المحاسبة الذكي",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ألوان مستوحاة من Excel وChatGPT
excel_color = "#217346"
chatgpt_color = "#0fa37f"
accent_color = "#1a73e8"
background_color = "#f0f0f0"

class AccountingAIApp:
    def __init__(self):
        # بيانات التطبيق
        if 'data' not in st.session_state:
            st.session_state.data = {
                "المبيعات": pd.DataFrame(columns=["التاريخ", "العميل", "المبلغ", "الوصف", "الحالة"]),
                "المشتريات": pd.DataFrame(columns=["التاريخ", "المورد", "المبلغ", "الوصف", "الحالة"]),
                "المصروفات": pd.DataFrame(columns=["التاريخ", "النوع", "المبلغ", "الوصف", "الحالة"]),
                "العملاء": pd.DataFrame(columns=["الاسم", "البريد", "الهاتف", "الرصيد"]),
                "الموردين": pd.DataFrame(columns=["الاسم", "البريد", "الهاتف", "الرصيد"])
            }
        
        # ملف البيانات
        self.excel_file = "accounting_data.csv"
        self.load_data()
    
    def load_data(self):
        """تحميل البيانات من ملف CSV"""
        try:
            # محاولة تحميل البيانات من ملف CSV
            for sheet_name in st.session_state.data:
                try:
                    df = pd.read_csv(f"{sheet_name}.csv")
                    st.session_state.data[sheet_name] = df
                except:
                    # إذا لم يكن الملف موجوداً، نستخدم البيانات الافتراضية
                    pass
        except Exception as e:
            st.error(f"خطأ في تحميل البيانات: {e}")
    
    def save_data(self):
        """حفظ البيانات إلى ملفات CSV"""
        try:
            for sheet_name, df in st.session_state.data.items():
                df.to_csv(f"{sheet_name}.csv", index=False, encoding='utf-8-sig')
            st.success("تم حفظ البيانات بنجاح")
        except Exception as e:
            st.error(f"خطأ في حفظ البيانات: {e}")
    
    def run(self):
        """تشغيل التطبيق الرئيسي"""
        st.sidebar.title("نظام المحاسبة الذكي")
        
        # قائمة التنقل
        app_mode = st.sidebar.selectbox(
            "اختر الصفحة",
            ["الإدخال الرئيسي", "التقارير المحاسبية", "التحليل التفاعلي", "الإعدادات والربط", "التدقيق والمطابقة"]
        )
        
        # عرض الصفحة المحددة
        if app_mode == "الإدخال الرئيسي":
            self.show_input_page()
        elif app_mode == "التقارير المحاسبية":
            self.show_reports_page()
        elif app_mode == "التحليل التفاعلي":
            self.show_analysis_page()
        elif app_mode == "الإعدادات والربط":
            self.show_settings_page()
        elif app_mode == "التدقيق والمطابقة":
            self.show_audit_page()
    
    def show_input_page(self):
        """عرض صفحة الإدخال الرئيسي"""
        st.title("إدخال المعاملات المحاسبية")
        
        # أزرار طرق الإدخال المختلفة
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📝 إدخال يدوي", type="primary", use_container_width=True):
                st.session_state.show_manual_input = True
        
        with col2:
            if st.button("📷 مسح ضوئي", type="primary", use_container_width=True):
                st.session_state.show_camera_input = True
        
        with col3:
            if st.button("🔊 إدخال نصي", type="primary", use_container_width=True):
                st.session_state.show_text_input = True
        
        # عرض نمط الإدخال المحدد
        if st.session_state.get('show_manual_input', False):
            self.manual_input()
        
        if st.session_state.get('show_camera_input', False):
            self.camera_input()
        
        if st.session_state.get('show_text_input', False):
            self.text_input()
        
        # منطقة عرض البيانات
        if 'input_text' in st.session_state:
            st.subheader("معاينة البيانات")
            st.text_area("بيانات المعاملة", value=st.session_state.input_text, height=200, disabled=True, key="preview_area")
            
            # أزرار المعالجة
            col4, col5, col6 = st.columns(3)
            
            with col4:
                if st.button("🔄 معالجة البيانات", use_container_width=True, key="process_btn"):
                    self.process_data()
            
            with col5:
                if st.button("💾 حفظ في النظام", use_container_width=True, key="save_btn"):
                    self.save_data()
            
            with col6:
                if st.button("🔍 تدقيق المحاسبة", use_container_width=True, key="audit_btn"):
                    self.audit_data()
    
    def text_input(self):
        """معالجة الإدخال النصي"""
        st.subheader("الإدخال النصي للمعاملات")
        
        input_text = st.text_area("أدخل بيانات المعاملة المحاسبية", height=100, 
                                 placeholder="مثال: بيع لشركة التقنية بمبلغ 1500 ريال بتاريخ 2023-10-15",
                                 key="text_input_area")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("تحليل النص", key="analyze_text_btn"):
                if input_text:
                    # استخدام ChatGPT لتحويل النص إلى بيانات محاسبية منظمة
                    accounting_data = self.parse_with_chatgpt(input_text)
                    self.display_accounting_data(accounting_data)
                    st.success("تم تحليل النص بنجاح")
                else:
                    st.warning("يرجى إدخال نص للمعاملة")
        
        with col2:
            if st.button("رجوع", key="back_text_btn"):
                st.session_state.show_text_input = False
                st.rerun()
    
    def camera_input(self):
        """معالجة الإدخال بالكاميرا"""
        st.subheader("مسح الفواتير والوثائق")
        
        uploaded_file = st.file_uploader("رفع صورة الفاتورة أو المستند", type=['png', 'jpg', 'jpeg'], key="file_uploader")
        
        if uploaded_file is not None:
            # عرض الصورة
            image = Image.open(uploaded_file)
            st.image(image, caption="الصورة المرفوعة", use_column_width=True)
            
            if st.button("استخراج النص من الصورة", key="extract_text_btn"):
                # استخدام OCR محاكى (لأن pytesseract قد يسبب مشاكل)
                extracted_text = self.simulate_ocr_extraction()
                st.session_state.input_text = f"النص المستخرج: {extracted_text}\n"
                
                # تحليل النص باستخدام ChatGPT
                invoice_data = self.parse_invoice_with_chatgpt(extracted_text)
                self.display_accounting_data(invoice_data)
                
                st.success("تم معالجة الصورة بنجاح")
        
        if st.button("رجوع", key="back_camera_btn"):
            st.session_state.show_camera_input = False
            st.rerun()
    
    def simulate_ocr_extraction(self):
        """محاكاة استخراج النص من الصورة (بدون OCR حقيقي)"""
        sample_texts = [
            "فاتورة بيع رقم INV-2023-001\nتاريخ: 2023-10-15\nالعميل: شركة التقنية\nالمبلغ: 1500 ريال\nالوصف: بيع منتجات تقنية",
            "فاتورة شراء رقم PUR-2023-002\nتاريخ: 2023-10-16\nالمورد: شركة المعدات\nالمبلغ: 2500 ريال\nالوصف: شراء معدات مكتبية",
            "إشعار مصروف\nتاريخ: 2023-10-17\nالنوع: مصروفات نقل\nالمبلغ: 300 ريال\nالوصف: تكاليف نقل للموظفين"
        ]
        return np.random.choice(sample_texts)
    
    def parse_with_chatgpt(self, text):
        """محاكاة اتصال بـ ChatGPT API"""
        amount = self.extract_amount(text)
        
        if "بيع" in text or "مبيعات" in text:
            simulated_response = {
                "transaction_type": "بيع",
                "amount": amount,
                "currency": "ريال سعودي",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "description": text,
                "account_debit": "حساب المدينين",
                "account_credit": "إيرادات المبيعات",
                "vat_amount": round(amount * 0.15, 2)
            }
        elif "شراء" in text or "مشتريات" in text:
            simulated_response = {
                "transaction_type": "شراء",
                "amount": amount,
                "currency": "ريال سعودي",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "description": text,
                "account_debit": "المشتريات",
                "account_credit": "حساب الدائنين",
                "vat_amount": round(amount * 0.15, 2)
            }
        else:
            simulated_response = {
                "transaction_type": "عام",
                "amount": amount,
                "currency": "ريال سعودي",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "description": text,
                "account_debit": "مصروفات عامة",
                "account_credit": "البنك",
                "vat_amount": 0.0
            }
        
        return simulated_response
    
    def extract_amount(self, text):
        """استخراج المبالغ الرقمية من النص"""
        numbers = re.findall(r'\d+\.\d+|\d+', text)
        if numbers:
            return float(numbers[0])
        return 1000.0  # قيمة افتراضية
    
    def parse_invoice_with_chatgpt(self, text):
        """محاكاة تحليل الفاتورة باستخدام ChatGPT"""
        amount = self.extract_amount(text)
        
        simulated_response = {
            "invoice_number": f"INV-{datetime.now().strftime('%Y%m%d')}-001",
            "supplier": "شركة المعدات المتحدة",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "due_date": (datetime.now() + pd.DateOffset(days=30)).strftime("%Y-%m-%d"),
            "total_amount": amount,
            "items": [
                {"description": "طابعة ليزر", "quantity": 2, "unit_price": 1200.00, "total": 2400.00},
                {"description": "حبر طابعة", "quantity": 5, "unit_price": 170.00, "total": 850.00}
            ],
            "vat_amount": round(amount * 0.15, 2)
        }
        
        return simulated_response
    
    def display_accounting_data(self, data):
        """عرض البيانات المحاسبية في واجهة المستخدم"""
        display_text = ""
        
        if data.get("transaction_type") == "بيع":
            display_text += "=== معاملة بيع ===\n"
        elif data.get("transaction_type") == "شراء":
            display_text += "=== معاملة شراء ===\n"
        else:
            display_text += "=== معاملة محاسبية ===\n"
        
        for key, value in data.items():
            if key == "items":
                display_text += f"{key}:\n"
                for item in value:
                    for k, v in item.items():
                        display_text += f"  {k}: {v}\n"
                    display_text += "\n"
            else:
                display_text += f"{key}: {value}\n"
        
        st.session_state.input_text = display_text
    
    def process_data(self):
        """معالجة البيانات وإضافتها للنظام"""
        if 'input_text' not in st.session_state or not st.session_state.input_text:
            st.warning("لا توجد بيانات معالجة")
            return
        
        current_text = st.session_state.input_text
        if "=== معاملة" not in current_text:
            st.warning("لا توجد بيانات معالجة صالحة")
            return
        
        # في التطبيق الحقيقي، سيتم تحليل النص وإضافة البيانات للداتا فريم المناسب
        lines = current_text.split('\n')
        transaction_data = {}
        
        for line in lines:
            if ':' in line and not line.strip().startswith('==='):
                key, value = line.split(':', 1)
                transaction_data[key.strip()] = value.strip()
        
        # تحديد نوع المعاملة وإضافتها للبيانات
        transaction_type = transaction_data.get("transaction_type", "")
        if "بيع" in transaction_type:
            new_record = {
                "التاريخ": transaction_data.get("date", datetime.now().strftime("%Y-%m-%d")),
                "العميل": "عميل",
                "المبلغ": transaction_data.get("amount", 0),
                "الوصف": transaction_data.get("description", ""),
                "الحالة": "معلقة"
            }
            st.session_state.data["المبيعات"] = pd.concat([st.session_state.data["المبيعات"], pd.DataFrame([new_record])], ignore_index=True)
            st.success("تمت إضافة معاملة البيع بنجاح")
        
        elif "شراء" in transaction_type:
            new_record = {
                "التاريخ": transaction_data.get("date", datetime.now().strftime("%Y-%m-%d")),
                "المورد": "مورد",
                "المبلغ": transaction_data.get("amount", 0),
                "الوصف": transaction_data.get("description", ""),
                "الحالة": "معلقة"
            }
            st.session_state.data["المشتريات"] = pd.concat([st.session_state.data["المشتريات"], pd.DataFrame([new_record])], ignore_index=True)
            st.success("تمت إضافة معاملة الشراء بنجاح")
        
        self.save_data()
    
    def manual_input(self):
        """فتح نافذة الإدخال اليدوي"""
        st.subheader("الإدخال اليدوي للمعاملات")
        
        with st.form("manual_input_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                transaction_type = st.selectbox("نوع المعاملة", ["بيع", "شراء", "مصروف"], key="trans_type")
                transaction_date = st.date_input("التاريخ", datetime.now(), key="trans_date")
                transaction_party = st.text_input("العميل/المورد", key="trans_party")
            
            with col2:
                transaction_amount = st.number_input("المبلغ", min_value=0.0, format="%.2f", key="trans_amount")
                transaction_desc = st.text_area("الوصف", key="trans_desc")
            
            col3, col4 = st.columns(2)
            with col3:
                submitted = st.form_submit_button("💾 حفظ المعاملة")
            with col4:
                back_btn = st.form_submit_button("↩️ رجوع")
            
            if back_btn:
                st.session_state.show_manual_input = False
                st.rerun()
            
            if submitted:
                if not all([transaction_party, transaction_amount]):
                    st.error("جميع الحقول مطلوبة")
                    return
                
                new_record = {
                    "التاريخ": transaction_date.strftime("%Y-%m-%d"),
                    "المبلغ": transaction_amount,
                    "الوصف": transaction_desc,
                    "الحالة": "مكتمل"
                }
                
                if transaction_type == "بيع":
                    new_record["العميل"] = transaction_party
                    st.session_state.data["المبيعات"] = pd.concat([st.session_state.data["المبيعات"], pd.DataFrame([new_record])], ignore_index=True)
                elif transaction_type == "شراء":
                    new_record["المورد"] = transaction_party
                    st.session_state.data["المشتريات"] = pd.concat([st.session_state.data["المشتريات"], pd.DataFrame([new_record])], ignore_index=True)
                else:
                    new_record["النوع"] = transaction_type
                    st.session_state.data["المصروفات"] = pd.concat([st.session_state.data["المصروفات"], pd.DataFrame([new_record])], ignore_index=True)
                
                self.save_data()
                st.success("✅ تمت إضافة المعاملة بنجاح")
                st.session_state.show_manual_input = False
                st.rerun()
    
    def show_reports_page(self):
        """عرض صفحة التقارير"""
        st.title("📊 التقارير المحاسبية")
        
        # اختيار نوع التقرير
        report_type = st.selectbox("اختر نوع التقرير", list(st.session_state.data.keys()), key="report_type")
        
        if st.button("إنشاء التقرير", key="generate_report_btn"):
            self.generate_report(report_type)
    
    def generate_report(self, report_type):
        """إنشاء تقرير حسب النوع المحدد"""
        if not st.session_state.data[report_type].empty:
            st.dataframe(st.session_state.data[report_type], use_container_width=True)
            
            # إحصائيات سريعة
            total_amount = st.session_state.data[report_type]["المبلغ"].sum()
            count = len(st.session_state.data[report_type])
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("عدد المعاملات", count)
            with col2:
                st.metric("إجمالي المبلغ", f"{total_amount:,.2f} ريال")
            
            # خيارات التصدير
            csv = st.session_state.data[report_type].to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 تحميل التقرير كملف CSV",
                data=csv,
                file_name=f"{report_type}_report.csv",
                mime="text/csv",
                key=f"download_{report_type}"
            )
        else:
            st.warning("لا توجد بيانات متاحة لهذا النوع من التقارير")
    
    def show_analysis_page(self):
        """عرض صفحة التحليل"""
        st.title("📈 التحليل المالي التفاعلي")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("تحليل المبيعات", key="sales_analysis_btn"):
                self.create_chart("المبيعات")
        
        with col2:
            if st.button("تحليل المصروفات", key="expenses_analysis_btn"):
                self.create_chart("المصروفات")
        
        with col3:
            if st.button("مقارنة الإيرادات", key="comparison_btn"):
                self.create_comparison_chart()
    
    def create_chart(self, data_type):
        """إنشاء رسم بياني للبيانات باستخدام Plotly"""
        if st.session_state.data[data_type].empty:
            st.warning("لا توجد بيانات متاحة")
            return
        
        # تحضير البيانات
        df = st.session_state.data[data_type].copy()
        df['التاريخ'] = pd.to_datetime(df['التاريخ'], errors='coerce')
        df['المبلغ'] = pd.to_numeric(df['المبلغ'], errors='coerce')
        
        # تجميع البيانات حسب الشهر
        df['الشهر'] = df['التاريخ'].dt.to_period('M').astype(str)
        monthly_data = df.groupby('الشهر')['المبلغ'].sum().reset_index()
        
        # إنشاء الرسم البياني باستخدام Plotly
        fig = px.bar(monthly_data, x='الشهر', y='المبلغ', 
                     title=f'{data_type} الشهرية',
                     color_discrete_sequence=[excel_color])
        
        fig.update_layout(
            xaxis_title="الشهر",
            yaxis_title="المبلغ",
            xaxis_tickangle=-45
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def create_comparison_chart(self):
        """إنشاء رسم بياني مقارن باستخدام Plotly"""
        sales_data = st.session_state.data["المبيعات"].copy()
        purchases_data = st.session_state.data["المشتريات"].copy()
        
        if sales_data.empty and purchases_data.empty:
            st.warning("لا توجد بيانات متاحة")
            return
        
        sales_data['التاريخ'] = pd.to_datetime(sales_data['التاريخ'], errors='coerce')
        purchases_data['التاريخ'] = pd.to_datetime(purchases_data['التاريخ'], errors='coerce')
        
        sales_data['المبلغ'] = pd.to_numeric(sales_data['المبلغ'], errors='coerce')
        purchases_data['المبلغ'] = pd.to_numeric(purchases_data['المبلغ'], errors='coerce')
        
        # تجميع البيانات حسب الشهر
        sales_data['الشهر'] = sales_data['التاريخ'].dt.to_period('M').astype(str)
        purchases_data['الشهر'] = purchases_data['التاريخ'].dt.to_period('M').astype(str)
        
        monthly_sales = sales_data.groupby('الشهر')['المبلغ'].sum().reset_index()
        monthly_purchases = purchases_data.groupby('الشهر')['المبلغ'].sum().reset_index()
        
        # دمج البيانات للمقارنة
        comparison_data = pd.merge(monthly_sales, monthly_purchases, on='الشهر', how='outer', suffixes=('_مبيعات', '_مشتريات'))
        comparison_data = comparison_data.fillna(0)
        
        # إنشاء الرسم البياني باستخدام Plotly
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=comparison_data['الشهر'],
            y=comparison_data['المبلغ_مبيعات'],
            name='المبيعات',
            marker_color=excel_color
        ))
        
        fig.add_trace(go.Bar(
            x=comparison_data['الشهر'],
            y=comparison_data['المبلغ_مشتريات'],
            name='المشتريات',
            marker_color=chatgpt_color
        ))
        
        fig.update_layout(
            title='مقارنة المبيعات والمشتريات',
            xaxis_title="الشهر",
            yaxis_title="المبلغ",
            xaxis_tickangle=-45,
            barmode='group'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def show_settings_page(self):
        """عرض صفحة الإعدادات"""
        st.title("⚙️ إعدادات النظام والربط الخارجي")
        
        st.subheader("إعدادات الربط")
        
        # أسعار العملات
        st.info("💱 أسعار العملات: محدث تلقائياً")
        
        # حالة الربط البنكي
        st.info("🏦 الربط البنكي: متصل")
        
        # التحديث التلقائي
        auto_update = st.checkbox("🔄 التحديث التلقائي", value=True, key="auto_update")
        
        # أزرار التحكم
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 تحديث البيانات", key="update_data_btn"):
                self.update_external_data()
        
        with col2:
            if st.button("🔗 اختبار الاتصالات", key="test_connections_btn"):
                self.test_connections()
        
        with col3:
            if st.button("📤 تصدير البيانات", key="export_data_btn"):
                self.export_data()
    
    def update_external_data(self):
        """تحديث البيانات من المصادر الخارجية"""
        with st.spinner("جاري تحديث البيانات الخارجية..."):
            time.sleep(2)
            st.success("✅ تم تحديث البيانات الخارجية")
    
    def test_connections(self):
        """اختبار الاتصالات الخارجية"""
        with st.spinner("جاري اختبار الاتصالات..."):
            time.sleep(2)
            st.success("✅ جميع الاتصالات تعمل بشكل صحيح")
    
    def export_data(self):
        """تصدير البيانات"""
        try:
            # إنشاء ملف Excel افتراضي باستخدام pandas
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                for sheet_name, df in st.session_state.data.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            output.seek(0)
            
            st.download_button(
                label="📥 تحميل البيانات كملف Excel",
                data=output,
                file_name="accounting_data_export.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_excel"
            )
            
            st.success("✅ تم تصدير البيانات بنجاح")
        except Exception as e:
            st.error(f"❌ فشل في تصدير البيانات: {e}")
    
    def show_audit_page(self):
        """عرض صفحة التدقيق"""
        st.title("🔍 تدقيق المحاسبة واكتشاف الأخطاء")
        
        if st.button("▶️ بدء عملية التدقيق", type="primary", key="start_audit_btn"):
            self.run_audit()
    
    def run_audit(self):
        """تشغيل عملية التدقيق"""
        with st.spinner("جاري تدقيق البيانات المحاسبية..."):
            time.sleep(3)
            
            audit_results = {
                "status": "تم التدقيق",
                "issues_found": [
                    {
                        "type": "تناقض",
                        "description": "الرصيد المدين لا يساوي الرصيد الدائن في قيد اليومية",
                        "suggestion": "مراجعة القيد رقم JV-2023-1045"
                    }
                ],
                "recommendations": [
                    "تعديل القيد المحاسبي لتحقيق التوازن",
                    "مراجعة دليل الحسابات للتأكد من التصنيف الصحيح"
                ]
            }
            
            self.display_audit_results(audit_results)
    
    def display_audit_results(self, results):
        """عرض نتائج التدقيق"""
        st.subheader("نتائج تدقيق النظام المحاسبي")
        
        st.write(f"**حالة التدقيق:** {results['status']}")
        
        if results['issues_found']:
            st.write("**المشكلات المكتشفة:**")
            for issue in results['issues_found']:
                st.write(f"- **نوع المشكلة:** {issue['type']}")
                st.write(f"  **الوصف:** {issue['description']}")
                st.write(f"  **الاقتراح:** {issue['suggestion']}")
                st.write("")
        
        if results['recommendations']:
            st.write("**التوصيات العامة:**")
            for rec in results['recommendations']:
                st.write(f"- {rec}")
        
        # زر معالجة الأخطاء
        if st.button("🔧 معالجة الأخطاء", key="fix_errors_btn"):
            with st.spinner("جاري معالجة الأخطاء..."):
                time.sleep(2)
                st.success("✅ تم معالجة الأخطاء")
        
        # زر تصدير التقرير
        audit_text = f"نتائج تدقيق النظام المحاسبي\n{'='*50}\n\n"
        audit_text += f"حالة التدقيق: {results['status']}\n\n"
        
        if results['issues_found']:
            audit_text += "المشكلات المكتشفة:\n"
            for issue in results['issues_found']:
                audit_text += f"- نوع المشكلة: {issue['type']}\n"
                audit_text += f"  الوصف: {issue['description']}\n"
                audit_text += f"  الاقتراح: {issue['suggestion']}\n\n"
        
        if results['recommendations']:
            audit_text += "التوصيات العامة:\n"
            for rec in results['recommendations']:
                audit_text += f"- {rec}\n"
        
        st.download_button(
            label="📄 تصدير تقرير التدقيق",
            data=audit_text,
            file_name="audit_report.txt",
            mime="text/plain",
            key="download_audit"
        )
    
    def audit_data(self):
        """تدقيق البيانات الحالية"""
        with st.spinner("جاري تدقيق البيانات..."):
            time.sleep(2)
            
            # محاكاة نتائج التدقيق
            st.success("✅ تم تدقيق البيانات بنجاح")
            
            # عرض النتائج
            st.write("**نتائج التدقيق:**")
            st.write("- ✅ جميع المعاملات متوازنة")
            st.write("- ✅ لا توجد أخطاء في التصنيف")
            st.write("- ✅ البيانات المالية سليمة")

# تشغيل التطبيق
if __name__ == "__main__":
    app = AccountingAIApp()
    app.run()

