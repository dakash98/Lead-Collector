import constants as const
from decouple import config
from flask import Flask, render_template, request
from fetch_lead import main as get_leads
from forms import LeadSearchForm

app = Flask(__name__)
app.debug = True


@app.route('/get-leads', methods=['GET', 'POST'])
def fetch_leads():
    from email_services import send_new_leads_to_client
    lead_list, search = [], LeadSearchForm(request.form)
    leads_dict, new_leads_list = get_leads()
    lead_list  = leads_dict.to_dict('records')[::-1]
    send_new_leads_to_client(new_leads_list)
    if request.method == 'POST':
        filtered_list = get_filtered_list(search.data, lead_list)
        return render_template('index.html', comments=filtered_list, page_reload_time=config(const.TIME_INTERVAL), form=search)
    return render_template('index.html', comments=lead_list, page_reload_time=config(const.TIME_INTERVAL), form=search)


def get_filtered_list(form, lead_list):
    field, value, filtered_list = form['select'], form['search'], []
    for lead in lead_list:
        lower_value = lead[field].lower()
        if lower_value.find(value.lower()) != -1:
            filtered_list.append(lead)
    return filtered_list
