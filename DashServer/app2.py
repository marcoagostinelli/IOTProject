from dash import Dash, dcc, html, ctx, Output, Input
from dash.dependencies import Input, Output, State
import dash_daq as daq
import RPi.GPIO as GPIO
import Freenove_DHT as DHT
import smtplib # to send email
from imap_tools import MailBox, AND # to receive email
import time
import dash_mqtt

app = Dash(__name__)

#email information
email_sender = "iotsender031@gmail.com"
sender_password = 'swrudrzlzoevsmtv'
email_receiver = "iottest031@gmail.com"
receiver_password = 'mxzfahmjxrjpbkhp'
server = 'smtp.gmail.com'
inbox_server = 'imap.gmail.com'
homehtml = 'home.html'
timer = time.time() + 60

#MQTT mosquitto server and portt
TEST_SERVER = '192.168.149.60'
TEST_SERVER_PORT = 1883
#TEST_SERVER_PATH = 'mqtt'
#topics
MESSAGE_OUT_TOPIC = 'IoTlab/photoValue'
MESSAGE_IN_TOPIC = 'IoTlab/photoValue'
#vanieriot

smtpobject = smtplib.SMTP(server, 587)
smtpobject.starttls()
smtpobject.login(email_sender,sender_password)

#login to the inbox
mb = MailBox(inbox_server).login(email_sender, sender_password)

#tpin -> DHT11
tpin = 35; #GPIO 19
motor_enable = 15; #GPIO 22
motor_turn = 13; #GPIO 27
isFanOn = False
#keepFanOff will be true if the user manually turned off the fan (the fan will no longer turn on by itself)
keepFanOff = False

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(motor_enable,GPIO.OUT)
GPIO.setup(motor_turn,GPIO.OUT)
dht = DHT.DHT(tpin)
GPIO.output(motor_enable, GPIO.LOW)

app.layout = html.Div(
    style={'background-image': 'url("/assets/background.jpg")', 'background-size': 'cover', 'width': '100%', 'height': '100%','position': 'fixed'},
    children=[
        dcc.Interval(id = "time"),
        html.H1(children="IOT Dashboard"),
            html.Div(
                style={'width':'100px', 'float':'left', 'margin-left':'450px','padding':'10px'},
                children=[
                    daq.Thermometer(
                    id='temperature',
                    value=0,
                    label="Current Temperature",
                    labelPosition='top',
                    max=50 
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

def getTemp(data,n_clicks):
    global isFanOn
    global keepFanOff
    #get button info
    dht.readDHT11()
    temp = dht.temperature
    humi = dht.humidity
    print ("temp is :",temp)
    #if the temp is over 22, send the user a notice
    if ((float(temp) > 20) and (isFanOn is False) and (keepFanOff is False)):
        message = 'Subject: Temperature Alert\n\nThe temperature of your room is {}, would you like to turn on the fan?\nYou have 1 minute to answer. '.format(temp)
        #send the email
        smtpobject.sendmail(email_sender, email_receiver, message)
        time.sleep(2)
        isFanOn = checkEmailReply()
        
    if (isFanOn and (n_clicks == 0)):
        #the fan can only be turned off through the button
        return('/assets/fan_on.png', temp, humi)
    else:
        #make sure fan is off
        GPIO.output(motor_enable,GPIO.LOW)
        return('/assets/fan_off.png', temp, humi)
   
@app.callback(
        Output('mqtt', 'message'),
        Input('send', 'n_clicks'),
        State('message_to_send', 'value')
    )

def display_output(n_clicks, message_payload):
    if n_clicks:
        return {
            'topic': MESSAGE_OUT_TOPIC,
            'payload' : message_payload
        }
    return {
            'topic': MESSAGE_OUT_TOPIC,
            'payload' : ""
        }

def checkEmailReply():
    global isFanOn
    #search for an email regarding the temature
    messages = mb.fetch(criteria=AND(subject='Temperature Alert', body='YES', from_= email_receiver))
    #this will contain YES if user resonded, or will be empty if they didnt
    
    #auto reply is set to YES so the fan will always turn on
    print('turn on fan')
    GPIO.output(motor_enable, GPIO.HIGH)
    GPIO.output(motor_turn, GPIO.HIGH)
    return True
        
if __name__ == "__main__":
    app.run_server(debug=True)