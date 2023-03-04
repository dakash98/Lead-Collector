import constants as const
from decouple import config
from flask_mail import Mail, Message
from flask import Flask, render_template
from fetch_lead import main as get_leads

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


@app.route('/get-leads', methods=['GET'])
def get_webhook():
    leads_dict = get_leads()
    lead_list  = leads_dict.to_dict('records')
    return render_template('index.html', comments=lead_list[::-1], page_reload_time=config(const.TIME_INTERVAL))

def send_email(lead_id):
    msg = Message(
                'Hello',
                sender ='akash.deep@sait.ac.in',
                recipients = ['dakash98@outlook.com']
               )
    msg.body = f'Hello Akash, You have received an email with lead id {lead_id}'
    mail.send(msg)
    return "Email Sent"