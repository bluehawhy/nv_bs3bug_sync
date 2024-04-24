#!/usr/bin/python
import os
import sys
import threading
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget
from PyQt5.QtWidgets import QLabel, QLineEdit, QPushButton, QGridLayout, QMessageBox, QTextBrowser, QComboBox
from PyQt5.QtCore import pyqtSlot, QTimer, QTime

from PyQt5.QtGui import QTextCursor



#add internal libary
from _src import bs3_sync


refer_api = "local"
#refer_api = "global"

if refer_api == "global":
    sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))))
    from _api import loggas, configus, zyra
if refer_api == "local":
    from _src._api import loggas, configus, zyra



logging = loggas.logger
logging_file_name = loggas.log_full_name


#set config
config_path = os.path.join('static','config','config.json')
qss_path = os.path.join('static','css','style.qss')
bs3_config_path = os.path.join('static','config','bs3_sync_config.json')

message_path = configus.load_config(config_path)['message_path']

class MyMainWindow(QMainWindow):
    def __init__(self, title):
        super().__init__()
        self.title = title
        logging.debug('qss_path is %s' %qss_path)
        self.setStyleSheet(open(qss_path, "r").read())
        #self.setWindowFlags(Qt.FramelessWindowHint)
        self.initUI()
        self.show()

    def initUI(self):
        self.statusBar().showMessage('Ready')
        self.setWindowTitle(self.title)
        self.setGeometry(200, 200, 600, 480)
        #self.setFixedSize(600, 480)
        self.form_widget = FormWidget(self,self.statusBar(),self.title)
        self.setCentralWidget(self.form_widget)


