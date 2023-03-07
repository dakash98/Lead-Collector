import os
import math
import json
import time
import smtplib
import requests
import schedule
import pandas as pd
import constants as const
from decouple import config


COOKIES = {const.COOKIE : config(const.COOKIES)}
URL = config(const.API_URL)


def get_url(page_no):
    return URL.format(page_no)


def find_request_count():
    request_count = 0
    try:
        x = requests.get(get_url(1), cookies=COOKIES)
        lead_data = json.loads(x.content)
        total_lead_count = lead_data[const.COUNT]
        request_count = math.ceil(total_lead_count/ 20)
        print(f'Total Lead Count : {total_lead_count}, Request Count : {request_count}')
    except Exception as e:
        print(f'{e} has occured in get_data function')
    return request_count


def get_data(url, cookies, page_no):
    results = []
    try:
        url = get_url(page_no)
        x = requests.get(url, cookies=cookies)
        lead_data = json.loads(x.content)
        results = lead_data[const.RESULTS]
    except Exception as e:
        print(f'{e} has occured in get_data function')
    return results


def delete_duplicate_clients(duplicate_id_list):
    print("Duplicate data list : ", duplicate_id_list)
    for duplicate_id in duplicate_id_list:
        a = requests.delete(f'https://web.privyr.com/api/dashboard-v2/api/v1/user-client/{duplicate_id}/', cookies=COOKIES)


def mark_new_lead_to_false(client_id):
    lead_status = requests.put(f'https://web.privyr.com/api/dashboard-v2/api/v2/user-client/{client_id}/set-auto-unmark-lead/', data={"unmark_type": "CLIENT_VIEWED"}, cookies=COOKIES)
    return lead_status


def fetch_and_iterate_through_leads():
    leads_list, leads_data_for_csv, duplicate_id_list, request_count = [], [], [], find_request_count()
    for iteration in range(request_count):
        leads = get_data(URL, COOKIES, iteration+1)
        leads_in_csv = read_csv_file(const.FILE_NAME) if checks_file_existence() else []
        return_value, leads_list, leads_data_for_csv, duplicate_id_list = iterate_leads_and_check_data_in_csv(leads, leads_in_csv, leads_list, leads_data_for_csv, duplicate_id_list)
        if return_value == const.CLIENT_EXIST:
            break
    return leads_data_for_csv, duplicate_id_list


def fetch_paginated_leads(page_no):
    '''return all leads of a particular page and total page count'''
    total_pages, leads = find_request_count(), get_data(URL, COOKIES, page_no) 
    leads_list = iterate_leads_and_convert_into_list(leads)
    return leads_list, total_pages


def iterate_leads_and_convert_into_list(leads):
    '''iterate through leads and convert into a list of representable format'''
    leads_list = []
    for lead in leads:
        interested_in, ad_name = get_interested_in_and_ad_name_from_notes(lead)
        leads_list.insert(0, {const.NAME: lead[const.NAME], const.PHONE_NUMBER : get_phone_number(lead), const.INTERESTED_IN : replace_underscore(interested_in), const.AD_NAME : replace_underscore(ad_name), const.SENT_EMAIL: True, const.NEW_LEAD: False})
    return leads_list


def is_client_already_exist(lead, leads_in_csv):
    last_item = len(leads_in_csv[const.NAME])-1
    if lead[const.NAME] == leads_in_csv[const.NAME][last_item]:
        return True
    return False


def check_mobile_number(lead, lead_in_csv):
    if lead_in_csv[const.PHONE_NUMBER]:
        return get_phone_number(lead) != int(lead_in_csv[const.PHONE_NUMBER])
    return False


def iterate_leads_and_check_data_in_csv(leads, leads_in_csv, leads_list, leads_data_for_csv, duplicate_id_list):
    for lead in leads:
        if (duplicate_id_list := check_duplicate_or_test_client(lead, leads_list, duplicate_id_list)):
            # delete_duplicate_clients([lead['id']])
            duplicate_id_list.pop()
            continue
        interested_in, ad_name = get_interested_in_and_ad_name_from_notes(lead)
        leads_list.insert(0, {const.NAME: lead[const.NAME], const.PHONE_NUMBER : get_phone_number(lead), const.INTERESTED_IN : interested_in, const.AD_NAME : ad_name})
        if checks_file_existence() and is_client_already_exist(lead, leads_in_csv):
            return const.CLIENT_EXIST, leads_list, leads_data_for_csv, duplicate_id_list
        leads_data_for_csv.insert(0, [lead[const.NAME], get_phone_number(lead), replace_underscore(interested_in), replace_underscore(ad_name), True, False])
    return '', leads_list, leads_data_for_csv, duplicate_id_list
        

def replace_underscore(data):
    return data.replace("_", " ")



def check_duplicate_or_test_client(lead, leads_list, duplicate_id_list):
    if ((lead.get('source_details') and lead['source_details']["lead_source"] == "WEBHOOK_GENERIC") or (lead[const.DISPLAY_NAME] == const.TEST_LEAD and lead[const.EMAIL] == const.SUPPORT_EMAIL) or (lead[const.DISPLAY_NAME] == const.PRIVYR_SUPPORT)) or  (len(leads_list) > 0 and leads_list[0][const.NAME] == lead[const.NAME] and leads_list[0][const.PHONE_NUMBER] == get_phone_number(lead)):
        duplicate_id_list.append(lead[const.ID])
    return duplicate_id_list


def get_interested_in_and_ad_name_from_notes(lead):
    notes_list = lead[const.NOTES].split('\n')
    interested_in, ad_name = '', ''
    for note in notes_list:
        splitted_notes = note.split(':')[-1]
        if const.INTERESTED in note:
            interested_in = splitted_notes
        if const.AD in note:
            ad_name = splitted_notes
    return interested_in, ad_name


def get_phone_number(lead):
    if lead.get(const.PHONE_NUMBER):
        return lead[const.PHONE_NUMBER][const.NATIONAL_NUMBER]
    return ""


def read_csv_file(filename):
    df = pd.read_csv(filename)
    return df.to_dict()


def create_csv_file(leads):
    filename = const.FILE_NAME
    fields = [const.NAME, const.PHONE_NUMBER, const.INTERESTED_IN, const.AD_NAME, const.SENT_EMAIL, const.NEW_LEAD]
    append_data_to_csv_file(leads, filename) if checks_file_existence() else create_and_add_data_to_csv_file(leads, fields, filename)


def checks_file_existence():
    path = const.FILE_NAME
    is_exist = os.path.isfile(path)
    return is_exist


def append_data_to_csv_file(leads, filename):
    df = pd.DataFrame(leads)
    df.to_csv(filename, mode='a', index=False, header=False)


def create_and_add_data_to_csv_file(leads, fields, filename):
    df = pd.DataFrame(leads, columns=fields)
    df.to_csv(filename, sep=',', index=False,header=True)    


def main():
    leads_data_for_csv, duplicate_id_list = fetch_and_iterate_through_leads()
    create_csv_file(leads_data_for_csv)
    print("Updated code : ", leads_data_for_csv)
    delete_duplicate_clients(duplicate_id_list)
    print('------------------')
    return read_csv_and_return_dataframe(), leads_data_for_csv


def read_csv_and_return_dataframe():
    df = pd.read_csv(const.FILE_NAME)
    return df


# main()


