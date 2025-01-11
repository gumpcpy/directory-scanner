import os
import csv
from pathlib import Path
import humanize
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from datetime import datetime
from reportlab.platypus import Image
from reportlab.lib.utils import ImageReader
import sys

def get_size(path):
    """獲取文件或目錄的大小"""
    if os.path.isfile(path):
        return os.path.getsize(path)
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            try:
                total_size += os.path.getsize(fp)
            except (OSError, FileNotFoundError):
                continue
    return total_size

def scan_directory_to_csv(root_path, max_depth, output_file):
    """將目錄結構輸出到CSV文件"""
    total_size = get_size(root_path)  # 計算總大小
    root_name = os.path.basename(root_path)  # 獲取根目錄名稱
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
         # 寫入根目錄名稱和總大小
        writer.writerow([f'Root Directory: {root_name}', f'Total Size: {humanize.naturalsize(total_size)}'])
        writer.writerow([])  # 空行
        
        # 寫入表頭
        headers = [f'Level {i+1}' for i in range(max_depth)]
        headers.extend(['Type', 'Size', 'Creation Time'])
        writer.writerow(headers)
        
        def write_directory_tree(directory, current_depth=0):
            if current_depth >= max_depth:
                return
            
            entries = list(directory.iterdir())
            entries.sort(key=lambda x: (not x.is_dir(), x.name))
            
            for entry in entries:
                if not entry.name.startswith('.'):
                    row = [''] * max_depth
                    row[current_depth] = entry.name
                    entry_type = "Directory" if entry.is_dir() else "File"
                    size = humanize.naturalsize(get_size(entry))
                    creation_time = datetime.fromtimestamp(entry.stat().st_ctime).strftime('%Y-%m-%d %H:%M:%S')
                    row.extend([entry_type, size, creation_time])
                    writer.writerow(row)
                    
                    if entry.is_dir():
                        write_directory_tree(entry, current_depth + 1)
        
        root_dir = Path(root_path)
        write_directory_tree(root_dir)


