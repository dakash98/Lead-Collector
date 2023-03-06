import constants as const
from decouple import config
from forms import LeadSearchForm
from fetch_lead import main as get_leads
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/get-leads', methods=['GET', 'POST'])
def fetch_leads():
    from email_services import send_new_leads_to_client
    lead_list, search = [], LeadSearchForm(request.form)
    leads_dict, new_leads_list = get_leads()
    lead_list  = leads_dict.to_dict('records')[::-1]
    send_new_leads_to_client(new_leads_list)
    if request.method == 'POST':
        lead_list = get_filtered_list(search.data, lead_list)
    response = jsonify({"leads" : lead_list, "page_reload_time" : config(const.TIME_INTERVAL)})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route('/fetch-leads', methods=['GET', 'POST'])
def retrieve_leads():
    from email_services import send_new_leads_to_client
    lead_list, search = [], request.value
    leads_dict, new_leads_list = get_leads()
    lead_list  = leads_dict.to_dict('records')[::-1]
    send_new_leads_to_client(new_leads_list)
    if request.method == 'POST':
        lead_list = get_filtered_list(search.data, lead_list)
    response = jsonify({"leads" : lead_list, "page_reload_time" : config(const.TIME_INTERVAL)})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


def get_filtered_list(req_data, lead_list):
    field, value, filtered_list = req_data['select'], req_data['search'], []
    for lead in lead_list:
        lower_value = lead[field].lower()
        if lower_value.find(value.lower()) != -1:
            filtered_list.append(lead)
    return filtered_list


# if __name__ == "__main__":
#     app.run(port=8000, debug=True)