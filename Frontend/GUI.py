from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QStackedWidget, QWidget, QLineEdit, QGridLayout, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QLabel, QSizePolicy

from PyQt5.QtGui import QIcon, QPainter, QMovie, QColor, QTextCharFormat, QFont, QPixmap, QTextBlockFormat

from PyQt5.QtCore import Qt, QSize, QTimer
from dotenv import dotenv_values, load_dotenv
import sys
import os

load_dotenv()
env_vars = dotenv_values(".env")
Assistantname = os.getenv("Assistantname")
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
temp_dir_path = os.path.join(root_dir, 'Frontend', 'Files')
graphics_dir_path = script_dir

print(script_dir)
# print(Assistantname)

def AnswerModifier(Answer):
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    modified_answer = '\n'.join(non_empty_lines)
    return modified_answer

def QueryModifier(Query):
    new_query = Query.lower().strip()
    query_words = new_query.split()
    question_words = ["who","what","when","where","why","how","is","are","do","does","did","can","could","would","should","what's","who's","where's","when's","why's","how's"]
    
    if any(word + " " in new_query for word in question_words):
        if query_words[-1][-1] in ['?', '.', '!']:
            new_query = new_query[:-1] + "?"
        else:
            new_query += "?"
    else:
        if new_query[-1][-1] not in ['.', '!', '?']:
            new_query = new_query[:-1] + "."
        else:
            new_query += " "
    return new_query.capitalize()

def SetMicrophoneStatus(Command):
    with open(os.path.join(temp_dir_path, 'Mic.data'), "w", encoding="utf-8") as file:
        file.write(Command)

def GetMicrophoneStatus():
    with open(os.path.join(temp_dir_path, 'Mic.data'), "r", encoding="utf-8") as file:
        status = file.read()
    return status

def SetAssistantStatus(Status):
    with open(os.path.join(temp_dir_path, 'Status.data'), "w", encoding="utf-8") as file:
        file.write(Status)
    
SetAssistantStatus("Initializing...")
def GetAssistantStatus():
    with open(os.path.join(temp_dir_path, 'Status.data'), "r", encoding="utf-8") as file:
        status = file.read()
    return status

def MicButtonInitialed():
    SetMicrophoneStatus("False")

def MicButtonClosed():
    SetMicrophoneStatus("True")
    
def GraphicDirectoryPath(Filename):
    return os.path.join(graphics_dir_path, Filename)

def TempDirectoryPath(Filename):
    return os.path.join(temp_dir_path, Filename)

def ShowTextToScreen(Text):
    with open(os.path.join(temp_dir_path, 'Response.data'), "w", encoding="utf-8") as file:
        file.write(Text)

class ChatSection(QWidget):
    
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 50, 50, 120)  # Adjusted margins for better spacing
        layout.setSpacing(10)  # Positive spacing for clarity
        self.chat_text_edit = QTextEdit()
        self.chat_text_edit.setReadOnly(True)
        self.chat_text_edit.setTextInteractionFlags(Qt.NoTextInteraction)
        self.chat_text_edit.setFrameStyle(QFrame.NoFrame)
        layout.addWidget(self.chat_text_edit, stretch=1)
        self.setStyleSheet("background-color: #000000;")  # Consistent black background
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        text_color = QColor(Qt.blue)
        text_color_text = QTextCharFormat()
        text_color_text.setForeground(text_color)
        self.chat_text_edit.setCurrentCharFormat(text_color_text)
        self.gif_label = QLabel()
        self.gif_label.setStyleSheet("border: none; background: transparent;")
        movie = QMovie(GraphicDirectoryPath("Jarvis.gif"))
        max_gif_size_w = 480
        max_gif_size_h = 270
        movie.setScaledSize(QSize(max_gif_size_w, max_gif_size_h))
        self.gif_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.gif_label.setMovie(movie)
        movie.start()
        layout.addWidget(self.gif_label, alignment=Qt.AlignRight)
        self.label = QLabel("")
        self.label.setStyleSheet("color: white; font-size: 16px; margin-right: 195px; border: none; margin-top: -20px;")
        self.label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.label, alignment=Qt.AlignRight)
        font = QFont()
        font.setPointSize(13)
        self.chat_text_edit.setFont(font)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.loadMessages)
        self.timer.timeout.connect(self.SpeechRecogText)
        self.timer.start(5)
        self.chat_text_edit.viewport().installEventFilter(self)
        self.setStyleSheet(self.styleSheet() + """
                           QScrollBar:vertical {
                               border: none;
                               background: #000000;
                               width: 10px;
                               margin: 0px 0px 0px 0px;
                           }
                           QScrollBar::handle:vertical {
                               background: #FFFFFF;
                               min-height: 20px;
                           }
                           QScrollBar::add-line:vertical {
                               background: #000000;
                               subcontrol-origin: margin;
                               subcontrol-position: bottom;
                               height: 10px;
                           }
                           QScrollBar::sub-line:vertical {
                               background: #000000;
                               subcontrol-origin: margin;
                               subcontrol-position: top;
                               height: 10px;
                           }
                           QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                               border: none;
                               background: none;
                               color: none;
                           }
                           QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                               background: none;
                           }
                           """)
        
    def loadMessages(self):
        global old_chats_messages
        try:
            with open(TempDirectoryPath("Response.data"), "r", encoding="utf-8") as file:
                new_message = file.read()
        except Exception:
            return
        if not new_message or len(new_message) <= 1:
            return
        if str(old_chats_messages) == str(new_message):
            return
        self.addMessage(new_message=new_message, color="white")
        old_chats_messages = new_message

    def SpeechRecogText(self):
        try:
            with open(TempDirectoryPath("Status.data"), "r", encoding="utf-8") as file:
                messages = file.read()
        except Exception:
            return
        self.label.setText(messages)

    def addMessage(self, new_message, color):
        cursor = self.chat_text_edit.textCursor()
        fmt = QTextCharFormat()
        block_fmt = QTextBlockFormat()
        block_fmt.setTopMargin(10)
        block_fmt.setLeftMargin(10)
        fmt.setForeground(QColor(color))
        cursor.setCharFormat(fmt)
        cursor.setBlockFormat(block_fmt)
        cursor.insertText(new_message + "\n")
        self.chat_text_edit.setTextCursor(cursor)
        self.chat_text_edit.ensureCursorVisible()  # Scroll to bottom for better UX
            
