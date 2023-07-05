# it is for uploading files (such as video and picture) from link and BS3
# 1. check directory in jira
#  - link, dir path
# 2. get list from directory
# 3. uploading files to jira (like sync)
#  - if exist -> skip
# author: miskang@navis-ams.com

from cgitb import lookup
import os, re
import shutil
import ast
from _src._api import jira_rest, config
from _src._api import logger, logging_message


logging = logger.logger

config_path = os.path.join('static','config','config.json')
qss_path = os.path.join('static','css','style.qss')
config_data =config.load_config(config_path)

message_path = config_data['message_path']
tmp_path = config_data['tmp_path']

# =====================================================================================================
# this is file copy from navis server ans sync to jira
# =====================================================================================================

def ignore_file_list(file):
    ignore_list = config_data['ignore_list']
    result = False
    for ig in ignore_list:
        if ig in file:
            result = True
    return result

def download_files_in_server(server_path=None, local_path=None):
    logging.debug(server_path)
    logging.debug(local_path)
    return_files = []
    #remove local folder 
    try:
        shutil.rmtree(local_path) if os.path.exists(local_path) else logging.debug('no local folder')
        os.makedirs(local_path)
    except:
        pass
    # =====================================================================================================
    #download from server
    # =====================================================================================================
    # check file list in server
    file_list = os.listdir(server_path) if os.path.exists(server_path) else []
    logging.debug('files in server : %s' %str(file_list))
    # ignore files 
    file_list = [file for file in file_list if ignore_file_list(file) is True]
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
                shutil.copy2(file_path,tmp_path)
                #add file list
                return_files.append(file_path)
    return return_files

def upload_files_into_jira(jira_rest_handler,key,local_file_list):
    # =====================================================================================================
    #upload file to jira
    # =====================================================================================================
    uploaded_file_list = jira_rest_handler.get_attachment(key)
    logging.debug("update file list in local : %s" %str(local_file_list))
    logging.debug("updated file list in jira : %s" %str(uploaded_file_list))
    #logging_message.input_message(path = message_path,message = 'update file list in local : %s'  %str(file_list))
    #logging_message.input_message(path = message_path,message = 'updated file list in jira : %s'  %str(uploaded_file_list))
    for file in local_file_list:
        file_path = os.path.join(tmp_path,file)
        logging.debug('upload file - %s' %file)
        if file in uploaded_file_list:
            logging.debug('it already uploaded - %s' %file)
            #logging_message.input_message(path = message_path,message = 'it already uploaded - %s' %file)
        else:
            logging.debug('start upload - %s' %file)
            #logging_message.input_message(path = message_path,message = 'start upload - %s' %file) 
            upload_attachment_result = jira_rest_handler.upload_attachment(key,file_path)
            logging.debug(upload_attachment_result)
    return 0

def sync_file_server_jira(jira_rest_handler,key,bs3_path):
    logging_message.input_message(path = message_path,message = '== start upload file ==')
    dante_id = jira_rest_handler.searchIssueByKey(key)['fields']['customfield_12304']
    server_path = os.path.join(bs3_path,dante_id)
    local_file_list = download_files_in_server(server_path=server_path, local_path=tmp_path)
    logging_message.input_message(path = message_path,message = 'download done!')
    logging.debug('download done!')
    upload_files_into_jira(jira_rest_handler,key,local_file_list)
    logging_message.input_message(path = message_path,message = '== upload done ==')
    logging.debug('== upload done ==')
# =====================================================================================================


# =====================================================================================================
# this is find field and labels in ticket
# =====================================================================================================
def update_fleid_by_find_list(text,search_listaaa,jira_ticket_key,jira_rest_handler):
    # get searching list
    logging.debug("list information: %s"%str(search_listaaa))
    search_reg = search_listaaa['search_reg']
    search_keys = search_listaaa['search_keys']
    change_to_jira = search_listaaa['result']
    #logging.debug("searchs is %s"%str(search_keys))
    #logging.debug("result is %s"%str(result))
    # ==================================================
    searching_reg_result = re.search(search_reg.lower(),text.lower())
    logging.debug('searching reg result: %s'%searching_reg_result)
    if searching_reg_result is not None:
        text = searching_reg_result.group(0)
        #logging_message.input_message(path = message_path,message = 'find something search_reg: %s'%text)
        return_flag = False
        dict_search_by_search_keys = {}
        for search_key in search_keys:
            for inner_search_key in search_keys[search_key]:
                search_temp = re.search(inner_search_key.lower(),text.lower())
                if search_temp is not None:
                    dict_search_by_search_keys[search_key] = search_temp
                    logging.debug('find something by search_keys list: %s'%str(search_temp))
                    #logging_message.input_message(path = message_path,message = 'find something by search_keys list: %s'%str(search_temp.group(0)))
                    update_fleid = ast.literal_eval(str(change_to_jira).replace('input',search_key))
                    logging_message.input_message(path = message_path,message = 'start update feild: %s'%str(update_fleid))
                    logging.debug('start update feild: %s'%str(update_fleid))
                    jira_rest_handler.updateissue(jira_ticket_key,update_fleid)                    
                    return_flag = True
                if return_flag == True:
                    break
            if return_flag == True:
                break
        
    else:
        logging.debug("there is no any string by search_key: %s - search_reg: %s" %(jira_ticket_key,search_reg))
        #logging_message.input_message(path = message_path,message = "there is no any string by search_key: %s - search_reg: %s" %(jira_ticket_key,search_reg)) 
    return 0

