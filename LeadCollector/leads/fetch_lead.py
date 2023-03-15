import os
import math
import json
import pytz 
import requests
# import pandas as pd
import leads.constants as const
from decouple import config
from datetime import datetime
# import redis


# COOKIES = {const.COOKIE : config(const.COOKIES)}
# URL = config(const.API_URL)


COOKIES = {const.COOKIE : '_fbp=fb.1.1676347846105.1522519858; _rdt_uuid=1676347848701.70269df5-4a9b-4791-8503-90e836217254; _gac_UA-116570030-1=1.1676348385.CjwKCAiA3KefBhByEiwAi2LDHDd3UYme_IrhAuflgGYu0IQV-atyaAWQSO-vSxgQL_oUlVT6F0eBSRoCWFAQAvD_BwE; _gcl_aw=GCL.1676348385.CjwKCAiA3KefBhByEiwAi2LDHDd3UYme_IrhAuflgGYu0IQV-atyaAWQSO-vSxgQL_oUlVT6F0eBSRoCWFAQAvD_BwE; pss_system_id=btsapx8uh5vjq3k9jqle9yu69tc5c0d0; _fw_crm_v=f19f9a6e-a9f3-42e8-ec25-ca3d7932fe6d; _gcl_au=1.1.1771656351.1676347846.702659208.1676905961.1676906038; _gid=GA1.2.1015926052.1677584094; _clck=1gpgl90|1|f9i|0; _clsk=1fsnc04|1677584141252|2|1|h.clarity.ms/collect; _ga=GA1.2.1588533433.1676347846; _ga_3WW6HT4Z8W=GS1.1.1677584094.10.1.1677584238.0.0.0; _ga_VZP1TNLJCN=GS1.1.1677584094.10.1.1677584238.60.0.0'}
URL = 'https://web.privyr.com/api/dashboard-v2/api/v2/user-client/?sort_key=created_at&sort_order=DESC&bare_data=false&page={0}&ignore_prefs=true'

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
    return request_count, total_lead_count


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
    request_count, _ = find_request_count()
    leads_list, latest_lead, duplicate_id_list, leads_data_for_csv = [], [], [], []
    for iteration in range(request_count):
        leads = get_data(URL, COOKIES, iteration+1)
        latest_lead = fetch_latest_lead()
        return_value, leads_list, leads_data_for_csv, duplicate_id_list = iterate_leads_and_check_data_in_csv(leads, latest_lead, leads_list, duplicate_id_list)
        if return_value == const.CLIENT_EXIST:
            break
    return leads_data_for_csv, duplicate_id_list


def fetch_latest_lead():
    from leads.models import LeadsModel
    latest_lead = LeadsModel.objects.all().first()
    return latest_lead



def fetch_paginated_leads(page_no):
    '''return all leads of a particular page and total page count'''
    from leads.models import LeadsModel
    total_pages, _ = find_request_count()
    leads = get_data(URL, COOKIES, page_no) 
    # leads_list = iterate_leads_and_convert_into_list(leads)
    fetch_and_iterate_through_leads()
    leads_list = LeadsModel.objects.all()
    return leads_list, total_pages


def iterate_leads_and_convert_into_list(leads):
    '''iterate through leads and convert into a list of representable format'''
    leads_list = []
    for lead in leads:
        interested_in, ad_name = get_interested_in_and_ad_name_from_notes(lead)
        leads_list.insert(0, {const.NAME: lead[const.NAME], const.PHONE_NUMBER : get_phone_number(lead), const.INTERESTED_IN : replace_underscore(interested_in), const.AD_NAME : replace_underscore(ad_name), const.SENT_EMAIL: True, const.NEW_LEAD: False, "created_at": get_date_from_timestamp(lead['created_at']) })
    return leads_list


def is_client_already_exist(lead, lastest_lead):
    if lastest_lead and lead[const.NAME] == getattr(lastest_lead, 'name'):
        return True
    return False


def check_mobile_number(lead, lead_in_csv):
    if lead_in_csv[const.PHONE_NUMBER]:
        return get_phone_number(lead) != int(lead_in_csv[const.PHONE_NUMBER])
    return False


def iterate_leads_and_check_data_in_csv(leads, latest_lead, leads_list, duplicate_id_list):
    from leads.models import LeadsModel
    for lead in leads:
        if (duplicate_id_list := check_duplicate_or_test_client(lead, leads_list, duplicate_id_list)):
            # delete_duplicate_clients([lead['id']])
            print("deleting dummy or duplicate client : ", lead)
            duplicate_id_list.pop()
            continue
        if is_client_already_exist(lead, latest_lead):
            print("wow client already exists")
            return const.CLIENT_EXIST, leads_list, [], duplicate_id_list
        interested_in, ad_name = get_interested_in_and_ad_name_from_notes(lead)
        lead_dict = {const.NAME: lead[const.NAME], const.PHONE_NUMBER : get_phone_number(lead), const.INTERESTED_IN : interested_in, const.AD_NAME : ad_name, "email_sent" : False, "new_lead": True, "created_at": get_date_from_timestamp(lead['created_at'])}
        leads_list.insert(0, lead_dict)
        lead_obj = LeadsModel(**lead_dict)
        lead_obj.save()
        # leads_data_for_csv.insert(0, [lead[const.NAME], get_phone_number(lead), replace_underscore(interested_in), replace_underscore(ad_name), True, False, get_date_from_timestamp(lead['created_at'])])
    return '', leads_list, [], duplicate_id_list
        

def replace_underscore(data):
    return data.replace("_", " ")


def get_date_from_timestamp(timestamp):
    time_zone = pytz.timezone('Asia/Kolkata') 
    return datetime.fromtimestamp(timestamp, tz=time_zone).strftime('%d-%b-%Y %I:%M %p')


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
    fields = [const.NAME, const.PHONE_NUMBER, const.INTERESTED_IN, const.AD_NAME, const.SENT_EMAIL, const.NEW_LEAD, 'created_at']
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


