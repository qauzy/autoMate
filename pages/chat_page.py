import traceback
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QEvent
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QMainWindow, QLabel, QTextEdit, QListWidgetItem, QSpacerItem, QSizePolicy, QAbstractItemView, QListWidget
from actions.action_util import ActionUtil
from agent.woker_agent import WorkerAgent
from pages.config_page import ConfigPage
from utils.qt_util import QtUtil

class ActionItems(QListWidgetItem):
    def __init__(self, action):
        super().__init__()
        self.action = action
        # 创建一个 QLabel 作为列表项的小部件
        self.label = QLabel()
        text = f"<p style='font-size:15px;color:blue;margin-bottom:0;'>{self.action.name}</p><p style='font-size:11px;color:gray;margin-top:0;'>{self.action.description}</p>"
        self.label.setText(text)
        self.setSizeHint(self.label.sizeHint())



class ActionList(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVisible(False)
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        actions = ActionUtil.get_funcs()
        self.setSpacing(3)
        for i in range(len(actions)):
            action = actions[i]
            item = ActionItems(action(args={}))
            self.insertItem(i, item)
            self.setItemWidget(item, item.label)

    def mousePressEvent(self, event):
        super(QListWidget, self).mousePressEvent(event)
        # 获取双击的项
        item = self.itemAt(event.pos())
        if item:
            item.action.config_page_show()
        event.accept()
    
    def set_visibility(self, visible: bool):
        self.setVisible(visible)
        

class ChatList(QListWidget):
    def __init__(self, parent=None, chat_page=None):
        super().__init__(parent)
        self.chat_page = chat_page
        self.setGeometry(QtCore.QRect(40, 0, 561, 571))
        self.setObjectName("chat_list")
        # 设置 QListWidget 的背景为透明
        self.setStyleSheet("""background: transparent;border: none;""")
        # 设置 QListWidget 的选择模式为 NoSelection
        self.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        # 设置 QListWidget 的焦点策略为 NoFocus
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        # 隐藏垂直滚动条
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # 隐藏水平滚动条
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def mousePressEvent(self, event):
        self.chat_page.action_list.set_visibility(False)

class WorkerThread(QThread):
    finished_signal = pyqtSignal(str)

    def __init__(self, text, chat_page):
        QThread.__init__(self)
        self.text = text
        self.chat_page = chat_page

    def run(self):
        try:
            agent_iter = WorkerAgent().get_iter(self.text)
            for step in agent_iter:
                content = ""
                if output := step.get("intermediate_step"):
                    action, value = output[0]
                    content = f"{action.tool} \n{value}"
                elif step.get("output"):
                    content = step["output"]
                content = content.replace("```", "")
                self.finished_signal.emit(content)
        except Exception as e:
            traceback.print_exc(e)


class ChatInput(QTextEdit):
    def __init__(self, parent=None, chat_page=None):
        super().__init__(parent)
        self.worker_thread = None
        self.chat_page = chat_page
        self.textChanged.connect(self.on_text_changed)
        self.previous_text = ""
        self.setFixedWidth(560)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return:
            self.chat_page.new_conversation(f"{self.toPlainText()}", "user")
            self.worker_thread = WorkerThread(self.toPlainText(), self.chat_page)
            # 清空输入框
            self.clear()
            # 连接线程的 finished 信号到槽函数，增加对话UI
            self.worker_thread.finished_signal.connect(lambda res: self.chat_page.new_conversation(f"{res}", "system"))
            self.worker_thread.start()
            event.accept()
        else:
            super().keyPressEvent(event)

    def on_text_changed(self):
        current_text = self.toPlainText()
        # 当输入中文不选择具体的文字时，也会进入到这里
        if self.previous_text == current_text:
            return
        
        if current_text == "/":
            self.chat_page.action_list.set_visibility(True)
        elif current_text.startswith("/") and self.chat_page.action_list.isVisible():
            current_text_without_slash = current_text[1:]
            self.chat_page.action_list.addItem(current_text_without_slash)
        self.previous_text = current_text
    
    def mousePressEvent(self, event):
        self.chat_page.action_list.set_visibility(False)

    # 窗口激活时，将输入框的焦点设置到这里
    def event(self, event):
        if event.type() == QEvent.Type.WindowActivate:
            self.setFocus()
            return True
        # Return the object and event.
        return super().event(event)

interface_ui = QtUtil.load_ui_type("chat_page.ui")
class ChatPage(QMainWindow, interface_ui):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setting_page = None
        self.action_list = None
        self.setup_up()
        self.new_conversation(
            "<b>你好，我叫智子，你的智能Agent助手！</b><br><br>你可以输入“/”搜索行为，有什么要求可以随时吩咐！",
            "system"
        )

    def setup_up(self):
        # self = QtUtil.load_ui("chat_page.ui")
        chat_input = ChatInput(parent=self.centralwidget, chat_page=self)
        chat_input.setGeometry(QtCore.QRect(40, 580, 601, 51))
        chat_input.setStyleSheet("border-radius: 30px")
        chat_input.setObjectName("chat_input")
        chat_input.setPlaceholderText("请输入“/”，选择运行的指令")
        
        self.chat_list = ChatList(parent=self.centralwidget, chat_page=self)
        self.action_list = ActionList(parent=self.centralwidget)
        self.action_list.setGeometry(QtCore.QRect(40, 390, 251, 181))
        self.action_list.setStyleSheet("border: none;")
        self.action_list.setObjectName("action_list")
        setting_action = self.setting_action
        setting_action.triggered.connect(self.open_setting_page)
        # 添加按钮点击事件，打开添加对话框
        # self.add_action.clicked.connect(self.open_add_dialog)


    def open_setting_page(self):
        self.setting_page = ConfigPage()
        self.setting_page.show()

    def mousePressEvent(self, event):
        self.action_list.setVisible(False)

    def new_conversation(self, text, role):
        text = text.replace("\n", "<br>")
        widget = QtWidgets.QWidget()
        widget.setGeometry(QtCore.QRect(110, 100, 160, 80))
        v_box = QtWidgets.QVBoxLayout(widget)
        h_box = QtWidgets.QHBoxLayout()
        if role == "system":
            role_pic = QtUtil.get_icon("logo.png")
            role_name = "智子"
        else:
            role_pic = QtUtil.get_icon("vip.png")
            role_name = "VIP用户"
        # 创建 QPixmap 对象并加载图片
        pixmap = QPixmap(role_pic)
        pixmap = pixmap.scaled(30, 30, QtCore.Qt.AspectRatioMode.KeepAspectRatio)
        # 创建 QLabel 对象并设置其 pixmap
        image_label = QLabel()
        image_label.setPixmap(pixmap)
        # 将 QLabel 对象添加到布局中
        h_box.addWidget(image_label)
        label = QLabel()
        label.setText(role_name)
        # 将 QLabel 对象添加到布局中
        h_box.addWidget(label)
        # 占位符
        spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        h_box.addItem(spacer)
        # 设置每个子元素所占的比例
        h_box.setStretch(0, 1)
        h_box.setStretch(1, 1)
        h_box.setStretch(2, 10)
        # 创建 QTextEdit 对象并设置其文本
        text_edit = QTextEdit(parent=widget)
        text_edit.setReadOnly(True)
        v_box.addLayout(h_box)
        # 设置 QTextEdit 的背景为白色，边角为椭圆
        text_edit.setStyleSheet("""
                   background-color: white;
                   border-radius: 10px;
               """)
        text_edit.setHtml(text)
        v_box.addWidget(text_edit)
        item = QListWidgetItem()
        # 连接文档大小改变的信号
        text_edit.document().documentLayout().documentSizeChanged.connect(
            lambda: self.update_size(widget, item, text_edit))
        # 将 item 添加到 QListWidget
        self.chat_list.insertItem(self.chat_list.count(), item)
        self.chat_list.setItemWidget(item, widget)

    @staticmethod
    def update_size(widget, item, text_edit):
        # 获取 QTextEdit 的文档的大小
        doc_size = text_edit.document().size().toSize()
        # 设置 widget、v_box 和 item 的大小
        widget.setFixedHeight(doc_size.height() + 60)
        item.setSizeHint(widget.size())
