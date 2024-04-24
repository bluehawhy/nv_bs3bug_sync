# it is for uploading files (such as video and picture) from link and BS3
# 1. check directory in jira
#  - link, dir path
# 2. get list from directory
# 3. uploading files to jira (like sync)
#  - if exist -> skip
# author: miskang@navis-ams.com

import os, re, sys
import shutil

refer_api = "local"
#refer_api = "global"

if refer_api == "global":
    sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))))
    from _api import loggas, configus, zyra
if refer_api == "local":
    from _src._api import loggas, configus, zyra


logging = loggas.logger

logging= loggas.logger
config_path = os.path.join('static','config','config.json')
bs3_config_path = os.path.join('static','config','bs3_sync_config.json')
message_path =configus.load_config(config_path)['message_path']

config_data = configus.load_config(config_path)
bs3_config_data = configus.load_config(bs3_config_path)


# =====================================================================================================
# this is file copy from navis server ans sync to jira
# =====================================================================================================

def ignore_file_list(file = None , ignore_list = None):
    result = False
    ignore_list = [x.lower() for x in ignore_list]
    file_extension = str(os.path.splitext(file)[1]).replace('.','').lower()
    if file_extension in ignore_list:
        result = True    
    return result

def download_files_from_server(server_path = None, local_path = None, ignore_list= None):
    return_files = []
    #renew local folder
    try:
        shutil.rmtree(local_path) if os.path.exists(local_path) else logging.debug('no local folder')
        os.makedirs(local_path)
    except Exception as E:
        logging.critical(E)
        pass
    
    # =====================================================================================================
    #download from server
    # =====================================================================================================
    # check file list in server
    file_list = os.listdir(server_path) if os.path.exists(server_path) else []
    logging.debug(f'flie list - {str(file_list)}')
    logging.debug(f'ignore list - {ignore_list}')
    # ignore files 
    for file in file_list:
        logging.info(f'{file} - {ignore_file_list(file = file, ignore_list =ignore_list)}')
    file_list = [file for file in file_list if ignore_file_list(file = file, ignore_list =ignore_list) is False]

    logging.debug('modified files in server : %s' %str(file_list))
    
    for file in file_list:
        file_path = os.path.join(server_path,file)
        #check file size
        file_size = os.path.getsize(file_path)
        logging.debug('%s size : %d' %(file,file_size))
        #check dir or file
        if not os.path.isdir(file_path):
            if file_size <= 200000000:
                #copy file
                shutil.copy2(file_path,local_path)
                #add file list
                return_files.append(file_path)
    return return_files

def upload_files_into_jira(zyra_handler,key,local_file_list,local_path):
    # =====================================================================================================
    #upload file to jira
    # =====================================================================================================
    local_file_list = os.listdir(local_path)
    uploaded_file_list = zyra_handler.get_attachment(key)
    logging.debug("update file list in local : %s" %str(local_file_list))
    logging.debug("updated file list in jira : %s" %str(uploaded_file_list))
    #loggas.input_message(path = message_path,message = 'update file list in local : %s'  %str(file_list))
    #loggas.input_message(path = message_path,message = 'updated file list in jira : %s'  %str(uploaded_file_list))
    #logging.debug('upload file - %s' %tmp_path)
    
    for file in local_file_list:
        logging.debug('upload file - %s' %file)
        file_path = os.path.join(local_path,file)
        if file in uploaded_file_list:
            logging.debug('it already uploaded - %s' %file)
            #loggas.input_message(path = message_path,message = 'it already uploaded - %s' %file)
        else:
            logging.debug('start upload - %s' %file)
            #loggas.input_message(path = message_path,message = 'start upload - %s' %file) 
            upload_attachment_result = zyra_handler.upload_attachment(key,file_path)
            logging.debug(upload_attachment_result)
    return 0

# =====================================================================================================
def sync_file_server_jira(zyra_handler,key,file_sync_info):
    bs3_path = file_sync_info['bs3_path']
    tmp_path = file_sync_info['tmp_path']
    ignore_list = file_sync_info['ignore_list']
    loggas.input_message(path = message_path,message = '== start upload file ==')
    logging.debug('== start upload file ==')
    dante_id = zyra_handler.searchIssueByKey(key)['fields']['customfield_12304']
    server_path = os.path.join(bs3_path,dante_id)
    loggas.input_message(path = message_path,message = f'start download from server')
    logging.debug(f'start download from server - {server_path}')
    local_file_list = download_files_from_server(server_path = server_path, local_path = tmp_path, ignore_list= ignore_list)
    loggas.input_message(path = message_path,message = f'download done!')
    logging.debug(f'download done!')
    upload_files_into_jira(zyra_handler,key,local_file_list,local_path = tmp_path)
    loggas.input_message(path = message_path,message = '== upload done ==')
    logging.debug('== upload done ==')