class InitialScreen(QWidget):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        desktop = QApplication.desktop()
        screen_width = desktop.screenGeometry().width()
        screen_height = desktop.screenGeometry().height()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        gif_label = QLabel()
        movie = QMovie(GraphicDirectoryPath("Jarvis.gif"))
        gif_label.setMovie(movie)
        max_gif_size_h = int(screen_width / 16 * 9)
        movie.setScaledSize(QSize(screen_width, max_gif_size_h))
        gif_label.setAlignment(Qt.AlignCenter)
        movie.start()
        gif_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setFixedSize(150, 150)
        self.icon_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.icon_label.setStyleSheet("background: transparent; border: none;")
        self.icon_label.mousePressEvent = self.toggle_icon
        self.toggled = True
        # status label shown above/below the icon
        self.label = QLabel("")
        self.label.setStyleSheet("color: white; font-size: 16px; margin-bottom: 0;")
        self.label.setAlignment(Qt.AlignCenter)
        # initialize icon using the loader (handles missing files)
        self.toggle_icon()
        content_layout.addWidget(gif_label, alignment=Qt.AlignCenter)
        content_layout.addWidget(self.label, alignment=Qt.AlignCenter)
        content_layout.addWidget(self.icon_label, alignment=Qt.AlignCenter)
        content_layout.setContentsMargins(0, 0, 0, 150)
        self.setLayout(content_layout)
        self.setFixedHeight(screen_height)
        self.setFixedWidth(screen_width)
        self.setStyleSheet("background-color: #000000;")
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.SpeechRecogText)
        self.timer.start(5)
        
    def SpeechRecogText(self):
        with open(TempDirectoryPath("Status.data"), "r", encoding="utf-8") as file:
            messages = file.read()
            self.label.setText(messages)
            
    def load_icons(self, path, width=60, height=60):
        pixmap = QPixmap(path)
        if pixmap.isNull():
            placeholder = QPixmap(width, height)
            placeholder.fill(QColor('transparent'))
            self.icon_label.setPixmap(placeholder)
            self.icon_label.setFixedSize(width, height)
            return
        new_pixmap = pixmap.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.icon_label.setPixmap(new_pixmap)
        self.icon_label.setFixedSize(new_pixmap.size())
        

    def toggle_icon(self, event=None):
        if self.toggled:
            self.load_icons(GraphicDirectoryPath("Mic_on.png"), 60, 60)
            MicButtonInitialed()
            
        else:
            self.load_icons(GraphicDirectoryPath("Mic_off.png"), 60, 60)
            MicButtonClosed()
        self.toggled = not self.toggled 
        
class MessageScreen(QWidget):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        desktop = QApplication.desktop()
        screen_width = desktop.screenGeometry().width()
        screen_height = desktop.screenGeometry().height()
        layout = QVBoxLayout()
        label = QLabel("")
        layout.addWidget(label)
        chat_section = ChatSection()
        layout.addWidget(chat_section, stretch=1)
        self.setLayout(layout)
        self.setFixedHeight(screen_height)
        self.setFixedWidth(screen_width)
        self.setStyleSheet("background-color: #000000;")
        
