import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import config


class Email(object):
    def __init__(self, _to, _from, _subject):
        self.msg = MIMEMultipart('mixed')
        self.msg['From'] = _from
        self.msg['To'] = _to
        self.msg['Subject'] = _subject

        self.server = smtplib.SMTP_SSL(config.smtp_server, config.smtp_port)
        self.server.ehlo()
        self.server.login(config.email_login, config.email_password)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def set_body(self, body):
        textPart = MIMEText(body, 'plain')
        self.msg.attach(textPart)

    def attach_pdf(self, file, name):
        with open(file, 'rb') as pdf:
            attach = MIMEApplication(pdf.read(), _subtype="pdf")
            attach.add_header('content-disposition', 'attachment', filename=('utf-8', '', name))
            self.msg.attach(attach)

    def send(self):
        self.server.send_message(self.msg)

    def close(self):
        self.server.close()
