# -*- coding: utf-8 -*-
# Crossword for EclipseCrossword
# https://github.com/AndreyKaiu/Anki_Crossword-for-EclipseCrossword
# Version 1.2, date: 2025-08-28
from aqt.qt import *
from aqt.editor import Editor
from aqt.browser.browser import Browser
from aqt import gui_hooks
from aqt.utils import showInfo
from pathlib import Path
import re
import json
import os
import shutil
import time
import random
from aqt.addcards import AddCards
from html import escape

from aqt import mw
import anki.lang
from aqt.utils import (showText, showInfo, tooltip) 
from bs4 import BeautifulSoup
# from aqt.gui_hooks import collection_did_load
from aqt.gui_hooks import profile_did_open

from anki.consts import MODEL_STD

try:
    from PyQt6.QtWidgets import QApplication, QVBoxLayout, QDialog, QMessageBox, QMainWindow     
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtCore import Qt, QObject, QTimer, QRegularExpression, QUrl
    from PyQt6.QtWebChannel import QWebChannel
    from PyQt6.QtGui import QFont, QFontDatabase
    pyqt_version = "PyQt6"
except ImportError:
    from PyQt5.QtWidgets import QApplication, QVBoxLayout, QDialog, QMessageBox, QMainWindow     
    from PyQt5.QtWebEngineWidgets import QWebEngineView
    from PyQt5.QtCore import Qt, QObject, QTimer, QRegExp, QUrl
    from PyQt5.QtWebChannel import QWebChannel   
    from PyQt5.QtGui import QFont, QFontDatabase
    pyqt_version = "PyQt5"


# ========================= CONFIG ============================================
# Loading the add-on configuration
config = mw.addonManager.getConfig(__name__)
meta  = mw.addonManager.addon_meta(__name__)
this_addon_provided_name = meta.provided_name

def configF(par1, par2, default=""):
    """get data from config"""
    try:
        ret = config[par1][par2]
        return ret
    except Exception as e:        
        print("logError: ", e)
        return default     

languageName = configF("GLOBAL_SETTINGS", "language", "en")
current_language = anki.lang.current_lang #en, pr-BR, en-GB, ru and the like
if not languageName: # if you need auto-detection     
    languageName = current_language
    if languageName not in config["LOCALIZATION"]:        
        languageName = "en" # If it is not supported, we roll back to English               
    
# print("languageName = ", languageName)    
try:
    localization = config["LOCALIZATION"][languageName]
except Exception as e:
    text = f"ERROR in add-on '{this_addon_provided_name}'\n"
    text += f"Config[\"GLOBAL_SETTINGS\"][\"language\"] does not contain '{languageName}'"
    text += "\nChange the add-on configuration, \"language\": \"en\""
    languageName = "en"
    config["GLOBAL_SETTINGS"]["language"] = languageName # change language
    mw.addonManager.writeConfig(__name__, config) # write the config with changes
    showText(text, type="error")

def localizationF(par1, default=""):
    """get data from localization = config["LOCALIZATION"][languageName] """
    try:
        ret = localization[par1]
        return ret
    except Exception as e:        
        print("logError: ", e)
        return default  
# =============================================================================


dialog = None
browserS = None


def browser_show(browser):
    global browserS
    browserS = browser 


