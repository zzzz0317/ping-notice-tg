import sys
import json
from ping3 import ping
import time
from datetime import datetime
import requests

CONFIG_FILE_PATH = "./config.json"
TARGET_HOST = ""
LOOP_DELAY = 0
RESEND_DELAY = 0
NOTICE_HEADER = "PingNoticeTG"
TELEGRAM_BOT_URL = ""
TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID = ""


def read_config():
    with open(CONFIG_FILE_PATH, 'r') as f:
        config = json.load(f)
        global TARGET_HOST
        TARGET_HOST = config["TARGET_HOST"]
        global LOOP_DELAY
        LOOP_DELAY = config["LOOP_DELAY"]
        global RESEND_DELAY
        RESEND_DELAY = config["RESEND_DELAY"]
        global NOTICE_HEADER
        NOTICE_HEADER = config["NOTICE_HEADER"]
        global TELEGRAM_BOT_URL
        TELEGRAM_BOT_URL = config["TELEGRAM_BOT_URL"]
        global TELEGRAM_BOT_TOKEN
        TELEGRAM_BOT_TOKEN = config["TELEGRAM_BOT_TOKEN"]
        global TELEGRAM_CHAT_ID
        TELEGRAM_CHAT_ID = config["TELEGRAM_CHAT_ID"]


def ping_target(target):
    result = ping(target)
    if result is None:
        print('ping {} fail'.format(target))
        return False
    print('ping {} succeed, reply time={}ms'.format(target, "%.2f" % (result * 1000)))
    return True


def get_notice_str(msg):
    global NOTICE_HEADER
    global TARGET_HOST
    return '{}\n{}\nTarget: {}\n{}'.format(NOTICE_HEADER, datetime.now(), TARGET_HOST, msg)


def send_notification(msg):
    global TELEGRAM_BOT_URL
    global TELEGRAM_BOT_TOKEN
    global TELEGRAM_CHAT_ID
    REQUEST_URL = "{}{}/sendMessage".format(TELEGRAM_BOT_URL, TELEGRAM_BOT_TOKEN)
    REQUEST_DATA = {'chat_id': TELEGRAM_CHAT_ID, 'text': msg, "disable_notification": "false"}
    try:
        requests.post(url=REQUEST_URL, data=REQUEST_DATA)
    except TimeoutError:
        print("Send notification timeout!")
        return
    except Exception as e:
        print("Send notification fail cause by {}".format(e))
        return


def get_unix_time():
    return int(time.time())


if __name__ == '__main__':
    if len(sys.argv) > 1:
        CONFIG_FILE_PATH = sys.argv[1]
    print("Read config file:", CONFIG_FILE_PATH)
    read_config()
    send_notification(get_notice_str("PingNoticeTG Initialized"))
    while True:
        if not ping_target(TARGET_HOST):
            print("Packet drop detected, wait 3s to confirm")
            time.sleep(3)
            if ping_target(TARGET_HOST):
                print("Packet drop false alarm")
            else:
                print("Packet drop confirmed, send notification")
                send_notification(get_notice_str("Packet drop confirmed"))
                TIME_OFFLINE = get_unix_time()
                while not ping_target(TARGET_HOST):
                    if (get_unix_time() - TIME_OFFLINE) >= RESEND_DELAY:
                        TIME_OFFLINE = get_unix_time()
                        print("Offline time reached set value, send notification")
                        send_notification(get_notice_str("Packet drop still not solve"))
                    print('sleep {}s to continue'.format(LOOP_DELAY))
                    time.sleep(LOOP_DELAY)
                print("Device online, send notification")
                send_notification(get_notice_str("Packet drop solved"))

        print('sleep {}s to continue'.format(LOOP_DELAY))
        time.sleep(LOOP_DELAY)
