from machine import Timer
from machine import I2C
from machine import SD
from robust import MQTTClient
from machine import UART
from machine import Pin
from machine import WDT
import network
import time
import machine
import os
import sht31
import pycom
import math
import binascii


wlan = network.WLAN(mode=network.WLAN.STA)
wlan.connect('WiFi_Name', auth=(network.WLAN.WPA2, 'WiFi_Password'))

while not wlan.isconnected():
    machine.idle()

print("Connected to Wifi\n")
client = MQTTClient("pi", "IP", port=1883)

client.connect()
time.sleep(10)
uart = UART(1, 9600, pins=("G28","G22"), timeout_chars=2000)
i2c = I2C(0, I2C.MASTER, baudrate=100000)
sensor = sht31.SHT31(i2c, addr=0x44)
rtc = machine.RTC()
rtc.ntp_sync("tw.pool.ntp.org", 3600)
sd = SD()
os.mount(sd, '/sd')

# check the content
os.listdir('/sd')

# try some standard file operations
deviceid = binascii.hexlify(machine.unique_id())
p_out = Pin('P3', mode=Pin.OUT)
p_out1 = Pin('P22', mode=Pin.OUT)
def axis():
    i2c.writeto_mem(29, 0x2A, bytes([0x00]))
    i2c.writeto_mem(29, 0x2A, bytes([0x01]))
    i2c.writeto_mem(29, 0x0E, bytes([0x00]))
    data = i2c.readfrom_mem(29, 0x00, 7)

    xAccl = (data[1] * 256 + data[2]) / 16
    if xAccl > 2047 :
        xAccl -= 4096

    yAccl = (data[3] * 256 + data[4]) / 16
    if yAccl > 2047 :
        yAccl -= 4096

    zAccl = (data[5] * 256 + data[6]) / 16
    if zAccl > 2047 :
        zAccl -= 4096
    mes =  '"' + 'x' + '"' + ':' + str(xAccl) + ','+ '"' + 'y' + '"' + ':' + str(yAccl) + ','+ '"' + 'z' + '"' + ':' + str(zAccl)
    return mes
def gps():
    while True:
        gps_data = uart.readline()
        st_data = str(gps_data)
        name = st_data[0:8]
        if name == "b'$GNGGA" :
            return st_data  
while True:
    th = sensor.get_temp_humi()
    p_out.value(0)
    p_out1.value(0)
    time.sleep(10)
    datetime = str(rtc.now()[0]) + '-' + str(rtc.now()[1]) +'-' + str(rtc.now()[2]) + ' ' + str(rtc.now()[3]) + ':' + str(rtc.now()[4]) + ':' + str(rtc.now()[5]) + '.' + str(rtc.now()[6])
    runaxis = axis()
    rungps = gps()
    bssid = binascii.hexlify(wlan.bssid())
    message = '{' + '"' +'deviceID' + '"' +':' + '"' + str(deviceid) + '"' + ',' + '"' +'temp' + '"' +':' + str(th[0]) + ',' + '"' + 'hum' + '"' + ':' + str(th[1]) + ','+ '"' + 'datetime'+ '"' + ':' + '"' + str(datetime) + '"' + ',' + str(runaxis) + ',' + '"' +'gps' + '"' +':' + '"' + str(rungps) + '"' + ',' + '"' +'bssid' + '"' +':' + '"' + str(bssid) + '"' +'}'
    status = wlan.isconnected()
    if status == True :
        print ("Upload mode\n")
        print (message)
        client.publish(topic="/" + str(deviceid) , msg=message)
        p_out.value(1)
        time.sleep(50)
    else :
        wlan.connect('IIS-NRL', auth=(network.WLAN.WPA2, 'wireless'))
        print ("Device mode\n")
        print (message)
        p_out1.value(1)
        time.sleep(50)
    f = open('/sd/data.txt','a')
    f.write(message)
    f.close()
    csvmessage = str(deviceid) + ',' + datetime + ',' + str(th[0]) + ','  + str(th[1]) + ','
    fc = open('/sd/data.csv','a')
    fc.write('\r')
    fc.write(csvmessage)
    fc.close()
