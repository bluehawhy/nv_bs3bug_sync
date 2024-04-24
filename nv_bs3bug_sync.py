from dataclasses import field
from gettext import find

import os, sys
import os.path
from PyQt5.QtWidgets import QApplication


#add internal libary
from _src import bs3_sync_ui, bs3_sync


refer_api = "local"
#refer_api = "global"

if refer_api == "global":
    sys.path.append((os.path.dirname(os.path.abspath(os.path.dirname(__file__)))))
    from _api import loggas, configus
if refer_api == "local":
    from _src._api import loggas, configus



logging= loggas.logger
config_path = os.path.join('static','config','config.json')
bs3_config_path = os.path.join('static','config','bs3_sync_config.json')
message_path =configus.load_config(config_path)['message_path']

config_data = configus.load_config(config_path)
bs3_config_data = configus.load_config(bs3_config_path)

version = 'nv bs3 bug sync v2.1'

revision_list=[
    'Revision list',
    'v1.0 (2022-11-18) : initial release',
    'v1.1 (2023-02-01) : disable button during sync',
    '                    change logs on UI',
    'v2.0 (2023-06-26) : modify for each project',
    'v2.1 (2023-02-15) : enable / disable file upload',
    '==============================================================================='
    ]


def debug_app():
    user = config_data['id']
    password = config_data['password']
    query = bs3_config_data['last_query']
    bs3_sync.sync_bs3bug(user,password,query)
    return 0
    

def start_app():
    if os.path.isfile(message_path):
        loggas.remove_message(message_path)
    for revision in revision_list:
        loggas.input_message(path = message_path,message = revision, settime= False)
    app = QApplication(sys.argv)
    ex = bs3_sync_ui.MyMainWindow(version)
    sys.exit(app.exec_())

if __name__ =='__main__':
    try:
        start_app()
    except Exception as E:
        logging.critical(E)
        loggas.input_message(path = message_path,message = E)