# =====================================================================================================


# =====================================================================================================
# this is find field and labels in ticket
# =====================================================================================================
def search_reg_value(search_key = None, search_value = None, summary = None, description = None):
    #logging.info(f'search_value - {search_value}')
    #logging.info(f'description - {description}')
    find_value = None
    find_text = None
    
    #logging.info(search_value['search_reg'].lower())
    searching_reg_results = re.findall(search_value['search_reg'].lower(),summary.lower()+'\n'+description.replace('\r\n','\n').lower())
    text = 'None' if not searching_reg_results else ','.join(searching_reg_results)
    #logging.info(text)
    search_keys = search_value['search_keys']
    for seach_key in search_keys:
        #logging.info(f're.search({seach_key},str(searching_reg_result))')
        find_result = re.search(seach_key.lower(),text)
        if find_result is not None:
            #logging.info(find_result.group(0))
            find_value = search_keys[seach_key]
            find_text = find_result.group(0)
            break
    #logging.info(f'find_text - {find_text}')
    #logging.info(f'find_value - {find_value}')
    return find_value

# =====================================================================================================
def upload_label_field(zyra_handler,key):
    logging.debug('this is key %s' %key)
    ticket_info = zyra_handler.searchIssueByKey(key)
    summary = ticket_info['fields']['summary']
    description = ticket_info['fields']['description']
    #find project
    field_label_sync = bs3_config_data['project'][str(key).split("-")[0]]['field_label_sync']
    search_fields = field_label_sync['fields']
    search_labels = field_label_sync['labels']
    for search_field in search_fields:
        search_result = search_reg_value(search_key = search_field, search_value = search_fields[search_field], summary = summary, description = description)
        logging.info(f'{search_field}, search_result - {search_result}')
        loggas.input_message(path = message_path,message = f'update info - {key} : {search_field} - {search_result}')
       
        input_result = None
        input_result = search_fields[search_field]['return_type']
        if search_result:
            if type(input_result) is list:
                if len(input_result) == 0:
                    input_result = [search_result]
                elif len(input_result) == 1:
                    input_result = [{"value":search_result}]
                else:
                    pass
            if type(input_result) is dict:
                input_result['value']=search_result
            zyra_handler.update_customfield(key, search_field,input_result)
    for search_label in search_labels:
        search_result = search_reg_value(search_key = search_label, search_value = search_labels[search_label], summary = summary, description = description)
        logging.info(f'{search_label}, search_result - {search_result}')
        loggas.input_message(path = message_path,message = f'update info - {key} : {search_label} - {search_result}')
        if search_result:
            zyra_handler.update_label(key = key, label = search_result)

    return 0
# =====================================================================================================
# =====================================================================================================


# =====================================================================================================
# this is file copy from navis server ans sync to jira
# =====================================================================================================
def sync_bs3bug(user=None, password = None, query = None):
    session, session_info, status_login = zyra.initsession(user, password ,jira_url = config_data['jira_url'])
    zyra_handler = zyra.Handler_Jira(session,jira_url = config_data['jira_url'])
    result = zyra_handler.searchIssueByQuery(query=query)
    for key in result:
        issuetype = result[key]['issuetype']['name']
        loggas.input_message(path = message_path,message = f'=============== start to check {key} - {issuetype} =============')
        if str(issuetype).lower() == 'bs3':
            if bs3_config_data['file_sync'] == "True":
                file_sync_info = bs3_config_data['project'][str(key).split("-")[0]]['file_sync_info']
                sync_file_server_jira(zyra_handler,key,file_sync_info)
            if bs3_config_data['flied_lable_sync'] == "True":
                upload_label_field(zyra_handler,key)
        elif str(issuetype).lower() == 'bug':
            if bs3_config_data['file_sync'] == "True":
                file_sync_info = bs3_config_data['project'][str(key).split("-")[0]]['file_sync_info']
            if bs3_config_data['flied_lable_sync'] == "True":
                upload_label_field(zyra_handler,key)
        else:
            pass
        logging.info(f'{key} - {issuetype} done')
        loggas.input_message(path = message_path,message = f'=============== end to check {key} - {issuetype} ===============')
    return 0
# =====================================================================================================
# =====================================================================================================