def show_image_dialog(self): 
    global dialog      
    
    # Обязательные поля и их назначение
    REQUIRED_FIELDS = {
        "word=transcription=translation=example=extranslation": "main_content",
        "Word_hint (file-type ewl)": "hint",
        "Crossword_code": "crossword_code",
        "Title": "main_content", 
        "Language_SpeechSynthesis": "main_content",
        "Symbols_for_buttons": "main_content"
    }
    REQUIRED_FIELDS_ORDER = [
        "word=transcription=translation=example=extranslation",
        "Word_hint (file-type ewl)",
        "Crossword_code"
    ]
    def get_tab_index(field):
        try:
            return 1 + REQUIRED_FIELDS_ORDER.index(field)
        except ValueError:
            return 1  # значение по умолчанию

    idx = getattr(self, "currentField", None)
    
    if idx is None:
        locF = localizationF("Unable_to_determine_active_field", "Unable to determine active field.")
        showInfo(locF)
        return

    

    # Получаем имя текущего поля по индексу
    field_names = list(self.note.keys())
    if idx < 0 or idx >= len(field_names):
        locF = localizationF("Invalid_field_index", "Invalid field index.")
        showInfo(locF)
        return
        
    field = field_names[idx]
    
    # Проверяем, что активное поле в списке допустимых
    if field not in REQUIRED_FIELDS:
        locF = localizationF("Invalid_field_type", 
                           "The record type must be 'Crossword' or contain 6 specified fields.\nCursor must be in one of these fields:") + f" {', '.join(REQUIRED_FIELDS)}"
        showInfo(locF)
        return
    
    # Проверяем наличие всех обязательных полей
    missing_fields = [field for field in REQUIRED_FIELDS if field not in self.note]
    if missing_fields:
        locF = localizationF("Missing_required_fields", 
                           "Note is missing required fields:") + f" {', '.join(missing_fields)}"
        showInfo(locF)
        return
    
    deck_id = self.note.cards()[0].did if self.note.cards() else self.mw.col.decks.selected()

    # Создаем диалоговое окно
    dialog = QDialog(self.widget)
    locF = self.note["Title"] + " - " + localizationF("WindowTitle", "Crossword for EclipseCrossword")
    dialog.setWindowTitle(locF)
    
    if pyqt_version == "PyQt6":
        dialog.setWindowFlag(dialog.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)
    else:
        dialog.setWindowFlag(Qt.WindowMaximizeButtonHint)
    
    dialog.setMinimumSize(800, 600)



    main_layout = QVBoxLayout()

    # Создаем виджет с вкладками
    tab_widget = QTabWidget()

    # 1. Вкладка Help
    help_tab = QWidget()
    help_layout = QVBoxLayout()

    help_label = QLabel(localizationF("Help", "Help"))
    help_layout.addWidget(help_label)

    help_text = QTextEdit()
    help_text.setReadOnly(True)    
    htxt = localizationF("help_str1", "") + "\n"
    htxt += localizationF("help_str2", "") + "\n"
    htxt += localizationF("help_str3", "") + "\n"
    htxt += localizationF("help_str4", "") + "\n"
    htxt += localizationF("help_str5", "") + "\n"
    htxt += localizationF("help_str6", "") + "\n"
    htxt += localizationF("help_str7", "") + "\n"
    htxt += localizationF("help_str8", "")
    help_text.setPlainText(htxt)
    help_scroll = QScrollArea()
    help_scroll.setWidget(help_text)
    help_scroll.setWidgetResizable(True)
    help_layout.addWidget(help_scroll, stretch=1)  # Растягиваем на все доступное пространство

    help_tab.setLayout(help_layout)
    tab_widget.addTab(help_tab, localizationF("HelpTab", "Help"))

    # 2. Вкладка Word Field
    word_tab = QWidget()
    word_layout = QVBoxLayout()

    word_label = QLabel(localizationF("WordField", "Field: word=transcription=translation=example=extranslation"))
    word_layout.addWidget(word_label)

    word_text = QTextEdit()
    raw_text = re.sub(r'<br\s*/?>', '\n', self.note["word=transcription=translation=example=extranslation"], flags=re.IGNORECASE)      
    raw_text = raw_text.replace("\n\n", "\n")
    word_text.setPlainText(BeautifulSoup(raw_text, "html.parser").get_text())
    word_scroll = QScrollArea()
    word_scroll.setWidget(word_text)
    word_scroll.setWidgetResizable(True)
    word_layout.addWidget(word_scroll, stretch=1)

    # Order of fields
    order_layout = QHBoxLayout()
    order_label = QLabel(localizationF("OrderFields", "The order of the insert fields is:"))
    order_layout.addWidget(order_label)


    def save_order_edit(txt_order):
        """Сохранить порядок полей при импорте"""
        try:
            # Путь к meta.json
            addon_dir = Path(mw.addonManager.addonsFolder()) / __name__ 
            meta_path = addon_dir / "meta.json"
            if meta_path.exists():
                original_mtime = os.path.getmtime(meta_path) # Сохраняем старую дату модификации
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    with open(meta_path, "w", encoding="utf-8") as f:                    
                        meta["OrderFields"] = txt_order
                        json.dump(meta, f, ensure_ascii=False, indent=4)                                              
                os.utime(meta_path, (original_mtime, original_mtime))  # Восстанавливаем дату модификации
        except Exception as e:          
            print("save_order_edit Error: ", e)
              

    def load_order_edit():
        """Загрузить порядок полей при импорте"""
        try:
            # Путь к meta.json
            addon_dir = Path(mw.addonManager.addonsFolder()) / __name__ 
            meta_path = addon_dir / "meta.json"
            if meta_path.exists():
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    return meta.get("OrderFields", "")
            return "" 
        except Exception as e:          
            return ""

    OrderFields = load_order_edit()
    if not OrderFields.strip():  # Если пустая строка
        OrderFields = "1=2=3=4=5"     

    order_edit = QLineEdit(OrderFields)
    
    order_layout.addWidget(order_edit)
    word_layout.addLayout(order_layout)

    # Word field buttons
    word_buttons_layout = QHBoxLayout()
    clear_word_btn = QPushButton(localizationF("Clear", "Clear"))
    clear_word_btn.clicked.connect(lambda: word_text.clear())
    word_buttons_layout.addWidget(clear_word_btn)

    add_from_txt_btn = QPushButton(localizationF("AddFromTxt", "Add from file TXT and convert TAB to ="))
    word_buttons_layout.addWidget(add_from_txt_btn)
    word_layout.addLayout(word_buttons_layout)

    word_hint_buttons_layout = QHBoxLayout()
    create_hint1_btn = QPushButton(localizationF("CreateHint1", "Create Word_hint (word: translation)"))
    word_hint_buttons_layout.addWidget(create_hint1_btn)

    create_hint2_btn = QPushButton(localizationF("CreateHint2", "Create Word_hint (word: example)"))
    word_hint_buttons_layout.addWidget(create_hint2_btn)
    word_layout.addLayout(word_hint_buttons_layout)

    word_tab.setLayout(word_layout)
    tab_widget.addTab(word_tab, localizationF("WordTab", "Words"))

    # 3. Вкладка Word Hint
    hint_tab = QWidget()
    hint_layout = QVBoxLayout()

    hint_label = QLabel(localizationF("WordHintField", "Field: Word_hint (file-type ewl)"))
    hint_layout.addWidget(hint_label)

    hint_text = QTextEdit()        
    raw_text = re.sub(r'<br\s*/?>', '\n', self.note["Word_hint (file-type ewl)"], flags=re.IGNORECASE)   
    raw_text = raw_text.replace("\n\n", "\n")   
    hint_text.setPlainText(BeautifulSoup(raw_text, "html.parser").get_text())
    hint_scroll = QScrollArea()
    hint_scroll.setWidget(hint_text)
    hint_scroll.setWidgetResizable(True)
    hint_layout.addWidget(hint_scroll, stretch=1)

    # Word_hint buttons
    hint_buttons_layout = QHBoxLayout()
    clear_hint_btn = QPushButton(localizationF("Clear", "Clear"))
    clear_hint_btn.clicked.connect(lambda: hint_text.clear())
    hint_buttons_layout.addWidget(clear_hint_btn)

    save_ewl_btn = QPushButton(localizationF("SaveEWL", "Save to file *.ewl"))
    hint_buttons_layout.addWidget(save_ewl_btn)
    hint_layout.addLayout(hint_buttons_layout)


    # Nstr input and buttons
    nstr_layout = QHBoxLayout()
    nstr_label = QLabel("Nstr=")
    nstr_layout.addWidget(nstr_label)

    nstr_input = QLineEdit("20")
    nstr_input.setMaxLength(3)  # Ограничение на 3 символа
    nstr_input.setFixedWidth(40)  # Фиксированная ширина поля    
    nstr_layout.addWidget(nstr_input)    
    
    Nstrok_btn = QPushButton("OK")
    nstr_layout.addWidget(Nstrok_btn)

    # Код для кнопки OK
    def handle_ok_button():        
        try:
            max_lines = int(nstr_input.text())
        except ValueError:
            return  # Если введено не число, ничего не делаем
                
        text = hint_text.toPlainText()
        lines = text.split('\n')    
        # Удаляем пустые строки
        lines = [line for line in lines if line.strip()]

        # Оставляем только первые max_lines строк
        new_text = '\n'.join(lines[:max_lines])
        hint_text.setPlainText(new_text)
        
        # if len(lines) > max_lines:
        #     # Оставляем только первые max_lines строк
        #     new_text = '\n'.join(lines[:max_lines])
        #     hint_text.setPlainText(new_text)

    Nstrok_btn.clicked.connect(handle_ok_button)


    rnd_btn = QPushButton("RND")
    nstr_layout.addWidget(rnd_btn)

    sort_btn = QPushButton("SORT A-Z")
    nstr_layout.addWidget(sort_btn)

    nstr_layout.addStretch()  # Растягиваемое пространство
    hint_layout.addLayout(nstr_layout)


    def handle_rnd_button():
        text = hint_text.toPlainText()
        lines = text.split('\n')    
        # Удаляем пустые строки
        lines = [line for line in lines if line.strip()]
     
        # Создаем список индексов и перемешиваем его
        indices = list(range(len(lines)))
        random.shuffle(indices)        
        # Переставляем строки согласно перемешанным индексам
        shuffled_lines = []
        for i in indices:
            shuffled_lines.append(lines[i])        
        # Объединяем обратно в текст
        new_text = '\n'.join(shuffled_lines)
        hint_text.setPlainText(new_text)

    rnd_btn.clicked.connect(handle_rnd_button)


    def handle_sort_button():
        text = hint_text.toPlainText()
        lines = text.split('\n')        
        # Удаляем пустые строки и сортируем оставшиеся
        non_empty_lines = [line for line in lines if line.strip()]
        sorted_lines = sorted(non_empty_lines)        
        # Объединяем обратно в текст
        new_text = '\n'.join(sorted_lines)
        hint_text.setPlainText(new_text)

    sort_btn.clicked.connect(handle_sort_button)


    # UTF-ANSI section
    utf_layout = QHBoxLayout()
    utf_label = QLabel("UTF=ANSI:")
    utf_layout.addWidget(utf_label)

    utf_input = QLineEdit()
    utf_input.setMinimumWidth(200)  # Минимальная ширина поля
    utf_layout.addWidget(utf_input)

    def save_utf_input(txt):
        """Сохранить строку замен UTF=ANSI"""
        try:
            # Путь к meta.json
            addon_dir = Path(mw.addonManager.addonsFolder()) / __name__ 
            meta_path = addon_dir / "meta.json"
            if meta_path.exists():
                original_mtime = os.path.getmtime(meta_path) # Сохраняем старую дату модификации
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    with open(meta_path, "w", encoding="utf-8") as f:                    
                        meta["ReplUTFtoANSI"] = txt
                        json.dump(meta, f, ensure_ascii=False, indent=4)                                              
                os.utime(meta_path, (original_mtime, original_mtime))  # Восстанавливаем дату модификации
        except Exception as e:          
            print("save_utf_input Error: ", e)
              

    def load_utf_input():
        """Загрузить строку UTF->ANSI"""
        try:
            # Путь к meta.json
            addon_dir = Path(mw.addonManager.addonsFolder()) / __name__ 
            meta_path = addon_dir / "meta.json"
            if meta_path.exists():
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    return meta.get("ReplUTFtoANSI", "")
            return "" 
        except Exception as e:          
            return ""
     
    get_utf_input = load_utf_input() 
    utf_input.setText( get_utf_input )


    hint_layout.addLayout(utf_layout)


    hint_tab.setLayout(hint_layout)
    tab_widget.addTab(hint_tab, localizationF("HintTab", "Word:  Hint"))

    

    # 4. Вкладка Crossword Code
    code_tab = QWidget()
    code_layout = QVBoxLayout()

    code_label = QLabel(localizationF("CrosswordCode", "Field: Crossword_code"))
    code_layout.addWidget(code_label)

    code_text = QTextEdit()    
    # Установка моноширинного шрифта
    fixed_font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
    fixed_font.setPointSize(10) 
    code_text.setFont(fixed_font)
    raw_text = self.note["Crossword_code"]    
    raw_text = raw_text.replace('\n','')
    raw_text = raw_text.replace('\r','')
    raw_text = re.sub(r'&nbsp;', '', raw_text, flags=re.IGNORECASE)
    raw_text = re.sub(r'<br\s*/?>\s*', '', raw_text, flags=re.IGNORECASE)
    raw_text = re.sub(r'^\s*', '', raw_text, flags=re.IGNORECASE) 
    raw_text = re.sub(r';', ';\n', raw_text, flags=re.IGNORECASE) 
    code_text.setPlainText(BeautifulSoup(raw_text, "html.parser").get_text())
    code_scroll = QScrollArea()
    code_scroll.setWidget(code_text)
    code_scroll.setWidgetResizable(True)
    code_layout.addWidget(code_scroll, stretch=1)

    # Crossword_code buttons
    code_buttons_layout = QHBoxLayout()
    clear_code_btn = QPushButton(localizationF("Clear", "Clear"))
    clear_code_btn.clicked.connect(lambda: code_text.clear())
    code_buttons_layout.addWidget(clear_code_btn)

    paste_html_btn = QPushButton(localizationF("PasteHTML", "Paste from crossword file *.html"))
    code_buttons_layout.addWidget(paste_html_btn)
    code_layout.addLayout(code_buttons_layout)

    code_buttons2_layout = QHBoxLayout()
    repl_utf_btn = QPushButton("REPL ClueArray ANSI->UTF")
    code_buttons2_layout.addWidget(repl_utf_btn)
    solveYes_btn = QPushButton(localizationF("Solution_hint", "Solution hint"))    
    code_buttons2_layout.addWidget(solveYes_btn)
    solveNo_btn = QPushButton(localizationF("No_solution_hint", "No solution hint"))
    code_buttons2_layout.addWidget(solveNo_btn)

    code_layout.addLayout(code_buttons2_layout)

    code_tab.setLayout(code_layout)
    tab_widget.addTab(code_tab, localizationF("CodeTab", "Crossword сode"))

    # активная вкладка зависит от поля
    tab_widget.setCurrentIndex( get_tab_index(field) ) 



    


    def extract_crossword_params(code_lines):
        params = {
            'width': None,
            'height': None,
            'word_lengths': None,
            'word_x': None,
            'word_y': None,
            'last_horizontal': None
        }
        
        for line in code_lines:
            line = line.strip()            
            if line.startswith('CrosswordWidth ='):
                params['width'] = int(line.split('=')[1].replace(';', '').strip())            
            elif line.startswith('CrosswordHeight ='):
                params['height'] = int(line.split('=')[1].replace(';', '').strip())                
            elif line.startswith('WordLength = new Array('):
                arr_str = line.split('(', 1)[1].rsplit(')', 1)[0]
                params['word_lengths'] = [int(x.strip()) for x in arr_str.split(',')]                
            elif line.startswith('WordX = new Array('):
                arr_str = line.split('(', 1)[1].rsplit(')', 1)[0]
                params['word_x'] = [int(x.strip()) for x in arr_str.split(',')]                
            elif line.startswith('WordY = new Array('):
                arr_str = line.split('(', 1)[1].rsplit(')', 1)[0]
                params['word_y'] = [int(x.strip()) for x in arr_str.split(',')]                
            elif line.startswith('LastHorizontalWord ='):
                params['last_horizontal'] = int(line.split('=')[1].replace(';', '').strip())        
        return params


    def draw_crossword(code_lines):
        params = extract_crossword_params(code_lines)        
        width = params['width']
        height = params['height']
        word_lengths = params['word_lengths']
        word_x = params['word_x']
        word_y = params['word_y']
        last_horizontal = params['last_horizontal']

        # Создаем пустую сетку
        grid = [['·' for _ in range(width)] for _ in range(height)]

        # Заполняем горизонтальные слова (первые last_horizontal+1 слов)
        for i in range(last_horizontal + 1):
            x = word_x[i]
            y = word_y[i]
            length = word_lengths[i]
            for dx in range(length):
                if x + dx < width:
                    grid[y][x + dx] = 'X'

        # Заполняем вертикальные слова (остальные слова)
        for i in range(last_horizontal + 1, len(word_x)):
            x = word_x[i]
            y = word_y[i]
            length = word_lengths[i]
            for dy in range(length):
                if y + dy < height:
                    grid[y + dy][x] = 'X'

        # Формируем текстовое представление
        crossword_text = "/*;\n"
        for row in grid:
            crossword_text += '// ' + ' '.join(row) + '  ;\n'
        crossword_text += "*/;"
        
        return crossword_text

    


    def setup_solution_buttons():
        solveYes_btn.clicked.connect(lambda: update_solve_status(True))
        solveNo_btn.clicked.connect(lambda: update_solve_status(False))

    def update_solve_status(solve_status):
        code_text_PT = code_text.toPlainText()       
        word_array_str = [] 
        # Проверяем и заполняем пустой массив Word
        if "Word = new Array();" in code_text_PT:
            word_array_str = fill_empty_word_array()
            if not word_array_str:
                return  # Если не удалось заполнить - выходим    
        # если нашли просто Word = new Array( то удалим все до );
        elif "Word = new Array(" in code_text_PT:
                # Нашли заполненный массив - сначала удаляем его
                start_index = code_text_PT.find("Word = new Array(")
                end_index = code_text_PT.find(");", start_index) + 2  # +2 чтобы включить ");"          
                # Проверяем, есть ли перевод строки после );
                if end_index < len(code_text_PT) and code_text_PT[end_index] == '\n':
                    end_index += 1  # Удаляем и перевод строки
                elif end_index < len(code_text_PT) and code_text_PT[end_index:end_index+2] == '\r\n':
                    end_index += 2  # Удаляем Windows-style перевод строки (\r\n)                        
                if end_index > start_index:
                    # Удаляем старый массив
                    code_text_PT = code_text_PT[:start_index] + code_text_PT[end_index:]

                word_array_str = fill_empty_word_array()
                if not word_array_str:
                    return  # Если не удалось заполнить - выходим  
        # если вообще не нашли
        else:
            word_array_str = fill_empty_word_array()
            if not word_array_str:
                return  # Если не удалось заполнить - выходим  
            

        # Обновляем/добавляем Solve
        solve_line = f"Solve = {str(solve_status).lower()};"           
        code_lines = code_text_PT.splitlines()
        if word_array_str != []:
            # Удаляем старую строку Solve (если есть) и Word = new (если есть) и комментарии 
            code_lines = [line for line in code_lines if not( line.strip().startswith("Solve =")
                                                              or line.strip().startswith("Word = new") or line.strip().startswith("//") or line.strip().startswith("/*") or line.strip().startswith("*/") ) ]
            # Добавляем новую строку Word = new
            code_lines.append(word_array_str) 
        else:
            # Удаляем старую строку Solve (если есть) и комментарии
            code_lines = [line for line in code_lines if not( line.strip().startswith("Solve =") 
                                                             or line.strip().startswith("//") or line.strip().startswith("/*") or line.strip().startswith("*/") ) ]      
        # Добавляем новую строку Solve
        code_lines.append(solve_line)
        # Добавляем вид кроссворда внешний
        code_lines.insert(0, draw_crossword(code_lines) )
        updated_code = "\n".join(code_lines)        
        code_text.setPlainText(updated_code)
        UpdateAnswerHash()




    def fill_empty_word_array():
        # Получаем текст с подсказками
        hint_text_PT= hint_text.toPlainText()        
        
        # Парсим массив Clue (если он определен в коде)
        clue_match = re.search(r'\s*Clue\s*=\s*new\s*Array\((.*"\s*)\);', code_text.toPlainText())
        
        if not clue_match:            
            QMessageBox.warning(dialog,
                                localizationF("Error", "Error"),
                                localizationF("Clue_array_not_found", "Clue array not found in the code!"))
            return False        
        
        try:
            # Извлекаем элементы Clue (удаляем кавычки и лишние пробелы)
            clue_str = clue_match.group(1)    
            # Заменяем '", "' на '","' для единообразного разделителя
            clue_str = clue_str.replace('", "', '","')
            # Разбиваем строку по '","' и очищаем элементы
            clue_items = [item.strip().strip('"') for item in clue_str.split('","')]    
            # Удаляем возможные оставшиеся кавычки в первом и последнем элементах
            if clue_items:
                clue_items[0] = clue_items[0].lstrip('"')
                clue_items[-1] = clue_items[-1].rstrip('"')            
        except:            
            QMessageBox.warning(dialog,
                                localizationF("Error", "Error"),
                                localizationF("Failed_to_parse_Clue_array", "Failed to parse 'Clue' array!"))
            return False
        
        
        
        # Парсим hint_text (формат "слово:  подсказка")
        word_hint_pairs = []
        for line in hint_text_PT.splitlines():
            if ":  " in line:
                word, hint = line.split(":  ", 1)
                word_hint_pairs.append((word.strip(), hint.strip()))
        
        # Сопоставляем Clue с hint_text
        word_array_items = []
        for clue_first_word in clue_items:
            found = False
            for word, hint in word_hint_pairs:                
                if clue_first_word.strip().lower() == hint.strip().lower():
                    wordUP = word.upper()
                    word_array_items.append(f'"{wordUP}"')
                    found = True
                    break
            
            if not found:                
                QMessageBox.warning(dialog,
                                localizationF("Error", "Error"),
                                localizationF("No_match_found_for_Clue_item", "No match found for Clue item") + f": {clue_first_word}")
                return False
        
        # Обновляем массив Word в коде
        word_array_str = f'Word = new Array({", ".join(word_array_items)});'       
        
        return word_array_str
      

    setup_solution_buttons()


    def add_from_txt():
        # Открываем диалог выбора файла
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            dialog,
            localizationF("OpenTXTFile", "Open Anki Export TXT File"),
            "",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if not file_path:
            return  # Пользователь отменил выбор файла
        
        try:
            # Читаем файл в UTF-8
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Проверяем обязательные параметры
            if len(lines) < 2 or not lines[0].startswith("#separator:tab"):
                QMessageBox.warning(dialog,
                                localizationF("InvalidFile", "Invalid File"),
                                localizationF("NotAnkiExport", "The selected file is not a valid Anki export (missing '#separator:tab' in first line)"))
                return
            
            # Проверяем html параметр
            if len(lines) >= 2 and lines[1].startswith("#html:"):
                html_param = lines[1].strip().split(":")[1]
                if html_param.lower() != "false":
                    QMessageBox.warning(dialog,
                                    localizationF("HTMLWarning", "HTML Warning"),
                                    localizationF("HTMLNotAllowed", "HTML is not allowed in the export file"))
                    return
            
            # Получаем порядок полей из QLineEdit
            order_str = order_edit.text().strip()
            if not order_str:
                order_str = "1=2=3=4=5"  # Значение по умолчанию
                order_edit.setText(order_str)
            
            # Парсим порядок полей
            try:
                field_order = [int(x) for x in order_str.split("=")]
            except ValueError:
                QMessageBox.warning(dialog,
                                localizationF("InvalidOrder", "Invalid Order"),
                                localizationF("OrderFormatError", "Field order should be numbers separated by '=' (e.g. '1=2=3=4=5')"))
                return
            
            # Обрабатываем строки (пропускаем первые 2, если они начинаются с #)
            processed_lines = []
            for line in lines:
                if line.startswith("#"):
                    continue
                line = line.strip()
                if not line:
                    continue
                
                # Разбиваем строку по табуляции
                fields = line.split("\t")
                
                # Формируем новую строку согласно порядку полей
                new_parts = []
                for field_num in field_order:
                    if field_num == 0:  # Пропускаем
                        new_parts.append("")
                    elif 1 <= field_num <= len(fields):
                        # Заменяем = на — в полях
                        field = fields[field_num-1].replace("=", "—")
                        new_parts.append(field)
                    else:
                        new_parts.append("")  # Если поле отсутствует
                
                # Собираем новую строку
                new_line = "=".join(new_parts)
                processed_lines.append(new_line)
            
            # Добавляем обработанные строки в QTextEdit
            current_text = word_text.toPlainText()
            if current_text:
                current_text += "\n"
            current_text += "\n".join(processed_lines)
            word_text.setPlainText(current_text)

            save_order_edit( order_edit.text().strip() ) 

            QMessageBox.information(dialog,
                                localizationF("Success", "Success"),
                                localizationF("ImportSuccess", "Imported from file and added lines: ") + f"{len(processed_lines)}")
            
        
        except Exception as e:
            QMessageBox.critical(dialog,
                            localizationF("Error", "Error"),
                            localizationF("ImportError", "Failed to import file: ") + f"{str(e)}")

    # Привязываем функцию к кнопке
    add_from_txt_btn.clicked.connect(add_from_txt)


    def create_word_hint_translation():
        """Создает подсказку в формате 'word:  translation'"""
        current_text = word_text.toPlainText()
        if not current_text.strip():
            QMessageBox.warning(dialog,
                            localizationF("Warning", "Warning"),
                            localizationF("NoContentWordField", "No content in word field!"))
            return
        
        hints = []
        for line in current_text.split('\n'):
            if not line.strip():
                continue
                
            parts = line.split('=')
            if len(parts) >= 3:  # Нужны как минимум word и translation
                word = parts[0].strip()
                translation = parts[2].strip()
                hints.append(f"{word}:  {translation}")
        
        if hints:
            hint_text.setPlainText('\n'.join(hints))
            tab_widget.setCurrentIndex(2) # Переключение на вкладку Word Hint
        else:
            QMessageBox.warning(dialog,
                            localizationF("Warning", "Warning"),
                            localizationF("NoValidLines", "No valid lines found for creating hints"))

    


    def create_word_hint_example():
        """Создает подсказку в формате 'word:  example' с заменой совпадений на ***"""
        current_text = word_text.toPlainText()
        if not current_text.strip():
            QMessageBox.warning(dialog,
                            localizationF("Warning", "Warning"),
                            localizationF("NoContentWordField", "No content in word field!"))
            return
        
        hints = []
        for line in current_text.split('\n'):
            if not line.strip():
                continue
                
            parts = line.split('=')
            if len(parts) >= 4:  # Нужны как минимум word и example
                word = parts[0].strip()
                example = parts[3].strip()
                
                # Создаем регулярное выражение для поиска 
                pattern = re.compile(r'\b' + re.escape(word), re.IGNORECASE)
                
                # Заменяем все вхождения на ***
                masked_example = pattern.sub('***', example)
                
                hints.append(f"{word}:  {masked_example}")
        
        if hints:
            hint_text.setPlainText('\n'.join(hints))            
            tab_widget.setCurrentIndex(2) # Переключение на вкладку Word Hint
        else:
            QMessageBox.warning(dialog,
                            localizationF("Warning", "Warning"),
                            localizationF("NoValidLines", "No valid lines found for creating hints"))
        
    # Привязываем функции к кнопкам
    create_hint1_btn.clicked.connect(create_word_hint_translation)
    create_hint2_btn.clicked.connect(create_word_hint_example)


    # Функция сохранения в EWL файл
    def save_ewl_file():
        hint_content = hint_text.toPlainText()

        save_utf_input( utf_input.text().strip() )
        
        if not hint_content.strip():
            QMessageBox.warning(dialog, 
                            localizationF("Warning", "Warning"),
                            localizationF("NoContent", "No content to save in Word_hint field!"))
            return
        
        # Диалог выбора кодировки
        encodings = [            
            ('Windows-1251 (Cyrillic)', 'windows-1251'),            
            ('Windows-1252 (Western)', 'windows-1252'),
            ('ISO-8859-1 (Latin-1)', 'iso-8859-1'),
            ('ISO-8859-2 (Latin-2)', 'iso-8859-2'),
            ('ISO-8859-3 (Latin-3)', 'iso-8859-3'),
            ('ISO-8859-4 (Latin-4)', 'iso-8859-4'),
            ('ISO-8859-5 (Latin/Cyrillic)', 'iso-8859-5'),
            ('ISO-8859-6 (Latin/Arabic)', 'iso-8859-6'),
            ('ISO-8859-7 (Latin/Greek)', 'iso-8859-7'),
            ('ISO-8859-8 (Latin/Hebrew)', 'iso-8859-8'),
            ('ISO-8859-9 ((Latin-5))', 'iso-8859-9'),
            ('ISO-8859-10 (Latin-6)', 'iso-8859-10'),
            ('ISO-8859-11 (Latin/Thai)', 'iso-8859-11'),            
            ('ISO-8859-13 (Latin-7)', 'iso-8859-13'),
            ('ISO-8859-14 (Latin-8)', 'iso-8859-14'),
            ('ISO-8859-15 (Latin-9)', 'iso-8859-15'),
            ('ISO-8859-16 (Latin-10)', 'iso-8859-16'),
            ('UTF-8 (no warranty)', 'utf-8'), 
            ('UTF-16 (no warranty)', 'utf-16')            
        ]
        
        encoding, ok = QInputDialog.getItem(
            dialog,
            localizationF("SelectEncoding", "Select File Encoding"),
            localizationF("ChooseEncoding", "Choose text encoding:"),
            [e[0] for e in encodings],
            0,  # индекс по умолчанию (windows-1251)
            False  # не редактируемый
        )
        
        if not ok:
            return  # пользователь отменил выбор
        
        # Получаем значение кодировки
        encoding_value = next((e[1] for e in encodings if e[0] == encoding), 'utf-8')

        

        # Получаем таблицу замен из utf_input
        replacement_map = {}
        replacements_text = utf_input.text().strip()
        
        # Разбираем пары замен
        if replacements_text:
            pairs = replacements_text.replace(';', ' ').split()
            for pair in pairs:
                if '=' in pair:
                    utf_char, ansi_char = pair.split('=', 1)
                    replacement_map[utf_char] = ansi_char
        
        new_replacements = set()  # Используем SET вместо list для уникальности
        has_replacements = False
        has_new_symbols = False
        
        encoded_content = ""
        
        for char in hint_content:
            try:
                char.encode(encoding_value)
                encoded_content += char
            except UnicodeEncodeError:
                has_replacements = True
                
                if char in replacement_map:
                    encoded_content += replacement_map[char]
                else:
                    # Проверяем, не добавляли ли уже этот символ в текущей сессии
                    if char not in new_replacements:
                        new_replacements.add(char)  # Добавляем в SET (уникальные)
                        has_new_symbols = True
                    
                    encoded_content += '?'  # Временная замена
        
        # Если найдены новые символы, добавляем их в utf_input
        if has_new_symbols:
            current_text = utf_input.text().strip()
            new_pairs = []
            
            # Добавляем только уникальные символы
            for char in new_replacements:
                new_pairs.append(f"{char}=?")
            
            if current_text:
                new_text = current_text + " " + " ".join(new_pairs)
            else:
                new_text = " ".join(new_pairs)
            
            utf_input.setText(new_text)



        if has_new_symbols:
            locF = "SaveError! UTF=ANSI: char=? "    
            tooltip(f"<p style='color: yellow; background-color: black'>{locF}</p>")
            return  # найдены новые has_new_symbols

        
        # Диалог сохранения файла
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(
            dialog,
            localizationF("SaveEWLFile", "Save Word Hint File"),
            "",
            "EWL Files (*.ewl);;All Files (*)"
        )
        
        if file_path:
            if not file_path.lower().endswith('.ewl'):
                file_path += '.ewl'
            
            try:
                with open(file_path, 'w', encoding=encoding_value) as f:
                    encoded_content_decode = encoded_content.encode(encoding_value, errors='replace').decode(encoding_value)
                    f.write(encoded_content_decode)
                
                # QMessageBox.information(dialog,
                #                     localizationF("Success", "Success"),
                #                     localizationF("FileSavedEncoding", "File saved successfully, encoding: ") + f"{encoding}")
                locF = localizationF("FileSavedEncoding", "File saved successfully, encoding: ") + f"{encoding}"    
                tooltip(f"<p style='color: yellow; background-color: black'>{locF}</p>")
            except Exception as e:
                QMessageBox.critical(dialog,
                                localizationF("Error", "Error"),
                                localizationF("SaveError", "Failed to save file: ") + f"{str(e)}")


    # Привязываем функцию к кнопке
    save_ewl_btn.clicked.connect(save_ewl_file)



    def advanced_clean_js_code(js_code):        
        # Удаляем пробелы и переводы строк вокруг запятых
        cleaned = re.sub(r'\s*,\s*(\n\s*)*', ', ', js_code)
        # Удаляем пробелы в начале и конце строк
        cleaned = re.sub(r'^\s+|\s+$', '', cleaned, flags=re.MULTILINE)
        # Удаляем множественные пробелы
        cleaned = re.sub(r'[ \t]{2,}', ' ', cleaned)

        # Убираем лишние переводы строк в массивах
        cleaned = re.sub(r'\[\s*\n\s*', '[', cleaned)
        cleaned = re.sub(r'\s*\n\s*\]', ']', cleaned)
        # cleaned = re.sub(r'\(\s*\n\s*', '(', cleaned)
        # cleaned = re.sub(r'\s*\n\s*\)', ')', cleaned)
        cleaned = re.sub(r',\s*\n\s*', ', ', cleaned)

        # Нормализуем переводы строк
        cleaned = re.sub(r'\r\n', '\n', cleaned)  # Унифицируем переводы строк
        cleaned = re.sub(r'\n{2,}', '\n', cleaned)  # Удаляем лишние пустые строки
        return cleaned


    def paste_from_html():
        # Открываем диалог выбора файла
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            dialog,
            localizationF("OpenHTMLFile", "Open Crossword HTML File"),
            "",
            "HTML Files (*.html *.htm);;All Files (*)"
        )
        
        if not file_path:
            return  # Пользователь отменил выбор файла
        
        try:
            # Читаем файл с правильной кодировкой
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Проверяем, что это файл кроссворда
            if "CrosswordWidth =" not in html_content:
                QMessageBox.warning(dialog,
                                localizationF("InvalidFile", "Invalid File"),
                                localizationF("NotCrosswordFile", "The selected file doesn't appear to be a crossword file (missing 'CrosswordWidth =')"))
                return
            
            # Извлекаем нужный участок кода
            start_idx = html_content.find("CrosswordWidth =")
            end_idx = html_content.find("//-->", start_idx)
            
            if end_idx == -1:
                QMessageBox.warning(dialog,
                                localizationF("InvalidFormat", "Invalid Format"),
                                localizationF("NoEndMarker", "Could not find the end marker '//-->' in the file"))
                return
            
            # Вырезаем нужный код (без //--> в конце)
            js_code = html_content[start_idx:end_idx].strip()
            
            # Вставляем в поле Crossword_code
            nJS = advanced_clean_js_code(js_code)
            code_text.setPlainText( nJS )
            
            # QMessageBox.information(dialog,
            #                     localizationF("Success", "Success"),
            #                     localizationF("CodeImported", "Crossword code imported successfully!"))
            locF = localizationF("CodeImported", "Crossword code imported successfully!")
            tooltip(f"<p style='color: yellow; background-color: black'>{locF}</p>")
        
        except UnicodeDecodeError:
            # Пробуем другие кодировки, если UTF-8 не сработал
            try:
                with open(file_path, 'r', encoding='cp1251') as f:
                    html_content = f.read()
                
                # Повторяем проверки и обработку
                if "CrosswordWidth =" not in html_content:
                    QMessageBox.warning(dialog,
                                    localizationF("InvalidFile", "Invalid File"),
                                    localizationF("NotCrosswordFile", "The selected file doesn't appear to be a crossword file (missing 'CrosswordWidth =')"))
                    return
                
                start_idx = html_content.find("CrosswordWidth =")
                end_idx = html_content.find("//-->", start_idx)
                
                if end_idx == -1:
                    QMessageBox.warning(dialog,
                                    localizationF("InvalidFormat", "Invalid Format"),
                                    localizationF("NoEndMarker", "Could not find the end marker '//-->' in the file"))
                    return
                
                js_code = html_content[start_idx:end_idx].strip()
                # Вставляем в поле Crossword_code
                nJS = advanced_clean_js_code(js_code)
                code_text.setPlainText( nJS )

                
                
                
                QMessageBox.information(dialog,
                                    localizationF("Success", "Success"),
                                    localizationF("CodeImported", "Crossword code imported successfully!"))
            
            except Exception as e:
                QMessageBox.critical(dialog,
                                localizationF("Error", "Error"),
                                localizationF("ReadError", "Failed to read file: ") + f"{str(e)}")
        
        except Exception as e:
            QMessageBox.critical(dialog,
                            localizationF("Error", "Error"),
                            localizationF("ReadError", "Failed to read file: ") + f"{str(e)}")

    # Привязываем функцию к кнопке
    paste_html_btn.clicked.connect(paste_from_html)


    # Добавляем вкладки в основной layout
    main_layout.addWidget(tab_widget, stretch=1)  # Растягиваем на все доступное пространство

    # Original buttons (Save and Close)
    button_layout = QHBoxLayout()    
    save_button = QPushButton(localizationF("Save","💾 Save"))    
    button_layout.addWidget(save_button)

    def RefreshDeck_id(deck_id):  
        """update the type of column maps"""     
        deck_name = browserS.mw.col.decks.name(deck_id)
        if Browser and deck_name:        
            browserS.sidebar.update_search(f'"deck:{deck_name}"')


    def prepare_text_for_saving(text):
        """Подготавливает текст для сохранения в HTML-поле"""        
        text = text.replace('\n', '<br>')        
        text = text.replace('  ', '&nbsp; ')
        return text


    def Nstr_OK():
        pass
    
    # Привязываем функцию к кнопке
    Nstrok_btn.clicked.connect(Nstr_OK)


    def RND_OK():
        pass
    
    # Привязываем функцию к кнопке
    rnd_btn.clicked.connect(RND_OK)
    

    def repl_utf():          
        code_text_PT = code_text.toPlainText()
        utfinput = utf_input.text().strip()        
        
        # Создаем словарь замен из utfinput
        replace_dict = {}
        for item in re.split(r'[;\s]+', utfinput):
            if '=' in item:
                utf_char, ansi_char = item.split('=')
                replace_dict[ansi_char] = utf_char

        # Ищем строку Clue = new Array(...)
        clue_match = re.search(r'(Clue\s*=\s*new\s*Array\()(.*?)(\);)', code_text_PT, re.DOTALL)
        if clue_match:
            # Извлекаем префикс, содержимое Array и суффикс
            prefix = clue_match.group(1)
            content = clue_match.group(2)
            suffix = clue_match.group(3)            
            # Заменяем символы в содержимом согласно replace_dict
            new_content = ''.join(replace_dict.get(char, char) for char in content)            
            # Собираем новую строку
            new_clue_str = prefix + new_content + suffix            
            # Заменяем исходную строку на измененную версию
            modified_text = code_text_PT[:clue_match.start()] + new_clue_str + code_text_PT[clue_match.end():]            
            # Применяем изменения к исходному code_text
            code_text.setPlainText(modified_text)


        # Привязываем функцию к кнопке
        repl_utf_btn.clicked.connect(repl_utf)
        

    # // Returns a one-way hash for a word.
    # function HashWord(Word)
    # {
    #     var x = (Word.charCodeAt(0) * 719) % 1138;
    #     var Hash = 837;
    #     var i;
    #     for (i = 1; i <= Word.length; i++)
    #         Hash = (Hash * i + 5 + (Word.charCodeAt(i - 1) - 64) * x) % 98503;
    #     return Hash;
    # }

    def hash_word(word):
        if not word:
            return 0
        
        x = (ord(word[0]) * 719) % 1138
        hash_val = 837
        
        for i in range(1, len(word) + 1):
            char_code = ord(word[i - 1]) - 64
            
            # Вычисляем как в JavaScript (с отрицательными промежуточными значениями)
            intermediate = hash_val * i + 5 + char_code * x
            
            # Эмулируем JavaScript поведение modulo для отрицательных чисел
            hash_val = intermediate % 98503
            if intermediate < 0:
                hash_val -= 98503
        
        return hash_val
    
    
    def UpdateAnswerHash(): 
        code_text_PT = code_text.toPlainText()
        # Ищем массив Word
        word_match = re.search(r'Word\s*=\s*new\s*Array\((.*?)\);', code_text_PT, re.DOTALL)
        if word_match:
            # Извлекаем содержимое массива и разбиваем по запятым
            array_content = word_match.group(1)
            # Удаляем все кавычки и пробелы, затем разбиваем
            words = [word.strip('" ') for word in array_content.split(',')]

            # Вычисляем новые хеши
            new_hashes = []
            for word in words:
                clean_word = word.replace('"', '').strip()
                hash_val = hash_word(clean_word)
                new_hashes.append(str(hash_val))
                        
            # Формируем новую строку AnswerHash
            new_answer_hash = f"AnswerHash = new Array({', '.join(new_hashes)});"
            
            # Заменяем старый AnswerHash на новый
            # Ищем старый AnswerHash
            answer_hash_match = re.search(r'AnswerHash\s*=\s*new\s*Array\(.*?\);', code_text_PT, re.DOTALL)
            if answer_hash_match:
                # Заменяем старый хеш на новый
                modified_text = code_text_PT[:answer_hash_match.start()] + new_answer_hash + code_text_PT[answer_hash_match.end():]            
                code_text.setPlainText(modified_text)
            else:
                # Если AnswerHash не найден, добавляем новый после Word
                modified_text = code_text_PT[:word_match.end()] + '\n' + new_answer_hash + code_text_PT[word_match.end():]                
                code_text.setPlainText(modified_text)  



    # Добавляем сохранение полей
    def save_to_fields():
        # Получаем текст из всех окон
        main_content = prepare_text_for_saving(word_text.toPlainText())  # основное окно
        hint_content = prepare_text_for_saving(hint_text.toPlainText())  # окно подсказки
        crossword_code_content = prepare_text_for_saving(code_text.toPlainText())  # окно кода кроссворда
        
        save_utf_input( utf_input.text().strip() )
        save_order_edit( order_edit.text().strip() ) 
        
        try:
            # Сохраняем в поле "word=transcription=translation=example=extranslation"
            self.note["word=transcription=translation=example=extranslation"] = main_content
            
            # Сохраняем в поле "Word_hint (file-type ewl)"
            self.note["Word_hint (file-type ewl)"] = hint_content
            
            # Сохраняем в поле "Crossword_code"
            self.note["Crossword_code"] = crossword_code_content
            
            # Обновляем заметку в Anki
            self.mw.col.update_note(self.note)

            QTimer.singleShot(500, lambda:RefreshDeck_id(deck_id))

            # QMessageBox.information(
            #     dialog,
            #     localizationF("Success", "Success"),
            #     localizationF("FieldsUpdated", "All fields have been successfully updated!")
            # )
            locF = localizationF("FieldsUpdated", "All fields have been successfully updated!")       
            tooltip(f"<p style='color: yellow; background-color: black'>{locF}</p>")

        except Exception as e:
            QMessageBox.critical(
                dialog,
                localizationF("Error", "Error"),
                localizationF("SaveErrorField", "Failed to save fields: ") + f"{str(e)}"
            )

    # Связываем кнопку с функцией сохранения
    save_button.clicked.connect(save_to_fields)


    close_button = QPushButton(localizationF("Close", "Close"))
    close_button.clicked.connect(dialog.close)
    button_layout.addWidget(close_button)

    main_layout.addLayout(button_layout)

    dialog.setLayout(main_layout)
    dialog.exec()
 


