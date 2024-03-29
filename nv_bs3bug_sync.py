from dataclasses import field
from gettext import find

import os, sys
import os.path
from PyQt5.QtWidgets import QApplication


from _src._api import logger, logging_message, config
from _src import bs3_sync_ui, bs3_sync



logging= logger.logger
logging_file_name = logger.log_full_name

config_path = os.path.join('static','config','config.json')
message_path =config.load_config(config_path)['message_path']

config_data = config.load_config(config_path)
version = 'nv bs3 bug sync v1.1'

revision_list=[
    'Revision list',
    'v1.0 (2022-11-18) : initial release',
    'v1.1 (2023-02-01) : disable button during sync',
    '                    change logs on UI',
    'v2.0 (2023-06-26) : modify for each project',
    '==============================================================================='
    ]


def debug_app():
    user = config_data['id']
    password = config_data['password']
    query = '--1'
    def test2():
        bs3_sync.sync_attachment(user,password,query)
        return 0
    test2()
    

def start_app():
    user = config_data['id']
    #os.system('color 0A') if user != 'miskang' else None
    #os.system('mode con cols=70 lines=5') if user != 'miskang' else None
    if os.path.isfile(message_path):
        logging_message.remove_message(message_path)
    for revision in revision_list:
        logging_message.input_message(path = message_path,message = revision, settime= False)
    app = QApplication(sys.argv)
    ex = bs3_sync_ui.MyMainWindow(version)
    sys.exit(app.exec_())

if __name__ =='__main__':
    try:
        debug_app()
    except Exception as E:
        logging_message.input_message(path = message_path,message = version)