def upload_label_field(jira_rest_handler,key):
    logging.debug('this is key %s' %key)
    summary = jira_rest_handler.searchIssueByKey(key)['fields']['summary']
    description = jira_rest_handler.searchIssueByKey(key)['fields']['description']
    #find project 
    find_list = config_data[key.spilt("-")[0]]["find_list"]
    #logging_message.input_message(path = message_path,message = "summary is: %s" %summary)
    #logging.debug('%s' %description)
    #logging.debug('%s' %str(find_list))
    logging_message.input_message(path = message_path,message = '==start feild update!==')
    for find in find_list['summary']['fields']:
        search_listaaa = find_list['summary']['fields'][find]
        update_fleid_by_find_list(summary,search_listaaa,key,jira_rest_handler)
        
    for find in find_list['description']['fields']:
        logging.debug("start find ['description']['fields']: %s"%str(find))
        search_listaaa = find_list['description']['fields'][find]
        update_fleid_by_find_list(description,search_listaaa,key,jira_rest_handler)
    #logging_message.input_message(path = message_path,message = '==feild update done!==')

    #logging_message.input_message(path = message_path,message = '==start labels update!==')
    for find in find_list['summary']['labels']:
        logging.debug("start find ['summary']['labels']: %s"%str(find))
        search_listaaa = find_list['summary']['fields'][find]
    
    for a in find_list['description']['labels']:
        logging.debug("start find ['summary']['labels']: %s"%str(find))
        logging.debug("['description']['labels'] is %s"%a)
    #logging_message.input_message(path = message_path,message = '==labels update done!==')    
    return 0

    for find_key in find_list.keys():
        logging.info(str(re.search(find_list[find_key],description)))
        if re.search(find_list[find_key],description) is not None:
            if re.search(find_list[find_key],description).group(0) in field_label_list.keys():
                find_result[find_key] = field_label_list[re.search(find_list[find_key],description).group(0)]
            else:
                find_result[find_key] = re.search(find_list[find_key],description).group(0)
    logging.debug('field and labes - %s' %str(find_result))
    logging_message.input_message(path = message_path,message = 'field and labes - %s' %str(find_result))

    ticket_info = jira_rest_handler.searchIssueByKey(key)
    ticket_category = ticket_info['fields']['customfield_13003']
    ticket_category = ticket_info['fields']['customfield_13003']

    def update_ticket_category(values):
        ticket_category_fields = {}
        ticket_category_fields['fields']={}
        ticket_category_fields["fields"]["customfield_13003"] = {'value':values}
        logging.debug('%s - %s' %(key,ticket_category_fields))
        #jira_rest_handler.updateissue(key,ticket_category_fields)
        return 0
    if ticket_category == None:
        update_ticket_category('Other')
    else:
        ticket_category = ticket_category['value']
    logging.debug('ticket category - %s' %ticket_category)
    for r in find_result:
        if '_field' in r:
            fields = {}
            fields['fields']={}
            fields["fields"]["customfield_11102"] = []
            fields["fields"]["customfield_11102"].append({'value':find_result[r]})
            if find_result[r] is None:
                logging.debug('field is %s so passed'%find_result[r])
                pass
            else:
                logging.debug('%s - %s' %(key,fields))
                #jira_rest_handler.updateissue(key,fields)
        elif '_label' in r:
            logging.debug(find_result[r])
            if find_result[r] == None:
                logging.debug('label is %s so passed' %find_result[r])
                pass
            else:
                logging.debug('%s - %s' %(key,find_result[r]))
                jira_rest_handler.update_label(key,find_result[r])
        else:
            pass
    return 0
# =====================================================================================================
# =====================================================================================================


# =====================================================================================================
# this is file copy from navis server ans sync to jira
# =====================================================================================================
def sync_attachment(user=None, password = None, query = None):
    session_list = jira_rest.initsession(user, password)
    session = session_list[0]
    session_info = session_list[1]
    jira_rest_handler = jira_rest.Handler_Jira(session)
    result = jira_rest_handler.searchIssueByQuery(query=query)
    for key in result:
        issuetype = result[key]['issuetype']['name']
        logging.debug('start key - %s and issuetype - %s' %(key,issuetype))
        if issuetype == 'BS3':
            logging_message.input_message(path = message_path,message = 'start to check %s' %key)
            bs3_path = config_data['project'][str(key).split("-")[0]]['bs3_path']
            logging.debug(bs3_path)
            sync_file_server_jira(jira_rest_handler,key,bs3_path)
            #upload_label_field(jira_rest_handler,key)
            logging.debug('key - %s and issuetype - %s done!\n' %(key,issuetype))
            logging_message.input_message(path = message_path,message = 'end to check %s\n' %key)
        elif issuetype == 'BUG':
            ticket_info = jira_rest_handler.searchIssueByKey(key)['fields']
            assignee = jira_rest_handler.searchIssueByKey(key)['fields']['assignee']
            reporter = jira_rest_handler.searchIssueByKey(key)['fields']['reporter']
            logging.info(assignee)
            logging.info(reporter)
        else:
            pass
        

# =====================================================================================================
# =====================================================================================================


