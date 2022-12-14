from dash import Dash, dcc, html, ctx, Output, Input
from dash.dependencies import Input, Output, State
import dash_daq as daq
import RPi.GPIO as GPIO
import Freenove_DHT as DHT
import smtplib # to send email
import time
from time import sleep
import dash_mqtt
import paho.mqtt.client as mqtt
import imaplib, email
import sqlite3

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

MESSAGE2_OUT_TOPIC = 'IoTlab/RFID'
MESSAGE2_IN_TOPIC = 'IoTlab/RFID'
#vanieriot

smtpobject = smtplib.SMTP(server, 587)
smtpobject.starttls()
smtpobject.login(email_sender,sender_password)

#login to the sender inbox
con = imaplib.IMAP4_SSL(server)
con.login(email_sender, sender_password)
con.select("INBOX")

#tpin -> DHT11                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               
tpin = 35; #GPIO 19
motor_enable = 15; #GPIO 22
motor_turn = 13; #GPIO 27
led_pin = 22; #GPIO 25
isFanOn = False
#keepFanOff will be true if the user manually turned off the fan (the fan will no longer turn on by itself)
keepFanOff = False
hasEmailSent = False
hasReplied = False
hasLEDEmailSent = False
lightresult = 0
LEDStatus = False
UserId = 0
Profile = ""
Lightdb = 0
Tempdb = 0
Humdb = 0
RFID = ""

def db():
    global UserId
    global Profile
    global Lightdb
    global Tempdb
    global Humdb
    global RFID
    try:
        #connection_obj = sqlite3.connect('IoTdb.db')
        print("Info has been added")
        #cursor_obj = connection_obj.cursor()
        #connection_obj.execute("""DROP TABLE users""")
        #connection_obj.execute("""CREATE TABLE users(UserId int,Profile varchar(100),RFID varchar(100),Lightdb int,Tempdb int,Humdb int);""")
      
        #connection_obj.execute(
         #   """INSERT INTO users (UserId,Profile,RFID,Lightdb,Tempdb,Humdb) VALUES (1,"Atoz","833463d",450,10,30)""")
      
        #connection_obj.commit()
      
    # Close the connection
        connection_obj.close()
    except:
        print("Information has been rejected")
        
    connection_obj = sqlite3.connect('IoTdb.db')
    # cursor object
    cursor_obj = connection_obj.cursor()
      
    # to select all column we will use
      
    cursor_obj.execute('SELECT * FROM users WHERE RFID = ?', (RFID, ))
      
    print("All the data")
    output = cursor_obj.fetchall()
    for row in output:
      print(row)
      UserId = row[0]
      Profile = row[1]
      Lightdb = row[3]
      Tempdb = row[4]
      Humdb = row[5]
    print(UserId)
      
    connection_obj.commit()
      
    # Close the connection
    connection_obj.close()

#some functions to help with reading emails
#gets the body of the email
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
con.logout()
#note the size of the inbox before functions are called
inboxSize = len(msgs)

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(led_pin,GPIO.OUT)
GPIO.setup(motor_enable,GPIO.OUT)
GPIO.setup(motor_turn,GPIO.OUT)
GPIO.setup(motor_turn,GPIO.OUT)
dht = DHT.DHT(tpin)
GPIO.output(motor_enable, GPIO.LOW)

app.layout = html.Div(
    style={'background-image': 'url("/assets/background.jpg")', 'background-size': 'cover', 'width': '100%', 'height': '100%','position': 'fixed'},
    children=[
        dcc.Interval(id = "time", interval = 3000),
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
        html.H1(children="Welcome Back, " + Profile),
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
        daq.LEDDisplay(
        id='intensity',
        label="Light Intensity",
        value=0,
        backgroundColor="#000000"
        ),
        html.Img(src='/assets/light_off.PNG', id="led", style={'margin-left':'auto','margin-right':'auto','display':'block'})
        ]
    )

@app.callback(
    Output('fan','src'),
    Output('temperature','value'),
    Output('humidity','value'),
    Output('intensity','value'),
    Output('led','src'),
    Input('time', 'n_intervals'),
    Input('turnOffFan', 'n_clicks')
)

