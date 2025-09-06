# app.py
import streamlit as st
import pandas as pd
import numpy as np
import re
import io
import time
from datetime import datetime
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

# ألوان
excel_color = "#217346"
chatgpt_color = "#0fa37f"
accent_color = "#1a73e8"
background_color = "#f0f0f0"


class AccountingAIApp:
    def __init__(self):
        # تهيئة بيانات الجلسة إذا لم تكن موجودة
        if 'data' not in st.session_state:
            st.session_state.data = {
                "المبيعات": pd.DataFrame(columns=["التاريخ", "العميل", "المبلغ", "الوصف", "الحالة"]),
                "المشتريات": pd.DataFrame(columns=["التاريخ", "المورد", "المبلغ", "الوصف", "الحالة"]),
                "المصروفات": pd.DataFrame(columns=["التاريخ", "النوع", "المبلغ", "الوصف", "الحالة"]),
                "العملاء": pd.DataFrame(columns=["الاسم", "البريد", "الهاتف", "الرصيد"]),
                "الموردين": pd.DataFrame(columns=["الاسم", "البريد", "الهاتف", "الرصيد"])
            }

        # مفاتيح الحالة الافتراضية
        st.session_state.setdefault('show_manual_input', False)
        st.session_state.setdefault('show_camera_input', False)
        st.session_state.setdefault('show_text_input', False)
        st.session_state.setdefault('input_text', "")

        # تحميل أي ملفات CSV موجودة
        self.load_data()

    def load_data(self):
        """تحميل البيانات من ملفات CSV إن وجدت"""
        try:
            for sheet_name in list(st.session_state.data.keys()):
                try:
                    df = pd.read_csv(f"{sheet_name}.csv", encoding='utf-8-sig')
                    # تحويل عمود المبلغ إلى رقمي إن وجد
                    if "المبلغ" in df.columns:
                        df['المبلغ'] = pd.to_numeric(df['المبلغ'], errors='coerce')
                    st.session_state.data[sheet_name] = df
                except FileNotFoundError:
                    # لا يوجد ملف بعد — نتجاهل
                    pass
                except Exception as e:
                    st.warning(f"مشكلة بقراءة {sheet_name}.csv: {e}")
        except Exception as e:
            st.error(f"خطأ في تحميل البيانات: {e}")

    def save_data(self):
        """حفظ البيانات إلى ملفات CSV"""
        try:
            for sheet_name, df in st.session_state.data.items():
                # احفظ مع ترميز utf-8-sig لتفادي مشاكل Excel مع العربية
                df.to_csv(f"{sheet_name}.csv", index=False, encoding='utf-8-sig')
            st.success("✅ تم حفظ البيانات محليًا (CSV)")
        except Exception as e:
            st.error(f"خطأ في حفظ البيانات: {e}")

    def run(self):
        """الواجهة الأساسية وتشغيل التطبيق"""
        st.sidebar.title("نظام المحاسبة الذكي")
        app_mode = st.sidebar.selectbox(
            "اختر الصفحة",
            ["الإدخال الرئيسي", "التقارير المحاسبية", "التحليل التفاعلي", "الإعدادات والربط", "التدقيق والمطابقة"]
        )

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

    # -------------------------
    # صفحة الإدخال
    # -------------------------
    def show_input_page(self):
        st.title("إدخال المعاملات المحاسبية")
        # أزرار الاختيار
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("📝 إدخال يدوي", key="btn_manual"):
                st.session_state.show_manual_input = True
                st.session_state.show_camera_input = False
                st.session_state.show_text_input = False
                st.session_state.input_text = ""
        with c2:
            if st.button("📷 مسح ضوئي", key="btn_camera"):
                st.session_state.show_camera_input = True
                st.session_state.show_manual_input = False
                st.session_state.show_text_input = False
                st.session_state.input_text = ""
        with c3:
            if st.button("🔊 إدخال نصي", key="btn_text"):
                st.session_state.show_text_input = True
                st.session_state.show_manual_input = False
                st.session_state.show_camera_input = False
                st.session_state.input_text = ""

        # عرض النماذج المطلوبة
        if st.session_state.show_manual_input:
            self.manual_input()
        if st.session_state.show_camera_input:
            self.camera_input()
        if st.session_state.show_text_input:
            self.text_input()

        # معاينة النص المحلل (إن وجد)
        if st.session_state.get('input_text'):
            st.subheader("معاينة البيانات")
            st.text_area("بيانات المعاملة (معاينة)", value=st.session_state.input_text, height=220, disabled=True)

            a, b, c = st.columns(3)
            with a:
                if st.button("🔄 معالجة البيانات", key="process_btn"):
                    self.process_data()
            with b:
                if st.button("💾 حفظ في النظام", key="save_btn"):
                    self.save_data()
            with c:
                if st.button("🔍 تدقيق سريع", key="quick_audit_btn"):
                    self.audit_data()

    # -------------------------
    # الإدخال النصي
    # -------------------------
    def text_input(self):
        st.subheader("الإدخال النصي للمعاملات")
        input_text = st.text_area(
            "أدخل بيانات المعاملة المحاسبية",
            height=160,
            placeholder="مثال: بيع لشركة التقنية بمبلغ 1500 ريال بتاريخ 2023-10-15",
            key="text_input_area"
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("تحليل النص", key="analyze_text_btn"):
                if input_text and input_text.strip():
                    accounting_data = self.parse_with_chatgpt(input_text)
                    self.display_accounting_data(accounting_data)
                    st.success("تم تحليل النص")
                else:
                    st.warning("الرجاء إدخال نص للتحليل")
        with col2:
            if st.button("رجوع", key="back_text_btn"):
                st.session_state.show_text_input = False
                st.session_state.input_text = ""
                st.experimental_rerun()

    # -------------------------
    # الإدخال بالكاميرا / صورة (محاكاة OCR)
    # -------------------------
    def camera_input(self):
        st.subheader("رفع صورة الفاتورة/المستند")
        uploaded_file = st.file_uploader("اختر صورة (PNG, JPG, JPEG)", type=['png', 'jpg', 'jpeg'], key="file_uploader")
        if uploaded_file:
            try:
                image = Image.open(uploaded_file)
                st.image(image, caption="الصورة المرفوعة", use_column_width=True)
            except Exception:
                st.warning("تعذر فتح الصورة، تحقق من الملف.")

            if st.button("استخراج النص من الصورة", key="extract_text_btn"):
                extracted_text = self.simulate_ocr_extraction()
                st.session_state.input_text = f"{extracted_text}\n"
                invoice_data = self.parse_invoice_with_chatgpt(extracted_text)
                self.display_accounting_data(invoice_data)
                st.success("تم استخراج وتحليل نص الصورة (محاكاة)")
        if st.button("رجوع", key="back_camera_btn"):
            st.session_state.show_camera_input = False
            st.session_state.input_text = ""
            st.experimental_rerun()

    def simulate_ocr_extraction(self):
        # نصوص عينة لاستخراجها عشوائياً كمحاكاة
        sample_texts = [
            "فاتورة بيع رقم INV-2023-001\nتاريخ: 2023-10-15\nالعميل: شركة التقنية\nالمبلغ: 1500 ريال\nالوصف: بيع منتجات تقنية",
            "فاتورة شراء رقم PUR-2023-002\nتاريخ: 2023-10-16\nالمورد: شركة المعدات\nالمبلغ: 2500 ريال\nالوصف: شراء معدات مكتبية",
            "إشعار مصروف\nتاريخ: 2023-10-17\nالنوع: مصروفات نقل\nالمبلغ: 300 ريال\nالوصف: تكاليف نقل للموظفين"
        ]
        return np.random.choice(sample_texts)

    # -------------------------
    # تحليل النص (محاكاة ChatGPT)
    # -------------------------
    def parse_with_chatgpt(self, text):
        amount = self.extract_amount(text)
        if "بيع" in text or "مبيعات" in text:
            return {
                "transaction_type": "بيع",
                "amount": amount,
                "currency": "ريال سعودي",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "description": text,
                "account_debit": "حساب المدينين",
                "account_credit": "إيرادات المبيعات",
                "vat_amount": round(amount * 0.15, 2)
            }
        if "شراء" in text or "مشتريات" in text:
            return {
                "transaction_type": "شراء",
                "amount": amount,
                "currency": "ريال سعودي",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "description": text,
                "account_debit": "المشتريات",
                "account_credit": "حساب الدائنين",
                "vat_amount": round(amount * 0.15, 2)
            }
        # افتراضي
        return {
            "transaction_type": "عام",
            "amount": amount,
            "currency": "ريال سعودي",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "description": text,
            "account_debit": "مصروفات عامة",
            "account_credit": "البنك",
            "vat_amount": 0.0
        }

    def extract_amount(self, text):
        """استخراج أول رقم يظهر في النص كعدد"""
        try:
            nums = re.findall(r'\d+\.\d+|\d+', str(text))
            if nums:
                return float(nums[0])
        except Exception:
            pass
        return 0.0

    def parse_invoice_with_chatgpt(self, text):
        amount = self.extract_amount(text)
        return {
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

    def display_accounting_data(self, data):
        """تحضير نص المعاينة من استجابة التحليل (محاكاة)"""
        lines = []
        if data.get("transaction_type") == "بيع":
            lines.append("=== معاملة بيع ===")
        elif data.get("transaction_type") == "شراء":
            lines.append("=== معاملة شراء ===")
        else:
            lines.append("=== معاملة محاسبية ===")

        for k, v in data.items():
            if k == "items" and isinstance(v, list):
                lines.append(f"{k}:")
                for item in v:
                    for ik, iv in item.items():
                        lines.append(f"  {ik}: {iv}")
                    lines.append("")
            else:
                lines.append(f"{k}: {v}")
        st.session_state.input_text = "\n".join(lines)

    # -------------------------
    # معالجة النص وتحويله إلى قيد
    # -------------------------
    def process_data(self):
        if not st.session_state.get('input_text'):
            st.warning("لا توجد بيانات لمعالجتها")
            return

        current_text = st.session_state.input_text
        if "=== معاملة" not in current_text:
            st.warning("نص المعاينة غير صالح")
            return

        # تحويل النص إلى مفتاح:قيمة
        transaction_data = {}
        for line in current_text.splitlines():
            if ':' in line and not line.strip().startswith('==='):
                key, val = line.split(':', 1)
                transaction_data[key.strip()] = val.strip()

        # أولاً: حالة الفاتورة (invoice) إذا وُجدت مفاتيح invoice/total_amount/supplier
        if 'invoice_number' in transaction_data or 'total_amount' in transaction_data or 'supplier' in transaction_data:
            amt = self.extract_amount(transaction_data.get('total_amount', transaction_data.get('المبلغ', 0)))
            date = transaction_data.get('date', datetime.now().strftime("%Y-%m-%d"))
            supplier = transaction_data.get('supplier', 'مورد')
            new_record = {
                "التاريخ": date,
                "المورد": supplier,
                "المبلغ": amt,
                "الوصف": transaction_data.get('description', ''),
                "الحالة": "معلقة"
            }
            st.session_state.data["المشتريات"] = pd.concat([st.session_state.data["المشتريات"], pd.DataFrame([new_record])], ignore_index=True)
            st.success("تمت إضافة فاتورة كمشتريات (محاكاة).")
            self.save_data()
            return

        ttype = transaction_data.get('transaction_type', '')
        # التعامل بحسب نوع المعاملة
        if 'بيع' in ttype:
            amt = self.extract_amount(transaction_data.get('amount', transaction_data.get('المبلغ', 0)))
            new_record = {
                "التاريخ": transaction_data.get('date', datetime.now().strftime("%Y-%m-%d")),
                "العميل": transaction_data.get('client', 'عميل'),
                "المبلغ": amt,
                "الوصف": transaction_data.get('description', ''),
                "الحالة": "معلقة"
            }
            st.session_state.data["المبيعات"] = pd.concat([st.session_state.data["المبيعات"], pd.DataFrame([new_record])], ignore_index=True)
            st.success("تمت إضافة معاملة بيع")
        elif 'شراء' in ttype:
            amt = self.extract_amount(transaction_data.get('amount', transaction_data.get('المبلغ', 0)))
            new_record = {
                "التاريخ": transaction_data.get('date', datetime.now().strftime("%Y-%m-%d")),
                "المورد": transaction_data.get('supplier', 'مورد'),
                "المبلغ": amt,
                "الوصف": transaction_data.get('description', ''),
                "الحالة": "معلقة"
            }
            st.session_state.data["المشتريات"] = pd.concat([st.session_state.data["المشتريات"], pd.DataFrame([new_record])], ignore_index=True)
            st.success("تمت إضافة معاملة شراء")
        else:
            st.info("نوع المعاملة غير محدد تفصيليًا — لم يتم إضافة قيد تلقائي")

        self.save_data()

    # -------------------------
    # الإدخال اليدوي (نموذج)
    # -------------------------
    def manual_input(self):
        st.subheader("الإدخال اليدوي للمعاملات")
        with st.form("manual_input_form"):
            c1, c2 = st.columns(2)
            with c1:
                transaction_type = st.selectbox("نوع المعاملة", ["بيع", "شراء", "مصروف"], key="trans_type")
                transaction_date = st.date_input("التاريخ", datetime.now(), key="trans_date")
                transaction_party = st.text_input("العميل/المورد", key="trans_party")
            with c2:
                transaction_amount = st.number_input("المبلغ", min_value=0.0, format="%.2f", key="trans_amount")
                transaction_desc = st.text_area("الوصف", key="trans_desc")

            c3, c4 = st.columns(2)
            with c3:
                submitted = st.form_submit_button("💾 حفظ المعاملة")
            with c4:
                back_btn = st.form_submit_button("↩️ رجوع")

            if back_btn:
                st.session_state.show_manual_input = False
                st.session_state.input_text = ""
                st.experimental_rerun()

            if submitted:
                if not transaction_party or transaction_amount is None:
                    st.error("يرجى ملء جميع الحقول المطلوبة")
                else:
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
                    st.session_state.input_text = ""
                    st.experimental_rerun()

    # -------------------------
    # التقارير
    # -------------------------
    def show_reports_page(self):
        st.title("📊 التقارير المحاسبية")
        report_type = st.selectbox("اختر نوع التقرير", list(st.session_state.data.keys()), key="report_type")
        if st.button("إنشاء التقرير", key="generate_report_btn"):
            self.generate_report(report_type)

    def generate_report(self, report_type):
        df = st.session_state.data.get(report_type, pd.DataFrame())
        if df.empty:
            st.warning("لا توجد بيانات لهذا التقرير.")
            return

        df_display = df.copy()
        if "المبلغ" in df_display.columns:
            df_display['المبلغ'] = pd.to_numeric(df_display['المبلغ'], errors='coerce').fillna(0)

        st.dataframe(df_display, use_container_width=True)
        total_amount = df_display['المبلغ'].sum() if 'المبلغ' in df_display.columns else 0
        count = len(df_display)

        c1, c2 = st.columns(2)
        with c1:
            st.metric("عدد المعاملات", count)
        with c2:
            st.metric("إجمالي المبلغ", f"{total_amount:,.2f} ريال")

        csv = df_display.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 تحميل التقرير كملف CSV",
            data=csv,
            file_name=f"{report_type}_report.csv",
            mime="text/csv",
            key=f"download_{report_type}"
        )

    # -------------------------
    # التحليل والرسوم
    # -------------------------
    def show_analysis_page(self):
        st.title("📈 التحليل المالي التفاعلي")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("تحليل المبيعات", key="sales_analysis_btn"):
                self.create_chart("المبيعات")
        with c2:
            if st.button("تحليل المصروفات", key="expenses_analysis_btn"):
                self.create_chart("المصروفات")
        with c3:
            if st.button("مقارنة الإيرادات", key="comparison_btn"):
                self.create_comparison_chart()

    def create_chart(self, data_type):
        df = st.session_state.data.get(data_type, pd.DataFrame()).copy()
        if df.empty:
            st.warning("لا توجد بيانات للرسم")
            return

        df['التاريخ'] = pd.to_datetime(df['التاريخ'], errors='coerce')
        df['المبلغ'] = pd.to_numeric(df['المبلغ'], errors='coerce').fillna(0)
        df = df.dropna(subset=['التاريخ'])
        if df.empty:
            st.warning("لا توجد تواريخ صالحة للرسم")
            return

        df['الشهر'] = df['التاريخ'].dt.to_period('M').astype(str)
        monthly = df.groupby('الشهر')['المبلغ'].sum().reset_index()
        fig = px.bar(monthly, x='الشهر', y='المبلغ', title=f'{data_type} الشهرية', color_discrete_sequence=[excel_color])
        fig.update_layout(xaxis_title="الشهر", yaxis_title="المبلغ", xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    def create_comparison_chart(self):
        sales = st.session_state.data.get("المبيعات", pd.DataFrame()).copy()
        purchases = st.session_state.data.get("المشتريات", pd.DataFrame()).copy()
        if sales.empty and purchases.empty:
            st.warning("لا توجد بيانات للمقارنة")
            return

        for df in (sales, purchases):
            if not df.empty:
                df['التاريخ'] = pd.to_datetime(df['التاريخ'], errors='coerce')
                df['المبلغ'] = pd.to_numeric(df['المبلغ'], errors='coerce').fillna(0)

        sales = sales.dropna(subset=['التاريخ'])
        purchases = purchases.dropna(subset=['التاريخ'])

        if not sales.empty:
            sales['الشهر'] = sales['التاريخ'].dt.to_period('M').astype(str)
            monthly_sales = sales.groupby('الشهر')['المبلغ'].sum().reset_index()
        else:
            monthly_sales = pd.DataFrame(columns=['الشهر', 'المبلغ'])

        if not purchases.empty:
            purchases['الشهر'] = purchases['التاريخ'].dt.to_period('M').astype(str)
            monthly_purchases = purchases.groupby('الشهر')['المبلغ'].sum().reset_index()
        else:
            monthly_purchases = pd.DataFrame(columns=['الشهر', 'المبلغ'])

        comparison = pd.merge(monthly_sales, monthly_purchases, on='الشهر', how='outer', suffixes=('_مبيعات', '_مشتريات')).fillna(0)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=comparison['الشهر'], y=comparison['المبلغ_مبيعات'], name='المبيعات', marker_color=excel_color))
        fig.add_trace(go.Bar(x=comparison['الشهر'], y=comparison['المبلغ_مشتريات'], name='المشتريات', marker_color=chatgpt_color))
        fig.update_layout(title='مقارنة المبيعات والمشتريات', xaxis_title="الشهر", yaxis_title="المبلغ", xaxis_tickangle=-45, barmode='group')
        st.plotly_chart(fig, use_container_width=True)

    # -------------------------
    # الإعدادات والربط
    # -------------------------
    def show_settings_page(self):
        st.title("⚙️ إعدادات النظام والربط الخارجي")
        st.subheader("إعدادات الربط")
        st.info("💱 أسعار العملات: محدث تلقائياً (محاكاة)")
        st.info("🏦 الربط البنكي: غير مفعل (محاكاة)")
        st.checkbox("🔄 التحديث التلقائي", value=True, key="auto_update")

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🔄 تحديث البيانات", key="update_data_btn"):
                self.update_external_data()
        with c2:
            if st.button("🔗 اختبار الاتصالات", key="test_connections_btn"):
                self.test_connections()
        with c3:
            if st.button("📤 تصدير البيانات", key="export_data_btn"):
                self.export_data()

    def update_external_data(self):
        with st.spinner("جاري تحديث البيانات..."):
            time.sleep(1.2)
            st.success("✅ تم تحديث البيانات (محاكاة)")

    def test_connections(self):
        with st.spinner("جاري اختبار الاتصالات..."):
            time.sleep(1.2)
            st.success("✅ اختبار الاتصالات ناجح (محاكاة)")

    def export_data(self):
        try:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                for sheet_name, df in st.session_state.data.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            data_bytes = output.getvalue()
            st.download_button(
                label="📥 تحميل البيانات كملف Excel",
                data=data_bytes,
                file_name="accounting_data_export.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_excel"
            )
            st.success("✅ تم تجهيز الملف للتنزيل")
        except Exception as e:
            st.error(f"فشل التصدير: {e}")

    # -------------------------
    # التدقيق والمطابقة
    # -------------------------
    def show_audit_page(self):
        st.title("🔍 تدقيق المحاسبة واكتشاف الأخطاء")
        if st.button("▶️ بدء عملية التدقيق", key="start_audit_btn"):
            self.run_audit()

    def run_audit(self):
        with st.spinner("جاري تدقيق البيانات..."):
            time.sleep(2.0)
            results = {
                "status": "تم التدقيق",
                "issues_found": [
                    {
                        "type": "تناقض",
                        "description": "مثال: رصيد مدين لا يساوي الرصيد الدائن لقيد معين (محاكاة)",
                        "suggestion": "مراجعة القيد رقم JV-XXXX"
                    }
                ],
                "recommendations": [
                    "مراجعة دليل الحسابات",
                    "التأكد من توازن قيود اليومية"
                ]
            }
            self.display_audit_results(results)

    def display_audit_results(self, results):
        st.subheader("نتائج التدقيق")
        st.write(f"**حالة التدقيق:** {results.get('status','')}")
        if results.get('issues_found'):
            st.write("**المشكلات المكتشفة:**")
            for issue in results['issues_found']:
                st.write(f"- **{issue.get('type','')}**: {issue.get('description','')}")
                st.write(f"  اقتراح: {issue.get('suggestion','')}")
        if results.get('recommendations'):
            st.write("**التوصيات:**")
            for rec in results['recommendations']:
                st.write(f"- {rec}")

        # زر تصدير تقرير نصي
        audit_text = "نتائج تدقيق النظام المحاسبي\n" + "="*50 + "\n\n"
        audit_text += f"حالة التدقيق: {results.get('status','')}\n\n"
        if results.get('issues_found'):
            audit_text += "المشكلات المكتشفة:\n"
            for issue in results['issues_found']:
                audit_text += f"- نوع المشكلة: {issue.get('type','')}\n  الوصف: {issue.get('description','')}\n  الاقتراح: {issue.get('suggestion','')}\n\n"
        if results.get('recommendations'):
            audit_text += "التوصيات:\n"
            for rec in results['recommendations']:
                audit_text += f"- {rec}\n"

        st.download_button(label="📄 تحميل تقرير التدقيق", data=audit_text, file_name="audit_report.txt", mime="text/plain", key="download_audit")


if __name__ == "__main__":
    app = AccountingAIApp()
    app.run()



