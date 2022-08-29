import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv

load_dotenv()
def send_email(name,email,phone_number, message):
    my_email =os.getenv('MY_EMAIL')
    my_password = os.getenv('MY_PASSWORD')
    email_message = f"Subject: FootBlog-Contact info \n\nName: {name}\nEmail: {email}\nPhone: {phone_number}\nMessage: {message}"
    with smtplib.SMTP('smtp.gmail.com') as connection:
        connection.starttls()
        connection.login(user=my_email, password=my_password)
        connection.sendmail(from_addr=my_email,
                            to_addrs=my_email,
                            msg=email_message)

def dict_helper(objlist):
    result2 = [item.obj_to_dict() for item in objlist]
    return result2