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

#tpin -> DHT11
tpin = 35; #GPIO 19
motor_enable = 15; #GPIO 22
motor_turn = 13; #GPIO 27

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(motor_enable,GPIO.OUT)
GPIO.setup(motor_turn,GPIO.OUT)
dht = DHT.DHT(tpin)
GPIO.output(motor_enable, GPIO.LOW)

app.layout = html.Div([
        #temp/hum
        dcc.Interval(id = "time"),
        html.H1(children="IOT Dashboard"),
        daq.Thermometer(
            id='temperature',
            value=0,
            label="Current Temperature",
            labelPosition='top',
            max=50
            ),
        html.Br(),
        html.Br(),
        daq.Gauge(
            id='humidity',
            label="Current Humidity",
            labelPosition='top',
            max=100,
            value=0
            ),
        #mqtt pub/sub
        dash_mqtt.DashMqtt(
        id='mqtt',
        broker_url=TEST_SERVER,
        broker_port = TEST_SERVER_PORT,
        #broker_path = TEST_SERVER_PATH,
        topics=[MESSAGE_IN_TOPIC]
        ),
        html.H1('MQTT echo'),
        html.P('MQTT echo server to ' + TEST_SERVER + ' on port ' + str(TEST_SERVER_PORT)),
        dcc.Input(
            id='message_to_send',
            placeholder='message to send',
            debounce = True),
        html.Button('Send',id='send'),
        html.Div(id='return_message')
        ]
    )

@app.callback(
    Output('temperature','value'),
    Output('humidity','value'),
    Input('time', 'n_intervals')
)

def getTemp(data):
        dht.readDHT11()
        temp = dht.temperature
        humi = dht.humidity
        
        #if the temp is over 22, send the user a notice
        if (float(temp) > 22):
            message = 'Subject: Temperature Alert\n\nThe temperature of your room is {}, would you like to turn on the fan?\nYou have 1 minute to answer. '.format(temp)
            #send the email
            smtpobject.sendmail(email_sender, email_receiver, message)
            time.sleep(2)
            checkEmailReply()
        return (temp,humi);
   
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
    #login to the inbox
    mb = MailBox(inbox_server).login(email_sender, sender_password)
    #search for an email regarding the temature
    messages = mb.fetch(criteria=AND(subject='Temperature Alert', body='YES', from_= email_receiver))
    #this will contain YES if user resonded, or will be empty if they didnt
    emails = ''
    #this contains the id of the email so it can be deleted
    emailId = 0
    for ms in messages:
        #assign the values
        emailId = ms.uid
        emails=ms.text
                
    #if the search did not find a YES response...
    if (emails == ''):
        print('user does not want fan')  
    #else delete the message once it has been processed by the program
    else:
        mb.delete(emailId)
        print('turn on fan')
        GPIO.output(motor_enable, GPIO.HIGH)
        GPIO.output(motor_turn, GPIO.HIGH)
        
if __name__ == "__main__":
    app.run_server(debug=True)