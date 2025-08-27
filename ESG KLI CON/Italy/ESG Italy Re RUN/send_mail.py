# import os
# from datetime import datetime
# import configparser
# import requests
# from bs4 import BeautifulSoup
# import json
# import smtplib
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText
# from email.mime.base import MIMEBase
# from email import encoders
#
# def send_email(attachments, keyword):
#     subject = f"Project Testing [{keyword}]"
#     body = "<h3>Report Attached.</h3>"
#     Sending_address = "Test_Project@innodata.com"
#     to_email_list = ["SL1253@innodata.com"]
#     cc_email_list = ["SL1253@innodata.com"]
#     port = 587
#
#     if attachments is None:
#         attachments = []
#
#     sender_address = Sending_address
#
#     message = MIMEMultipart()
#     message['From'] = sender_address
#     message['To'] = ", ".join(to_email_list)
#     message['CC'] = ", ".join(cc_email_list)
#     message['Subject'] = subject
#     message.attach(MIMEText(body, 'html'))
#
#     if attachments != []:
#         try:
#             csv_filename = os.path.basename(attachments)
#             with open(attachments, "rb") as attachment:
#                 part = MIMEBase('multipart', 'plain')
#                 part.set_payload(attachment.read())
#                 attachment.close()
#             encoders.encode_base64(part)
#             part.add_header("Content-Disposition", f"attachment; filename={csv_filename}")
#             message.attach(part)
#         except Exception as e:
#             print(f"⚠️ Failed to attach file {attachments}: {e}")
#
#     try:
#         session = smtplib.SMTP('smtpsgp.innodata.com', port)
#         text = message.as_string()
#         session.sendmail(sender_address, to_email_list + cc_email_list, text)
#         session.quit()
#         print("✅ Email sent successfully.")
#     except Exception as e:
#         print(f"❌ Failed to send email: {e}")
