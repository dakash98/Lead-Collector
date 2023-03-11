import pandas as pd
import constants as const
from decouple import config
from forms import LeadSearchForm
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request, jsonify, render_template, redirect, url_for, send_file
from fetch_lead import fetch_paginated_leads, main as get_leads, fetch_and_iterate_through_leads, create_csv_file



app = Flask(__name__)
# app.config ['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:postgres@localhost:5432/facebook_leads"
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# db = SQLAlchemy(app)
# migrate = Migrate(app, db)



# class LeadModel(db.Model):
#     __tablename__ = 'leads'

#     id = db.Column('lead_id', db.Integer, primary_key = True)
#     name = db.Column(db.String())
#     phone_number = db.Column(db.String())
#     interested_in = db.Column(db.String())
#     ad_name = db.Column(db.String())
#     email_sent = db.Column(db.Boolean)
#     new_lead = db.Column(db.Boolean)
#     created_at = db.Column(db.String())

#     def __init__(self, name, phone_number, interested_in, ad_name, email_sent, new_lead, created_at):
#         self.name = name
#         self.phone_number = phone_number
#         self.interested_in = interested_in
#         self.ad_name = ad_name
#         self.email_sent = email_sent
#         self.new_lead = new_lead
#         self.created_at = created_at

#     def __repr__(self):
#         return '<name {}>'.format(self.name)


@app.route('/get-leads', methods=['GET', 'POST'])
def get_leads_with_flask_template():
    from email_services import send_new_leads_to_client
    lead_list, search = [], LeadSearchForm(request.form)
    leads_dict, leads_list = get_leads()
    unique_ad_name,  unqiue_interested_in = leads_dict.ad_name.unique(), leads_dict.interested_in.unique()
    lead_list  = leads_dict.to_dict('records')[::-1]
    send_new_leads_to_client(leads_list)
    if request.method == 'POST':
        filtered_list = get_filtered_list(search.data, lead_list)
        return render_template('index.html', comments=filtered_list, page_reload_time=config(const.TIME_INTERVAL), form=search, unique_ad_name= unique_ad_name, unique_interested_in=unqiue_interested_in)
    return render_template('index.html', comments=lead_list, page_reload_time=config(const.TIME_INTERVAL), form=search)


@app.route('/fetch-leads', methods=['GET', 'POST'])
def get_all_leads():
    from email_services import send_new_leads_to_client
    leads_dict, new_leads_list = get_leads()
    unique_ad_name,  unqiue_interested_in = leads_dict.ad_name.unique().tolist(), leads_dict.interested_in.unique().tolist()
    lead_list  = leads_dict.to_dict('records')[::-1]
    send_new_leads_to_client(new_leads_list)
    if request.method == 'POST':
        lead_list = get_filtered_list(request.form, lead_list)
    response = jsonify({"leads" : lead_list, "page_reload_time" : config(const.TIME_INTERVAL), "unique_ad_name": unique_ad_name, "unique_interested_in": unqiue_interested_in})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route('/retrieve-leads/<page_no>', methods=['GET', 'POST'])
def retrieve_pagniated_leads(page_no=1):
    if page_no == 'all':
        return redirect(url_for('get_all_leads'))
    leads_list, page_count = fetch_paginated_leads(page_no)
    df = pd.DataFrame(leads_list)
    unique_ad_name,  unqiue_interested_in = df.ad_name.unique().tolist(), df.interested_in.unique().tolist()
    if request.method == 'POST':
        leads_list = get_filtered_list(request.form, leads_list)
    response = jsonify({"leads" : leads_list[::-1], "page_reload_time" : config(const.TIME_INTERVAL), "unique_ad_name": unique_ad_name, "unique_interested_in": unqiue_interested_in, "count": page_count})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route('/download-leads-csv')
def download_csv_file():
    # https://stackoverflow.com/questions/30024948/flask-download-a-csv-file-on-clicking-a-button
    return send_file(
        'lead_records.csv',
        mimetype='text/csv',
        download_name='Leads.csv',
        as_attachment=True
    )


def get_new_leads_and_update_csv():
    from email_services import send_new_leads_to_client
    new_leads_list, _ = fetch_and_iterate_through_leads()
    if new_leads_list:
        print("this function is running")
        create_csv_file(new_leads_list)
        send_new_leads_to_client(new_leads_list)


def get_filtered_list(req_data, lead_list):
    field, value, filtered_list = req_data['select'], req_data['search'], []
    for lead in lead_list:
        lower_value = lead[field].lower()
        if lower_value.find(value.lower()) != -1:
            filtered_list.append(lead)
    return filtered_list


# https://betterprogramming.pub/introduction-to-apscheduler-86337f3bb4a6
# sched = BackgroundScheduler(daemon=True)
# sched.add_job(get_new_leads_and_update_csv,'interval',minutes=1)
# sched.start()

if __name__ == "__main__":
    app.run(port=8000, debug=True)


# As for the second problem which is refreshing the client view every time the job runs, you can't do that directly 
# from Flask. An ugly but simple way would be to add <meta http-equiv="refresh" content="1" > to the HTML page to 
# instruct the browser to refresh it every second. A much better implementation would be to use SocketIO to send 
# new data in real-time to the web client.