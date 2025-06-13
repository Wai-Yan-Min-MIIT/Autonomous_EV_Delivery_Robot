import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Email configuration
sender_email = "alphatechmiit@gmail.com"
receiver_email = "waiyanminmiit@gmail.com"
password = "dvkahcgxtbaocnxc"  # Replace with the App Password (e.g., abcd efgh ijkl mnop)

# Create the email message
subject = "Test Email from EV Delivery App"
body = "Hello Wai Yan,\n\nThis is a test email from your EV Delivery Robot app. If you received this, the email setup is working!\n\nBest regards,\nAlphaTech Team"

msg = MIMEMultipart()
msg['From'] = sender_email
msg['To'] = receiver_email
msg['Subject'] = subject
msg.attach(MIMEText(body, 'plain'))

# Connect to Gmail's SMTP server and send the email
try:
    # Create an SMTP session
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()  # Enable TLS
    server.login(sender_email, password)  # Login to Gmail
    server.sendmail(sender_email, receiver_email, msg.as_string())  # Send the email
    print("Email sent successfully!")
except Exception as e:
    print(f"Failed to send email: {e}")
finally:
    server.quit()  # Close the SMTP session