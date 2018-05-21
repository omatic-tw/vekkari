#!/usr/bin/env python

##
# epaper-clock.py
#
# Copyright (C) Jukka Aittola (jaittola(at)iki.fi)
#
 # Permission is hereby granted, free of charge, to any person obtaining a copy
 # of this software and associated documnetation files (the "Software"), to deal
 # in the Software without restriction, including without limitation the rights
 # to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 # copies of the Software, and to permit persons to  whom the Software is
 # furished to do so, subject to the following conditions:
 #
 # The above copyright notice and this permission notice shall be included in
 # all copies or substantial portions of the Software.
 #
 # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 # IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 # FITNESS OR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 # AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 # LIABILITY WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 # OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 # THE SOFTWARE.
 ##

##
 #  @filename   :   main.cpp
 #  @brief      :   2.9inch e-paper display (B) demo
 #  @author     :   Yehui from Waveshare
 #
 #  Copyright (C) Waveshare     July 31 2017
 #
 # Permission is hereby granted, free of charge, to any person obtaining a copy
 # of this software and associated documnetation files (the "Software"), to deal
 # in the Software without restriction, including without limitation the rights
 # to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 # copies of the Software, and to permit persons to  whom the Software is
 # furished to do so, subject to the following conditions:
 #
 # The above copyright notice and this permission notice shall be included in
 # all copies or substantial portions of the Software.
 #
 # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 # IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 # FITNESS OR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 # AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 # LIABILITY WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 # OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 # THE SOFTWARE.
 ##

import epd2in7b
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

import RPi.GPIO as GPIO

from datetime import datetime
import time
import locale
import subprocess
import socket

COLORED = 1
UNCOLORED = 0

LOCALE="fi_FI"
DATEFORMAT = "%a %x"
TIMEFORMAT = "%H:%M"
FONT = '/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf'

class Fonts:
    def __init__(self, timefont_size, datefont_size, datafont_size):
        self.timefont = ImageFont.truetype(FONT, timefont_size)
        self.datefont = ImageFont.truetype(FONT, datefont_size)
        self.datafont = ImageFont.truetype(FONT, datafont_size)

def main():
    #locale.setlocale(locale.LC_ALL, LOCALE)
    locale.setlocale(locale.LC_ALL,'en_US.UTF-8')

    epd = epd2in7b.EPD()
    epd.init()
    epd.set_rotate(epd2in7b.ROTATE_270)

    fonts = Fonts(timefont_size = 40, datefont_size = 20, datafont_size = 20)

    read_button4_for_shutdown()
    clock_loop(epd, fonts)

def clock_loop(epd, fonts):
    while True:
        now = datetime.now()
        draw_clock_data(epd, fonts, now)
        now = datetime.now()
        seconds_until_next_refresh = 120 - now.time().second
        time.sleep(seconds_until_next_refresh)

def draw_clock_data(epd, fonts, datetime_now):
    datestring = datetime_now.strftime(DATEFORMAT).capitalize()
    timestring = datetime_now.strftime(TIMEFORMAT)
    hoststring = socket.gethostname()

    # Create frame buffers
    frame_black = [0] * (epd.width * epd.height / 8)
    frame_red = [0] * (epd.width * epd.height / 8)

    epd.draw_string_at(frame_black, 20, 0, timestring, fonts.timefont, COLORED)
    epd.draw_string_at(frame_red, 20, 40, datestring, fonts.datefont, COLORED)
    epd.draw_string_at(frame_black, 20, 65, hoststring, fonts.datafont, COLORED)
    epd.draw_string_at(frame_black, 20, 90, "Owner : Jeremy Wu", fonts.datafont, COLORED)
    fn_ip_show(epd, fonts, frame_black, frame_red)
    epd.display_frame(frame_black, frame_red)

def read_button4_for_shutdown():
    GPIO.setmode(GPIO.BCM)
    pin = 19  # 4th button in the 2.7 inch hat this pin according to the schematics.
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(pin, GPIO.FALLING, callback=shutdown_button_pressed, bouncetime=200)

# management interface name
mgmt_intf = 'eth0'
mgmt_intf_wlan1 = 'wlan2'
mgmt_intf_ip_addr = ['192', '168', '000', '001']
mgmt_intf_prefix = 24

def fn_intf_is_avail(intf):
    import netifaces

    intf_list = netifaces.interfaces()
    return (intf in intf_list)

def fn_intf_is_linkup(intf):
    link_state = tuple(open('/sys/class/net/'+intf+'/operstate', 'r'))
    return ('up' in link_state[0])

def fn_ip_show(epd, fonts, frame_black, frame_red):
    import socket
    import netifaces
    global mgmt_intf
    global mgmt_intf_wlan1

#    buttons = (
#        rdas_lcd_plate.BTN_SEL, rdas_lcd_plate.BTN_UP, rdas_lcd_plate.BTN_DOWN, rdas_lcd_plate.BTN_LEFT, rdas_lcd_plate.BTN_RIGHT # return
#    )

    # show IP address and subnet mask settings
    addr_info_wlan1 = False
    if fn_intf_is_avail(mgmt_intf) is False:
        epd.draw_string_at(frame_red, 20, 120, mgmt_intf+' not exist', fonts.datafont, COLORED)
    elif fn_intf_is_linkup(mgmt_intf) is False:
        epd.draw_string_at(frame_red, 20, 120, mgmt_intf+' link-down', fonts.datafont, COLORED)
    else:
        addr_info = netifaces.ifaddresses(mgmt_intf)
        if netifaces.AF_INET in addr_info.keys():
            ip_addr = addr_info[netifaces.AF_INET][0]['addr']
            netmask = addr_info[netifaces.AF_INET][0]['netmask']
            epd.draw_string_at(frame_black, 20, 120, 'Eth0  : ', fonts.datafont, COLORED)
            epd.draw_string_at(frame_red, 110, 120, ip_addr, fonts.datafont, COLORED)
        else:
            epd.draw_string_at(frame_red, 20, 120, 'Eth0 ha no address.', fonts.datafont, COLORED)


    if fn_intf_is_avail(mgmt_intf_wlan1) is False:
        epd.draw_string_at(frame_red, 20, 140, mgmt_intf_wlan1+' not exist', fonts.datafont, COLORED)
    elif fn_intf_is_linkup(mgmt_intf_wlan1) is False:
        epd.draw_string_at(frame_red, 20, 140, mgmt_intf_wlan1+' link-down', fonts.datafont, COLORED)
    else:
        addr_info_wlan1 = netifaces.ifaddresses(mgmt_intf_wlan1)
        if netifaces.AF_INET in addr_info_wlan1.keys():
            ip_addr_wlan1 = addr_info_wlan1[netifaces.AF_INET][0]['addr']
            epd.draw_string_at(frame_black, 20, 140, 'Wlan2 : ', fonts.datafont, COLORED)
            epd.draw_string_at(frame_red, 110, 140, ip_addr_wlan1, fonts.datafont, COLORED)
        else:
            epd.draw_string_at(frame_red, 20, 140, 'Wlan2 has no address.', fonts.datafont, COLORED)



def shutdown_button_pressed(pin):
    print("Button %d was pressed. Shutting down" % pin)
    subprocess.call(["sudo", "poweroff"])

if __name__ == '__main__':
    main()
