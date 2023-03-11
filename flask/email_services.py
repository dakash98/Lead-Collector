import ast
from app import app
import constants as const
from decouple import config
from flask_mail import Mail, Message

# mail = Mail(app) # instantiate the mail class

# configuration of mail
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = config(const.GMAIL_USER)
app.config['MAIL_PASSWORD'] = config(const.GMAIL_PASSWORD)
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)


def send_new_leads_to_client(new_leads_list):
    for lead in new_leads_list:
        print(lead)
        send_email(lead[0], lead[1], lead[2], lead[3])


def send_email(name, phone_number, interested_in, ad_name):
    recipients_list = ast.literal_eval(config('EMAIL_RECIPIENTS'))
    msg = Message(
                f'{ad_name}',
                sender =config(const.GMAIL_USER),
                recipients = recipients_list
               )
    msg.body = f'Hello, You have received a new lead, Name : {name}, Phone Number : {phone_number}, Interested In : {interested_in}'
    # https://stackoverflow.com/questions/21362700/using-flask-mail-asynchronously-results-in-runtimeerror-working-outside-of-app
    with app.app_context():
        mail.send(msg)
    return "Email Sent"