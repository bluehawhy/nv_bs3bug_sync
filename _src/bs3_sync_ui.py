#!/usr/bin/python
import os
import sys
import time
import threading
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget
from PyQt5.QtWidgets import QLabel, QLineEdit, QPushButton, QGridLayout, QPlainTextEdit, QFileDialog, QMessageBox, QTextBrowser
from PyQt5.QtCore import pyqtSlot, QTimer, QTime

from PyQt5.QtGui import QTextCursor
from datetime import date


from _src._api import filepath, logger, jira_rest, config, logging_message
from _src import bs3_sync

logging = logger.logger
logging_file_name = logger.log_full_name


#set config

config_path = os.path.join('static','config','config.json')
qss_path = os.path.join('static','css','style.qss')
config_data =config.load_config(config_path)
message_path = config_data['message_path']

class MyMainWindow(QMainWindow):
    def __init__(self, title):
        super().__init__()
        self.title = title
        logging.debug('qss_path is %s' %qss_path)
        self.setStyleSheet(open(qss_path, "r").read())
        self.initUI()
        self.show()

    def initUI(self):
        self.statusBar().showMessage('Ready')
        self.setWindowTitle(self.title)
        self.setGeometry(200, 200, 1200,600)
        #self.setFixedSize(600, 480)
        self.form_widget = FormWidget(self,self.statusBar())
        self.setCentralWidget(self.form_widget)


class FormWidget(QWidget):
    def __init__(self, parent, statusbar):
        super(FormWidget, self).__init__(parent)
        self.user = ''
        self.statusbar_status = 'not logged in'
        self.session_info = None
        self.logging_temp = None
        self.statusbar = statusbar
        self.initUI() 
        self.show()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.thread_ui)
        self.timer.start(1000)

    def initUI(self):
        self.setStyleSheet(open(qss_path, "r").read())
        # make layout
        self.layout_main = QVBoxLayout(self)
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
        self.query = config_data['last_query']
        self.line_query = QLineEdit(self.query)
        self.line_query.setReadOnly(1)
        self.layout_query.addWidget(self.qlabel_query)
        self.layout_query.addWidget(self.line_query)
        self.layout_main.addLayout(self.layout_query)
        
        # add log layout
        self.qtext_log_browser = QTextBrowser()
        self.qtext_log_browser.setReadOnly(1)
        self.layout_main.addWidget(self.qtext_log_browser)



        #set layout
        self.setLayout(self.layout_main)

        #login / import event
        self.login_import_button.clicked.connect(self.on_start)
        self.line_password.returnPressed.connect(self.on_start)
    
    @pyqtSlot()
    def on_start(self):
        if self.statusbar_status == 'not logged in':
            self.user = self.line_id.text()
            self.password = self.line_password.text()
            logging_message.input_message(path = message_path,message = 'user: %s password: %s' %(self.user,'self.password'))
            self.session_list = jira_rest.initsession(self.user, self.password)
            self.session = self.session_list[0]
            self.session_info = self.session_list[1]
            #fail to login
            if self.session_info == None:
                logging_message.input_message(path = message_path,message = "Login Fail")
                logging_message.input_message(path = message_path,message = "please check your id and password or check internet connection")
                QMessageBox.about(self, "Login Fail", "please check your id and password or check internet connection")
            #if loggin success
            else:
                self.login_import_button.setText('Jira\nSync')
                self.statusbar_status = 'logged in'
                logging_message.input_message(path = message_path,message = 'login succeed, please start to attach files~!')
                logging_message.input_message(path = message_path,message = 'user: %s password: %s' %(self.user,'self.password'))
                config_data['id'] = self.user
                config_data['password'] = self.password
                config.save_config(config_data,config_path)
                self.line_id.setReadOnly(1)
                self.line_password.setReadOnly(1)
                self.line_query.setReadOnly(0)
        else:
            
            def bs3_syncment_start():
                self.statusbar_status = 'start file attachemnt~'
                self.query = self.line_query.text()
                logging_message.input_message(path = message_path,message = 'start file attachemnt~')
                logging_message.input_message(path = message_path,message = 'query is %s' %self.query)
                bs3_sync.sync_attachment(self.user,self.password,self.query)
                #save query 
                config_data['last_query'] = self.query
                config.save_config(config_data,config_path)
                return 0
            if self.query == '':
                logging_message.input_message(path = message_path,message = 'query is empty, please checek query')
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
      

        