class FormWidget(QWidget):
    def __init__(self, parent, statusbar,title):
        super(FormWidget, self).__init__(parent)
        self.user = ''
        self.statusbar_status = 'not logged in'
        self.session = None
        self.session_info = None
        self.logging_temp = None
        self.title = title
        self.statusbar = statusbar
        self.status_sync = None
        self.initUI() 
        self.show()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.thread_ui)
        self.timer.start(1000)

    def initUI(self):
        config_data = configus.load_config(config_path)
        bs3_config_data = configus.load_config(bs3_config_path)
        self.setStyleSheet(open(qss_path, "r").read())
        # make layout
        self.layout_main = QVBoxLayout(self)

        #menu layout
        self.menu_layout = QHBoxLayout(self)
        self.qlabel_title = QLabel(self.title)
        self.menu_layout.addWidget(self.qlabel_title)

        self.menu_button_layout = QHBoxLayout(self)
        self.quit_button = QPushButton('X')
        self.quit_button.setFixedSize(30,30)
        self.menu_button_layout.addWidget(self.quit_button)
        self.menu_layout.addLayout(self.menu_button_layout)
        #self.layout_main.addLayout(self.menu_layout)

        # login page layout
        self.login_layout = QHBoxLayout(self)
        self.login_layout_id_pw = QGridLayout(self)
        #set user data
        self.user = config_data['id']
        self.password = config_data['password']
        self.line_id = QLineEdit(self.user)
        self.line_password = QLineEdit(self.password)
        self.line_password.setEchoMode(QLineEdit.Password)
        self.login_import_button = QPushButton('Log In')
        self.login_layout_id_pw.addWidget(QLabel('ID') , 1, 0)
        self.login_layout_id_pw.addWidget(QLabel('Password') , 2, 0)
        self.login_layout_id_pw.addWidget(self.line_id, 1, 2)
        self.login_layout_id_pw.addWidget(self.line_password, 2, 2)
        self.login_layout.addLayout(self.login_layout_id_pw)
        self.login_layout.addWidget(self.login_import_button)
        self.layout_main.addLayout(self.login_layout)
        
        # add query layout
        self.layout_query = QHBoxLayout(self)
        self.qlabel_query = QLabel('Query : ')
        self.query = bs3_config_data['last_query']
        self.line_query = QLineEdit(self.query)
        self.line_query.setReadOnly(1)
        self.layout_query.addWidget(self.qlabel_query)
        self.layout_query.addWidget(self.line_query)
        self.layout_main.addLayout(self.layout_query)

        # add sync layout
        self.status_sync = bs3_config_data['file_sync']
        self.layout_sync = QHBoxLayout(self)
        self.qlabel_sync = QLabel('File Sync : ')
        self.combo_sync = QComboBox()
        self.combo_sync.addItems(['True','False'])
        self.combo_sync.setCurrentText(bs3_config_data['file_sync'])
        self.layout_query.addWidget(self.qlabel_sync)
        self.layout_query.addWidget(self.combo_sync)
        self.layout_main.addLayout(self.layout_sync)

        self.combo_sync.currentIndexChanged.connect(self.sync_status)
        
        # add log layout
        self.qtext_log_browser = QTextBrowser()
        self.qtext_log_browser.setReadOnly(1)
        self.layout_main.addWidget(self.qtext_log_browser)

        #set layout
        self.setLayout(self.layout_main)

        #login / import event
        self.login_import_button.clicked.connect(self.on_start)
        self.line_password.returnPressed.connect(self.on_start)


    def sync_status(self):
        bs3_config_data = configus.load_config(bs3_config_path)
        #logging.info(self.combo_sync.currentText())
        bs3_config_data['file_sync'] = self.combo_sync.currentText()
        bs3_config_data = configus.save_config(bs3_config_data,bs3_config_path)

    @pyqtSlot()
    def on_start(self):
        def try_login():
            config_data = configus.load_config(config_path)
            self.user = self.line_id.text()
            self.password = self.line_password.text()
            self.session,self.session_info, self.status_login = zyra.initsession(self.user, self.password, config_data['jira_url'])
            #fail to login
            if self.status_login is False:
                loggas.input_message(path = message_path,message = "Login Fail")
                loggas.input_message(path = message_path,message = "please check your id and password or check internet connection")
                QMessageBox.about(self, "Login Fail", "please check your id and password or check internet connection")
            #if loggin success
            else:
                self.login_import_button.setText('Jira\nSync')
                self.statusbar_status = 'logged in'
                loggas.input_message(path = message_path,message = 'login succeed, please start to attach files~!')
                config_data['id'] = self.user
                config_data['password'] = self.password
                config_data = configus.save_config(config_data,config_path)
                self.line_id.setReadOnly(1)
                self.line_password.setReadOnly(1)
                self.line_query.setReadOnly(0)
            return 0
            
        def bs3_syncment_start():
            bs3_config_data = configus.load_config(bs3_config_path)
            self.login_import_button.setEnabled(False)
            self.statusbar_status = 'bs sync~'
            self.query = self.line_query.text()
            loggas.input_message(path = message_path,message = 'start bs sync~')
            loggas.input_message(path = message_path,message = 'query is %s' %self.query)
            bs3_sync.sync_bs3bug(self.user,self.password,self.query)
            #save query 
            bs3_config_data['last_query'] = self.query
            bs3_config_data = configus.save_config(bs3_config_data,bs3_config_path)
            loggas.input_message(path = message_path,message = 'bs sync done~')
            self.login_import_button.setEnabled(True)
            self.statusbar_status = 'logged in'
            return 0

        if self.statusbar_status == 'not logged in':
            try_login()
        else:
            if self.query == '':
                loggas.input_message(path = message_path,message = 'query is empty, please checek query')
            else:
                thread_import = threading.Thread(target=bs3_syncment_start)
                thread_import.start()


    #set tread to change status bar and log browser
    def thread_ui(self):
        def show_time_statusbar():
            self.statusbar_time = QTime.currentTime().toString("hh:mm:ss")
            self.statusbar_message = self.statusbar_time + '\t-\t' + self.statusbar_status  
            self.statusbar.showMessage(str(self.statusbar_message))
          
        def show_logging():
            with open(message_path, 'r') as myfile:
                self.output = myfile.read()
            if self.logging_temp == self.output:
                pass
            else:
                self.qtext_log_browser.setText(self.output)
                self.logging_temp = self.output
                self.qtext_log_browser.moveCursor(QTextCursor.End)
        show_time_statusbar()
        show_logging()
      

        
