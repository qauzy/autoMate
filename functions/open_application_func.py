import subprocess

from PyQt6.QtWidgets import QHBoxLayout, QLineEdit, QLabel, QWidget

from functions.function_base import FunctionBase
from utils.qt_util import QtUtil


class OpenApplicationFunc(FunctionBase):
    name = "打开应用"
    description = "打开指定目录的应用"
    uni_tag = "open_application"

    # 打开指定目录的应用
    def run(self, path):
        subprocess.Popen(path)

    def config_page_ui(self):
        self.config_ui = QtUtil.load_ui("config_page.ui")
        # 水平布局
        h_box_layout = QHBoxLayout()
        label = QLabel(self.config_ui)
        label.setText("路径")
        line_edit = QLineEdit(self.config_ui)
        h_box_layout.addWidget(label)
        h_box_layout.addWidget(line_edit)
        container_widget = QWidget(self.config_ui)
        container_widget.setLayout(h_box_layout)
        self.config_ui.config_list.addWidget(container_widget)