class CustomTopBar(QWidget):
    
    def __init__(self, parent, stacked_widget):
        super().__init__(parent)
        self.initUI()
        self.current_screen = None
        self.stacked_widget = stacked_widget
        
    def initUI(self):
        self.setFixedHeight(50)
        layout = QHBoxLayout(self)
        layout.setAlignment(Qt.AlignRight)
        home_button = QPushButton()
        home_icon = QIcon(GraphicDirectoryPath("Home.png"))
        home_button.setIcon(home_icon)
        home_button.setText(" Home")
        home_button.setStyleSheet("height: 40px; line-height: 40px; background-color: #FFFFFF; color: #000000; border-radius: 5px;")  # Rounded for better look
        message_button = QPushButton()
        message_icon = QIcon(GraphicDirectoryPath("Chats.png"))
        message_button.setIcon(message_icon)
        message_button.setText(" Chat")
        message_button.setStyleSheet("height: 40px; line-height: 40px; background-color: #FFFFFF; color: #000000; border-radius: 5px;")
        minimize_button = QPushButton()
        minimize_icon = QIcon(GraphicDirectoryPath("Minimize2.png"))
        minimize_button.setIcon(minimize_icon)
        minimize_button.setStyleSheet("background-color: #FFFFFF; border-radius: 5px;")
        self.maximize_button = QPushButton()
        
        self.maximize_icon = QIcon(GraphicDirectoryPath("Maximize.png"))
        self.restore_icon = QIcon(GraphicDirectoryPath("Minimize.png"))
        self.maximize_button.setIcon(self.maximize_icon)
        self.maximize_button.setFlat(True)
        self.maximize_button.setStyleSheet("background-color: #FFFFFF; border-radius: 5px;")
        self.maximize_button.clicked.connect(self.maximizeWindow)
        close_button = QPushButton()
        close_icon = QIcon(GraphicDirectoryPath("Close.png"))
        close_button.setIcon(close_icon)
        close_button.setStyleSheet("background-color: #FFFFFF; border-radius: 5px;")
        close_button.clicked.connect(self.closeWindow)
        line_frame = QFrame()
        line_frame.setFixedHeight(1)
        line_frame.setFrameShape(QFrame.HLine)
        
        line_frame.setFrameShadow(QFrame.Sunken)
        line_frame.setStyleSheet("border-color: #000000;")
        title_label = QLabel(f"{str(Assistantname).capitalize()} AI   ")
        title_label.setStyleSheet("font-size: 18px; color: #000000; font-weight: bold; background-color: #FFFFFF;")
        home_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        message_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        layout.addWidget(title_label)
        layout.addStretch(1)
        layout.addWidget(home_button)
        layout.addWidget(message_button)
        layout.addStretch(1)
        layout.addWidget(minimize_button)
        layout.addWidget(self.maximize_button)
        layout.addWidget(close_button)
        layout.addWidget(line_frame)
        self.draggable = True
        self.offset = None
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(Qt.white))
        super().paintEvent(event)
        
    def minimizeWindow(self):
        self.parent().showMinimized()
        
    def maximizeWindow(self):
        if self.parent().isMaximized():
            self.parent().showNormal()
            self.maximize_button.setIcon(self.maximize_icon)
        else:
            self.parent().showMaximized()
            self.maximize_button.setIcon(self.restore_icon)
            
    def closeWindow(self):
        self.parent().close()
        
    def mousePressEvent(self, event):
        if self.draggable:
            self.offset = event.pos()
            
    def mouseMoveEvent(self, event):
        if self.draggable and self.offset:
            new_pos = event.globalPos() - self.offset
            self.parent().move(new_pos)

    def ShowMessageScreen(self):
        if self.current_screen is not None:
            self.current_screen.hide()
            
        message_screen = MessageScreen(self)
        layout = self.parent().layout()
        if layout is not None:
            layout.addWidget(message_screen)
        self.current_screen = message_screen
        
    def showInitialScreen(self):
        if self.current_screen is not None:
            self.current_screen.hide()
            
        initial_screen = InitialScreen(self)
        layout = self.parent().layout()
        if layout is not None:
            layout.addWidget(initial_screen)
        self.current_screen = initial_screen
        
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.initUI()
        
    def initUI(self):
        desktop = QApplication.desktop()
        screen_width = desktop.screenGeometry().width()
        screen_height = desktop.screenGeometry().height()
        stacked_widget = QStackedWidget(self)
        initial_screen = InitialScreen()
        message_screen = MessageScreen()
        stacked_widget.addWidget(initial_screen)
        stacked_widget.addWidget(message_screen)
        self.setGeometry(0, 0, screen_width, screen_height)
        self.setStyleSheet("background-color: #000000;")
        top_bar = CustomTopBar(self, stacked_widget)
        self.setMenuWidget(top_bar)
        self.setCentralWidget(stacked_widget)
        
def GraphicalUserInterface():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

old_chats_messages = ""

if __name__ == "__main__":
    GraphicalUserInterface()