def setup_image_button(buttons, editor):
    locF = localizationF("Crossword_for_EclipseCrossword", "Crossword for EclipseCrossword")
    image_button = editor.addButton(
        icon=None,
        cmd="Crossword_for_EclipseCrossword",        
        func=lambda selfEditor=editor: QTimer.singleShot(0, lambda: show_image_dialog(selfEditor)),
        tip=locF,        
        label='''
        <div style="position: relative; width: 20px; height: 20px; display: block; text-align: center; line-height: 16px; font-size: 12px;">
            <svg width="20" height="20" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
        <!-- Фон - белый квадрат -->
        <rect x="0" y="0" width="20" height="20" fill="white" stroke="black" stroke-width="0.2"/>
        
        <!-- Закрашенные клетки 2-й строки (y от 5 до 10) -->
        <rect x="0" y="5" width="5" height="5" fill="#aaaaFF"/>
        <rect x="5" y="5" width="5" height="5" fill="#aaaaFF"/>
        <rect x="10" y="5" width="5" height="5" fill="#aaaaFF"/>
        <rect x="15" y="5" width="5" height="5" fill="#aaaaFF"/>
        
        <!-- Закрашенные клетки 2-го столбца (x от 5 до 10) -->
        <rect x="5" y="0" width="5" height="5" fill="#aaaaFF"/>
        <rect x="5" y="5" width="5" height="5" fill="#aaaaFF"/>
        <rect x="5" y="10" width="5" height="5" fill="#aaaaFF"/>
        <rect x="5" y="15" width="5" height="5" fill="#aaaaFF"/>
        
        <!-- Горизонтальные линии сетки (5 линий) -->
        <line x1="0" y1="0" x2="20" y2="0" stroke="black" stroke-width="0.2"/>
        <line x1="0" y1="5" x2="20" y2="5" stroke="black" stroke-width="0.2"/>
        <line x1="0" y1="10" x2="20" y2="10" stroke="black" stroke-width="0.2"/>
        <line x1="0" y1="15" x2="20" y2="15" stroke="black" stroke-width="0.2"/>
        <line x1="0" y1="20" x2="20" y2="20" stroke="black" stroke-width="0.2"/>
        
        <!-- Вертикальные линии сетки (5 линий) -->
        <line x1="0" y1="0" x2="0" y2="20" stroke="black" stroke-width="0.2"/>
        <line x1="5" y1="0" x2="5" y2="20" stroke="black" stroke-width="0.2"/>
        <line x1="10" y1="0" x2="10" y2="20" stroke="black" stroke-width="0.2"/>
        <line x1="15" y1="0" x2="15" y2="20" stroke="black" stroke-width="0.2"/>
        <line x1="20" y1="0" x2="20" y2="20" stroke="black" stroke-width="0.2"/>
        
        <!-- Буквы "w o r d" во 2-й строке -->
        <text x="2.5" y="8" font-size="4" font-weight="bold" fill="black" text-anchor="middle" dominant-baseline="middle">W</text>
        <text x="7.5" y="8" font-size="4" font-weight="bold" fill="black" text-anchor="middle" dominant-baseline="middle">O</text>
        <text x="12.5" y="8" font-size="4" font-weight="bold" fill="black" text-anchor="middle" dominant-baseline="middle">R</text>
        <text x="17.5" y="8" font-size="4" font-weight="bold" fill="black" text-anchor="middle" dominant-baseline="middle">D</text>
        
        <!-- Буквы "w o r d" во 2-м столбце -->
        <text x="7.5" y="3" font-size="4" font-weight="bold" fill="black" text-anchor="middle" dominant-baseline="middle">W</text>
        <text x="7.5" y="8" font-size="4" font-weight="bold" fill="black" text-anchor="middle" dominant-baseline="middle">O</text>
        <text x="7.5" y="13" font-size="4" font-weight="bold" fill="black" text-anchor="middle" dominant-baseline="middle">R</text>
        <text x="7.5" y="18" font-size="4" font-weight="bold" fill="black" text-anchor="middle" dominant-baseline="middle">D</text>
        
    </svg>
        </div>
        '''
    )
    buttons.append(image_button)
    return buttons



