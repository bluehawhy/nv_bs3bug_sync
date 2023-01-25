import sys
import datetime
from PyQt5.QtWidgets import *


from _src._api import  config, jira_rest, license_key


config_path ='static\config\config.json'
config_data =config.load_config(config_path)
message_path = config_data['message_path']
qss_path  = config_data['qss_path']




class MyMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(open(qss_path, "r").read())
        self.initUI()
        self.show()
        msg = QMessageBox()
        msg.setWindowTitle('Login - update license')
        msg.setGeometry(300,300,400,200)
        msg.setText('license is invaild so please login again')
        msg.exec_()

    def initUI(self):
        self.statusBar().showMessage('')
        self.setWindowTitle('Login - update license')
        self.setGeometry(300,300,400,200)
        #self.setFixedSize(600, 480)
        self.LoginForm = LoginForm(self)
        self.setCentralWidget(self.LoginForm)

class LoginForm(QWidget):
    def __init__(self, parent):
        super(LoginForm, self).__init__(parent)
        layout = QGridLayout()
        
        user = config_data['id']
        label_name = QLabel('Username')
        self.line_id = QLineEdit(user)
        self.line_id.setPlaceholderText('Please enter your username')
        layout.addWidget(label_name, 0, 0)
        layout.addWidget(self.line_id, 0, 1)

        password = config_data['password'] 
        label_password = QLabel('Password')
        self.line_password = QLineEdit(password)
        self.line_password.setPlaceholderText('Please enter your password')
        self.line_password.setEchoMode(QLineEdit.Password)
        layout.addWidget(label_password, 1, 0)
        layout.addWidget(self.line_password, 1, 1)

        self.button_login = QPushButton('Login')
        self.button_login.clicked.connect(self.make_license)
        layout.addWidget(self.button_login, 2, 0, 1, 2)
        layout.setRowMinimumHeight(2, 75)

        self.setLayout(layout)

    def make_license(self):
        msg = QMessageBox()
        self.user = self.line_id.text()
        self.password = self.line_password.text()
        self.session_list = jira_rest.initsession(self.user, self.password)
        self.session = self.session_list[0]
        self.session_info = self.session_list[1]
        #fail to login
        if self.session_info == None:
            QMessageBox.about(self, "Login Fail", "please check your password or internet connection")
        #if loggin success
        else:
            QMessageBox.about(self, "Login success", "please close the window and restart again")
            config_data['id'] = self.user
            config_data['password'] = self.password
            config.save_config(config_data,config_path)
            self.line_id.setReadOnly(1)
            self.line_password.setReadOnly(1)
            self.button_login.setEnabled(False)
            #create license
            license_for_day_100 = datetime.date.today() + datetime.timedelta(days=100)
            licen_raw = self.user+"_"+ license_for_day_100.strftime("%Y%m%d")
            license_key.createLicense(licen_raw)
        return 0
            

if __name__ == '__main__':
    app = QApplication(sys.argv)
    form = LoginForm()
    form.show()
    
    sys.exit(app.exec_())