from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QPushButton, QFileDialog, QSpinBox, QCheckBox, QLineEdit,
                           QLabel, QTextEdit, QMenuBar, QMenu, QAction, QHBoxLayout)
from PyQt5.QtCore import Qt, QLocale
from PyQt5.QtGui import QIcon
import sys
import yaml
from pathlib import Path
from directory_scanner import scan_directory_to_csv, create_pdf_report
from enum import Enum
from datetime import datetime
import os

class Language(Enum):
    EN = "English"
    ZH_TW = "繁體中文"
    ZH_CN = "简体中文"

class DirectoryScannerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.load_config()
        
        # 根據系統語言設置默認語言
        system_locale = QLocale.system().name()
        if system_locale.startswith('zh'):
            if 'TW' in system_locale or 'HK' in system_locale:
                self.current_language = Language.ZH_TW
            else:
                self.current_language = Language.ZH_CN
        else:
            self.current_language = Language.EN
        
        self.initUI()
        self.update_ui_text()
        self.log("status_ready")

    def load_config(self):
        """載入配置文件"""
        config_path = Path(__file__).parent / 'config.yaml'
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.translations = {
            Language.EN: self.config['translations']['en'],
            Language.ZH_TW: self.config['translations']['zh_tw'],
            Language.ZH_CN: self.config['translations']['zh_cn']
        }
        
        self.version = self.config['version']
        self.usage_steps = self.config['usage_steps']

    def initUI(self):
        # 創建中心小部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 創建菜單欄
        self.create_menu_bar()
        
        # 項目名稱行
        project_layout = QHBoxLayout()
        project_label = QLabel(self)
        project_label.setMinimumWidth(80)
        self.project_name_label = project_label
        self.project_name_input = QLineEdit(self)
        project_layout.addWidget(project_label)
        project_layout.addWidget(self.project_name_input)
        layout.addLayout(project_layout)

        # 修改瀏覽按鈕樣式
        button_style = """
            QPushButton {
                background-color: #90EE90;  /* 淺綠色 */
                border: 1px solid #555;
                border-radius: 4px;
                padding: 4px 8px;
                color: black;
            }
            QPushButton:hover {
                background-color: #98FB98;  /* 懸停時稍微變亮 */
            }
        """                      
        
        # 掃描路徑行
        folder_layout = QHBoxLayout()
        folder_label = QLabel(self)
        folder_label.setMinimumWidth(80)
        self.folder_path_label = folder_label
        self.folder_path_input = QLineEdit(self)
        self.folder_path_input.setReadOnly(True)
        self.folder_path_input.setPlaceholderText(self.translations[self.current_language]['select_folder_placeholder'])
        self.folder_button = QPushButton(self)
        self.folder_button.setStyleSheet(button_style)
        self.folder_button.clicked.connect(self.select_folder)
        folder_layout.addWidget(folder_label)
        folder_layout.addWidget(self.folder_path_input)
        folder_layout.addWidget(self.folder_button)
        layout.addLayout(folder_layout)
        
        # 顯示選擇的文件夾路徑
        # self.folder_label = QLabel(self)
        # layout.addWidget(self.folder_label)
        
        # 最大層數選擇（修改為水平布局）
        depth_layout = QHBoxLayout()
        self.depth_label = QLabel(self)
        self.depth_label.setMinimumWidth(80)
        self.depth_spinbox = QSpinBox(self)
        self.depth_spinbox.setRange(1, 10)
        self.depth_spinbox.setValue(2)
        self.depth_spinbox.setMaximumWidth(60)  # 設置最大寬度
        depth_layout.addWidget(self.depth_label)
        depth_layout.addWidget(self.depth_spinbox)
        depth_layout.addStretch()  # 添加彈性空間
        layout.addLayout(depth_layout)
        
        # CSV 和 PDF 選擇
        self.csv_checkbox = QCheckBox(self)
        self.pdf_checkbox = QCheckBox(self)
        self.pdf_checkbox.setChecked(True)  # 預設勾選 PDF
        layout.addWidget(self.csv_checkbox)
        layout.addWidget(self.pdf_checkbox)
        
        # 輸出路徑行
        output_layout = QHBoxLayout()
        output_label = QLabel(self)
        output_label.setMinimumWidth(80)
        self.output_path_label = output_label
        self.output_path_input = QLineEdit(self)
        self.output_path_input.setReadOnly(True)
        self.output_path_input.setPlaceholderText(self.translations[self.current_language]['select_output_placeholder'])
        self.output_button = QPushButton(self)
        self.output_button.setStyleSheet(button_style)
        self.output_button.clicked.connect(self.select_output_folder)
        output_layout.addWidget(output_label)
        output_layout.addWidget(self.output_path_input)
        output_layout.addWidget(self.output_button)
        layout.addLayout(output_layout)
        
        # 開始處理按鈕
        self.start_button = QPushButton(self)
        self.start_button.setStyleSheet("""
            background-color: lightblue; 
            border: 1px solid #555;  /* 邊框顏色 */
            border-radius: 4px;        /* 圓角 */
            padding: 6px;              /* 增加內邊距以增高 */
            font-weight: bold;       /* 粗體 */
            color: black;            /* 文字顏色 */
        """)
        self.start_button.clicked.connect(self.start_processing)
        layout.addWidget(self.start_button)

        # 添加狀態日誌顯示區域
        self.log_text = QTextEdit(self)
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(100)
        layout.addWidget(self.log_text)
        
        # 添加底部信息欄
        bottom_info = QHBoxLayout()
        
        # 公司名稱（左對齊）
        company_label = QLabel(self)
        company_label.setStyleSheet("color: gray;")
        bottom_info.addWidget(company_label)
        self.company_label = company_label
        
        # 版權信息（中間對齊）
        copyright_label = QLabel(self)
        copyright_label.setStyleSheet("color: gray;")
        copyright_label.setAlignment(Qt.AlignCenter)
        bottom_info.addWidget(copyright_label)
        self.copyright_label = copyright_label
        
        # 版本信息（右對齊）
        version_label = QLabel(self)
        version_label.setStyleSheet("color: gray;")
        version_label.setAlignment(Qt.AlignRight)
        bottom_info.addWidget(version_label)
        self.version_label = version_label
        
        layout.addLayout(bottom_info)

        self.setGeometry(300, 300, 600, 400)

    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # 幫助菜單
        help_menu = menubar.addMenu('')  # 文字會在update_ui_text中更新
        self.help_menu = help_menu
        
        # 用法介紹
        info_action = QAction('', self)
        info_action.triggered.connect(self.show_info)
        help_menu.addAction(info_action)
        self.info_action = info_action
        
        # 關於
        about_action = QAction('', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        self.about_action = about_action
        
        # 語言菜單
        language_menu = menubar.addMenu('')
        self.language_menu = language_menu
        
        # 添加語言選項
        for lang in Language:
            action = QAction(lang.value, self)
            action.setData(lang)
            action.triggered.connect(self.change_language)
            language_menu.addAction(action)

    def update_ui_text(self):
        """更新界面文字"""
        texts = self.translations[self.current_language]
        
        self.setWindowTitle(texts['window_title'])
        self.project_name_label.setText(texts['project_name'])
        self.folder_path_label.setText(texts['select_folder'])
        self.depth_label.setText(texts['max_depth'])
        self.csv_checkbox.setText(texts['generate_csv'])
        self.pdf_checkbox.setText(texts['generate_pdf'])
        self.output_path_label.setText(texts['select_output'])
        self.start_button.setText(texts['start_processing'])
        
        # 更新佔位符文字
        self.folder_path_input.setPlaceholderText(texts['select_folder_placeholder'])
        self.output_path_input.setPlaceholderText(texts['select_output_placeholder'])
        
        # 更新菜單文字
        self.help_menu.setTitle(texts['menu_help'])
        self.info_action.setText(texts['menu_usage'])
        self.about_action.setText(texts['menu_about'])
        self.language_menu.setTitle(texts['language'])
        
        # 更新底部信息
        self.company_label.setText(texts['company_name'])
        self.copyright_label.setText(texts['copyright'])
        self.version_label.setText(texts['version_text'].format(self.version)) 
        
        self.folder_button.setText(texts['browse_button'])
        self.output_button.setText(texts['browse_button'])

    def log(self, message_key, *args):
        """添加日誌消息到日誌區域"""
        text = self.translations[self.current_language].get(message_key, message_key)
        if args:
            text = text.format(*args)
        self.log_text.append(text)

    def change_language(self):
        """切換語言"""
        action = self.sender()
        self.current_language = action.data()
        self.update_ui_text()
        self.log("status_ready")

    def show_info(self):
        """顯示使用說明"""
        # 實現使用說明對話框
        pass

    def show_about(self):
        """顯示關於信息"""
        # 實現關於對話框
        pass

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self)
        if folder:
            self.folder_path_input.setStyleSheet("")  # 重置樣式
            self.folder_path_input.setText(folder)
            self.log("Selected folder: " + folder)

    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self)
        if folder:
            self.output_path_input.setStyleSheet("")  # 重置樣式
            self.output_path_input.setText(folder)
            self.log("Selected output folder: " + folder)

    def start_processing(self):
        # 檢查輸入和輸出路徑
        root_path = self.folder_path_input.text()
        output_folder = self.output_path_input.text()
        project_name = self.project_name_input.text()
        
        # 檢查是否選擇了輸入路徑
        if not root_path:
            self.folder_path_input.setStyleSheet("color: red;")
            self.folder_path_input.setText(self.translations[self.current_language]['no_folder_selected'])
            self.log("error_no_input_folder")
            return
            
        # 檢查是否選擇了輸出路徑
        if not output_folder:
            self.output_path_input.setStyleSheet("color: red;")
            self.output_path_input.setText(self.translations[self.current_language]['no_output_selected'])
            self.log("error_no_output_folder")
            return
            
        # 檢查是否至少選擇了一種輸出格式
        if not (self.csv_checkbox.isChecked() or self.pdf_checkbox.isChecked()):
            self.log("error_no_output_format")
            return
        
        self.log("status_processing")
        try:
            max_depth = self.depth_spinbox.value()
            project_name = self.project_name_input.text()
            hdd_name = root_path.split('/')[-1]
            timestamp = datetime.now().strftime("%Y_%m%d_%H%M%S")  # 添加时间戳
            
            if self.csv_checkbox.isChecked():
                csv_output = f"{output_folder}/{project_name}_{hdd_name}_{timestamp}.csv"
                scan_directory_to_csv(root_path, max_depth, csv_output)
                self.log("Generated CSV: " + csv_output)
            
            if self.pdf_checkbox.isChecked():
                pdf_output = f"{output_folder}/{project_name}_{hdd_name}_{timestamp}.pdf"
                # 獲取 logo 的路徑
                if hasattr(sys, '_MEIPASS'):  # 如果是打包後的執行檔
                    logo_path = os.path.join(sys._MEIPASS, 'logo.png')
                else:  # 如果是直接運行 Python 腳本
                    logo_path = os.path.join(os.path.dirname(__file__), 'logo.png')
                    
                create_pdf_report(root_path, max_depth, pdf_output, 
                                    project_name, self.translations[self.current_language], logo_path)
                self.log("Generated PDF: " + pdf_output)
            
            self.log("status_complete")
        except Exception as e:
            self.log("status_error", str(e)) 

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = DirectoryScannerApp()
    ex.show()
    sys.exit(app.exec_()) 