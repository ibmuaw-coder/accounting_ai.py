import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import openpyxl
from openpyxl import Workbook
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.font_manager import FontProperties
import speech_recognition as sr
import pytesseract
from PIL import Image, ImageTk, ImageOps
import cv2
import requests
import json
from datetime import datetime
import threading
import queue
import os
import numpy as np
import re
from num2words import num2words
from gtts import gTTS
import pygame
import time
from arabic_reshaper import reshape
from bidi.algorithm import get_display
import unicodedata

# تهيئة pygame للصوت
pygame.mixer.init()

class AccountingAIApp:
    def __init__(self, root):
        self.root = root
        self.root.title("نظام المحاسبة الذكي - ChatGPT Excel Accounting")
        self.root.geometry("1300x850")
        self.root.configure(bg='#f0f0f0')
        
        # ألوان مستوحاة من Excel وChatGPT
        self.excel_color = "#217346"
        self.chatgpt_color = "#0fa37f"
        self.accent_color = "#1a73e8"
        self.background_color = "#f0f0f0"
        
        # بيانات التطبيق
        self.data = {
            "المبيعات": pd.DataFrame(columns=["التاريخ", "العميل", "المبلغ", "الوصف", "الحالة"]),
            "المشتريات": pd.DataFrame(columns=["التاريخ", "المورد", "المبلغ", "الوصف", "الحالة"]),
            "المصروفات": pd.DataFrame(columns=["التاريخ", "النوع", "المبلغ", "الوصف", "الحالة"]),
            "العملاء": pd.DataFrame(columns=["الاسم", "البريد", "الهاتف", "الرصيد"]),
            "الموردين": pd.DataFrame(columns=["الاسم", "البريد", "الهاتف", "الرصيد"])
        }
        
        # إنشاء ملف Excel إذا لم يكن موجوداً
        self.excel_file = "accounting_data.xlsx"
        self.setup_excel_file()
        
        # طابور للمهام
        self.task_queue = queue.Queue()
        
        self.setup_ui()
        self.load_data()
        self.update_external_data()
        
        # بدء عملية معالجة المهام في الخلفية
        self.process_tasks()
    
    def setup_excel_file(self):
        """إنشاء ملف Excel مع أوراق العمل الأساسية إذا لم يكن موجوداً"""
        if not os.path.exists(self.excel_file):
            wb = Workbook()
            # إزالة الورقة الافتراضية
            if "Sheet" in wb.sheetnames:
                wb.remove(wb["Sheet"])
            
            # إنشاء أوراق العمل الأساسية
            for sheet_name in ["المبيعات", "المشتريات", "المصروفات", "العملاء", "الموردين", "التقارير"]:
                wb.create_sheet(sheet_name)
            
            wb.save(self.excel_file)
    
    def load_data(self):
        """تحميل البيانات من ملف Excel"""
        try:
            excel_data = pd.read_excel(self.excel_file, sheet_name=None)
            for sheet_name in self.data:
                if sheet_name in excel_data:
                    self.data[sheet_name] = excel_data[sheet_name].fillna("")
        except Exception as e:
            print(f"خطأ في تحميل البيانات: {e}")
    
    def save_data(self):
        """حفظ البيانات إلى ملف Excel"""
        try:
            with pd.ExcelWriter(self.excel_file, engine='openpyxl') as writer:
                for sheet_name, df in self.data.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
        except Exception as e:
            print(f"خطأ في حفظ البيانات: {e}")
    
    def setup_ui(self):
        # إنشاء واجهة مستخدم متعددة الألسنة
        style = ttk.Style()
        style.configure("TNotebook", background=self.background_color)
        style.configure("TNotebook.Tab", font=('Arial', 10, 'bold'), padding=[10, 5])
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # إنشاء الإطارات الرئيسية
        self.create_input_frame()
        self.create_reports_frame()
        self.create_analysis_frame()
        self.create_settings_frame()
        self.create_audit_frame()
        
        # شريط الحالة
        self.status_var = tk.StringVar()
        self.status_var.set("جاهز")
        status_bar = tk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def create_input_frame(self):
        """إنشاء إطار الإدخال الرئيسي"""
        self.input_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.input_frame, text="الإدخال الرئيسي")
        
        # عنوان الإطار
        title_label = tk.Label(self.input_frame, text="إدخال المعاملات المحاسبية", 
                              font=("Arial", 16, "bold"), fg=self.excel_color, bg=self.background_color)
        title_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        # أزرار طرق الإدخال المختلفة
        input_methods_frame = tk.Frame(self.input_frame, bg=self.background_color)
        input_methods_frame.grid(row=1, column=0, columnspan=3, pady=10)
        
        voice_btn = tk.Button(input_methods_frame, text="إدخال صوتي", command=self.voice_input,
                             bg=self.chatgpt_color, fg="white", width=15, font=('Arial', 10, 'bold'))
        voice_btn.grid(row=0, column=0, padx=5, pady=5)
        
        camera_btn = tk.Button(input_methods_frame, text="مسح ضوئي", command=self.camera_input,
                              bg=self.accent_color, fg="white", width=15, font=('Arial', 10, 'bold'))
        camera_btn.grid(row=0, column=1, padx=5, pady=5)
        
        manual_btn = tk.Button(input_methods_frame, text="إدخال يدوي", command=self.manual_input,
                              bg=self.excel_color, fg="white", width=15, font=('Arial', 10, 'bold'))
        manual_btn.grid(row=0, column=2, padx=5, pady=5)
        
        # منطقة عرض البيانات
        display_frame = tk.Frame(self.input_frame, bg=self.background_color)
        display_frame.grid(row=2, column=0, columnspan=3, padx=5, pady=10, sticky="nsew")
        
        self.data_display = tk.Text(display_frame, height=15, width=80, font=('Arial', 10))
        self.data_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(display_frame, orient=tk.VERTICAL, command=self.data_display.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.data_display.config(yscrollcommand=scrollbar.set)
        
        # أزرار المعالجة
        buttons_frame = tk.Frame(self.input_frame, bg=self.background_color)
        buttons_frame.grid(row=3, column=0, columnspan=3, pady=10)
        
        process_btn = tk.Button(buttons_frame, text="معالجة البيانات", command=self.process_data,
                               bg="#4caf50", fg="white", width=15, font=('Arial', 10, 'bold'))
        process_btn.grid(row=0, column=0, padx=5, pady=5)
        
        save_btn = tk.Button(buttons_frame, text="حفظ في النظام", command=self.save_data,
                            bg="#ff9800", fg="white", width=15, font=('Arial', 10, 'bold'))
        save_btn.grid(row=0, column=1, padx=5, pady=5)
        
        audit_btn = tk.Button(buttons_frame, text="تدقيق المحاسبة", command=self.audit_data,
                             bg="#f44336", fg="white", width=15, font=('Arial', 10, 'bold'))
        audit_btn.grid(row=0, column=2, padx=5, pady=5)
        
        # تكوين الأوزان للأعمدة والصفوف
        self.input_frame.grid_columnconfigure(0, weight=1)
        self.input_frame.grid_rowconfigure(2, weight=1)
    
    def create_reports_frame(self):
        """إنشاء إطار التقارير"""
        self.reports_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.reports_frame, text="التقارير المحاسبية")
        
        # عنوان الإطار
        title_label = tk.Label(self.reports_frame, text="التقارير المحاسبية", 
                              font=("Arial", 16, "bold"), fg=self.excel_color, bg=self.background_color)
        title_label.pack(pady=10)
        
        # اختيار نوع التقرير
        report_type_frame = tk.Frame(self.reports_frame, bg=self.background_color)
        report_type_frame.pack(pady=10)
        
        tk.Label(report_type_frame, text="اختر نوع التقرير:", 
                bg=self.background_color, font=('Arial', 12)).grid(row=0, column=0, padx=5)
        
        self.report_type = tk.StringVar(value="المبيعات")
        report_combo = ttk.Combobox(report_type_frame, textvariable=self.report_type, 
                                   values=list(self.data.keys()), state="readonly", width=15)
        report_combo.grid(row=0, column=1, padx=5)
        
        generate_btn = tk.Button(report_type_frame, text="إنشاء التقرير", 
                                command=self.generate_report, bg=self.excel_color, 
                                fg="white", font=('Arial', 10, 'bold'))
        generate_btn.grid(row=0, column=2, padx=5)
        
        # منطقة عرض التقرير
        report_display_frame = tk.Frame(self.reports_frame, bg=self.background_color)
        report_display_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # إنشاء Treeview لعرض البيانات بشكل جدولي
        columns = ("التاريخ", "العميل/المورد", "المبلغ", "الوصف", "الحالة")
        self.report_tree = ttk.Treeview(report_display_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.report_tree.heading(col, text=col)
            self.report_tree.column(col, width=120)
        
        # شريط التمرير
        scrollbar = ttk.Scrollbar(report_display_frame, orient=tk.VERTICAL, command=self.report_tree.yview)
        self.report_tree.configure(yscrollcommand=scrollbar.set)
        
        self.report_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_analysis_frame(self):
        """إنشاء إطار التحليل"""
        self.analysis_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.analysis_frame, text="التحليل التفاعلي")
        
        title_label = tk.Label(self.analysis_frame, text="التحليل المالي التفاعلي", 
                              font=("Arial", 16, "bold"), fg=self.excel_color, bg=self.background_color)
        title_label.pack(pady=10)
        
        # إطار للرسوم البيانية
        self.chart_frame = tk.Frame(self.analysis_frame, bg="white", relief=tk.RAISED, bd=2)
        self.chart_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # أزرار التحليل
        buttons_frame = tk.Frame(self.analysis_frame, bg=self.background_color)
        buttons_frame.pack(pady=10)
        
        tk.Button(buttons_frame, text="تحليل المبيعات", command=lambda: self.create_chart("المبيعات"),
                 bg=self.chatgpt_color, fg="white", font=('Arial', 10, 'bold')).grid(row=0, column=0, padx=5)
        
        tk.Button(buttons_frame, text="تحليل المصروفات", command=lambda: self.create_chart("المصروفات"),
                 bg=self.accent_color, fg="white", font=('Arial', 10, 'bold')).grid(row=0, column=1, padx=5)
        
        tk.Button(buttons_frame, text="مقارنة الإيرادات", command=self.create_comparison_chart,
                 bg=self.excel_color, fg="white", font=('Arial', 10, 'bold')).grid(row=0, column=2, padx=5)
    
    def create_settings_frame(self):
        """إنشاء إطار الإعدادات"""
        self.settings_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.settings_frame, text="الإعدادات والربط")
        
        title_label = tk.Label(self.settings_frame, text="إعدادات النظام والربط الخارجي", 
                              font=("Arial", 16, "bold"), fg=self.excel_color, bg=self.background_color)
        title_label.pack(pady=10)
        
        # إعدادات الربط الخارجي
        settings_group = tk.LabelFrame(self.settings_frame, text="إعدادات الربط", 
                                      font=('Arial', 12, 'bold'), bg=self.background_color)
        settings_group.pack(fill=tk.X, padx=10, pady=10)
        
        # أسعار العملات
        currency_frame = tk.Frame(settings_group, bg=self.background_color)
        currency_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(currency_frame, text="أسعار العملات:", 
                bg=self.background_color, font=('Arial', 10)).grid(row=0, column=0, sticky=tk.W)
        
        self.currency_var = tk.StringVar(value="محدث تلقائياً")
        currency_label = tk.Label(currency_frame, textvariable=self.currency_var, 
                                 bg=self.background_color, font=('Arial', 10))
        currency_label.grid(row=0, column=1, sticky=tk.W, padx=10)
        
        # حالة الربط البنكي
        bank_frame = tk.Frame(settings_group, bg=self.background_color)
        bank_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(bank_frame, text="الربط البنكي:", 
                bg=self.background_color, font=('Arial', 10)).grid(row=0, column=0, sticky=tk.W)
        
        self.bank_var = tk.StringVar(value="غير متصل")
        bank_label = tk.Label(bank_frame, textvariable=self.bank_var, 
                             bg=self.background_color, font=('Arial', 10))
        bank_label.grid(row=0, column=1, sticky=tk.W, padx=10)
        
        # التحديث التلقائي
        update_frame = tk.Frame(settings_group, bg=self.background_color)
        update_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(update_frame, text="التحديث التلقائي:", 
                bg=self.background_color, font=('Arial', 10)).grid(row=0, column=0, sticky=tk.W)
        
        self.auto_update = tk.BooleanVar(value=True)
        update_check = tk.Checkbutton(update_frame, variable=self.auto_update, 
                                     bg=self.background_color)
        update_check.grid(row=0, column=1, sticky=tk.W, padx=10)
        
        # أزرار التحكم
        buttons_frame = tk.Frame(self.settings_frame, bg=self.background_color)
        buttons_frame.pack(pady=10)
        
        tk.Button(buttons_frame, text="تحديث البيانات", command=self.update_external_data,
                 bg=self.excel_color, fg="white", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        
        tk.Button(buttons_frame, text="اختبار الاتصالات", command=self.test_connections,
                 bg=self.chatgpt_color, fg="white", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        
        tk.Button(buttons_frame, text="تصدير البيانات", command=self.export_data,
                 bg=self.accent_color, fg="white", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
    
    def create_audit_frame(self):
        """إنشاء إطار التدقيق"""
        self.audit_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.audit_frame, text="التدقيق والمطابقة")
        
        title_label = tk.Label(self.audit_frame, text="تدقيق المحاسبة واكتشاف الأخطاء", 
                              font=("Arial", 16, "bold"), fg=self.excel_color, bg=self.background_color)
        title_label.pack(pady=10)
        
        # زر بدء التدقيق
        audit_btn = tk.Button(self.audit_frame, text="بدء عملية التدقيق", command=self.run_audit,
                             bg="#f44336", fg="white", font=('Arial', 12, 'bold'))
        audit_btn.pack(pady=10)
        
        # منطقة نتائج التدقيق
        audit_result_frame = tk.Frame(self.audit_frame, bg=self.background_color)
        audit_result_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.audit_text = tk.Text(audit_result_frame, height=15, width=80, font=('Arial', 10))
        self.audit_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(audit_result_frame, orient=tk.VERTICAL, command=self.audit_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.audit_text.config(yscrollcommand=scrollbar.set)
        
        # أزرار معالجة الأخطاء
        buttons_frame = tk.Frame(self.audit_frame, bg=self.background_color)
        buttons_frame.pack(pady=10)
        
        tk.Button(buttons_frame, text="معالجة الأخطاء", command=self.fix_errors,
                 bg="#4caf50", fg="white", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        
        tk.Button(buttons_frame, text="تصدير التقرير", command=self.export_audit_report,
                 bg="#ff9800", fg="white", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
    
    def voice_input(self):
        """معالجة الإدخال الصوتي"""
        self.status_var.set("جاري الاستماع... قل بيانات المعاملة المحاسبية")
        
        def recognize_speech():
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                self.data_display.insert(tk.END, "جاري الاستماع... قل بيانات المعاملة المحاسبية\n")
                recognizer.adjust_for_ambient_noise(source)
                try:
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                    
                    text = recognizer.recognize_google(audio, language="ar-AR")
                    self.data_display.delete(1.0, tk.END)
                    self.data_display.insert(tk.END, f"النص المعترف به: {text}\n")
                    
                    # استخدام ChatGPT لتحويل النص إلى بيانات محاسبية منظمة
                    accounting_data = self.parse_with_chatgpt(text)
                    self.display_accounting_data(accounting_data)
                    
                    self.status_var.set("تم التعرف على الصوت بنجاح")
                    
                except sr.WaitTimeoutError:
                    self.status_var.set("انتهى وقت الانتظار")
                    self.data_display.insert(tk.END, "لم يتم الكشف عن أي صوت\n")
                except sr.UnknownValueError:
                    self.status_var.set("لم يتم التعرف على الكلام")
                    self.data_display.insert(tk.END, "لم يتم التعرف على الكلام\n")
                except sr.RequestError as e:
                    self.status_var.set("خطأ في خدمة التعرف على الصوت")
                    self.data_display.insert(tk.END, f"خطأ في خدمة التعرف على الصوت: {e}\n")
        
        # تشغيل التعرف على الصوت في خيط منفصل
        threading.Thread(target=recognize_speech, daemon=True).start()
    
    def camera_input(self):
        """معالجة الإدخال بالكاميرا"""
        self.status_var.set("جاري فتح الكاميرا...")
        
        def capture_image():
            # فتح الكاميرا لالتقاط صورة
            cap = cv2.VideoCapture(0)
            
            if not cap.isOpened():
                self.status_var.set("无法打开摄像头")
                self.data_display.insert(tk.END, "无法打开摄像头\n")
                return
                
            ret, frame = cap.read()
            if ret:
                # حفظ الصورة مؤقتًا
                cv2.imwrite('temp_invoice.jpg', frame)
                
                # استخدام OCR لاستخراج النص
                extracted_text = self.extract_text_from_image('temp_invoice.jpg')
                self.data_display.insert(tk.END, f"النص المستخرج: {extracted_text}\n")
                
                # تحليل النص باستخدام ChatGPT
                invoice_data = self.parse_invoice_with_chatgpt(extracted_text)
                self.display_accounting_data(invoice_data)
                
                self.status_var.set("تم معالجة الصورة بنجاح")
                
            cap.release()
        
        threading.Thread(target=capture_image, daemon=True).start()
    
    def extract_text_from_image(self, image_path):
        """استخراج النص من الصورة باستخدام OCR"""
        try:
            image = Image.open(image_path)
            # تحسين الصورة لتحسين دقة OCR
            image = ImageOps.exif_transpose(image)
            image = image.convert('L')  # تحويل إلى تدرج الرمادي
            text = pytesseract.image_to_string(image, lang='ara')
            return text
        except Exception as e:
            return f"خطأ في استخراج النص: {e}"
    
    def parse_with_chatgpt(self, text):
        """محاكاة اتصال بـ ChatGPT API"""
        # في التطبيق الحقيقي، سيتم استخدام OpenAI API
        
        # محاكاة استجابة ChatGPT بناءً على النص المدخل
        if "بيع" in text or "مبيعات" in text:
            simulated_response = {
                "transaction_type": "بيع",
                "amount": self.extract_amount(text),
                "currency": "ريال سعودي",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "description": text,
                "account_debit": "حساب المدينين",
                "account_credit": "إيرادات المبيعات",
                "vat_amount": round(self.extract_amount(text) * 0.15, 2)
            }
        elif "شراء" in text or "مشتريات" in text:
            simulated_response = {
                "transaction_type": "شراء",
                "amount": self.extract_amount(text),
                "currency": "ريال سعودي",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "description": text,
                "account_debit": "المشتريات",
                "account_credit": "حساب الدائنين",
                "vat_amount": round(self.extract_amount(text) * 0.15, 2)
            }
        else:
            simulated_response = {
                "transaction_type": "عام",
                "amount": self.extract_amount(text),
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
        # محاكاة تحليل الفاتورة
        simulated_response = {
            "invoice_number": f"INV-{datetime.now().strftime('%Y%m%d')}-001",
            "supplier": "شركة المعدات المتحدة",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "due_date": (datetime.now() + pd.DateOffset(days=30)).strftime("%Y-%m-%d"),
            "total_amount": self.extract_amount(text),
            "items": [
                {"description": "طابعة ليزر", "quantity": 2, "unit_price": 1200.00, "total": 2400.00},
                {"description": "حبر طابعة", "quantity": 5, "unit_price": 170.00, "total": 850.00}
            ],
            "vat_amount": round(self.extract_amount(text) * 0.15, 2)
        }
        
        return simulated_response
    
    def display_accounting_data(self, data):
        """عرض البيانات المحاسبية في واجهة المستخدم"""
        self.data_display.delete(1.0, tk.END)
        
        if data.get("transaction_type") == "بيع":
            self.data_display.insert(tk.END, "=== معاملة بيع ===\n")
        elif data.get("transaction_type") == "شراء":
            self.data_display.insert(tk.END, "=== معاملة شراء ===\n")
        else:
            self.data_display.insert(tk.END, "=== معاملة محاسبية ===\n")
        
        for key, value in data.items():
            if key == "items":
                self.data_display.insert(tk.END, f"{key}:\n")
                for item in value:
                    for k, v in item.items():
                        self.data_display.insert(tk.END, f"  {k}: {v}\n")
                    self.data_display.insert(tk.END, "\n")
            else:
                self.data_display.insert(tk.END, f"{key}: {value}\n")
    
    def process_data(self):
        """معالجة البيانات وإضافتها للنظام"""
        current_text = self.data_display.get(1.0, tk.END).strip()
        if not current_text or "=== معاملة" not in current_text:
            messagebox.showwarning("تحذير", "لا توجد بيانات معالجة")
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
            self.data["المبيعات"] = pd.concat([self.data["المبيعات"], pd.DataFrame([new_record])], ignore_index=True)
            messagebox.showinfo("نجاح", "تمت إضافة معاملة البيع بنجاح")
        
        elif "شراء" in transaction_data.get("transaction_type", ""):
            new_record = {
                "التاريخ": transaction_data.get("date", datetime.now().strftime("%Y-%m-%d")),
                "المورد": "مورد",
                "المبلغ": transaction_data.get("amount", 0),
                "الوصف": transaction_data.get("description", ""),
                "الحالة": "معلقة"
            }
            self.data["المشتريات"] = pd.concat([self.data["المشتريات"], pd.DataFrame([new_record])], ignore_index=True)
            messagebox.showinfo("نجاح", "تمت إضافة معاملة الشراء بنجاح")
        
        self.save_data()
        self.status_var.set("تمت معالجة البيانات بنجاح")
    
    def manual_input(self):
        """فتح نافذة الإدخال اليدوي"""
        manual_window = tk.Toplevel(self.root)
        manual_window.title("الإدخال اليدوي للمعاملات")
        manual_window.geometry("600x500")
        manual_window.configure(bg=self.background_color)
        
        tk.Label(manual_window, text="الإدخال اليدوي للمعاملات", 
                font=("Arial", 14, "bold"), fg=self.excel_color, bg=self.background_color).pack(pady=10)
        
        # نوع المعاملة
        type_frame = tk.Frame(manual_window, bg=self.background_color)
        type_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(type_frame, text="نوع المعاملة:", bg=self.background_color).grid(row=0, column=0, sticky=tk.W)
        transaction_type = ttk.Combobox(type_frame, values=["بيع", "شراء", "مصروف"], state="readonly")
        transaction_type.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        transaction_type.set("بيع")
        
        # التاريخ
        date_frame = tk.Frame(manual_window, bg=self.background_color)
        date_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(date_frame, text="التاريخ:", bg=self.background_color).grid(row=0, column=0, sticky=tk.W)
        transaction_date = tk.Entry(date_frame)
        transaction_date.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        transaction_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        # الطرف الثاني
        party_frame = tk.Frame(manual_window, bg=self.background_color)
        party_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(party_frame, text="العميل/المورد:", bg=self.background_color).grid(row=0, column=0, sticky=tk.W)
        transaction_party = tk.Entry(party_frame)
        transaction_party.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # المبلغ
        amount_frame = tk.Frame(manual_window, bg=self.background_color)
        amount_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(amount_frame, text="المبلغ:", bg=self.background_color).grid(row=0, column=0, sticky=tk.W)
        transaction_amount = tk.Entry(amount_frame)
        transaction_amount.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # الوصف
        desc_frame = tk.Frame(manual_window, bg=self.background_color)
        desc_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(desc_frame, text="الوصف:", bg=self.background_color).grid(row=0, column=0, sticky=tk.W)
        transaction_desc = tk.Text(desc_frame, height=5, width=40)
        transaction_desc.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # زر الحفظ
        def save_manual_transaction():
            trans_type = transaction_type.get()
            date = transaction_date.get()
            party = transaction_party.get()
            amount = transaction_amount.get()
            desc = transaction_desc.get(1.0, tk.END).strip()
            
            if not all([date, party, amount]):
                messagebox.showerror("خطأ", "جميع الحقول مطلوبة")
                return
            
            new_record = {
                "التاريخ": date,
                "العميل/المورد": party,
                "المبلغ": amount,
                "الوصف": desc,
                "الحالة": "مكتمل"
            }
            
            if trans_type == "بيع":
                new_record["العميل"] = party
                del new_record["العميل/المورد"]
                self.data["المبيعات"] = pd.concat([self.data["المبيعات"], pd.DataFrame([new_record])], ignore_index=True)
            elif trans_type == "شراء":
                new_record["المورد"] = party
                del new_record["العميل/المورد"]
                self.data["المشتريات"] = pd.concat([self.data["المشتريات"], pd.DataFrame([new_record])], ignore_index=True)
            else:
                new_record["النوع"] = trans_type
                del new_record["العميل/المورد"]
                self.data["المصروفات"] = pd.concat([self.data["المصروفات"], pd.DataFrame([new_record])], ignore_index=True)
            
            self.save_data()
            messagebox.showinfo("نجاح", "تمت إضافة المعاملة بنجاح")
            manual_window.destroy()
        
        save_btn = tk.Button(manual_window, text="حفظ المعاملة", command=save_manual_transaction,
                            bg=self.excel_color, fg="white", font=('Arial', 10, 'bold'))
        save_btn.pack(pady=10)
    
    def generate_report(self):
        """إنشاء تقرير حسب النوع المحدد"""
        report_type = self.report_type.get()
        
        # مسح البيانات الحالية في الشجرة
        for item in self.report_tree.get_children():
            self.report_tree.delete(item)
        
        # إضافة البيانات الجديدة
        if not self.data[report_type].empty:
            for _, row in self.data[report_type].iterrows():
                values = tuple(row[col] for col in self.report_tree['columns'])
                self.report_tree.insert("", tk.END, values=values)
        
        self.status_var.set(f"تم إنشاء تقرير {report_type}")
    
    def create_chart(self, data_type):
        """إنشاء رسم بياني للبيانات"""
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        
        if self.data[data_type].empty:
            tk.Label(self.chart_frame, text="لا توجد بيانات متاحة", font=('Arial', 14), 
                    bg="white").pack(expand=True)
            return
        
        # تحضير البيانات
        df = self.data[data_type].copy()
        df['التاريخ'] = pd.to_datetime(df['التاريخ'], errors='coerce')
        df['المبلغ'] = pd.to_numeric(df['المبلغ'], errors='coerce')
        
        # تجميع البيانات حسب الشهر
        monthly_data = df.groupby(df['التاريخ'].dt.to_period('M'))['المبلغ'].sum()
        
        # إنشاء الرسم البياني
        fig, ax = plt.subplots(figsize=(8, 6))
        months = [str(period) for period in monthly_data.index]
        amounts = monthly_data.values
        
        ax.bar(months, amounts, color=self.excel_color)
        ax.set_title(f'{data_type} الشهرية', fontsize=16)
        ax.set_ylabel('المبلغ', fontsize=12)
        ax.tick_params(axis='x', rotation=45)
        
        # تضمين الرسم في واجهة التطبيق
        canvas = FigureCanvasTkAgg(fig, self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def create_comparison_chart(self):
        """إنشاء رسم بياني مقارن"""
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        
        # تحضير البيانات
        sales_data = self.data["المبيعات"].copy()
        purchases_data = self.data["المشتريات"].copy()
        
        if sales_data.empty and purchases_data.empty:
            tk.Label(self.chart_frame, text="لا توجد بيانات متاحة", font=('Arial', 14), 
                    bg="white").pack(expand=True)
            return
        
        sales_data['التاريخ'] = pd.to_datetime(sales_data['التاريخ'], errors='coerce')
        purchases_data['التاريخ'] = pd.to_datetime(purchases_data['التاريخ'], errors='coerce')
        
        sales_data['المبلغ'] = pd.to_numeric(sales_data['المبلغ'], errors='coerce')
        purchases_data['المبلغ'] = pd.to_numeric(purchases_data['المبلغ'], errors='coerce')
        
        # تجميع البيانات حسب الشهر
        monthly_sales = sales_data.groupby(sales_data['التاريخ'].dt.to_period('M'))['المبلغ'].sum()
        monthly_purchases = purchases_data.groupby(purchases_data['التاريخ'].dt.to_period('M'))['المبلغ'].sum()
        
        # إنشاء الرسم البياني
        fig, ax = plt.subplots(figsize=(8, 6))
        
        months = [str(period) for period in monthly_sales.index]
        sales = monthly_sales.values
        purchases = monthly_purchases.reindex(monthly_sales.index, fill_value=0).values
        
        bar_width = 0.35
        x = np.arange(len(months))
        
        ax.bar(x - bar_width/2, sales, bar_width, label='المبيعات', color=self.excel_color)
        ax.bar(x + bar_width/2, purchases, bar_width, label='المشتريات', color=self.chatgpt_color)
        
        ax.set_xlabel('الشهر')
        ax.set_ylabel('المبلغ')
        ax.set_title('مقارنة المبيعات والمشتريات')
        ax.set_xticks(x)
        ax.set_xticklabels(months, rotation=45)
        ax.legend()
        
        # تضمين الرسم في واجهة التطبيق
        canvas = FigureCanvasTkAgg(fig, self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def update_external_data(self):
        """تحديث البيانات من المصادر الخارجية"""
        self.status_var.set("جاري تحديث البيانات الخارجية...")
        
        def update_task():
            try:
                # محاكاة تحديث أسعار العملات
                self.currency_var.set("محدث: " + datetime.now().strftime("%Y-%m-%d %H:%M"))
                
                # محاكاة الربط البنكي
                self.bank_var.set("متصل")
                
                self.status_var.set("تم تحديث البيانات الخارجية")
            except Exception as e:
                self.status_var.set("فشل في تحديث البيانات")
                messagebox.showerror("خطأ", f"فشل في تحديث البيانات: {e}")
        
        threading.Thread(target=update_task, daemon=True).start()
    
    def test_connections(self):
        """اختبار الاتصالات الخارجية"""
        self.status_var.set("جاري اختبار الاتصالات...")
        
        def test_task():
            try:
                # محاكاة اختبار الاتصالات
                time.sleep(2)  # محاكاة وقت الانتظار
                
                messagebox.showinfo("نتيجة الاختبار", "جميع الاتصالات تعمل بشكل صحيح")
                self.status_var.set("جميع الاتصالات تعمل بشكل صحيح")
            except Exception as e:
                messagebox.showerror("خطأ", f"فشل في اختبار الاتصالات: {e}")
                self.status_var.set("فشل في اختبار الاتصالات")
        
        threading.Thread(target=test_task, daemon=True).start()
    
    def export_data(self):
        """تصدير البيانات"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                    for sheet_name, df in self.data.items():
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                messagebox.showinfo("نجاح", "تم تصدير البيانات بنجاح")
                self.status_var.set("تم تصدير البيانات")
            except Exception as e:
                messagebox.showerror("خطأ", f"فشل في تصدير البيانات: {e}")
                self.status_var.set("فشل في تصدير البيانات")
    
    def run_audit(self):
        """تشغيل عملية التدقيق"""
        self.audit_text.delete(1.0, tk.END)
        self.audit_text.insert(tk.END, "جاري تدقيق البيانات المحاسبية...\n")
        self.status_var.set("جاري تدقيق البيانات المحاسبية")
        
        def audit_task():
            try:
                # محاكاة عملية التدقيق
                time.sleep(3)  # محاكاة وقت التدقيق
                
                audit_results = {
                    "status": "تم التدقيق",
                    "issues_found": [
                        {
                            "type": "تناقض",
                            "description": "الرصيد المدين لا يساوي الرصيد الدائن في قيد اليومية",
                            "suggestion": "مراجعة القيد رقم JV-2023-1045"
                        },
                        {
                            "type": "خطأ في التصنيف",
                            "description": "مصروفات تسويق مصنفة كمصروفات عمومية",
                            "suggestion": "إعادة تصنيف المبلغ 1250 ريال إلى حساب مصروفات التسويق"
                        }
                    ],
                    "recommendations": [
                        "تعديل القيد المحاسبي لتحقيق التوازن",
                        "مراجعة دليل الحسابات للتأكد من التصنيف الصحيح"
                    ]
                }
                
                self.display_audit_results(audit_results)
                self.status_var.set("تم الانتهاء من التدقيق")
            except Exception as e:
                self.audit_text.insert(tk.END, f"حدث خطأ أثناء التدقيق: {e}\n")
                self.status_var.set("فشل في عملية التدقيق")
        
        threading.Thread(target=audit_task, daemon=True).start()
    
    def display_audit_results(self, results):
        """عرض نتائج التدقيق"""
        self.audit_text.delete(1.0, tk.END)
        
        self.audit_text.insert(tk.END, "نتائج تدقيق النظام المحاسبي\n")
        self.audit_text.insert(tk.END, "="*50 + "\n\n")
        
        self.audit_text.insert(tk.END, f"حالة التدقيق: {results['status']}\n\n")
        
        if results['issues_found']:
            self.audit_text.insert(tk.END, "المشكلات المكتشفة:\n")
            for issue in results['issues_found']:
                self.audit_text.insert(tk.END, f"- نوع المشكلة: {issue['type']}\n")
                self.audit_text.insert(tk.END, f"  الوصف: {issue['description']}\n")
                self.audit_text.insert(tk.END, f"  الاقتراح: {issue['suggestion']}\n\n")
        
        if results['recommendations']:
            self.audit_text.insert(tk.END, "التوصيات العامة:\n")
            for rec in results['recommendations']:
                self.audit_text.insert(tk.END, f"- {rec}\n")
    
    def fix_errors(self):
        """معالجة الأخطاء المكتشفة"""
        # في التطبيق الحقيقي، سيتم تنفيذ الإصلاحات تلقائياً أو يدوياً
        messagebox.showinfo("معالجة الأخطاء", "جاري معالجة الأخطاء...")
        self.status_var.set("تم معالجة الأخطاء")
    
    def export_audit_report(self):
        """تصدير تقرير التدقيق"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.audit_text.get(1.0, tk.END))
                
                messagebox.showinfo("نجاح", "تم تصدير تقرير التدقيق بنجاح")
                self.status_var.set("تم تصدير تقرير التدقيق")
            except Exception as e:
                messagebox.showerror("خطأ", f"فشل في تصدير التقرير: {e}")
                self.status_var.set("فشل في تصدير التقرير")
    
    def process_tasks(self):
        """معالجة المهام في قائمة الانتظار"""
        try:
            while True:
                task = self.task_queue.get_nowait()
                task()
        except queue.Empty:
            pass
        
        # الاستمرار في فحص قائمة الانتظار
        self.root.after(100, self.process_tasks)

def main():
    """الدالة الرئيسية لتشغيل التطبيق"""
    root = tk.Tk()
    app = AccountingAIApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