# Connect the button to the editor
gui_hooks.editor_did_init_buttons.append(setup_image_button)

gui_hooks.browser_will_show.append(browser_show)



def create_note_type_if_not_exists():    
    col = mw.col
    models = col.models    
    name = "Crossword (v1.2)"
    if models.by_name(name):
        return

    # Loading HTML and CSS
    base_path = Path(__file__).parent / "note_type"
    front = (base_path / "Crossword_Front_Side.html").read_text(encoding="utf-8")
    back = (base_path / "Crossword_Back_Side.html").read_text(encoding="utf-8")
    styling = (base_path / "Crossword_CSS.css").read_text(encoding="utf-8")

    # замены с учетом языка
    front_vars1 = [f"var z_lang_front0{i:d}" for i in range(6)]  # 00..05
    front_vars2 = [f"var z_lang_front{i:d}" for i in range(1,11)]  # 1..10
    front_vars = front_vars1 + front_vars2 
    for var in front_vars:
        loc = localizationF(var, "---")        
        if loc != "---":
            escaped_loc = loc.replace('"', r'\"') # Экранируем кавычки в заменяемом тексте            
            front = re.sub( fr'({var}\s*=\s*")((?:\\.|[^"\\])*)(";)', fr'\g<1>{escaped_loc}\g<3>', front )  

    back_vars = [f"var z_lang_back{i:d}" for i in range(1,20)]  # 1..19
    for var in back_vars:
        loc = localizationF(var, "---")
        if loc != "---":
            escaped_loc = loc.replace('"', r'\"') # Экранируем кавычки в заменяемом тексте
            back = re.sub( fr'({var}\s*=\s*")((?:\\.|[^"\\])*)(";)', fr'\g<1>{escaped_loc}\g<3>', back )


    model = models.new(name)
    model["type"] = MODEL_STD
    model["sortf"] = 0  # set sortfield to question
    model["css"] = styling

    models.add_field(model, models.new_field("Title"))
    models.add_field(model, models.new_field("word=transcription=translation=example=extranslation"))
    models.add_field(model, models.new_field("Word_hint (file-type ewl)"))
    models.add_field(model, models.new_field("Crossword_code"))
    models.add_field(model, models.new_field("Language_SpeechSynthesis"))
    models.add_field(model, models.new_field("Symbols_for_buttons"))

    # Add template
    template = models.new_template("Card 1")
    template["qfmt"] = front
    template["afmt"] = back
    models.add_template(model, template)
    models.add(model)    

profile_did_open.append(create_note_type_if_not_exists)