def create_pdf_report(root_path, max_depth, pdf_output, project_name, translations, logo_path):
    """創建包含樹狀圖和表格的PDF報告"""
    doc = SimpleDocTemplate(pdf_output, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []
    
    # 註冊中文字體
    try:
        # 嘗試多個可能的中文字體路徑
        if hasattr(sys, '_MEIPASS'):  # 如果是打包後的執行檔
            font_path = os.path.join(sys._MEIPASS, 'DroidSansFallback.ttf')
        else:
            font_path = 'DroidSansFallback.ttf'
            
        if not os.path.exists(font_path):
            # Windows 系統字體路徑
            windows_font = "C:/Windows/Fonts/msjh.ttc"  # 微軟正黑體
            mac_font = "/System/Library/Fonts/PingFang.ttc"  # macOS 蘋方字體
            
            if os.path.exists(windows_font):
                font_path = windows_font
            elif os.path.exists(mac_font):
                font_path = mac_font
                
        pdfmetrics.registerFont(TTFont('CustomFont', font_path))
        font_name = 'CustomFont'
    except:
        print("警告：無法載入中文字體，將使用基本字體")
        font_name = 'Helvetica'
    
    # 創建標題樣式
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=font_name,
        fontSize=16,
        spaceAfter=30
    )
    
    # 創建正文樣式
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=10,
        leading=12
    )
    
    # 添加項目名稱和公司 logo（添加錯誤處理）
    project_title = Paragraph(f"{translations['project_name']} {project_name}", title_style)
    try:
        # 使用 ImageReader 獲取圖像的原始尺寸
        logo_reader = ImageReader(logo_path)
        original_width, original_height = logo_reader.getSize()
        
        # 計算保持比例的高度
        aspect_ratio = original_height / original_width
        logo_width = 120
        logo_height = logo_width * aspect_ratio
        
        # 創建 Image 對象，使用計算出的高度
        logo = Image(logo_path, width=logo_width, height=logo_height)

        title_and_logo_table = Table([[project_title, logo]], colWidths=[350, 120])
    except:
        # 如果無法載入 logo，只顯示標題
        title_and_logo_table = Table([[project_title, '']], colWidths=[450, 0])
    
    # 設置表格樣式
    title_and_logo_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # 垂直居中
        ('ALIGN', (1, 0), (1, 0), 'RIGHT')  # 右側 logo 水平對齊
    ]))
    
    elements.append(title_and_logo_table)
    elements.append(Spacer(1, 20))
       
    # 創建交接單表格   
    handover_data = [
        [translations['prepared_by'], '', translations['date'], ''],
        [translations['received_by'], '', translations['date'], ''],
    ]
    handover_table = Table(handover_data, colWidths=[100, 150, 100, 150])
    handover_style = TableStyle([
        ('FONT', (0, 0), (-1, -1), font_name),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ])
    handover_table.setStyle(handover_style)
    elements.append(handover_table)
    
    elements.append(Spacer(1, 30))
    
    # 添加總大小信息
    root_name = os.path.basename(root_path)
    total_size = get_size(root_path)
    elements.append(Paragraph(f"{root_name} - {translations['total_size'].format(humanize.naturalsize(total_size))}", 
                            normal_style))
    elements.append(Spacer(1, 10))
    
    # 創建表格數據
    table_data = [['Path', translations['file_type'], translations['file_size'], translations['creation_time']]]
    table_data.extend(get_table_data(root_path, max_depth))
    
    # 創建表格並設置樣式
    table = Table(table_data, colWidths=[280, 70, 70, 100])
    table_style = TableStyle([
        ('FONT', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
    ])
    table.setStyle(table_style)
    elements.append(table)  
    
    # 生成PDF
    doc.build(elements)

def get_table_data(root_path, max_depth):      
    """獲取目錄樹狀結構"""
    table_data = []
    root_dir = Path(root_path)
    
    def inner_print_tree(directory, prefix="", current_depth=0):
        if current_depth >= max_depth:
            return
            
        entries = list(directory.iterdir())
        entries.sort(key=lambda x: (not x.is_dir(), x.name))
        
        for i, entry in enumerate(entries):
            if not entry.name.startswith('.'):
                is_last = i == len(entries) - 1
                current_prefix = "└── " if is_last else "├── "
                size = humanize.naturalsize(get_size(entry))
                # file_ext = f"({entry.suffix})" if not entry.is_dir() and entry.suffix else "File"
                entry_type = "Directory" if entry.is_dir() else "File"                
            
                creation_time = datetime.fromtimestamp(os.path.getctime(entry)).strftime('%Y-%m-%d %H:%M:%S')
                table_data.append([f"{prefix}{current_prefix}{entry.name}", entry_type, size, creation_time])
                
                
                if entry.is_dir():
                    extension = "    " if is_last else "│   "
                    inner_print_tree(entry, prefix + extension, current_depth + 1)
        
    table_data.append([f"{root_dir.name}/","","",""])
    inner_print_tree(root_dir)
    return table_data

def main():  
    
    root_path = "/Users/gump/Documents/_Proj/dit_proj/dataclip"  
    max_depth = 3
    
    # 生成CSV文件
    csv_output = "directory_structure.csv"
    scan_directory_to_csv(root_path, max_depth, csv_output)
    print(f"\nCSV文件已生成: {csv_output}")
    
    # 生成PDF文件
    pdf_output = "directory_structure.pdf"
    project_name = "Wo虎饞龍"  # 這裡可以替換為實際的項目名稱
    translations = {
        'project_name': '項目名稱',
        'report_date': '報告日期',
        'directory_structure': '目錄結構',
        'table_view': '表格視圖',
        'file_type': '文件類型',
        'file_size': '文件大小',
        'creation_time': '建立時間',
        'handover_form': '交接單',
        'prepared_by': '準備人',
        'received_by': '接收人',
        'date': '日期',
        'signature': '簽名',
        'total_size': '總大小'
    }
    
    # 呼叫 create_pdf_report 生成 PDF 報告
    logo_path = "logo.png"
    create_pdf_report(root_path, max_depth, pdf_output, project_name, translations, logo_path)
    print(f"\nPDF文件已生成: {pdf_output}")

if __name__ == "__main__":
    main() 