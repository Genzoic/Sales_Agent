import os
import json
import smtplib
import pandas as pd
import streamlit as st
from email.mime.text import MIMEText
from datetime import datetime

# read this from config


def send_email(smtp_server, smtp_port, username, password, from_addr, to_addr, subject, body):
    print("Called send email function")
    '''function to send email'''
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = to_addr

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(username, password)
        server.send_message(msg)
        server.quit()
        print("Email sent successfully")
        st.write("Email Sent Successfully")
        st.write("\n")
    except Exception as e:
        print("An error occurred: ", str(e))