def displayData(data,n_clicks):
    global hasEmailSent
    global hasReplied
    global con
    global isFanOn
    global lightresult
    global LEDStatus
    #the default state of ledImage
    ledImage = '/assets/light_off.PNG'

    #assign the correct image based on LEDStatus
    print(LEDStatus)
    if (LEDStatus is True):
        ledImage = '/assets/light_on.png'
    else:
        ledImage = '/assets/light_off.PNG'
        
    #get button info
    dht.readDHT11()
    temp = dht.temperature
    humi = dht.humidity
    print ("temp is :",temp)
    #if the temp is over 22, send the user a notice
    if ((float(temp) > tempdb) and (hasEmailSent is False)):
        message = 'Subject: Temperature Alert\n\nThe temperature of your room is {}, would you like to turn on the fan?\n'.format(temp)
        #send the email
        smtpobject.sendmail(email_sender, email_receiver, message)
        hasEmailSent = True
        return('/assets/fan_off.png', temp, humi,lightresult,ledImage)
        
    #constantly check for email reply. refresh inbox and check if the size has changed

    con = imaplib.IMAP4_SSL(server)
    con.login(email_sender, sender_password)
    con.select("INBOX")
    updatedInbox = get_emails(search('FROM', 'iottest031@gmail.com', con))
    con.logout()
    

    #while there is no reply, keep checking, and keep fan off

    if(inboxSize == len(updatedInbox)):
        return('/assets/fan_off.png', temp, humi, lightresult,ledImage)
    

    #if there is a reply, check if the user said yes
    if ((hasReplied is False) and checkEmailReply(updatedInbox)):
        GPIO.output(motor_enable,GPIO.HIGH)
        GPIO.output(motor_turn,GPIO.HIGH)
        return ('/assets/fan_on.png', temp, humi, lightresult,ledImage)
    elif(hasReplied is False) and (checkEmailReply(updatedInbox) is False):
        return('/assets/fan_off.png', temp, humi, lightresult,ledImage)
    
    #check button status
    if (isFanOn and (n_clicks == 0)):
        #the fan can only be turned off through the button
        return('/assets/fan_on.png', temp, humi, lightresult,ledImage)
    else:
        #make sure fan is off
        isFanOn = False
        GPIO.output(motor_enable,GPIO.LOW)
        GPIO.output(motor_turn,GPIO.LOW)
        return('/assets/fan_off.png', temp, humi, lightresult,ledImage)

    return ('/assets/fan_off.png', temp, humi, lightresult,ledImage) 
   
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

def checkEmailReply(inbox):
    global hasReplied
    global isFanOn
    print("checking reply")
    hasReplied = True
    #Once the sender has received a reply from the user, check if the user said yes
    #get the most recent email
    msg = inbox[len(inbox)-1]
    #get the body of the email
    body = get_body(email.message_from_bytes(msg[0][1]))
    #if the user said yes, turn on the fan
    if ("yes" in str(body)):
        GPIO.output(motor_enable,GPIO.HIGH)
        GPIO.output(motor_turn,GPIO.HIGH)
        isFanOn = True
        print("user replied yes")
        return True
    else:
        print("user did not reply yes")
        return False

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("IoTlab/photoValue")
    client.subscribe("IoTlab/RFID")

def on_message(client, userdata, msg):
    global hasLEDEmailSent
    global lightresult
    global LEDStatus
    global RFID
    global Lightdb
    date = time.strftime('%d/%m/%Y %H:%M:%S')
    print(msg.payload.decode("utf-8"))
    if('photoValue' in msg.topic):
        lightresult = float(msg.payload.decode("utf-8"))
        print(lightresult + float(0))
        if (lightresult <= Lightdb) and (hasLEDEmailSent is False):
            GPIO.output(led_pin,GPIO.HIGH)
            message = 'Subject: The Light is ON at {}\n'.format(date) #, date)
            #send the email
            smtpobject.sendmail(email_sender, email_receiver, message)
            hasLEDEmailSent = True
            LEDStatus = True
            sleep(3)
        #if an email has already been sent but the light must be turned on
        elif (lightresult <= Lightdb):
            GPIO.output(led_pin,GPIO.HIGH)
            LEDStatus = True
        else:
            GPIO.output(led_pin,GPIO.LOW)
            LEDStatus = False
    if('RFID' in msg.topic):
        print(msg.payload.decode("utf-8"))
        RFID = str(msg.payload.decode("utf-8"))
        print(RFID)
        db()
    
if __name__ == "__main__":
    client = mqtt.Client()
    client.connect("0.0.0.0", 1883)
    client.on_connect = on_connect
    client.on_message = on_message
    client.loop_start()
    app.run_server(debug=True)