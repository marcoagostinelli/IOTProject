from dash import Dash, dcc, html, ctx, Output, Input
import dash_daq as daq
#import RPi.GPIO as GPIO
#import Freenove_DHT as DHT
import smtplib # to send email
import imaplib, email
import time

app = Dash(__name__)
#tpin -> DHT11
tpin = 35; #GPIO 19
#GPIO.setwarnings(False)
#dht = DHT.DHT(tpin)

#email information
email_sender = "iotsender031@gmail.com"
sender_password = 'swrudrzlzoevsmtv'
email_receiver = "iottest031@gmail.com"
receiver_password = 'mxzfahmjxrjpbkhp'
server = 'smtp.gmail.com'
inbox_server = 'imap.gmail.com'
homehtml = 'home.html'

smtpobject = smtplib.SMTP(server, 587)
smtpobject.starttls()
smtpobject.login(email_sender,sender_password)

#login to the sender inbox
con = imaplib.IMAP4_SSL(server)
con.login(email_sender, sender_password)
con.select("INBOX")

#keepFanOff will be true if the user manually turned off the fan (the fan will no longer turn on by itself)
keepFanOff = False
isFanOn = False
motor_enable = 15; #GPIO 22
motor_turn = 13; #GPIO 27
hasEmailSent = False



#GPIO.setup(motor_enable,GPIO.OUT)
#GPIO.setup(motor_turn,GPIO.OUT)

#some functions to help with reading emails
#gets the body of the email
def get_body(msg):
    if msg.is_multipart():
        return get_body(msg.get_payload(0))
    else:
        return msg.get_payload(None, True)

#searches for emails with a specific key and value (from a specific person)
def search(key, value, con):
    result, data = con.search(None, key, '"{}"'.format(value))
    return data

#gets all the emails from the inbox
def get_emails(result_bytes):
    msgs = []
    for num in result_bytes[0].split():
        typ, data = con.fetch(num, '(RFC822)')
        msgs.append(data)
    return msgs

#only look at emails from one person
msgs = get_emails(search('FROM', 'iottest031@gmail.com', con))
#note the size of the inbox before functions are called
inboxSize = len(msgs)

app.layout = html.Div(
    style={'background-image': 'url("/assets/background.jpg")', 'background-size': 'cover', 'width': '100%', 'height': '100%','position': 'fixed'},
    children=[
        dcc.Interval(id = "time", interval = 1000, n_intervals = 0),
        html.H1(children="IOT Dashboard"),
            html.Div(
                style={'width':'100px', 'float':'left', 'margin-left':'450px','padding':'10px'},
                children=[
                    daq.Thermometer(
                    id='temperature',
                    value=0,
                    label="Current Temperature",
                    labelPosition='top',
                    max=30
                    ) ,
                    html.Button(
                        style={'margin-top':'50px'}, 
                        id='turnOffFan', 
                        n_clicks=0,
                        children=[html.Img(src='/assets/fan_off.png',  id="fan", style={'width':'100%','height':'100%'})]
                    )
                ]
            ),
            html.Div(
                style={'float':'left','margin-top':'50px'},
                children=[
                    
                ]),
        html.Br(),
        html.Br(),
        html.Br(),
        html.Br(),
        html.Br(),
        html.Br(),
        html.Br(),
        html.Br(),
        html.Div(
            style={'margin-left':'800px'},
            children=[
                daq.Gauge(
                id='humidity',
                label="Current Humidity",
                labelPosition='top',
                max=100,
                value=0
                )
            ]
        ),
        html.Br(),
        daq.GraduatedBar(
        style={'left':'50%'},
        id='intensity',
        label="Light Intensity",
        max=100,
        value=0
        )
        ]
    )

@app.callback(
    Output('fan','src'),
    Output('temperature','value'),
    Output('humidity','value'),
    Input('time', 'n_intervals'),
    Input('turnOffFan', 'n_clicks')
)
def getTemp(data, n_clicks):
    global isFanOn
    global hasEmailSent
    #dht.readDHT11()
    #temp = dht.temperature
    temp = 24
    #humi = dht.humidity
    humi = 50
    #if the temp is over 22 and an email has not been sent, send an email
    if ((float(temp) > 22) and (hasEmailSent is False)):
        message = 'Subject: Temperature Alert\n\nThe temperature of your room is {}, would you like to turn on the fan?\nAnswer YES '.format(temp)
        #send the email
        smtpobject.sendmail(email_sender, email_receiver, message)
        print("email sent")
        hasEmailSent = True
        return('/assets/fan_off.png', temp, humi)

    #constantly check for email reply. refresh inbox and check if the size has changed
    con.recent()
    updatedInbox = get_emails(search('FROM', 'iottest031@gmail.com', con))
    #while there is no reply, keep checking, and keep fan off
    if(inboxSize == len(updatedInbox)):
        print(updatedInbox)
        return('/assets/fan_off.png', temp, humi)

    #if there is a reply, check if the user said yes
    if (checkEmailReply(updatedInbox)):
        return ('/assets/fan_on.png', temp, humi)
    else:
        return('/assets/fan_off.png', temp, humi)

    # if (isFanOn and (n_clicks == 0)):
    #     #the fan can only be turned off through the button
    #     return('/assets/fan_on.png', temp, humi)
    # else:
    #     #make sure fan is off
    #     isFanOn = False
    #     #GPIO.output(motor_enable,GPIO.LOW)
    #     return('/assets/fan_off.png', temp, humi)
                         
            
def checkEmailReply(inbox):
    print("checking reply")
    #Once the sender has received a reply from the user, check if the user said yes
    #get the most recent email
    msg = inbox[len(inbox)-1]
    #get the body of the email
    body = get_body(email.message_from_bytes(msg[0][1]))
    #if the user said yes, turn on the fan
    if ("YES" in str(body)):
        #GPIO.output(motor_enable,GPIO.HIGH)
        #GPIO.output(motor_turn,GPIO.HIGH)
        isFanOn = True
        return True
    else:
        return False


    
if __name__ == "__main__":
    app.run_server(debug=True)