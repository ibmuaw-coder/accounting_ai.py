import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import base64
import io
from datetime import datetime
import time
import re
import numpy as np
from PIL import Image
import pytesseract

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
                self.manual_input()
        
        with col2:
            if st.button("📷 مسح ضوئي", type="primary", use_container_width=True):
                self.camera_input()
        
        with col3:
            if st.button("🔊 إدخال نصي", type="primary", use_container_width=True):
                self.text_input()
        
        # منطقة عرض البيانات
        if 'input_text' in st.session_state:
            st.subheader("معاينة البيانات")
            st.text_area("بيانات المعاملة", value=st.session_state.input_text, height=200, disabled=True)
            
            # أزرار المعالجة
            col4, col5, col6 = st.columns(3)
            
            with col4:
                if st.button("🔄 معالجة البيانات", use_container_width=True):
                    self.process_data()
            
            with col5:
                if st.button("💾 حفظ في النظام", use_container_width=True):
                    self.save_data()
            
            with col6:
                if st.button("🔍 تدقيق المحاسبة", use_container_width=True):
                    self.audit_data()
    
    def text_input(self):
        """معالجة الإدخال النصي"""
        st.subheader("الإدخال النصي للمعاملات")
        
        input_text = st.text_area("أدخل بيانات المعاملة المحاسبية", height=100, 
                                 placeholder="مثال: بيع لشركة التقنية بمبلغ 1500 ريال بتاريخ 2023-10-15")
        
        if st.button("تحليل النص"):
            if input_text:
                # استخدام ChatGPT لتحويل النص إلى بيانات محاسبية منظمة
                accounting_data = self.parse_with_chatgpt(input_text)
                self.display_accounting_data(accounting_data)
                st.success("تم تحليل النص بنجاح")
            else:
                st.warning("يرجى إدخال نص للمعاملة")
    
    def camera_input(self):
        """معالجة الإدخال بالكاميرا"""
        st.subheader("مسح الفواتير والوثائق")
        
        uploaded_file = st.file_uploader("رفع صورة الفاتورة أو المستند", type=['png', 'jpg', 'jpeg'])
        
        if uploaded_file is not None:
            # عرض الصورة
            image = Image.open(uploaded_file)
            st.image(image, caption="الصورة المرفوعة", use_column_width=True)
            
            if st.button("استخراج النص من الصورة"):
                # استخدام OCR لاستخراج النص
                extracted_text = self.extract_text_from_image(image)
                st.session_state.input_text = f"النص المستخرج: {extracted_text}\n"
                
                # تحليل النص باستخدام ChatGPT
                invoice_data = self.parse_invoice_with_chatgpt(extracted_text)
                self.display_accounting_data(invoice_data)
                
                st.success("تم معالجة الصورة بنجاح")
    
    def extract_text_from_image(self, image):
        """استخراج النص من الصورة باستخدام OCR"""
        try:
            # تحسين الصورة لتحسين دقة OCR
            image = image.convert('L')  # تحويل إلى تدرج الرمادي
            text = pytesseract.image_to_string(image, lang='ara+eng')
            return text
        except Exception as e:
            return f"خطأ في استخراج النص: {e}"
    
    def parse_with_chatgpt(self, text):
        """محاكاة اتصال بـ ChatGPT API"""
        # محاكاة استجابة ChatGPT بناءً على النص المدخل
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
        if "بيع" in transaction_data.get("transaction_type", ""):
            new_record = {
                "التاريخ": transaction_data.get("date", datetime.now().strftime("%Y-%m-%d")),
                "العميل": "عميل",
                "المبلغ": transaction_data.get("amount", 0),
                "الوصف": transaction_data.get("description", ""),
                "الحالة": "معلقة"
            }
            st.session_state.data["المبيعات"] = pd.concat([st.session_state.data["المبيعات"], pd.DataFrame([new_record])], ignore_index=True)
            st.success("تمت إضافة معاملة البيع بنجاح")
        
        elif "شراء" in transaction_data.get("transaction_type", ""):
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
                transaction_type = st.selectbox("نوع المعاملة", ["بيع", "شراء", "مصروف"])
                transaction_date = st.date_input("التاريخ", datetime.now())
                transaction_party = st.text_input("العميل/المورد")
            
            with col2:
                transaction_amount = st.number_input("المبلغ", min_value=0.0, format="%.2f")
                transaction_desc = st.text_area("الوصف")
            
            submitted = st.form_submit_button("💾 حفظ المعاملة")
            
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
    
    def show_reports_page(self):
        """عرض صفحة التقارير"""
        st.title("📊 التقارير المحاسبية")
        
        # اختيار نوع التقرير
        report_type = st.selectbox("اختر نوع التقرير", list(st.session_state.data.keys()))
        
        if st.button("إنشاء التقرير"):
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
                mime="text/csv"
            )
        else:
            st.warning("لا توجد بيانات متاحة لهذا النوع من التقارير")
    
    def show_analysis_page(self):
        """عرض صفحة التحليل"""
        st.title("📈 التحليل المالي التفاعلي")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("تحليل المبيعات"):
                self.create_chart("المبيعات")
        
        with col2:
            if st.button("تحليل المصروفات"):
                self.create_chart("المصروفات")
        
        with col3:
            if st.button("مقارنة الإيرادات"):
                self.create_comparison_chart()
    
    def create_chart(self, data_type):
        """إنشاء رسم بياني للبيانات"""
        if st.session_state.data[data_type].empty:
            st.warning("لا توجد بيانات متاحة")
            return
        
        # تحضير البيانات
        df = st.session_state.data[data_type].copy()
        df['التاريخ'] = pd.to_datetime(df['التاريخ'], errors='coerce')
        df['المبلغ'] = pd.to_numeric(df['المبلغ'], errors='coerce')
        
        # تجميع البيانات حسب الشهر
        monthly_data = df.groupby(df['التاريخ'].dt.to_period('M'))['المبلغ'].sum()
        
        # إنشاء الرسم البياني
        fig, ax = plt.subplots(figsize=(10, 6))
        months = [str(period) for period in monthly_data.index]
        amounts = monthly_data.values
        
        ax.bar(months, amounts, color=excel_color)
        ax.set_title(f'{data_type} الشهرية', fontsize=16)
        ax.set_ylabel('المبلغ', fontsize=12)
        ax.tick_params(axis='x', rotation=45)
        
        st.pyplot(fig)
    
    def create_comparison_chart(self):
        """إنشاء رسم بياني مقارن"""
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
        monthly_sales = sales_data.groupby(sales_data['التاريخ'].dt.to_period('M'))['المبلغ'].sum()
        monthly_purchases = purchases_data.groupby(purchases_data['التاريخ'].dt.to_period('M'))['المبلغ'].sum()
        
        # إنشاء الرسم البياني
        fig, ax = plt.subplots(figsize=(10, 6))
        
        months = [str(period) for period in monthly_sales.index]
        sales = monthly_sales.values
        purchases = monthly_purchases.reindex(monthly_sales.index, fill_value=0).values
        
        bar_width = 0.35
        x = np.arange(len(months))
        
        ax.bar(x - bar_width/2, sales, bar_width, label='المبيعات', color=excel_color)
        ax.bar(x + bar_width/2, purchases, bar_width, label='المشتريات', color=chatgpt_color)
        
        ax.set_x

