from dash import Dash, dcc, html, ctx, Output, Input
import dash_daq as daq
#import RPi.GPIO as GPIO
#import Freenove_DHT as DHT
import smtplib # to send email
from imap_tools import MailBox, AND # to receive email
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
mb = MailBox(inbox_server).login(email_sender, sender_password)

isFanOn = False
motor_enable = 15; #GPIO 22
motor_turn = 13; #GPIO 27


#GPIO.setup(motor_enable,GPIO.OUT)
#GPIO.setup(motor_turn,GPIO.OUT)


app.layout = html.Div([
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
        daq.GraduatedBar(
        id='intensity',
        label="Light Intensity",
        max=100,
        value=0
        )
        ]
    )

@app.callback(
    Output('temperature','value'),
    Output('humidity','value'),
    Input('time', 'n_intervals')
)
def getTemp(data):
    global isFanOn
    #dht.readDHT11()
    #temp = dht.temperature
    temp = 20
    #humi = dht.humidity
    humi = 50
    #if the temp is over 22, send the user a notice
    print(isFanOn, 'isFanOn before')
    if ((float(temp) > 22) and (isFanOn is False)):
        message = 'Subject: Temperature Alert\n\nThe temperature of your room is {}, would you like to turn on the fan?\nYou have 1 minute to answer. '.format(temp)
        #send the email
        smtpobject.sendmail(email_sender, email_receiver, message)
        print("email sent")
        time.sleep(2)
        #check if the user responded YES, if so turn on the fan
        isFanOn = checkEmailReply()
    print("displaying data", temp, humi, isFanOn)    
    return (temp,humi)
                     
            
            
def checkEmailReply():
    global isFanOn
    
    #search for an email regarding the temature
    messages = mb.fetch(criteria=AND(subject='Temperature Alert', body='YES', from_= email_receiver))
    #this will contain YES if user resonded, or will be empty if they didnt
    # emails = ''
    # #this contains the id of the email
    # emailId = 0
    # print("going in emails")
    # for ms in messages:
    #     #assign the values
    #     emailId = ms.uid
    #     emails=ms.text
    #     print("checking email")

                
    # #if the search did not find a YES response...
    # if (emails == ''):
    #     print('user does not want fan')
    #     return False
    # #else turn on the fan
    # else:
    #     print('turn on fan')
    #     #GPIO.output(motor_enable, GPIO.HIGH)
    #     #GPIO.output(motor_turn, GPIO.HIGH)
    #     return True

    #User is set to auto-reply YES, so the fan is turned on
    #GPIO.output(motor_enable, GPIO.HIGH)
    #GPIO.output(motor_turn, GPIO.HIGH)
    return True

    
if __name__ == "__main__":
    app.run_server(debug=True)