import constants as const
from decouple import config
from flask_mail import Mail, Message
from flask import Flask, render_template, request
from fetch_lead import main as get_leads
from forms import LeadSearchForm

app = Flask(__name__)
app.debug = True
mail = Mail(app) # instantiate the mail class
   

# configuration of mail
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = config(const.GMAIL_USER)
app.config['MAIL_PASSWORD'] = config(const.GMAIL_PASSWORD)
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)


@app.route('/get-leads', methods=['GET', 'POST'])
def get_webhook():
    lead_list, search = [], LeadSearchForm(request.form)
    leads_dict = get_leads()
    lead_list  = leads_dict.to_dict('records')[::-1]
    if request.method == 'POST':
        
        filtered_list = get_filtered_list(search.data, lead_list)

        print(search.data)
        return render_template('index.html', comments=filtered_list, page_reload_time=config(const.TIME_INTERVAL), form=search)
    return render_template('index.html', comments=lead_list, page_reload_time=config(const.TIME_INTERVAL), form=search)


def send_email(lead_id):
    msg = Message(
                'Hello',
                sender ='akash.deep@sait.ac.in',
                recipients = ['dakash98@outlook.com']
               )
    msg.body = f'Hello Akash, You have received an email with lead id {lead_id}'
    mail.send(msg)
    return "Email Sent"


def get_filtered_list(form, lead_list):
    field, value, filtered_list = form['select'], form['search'], []
    for lead in lead_list:
        lower_value = lead[field].lower()
        if lower_value.find(value.lower()) != -1:
            filtered_list.append(lead)
    return filtered_list
