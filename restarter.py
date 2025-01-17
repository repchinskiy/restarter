import datetime
import socket
import subprocess
import sys
import threading
import time

import requests
from flask import Flask

app = Flask(__name__)

TELEGRAM_ALERT_BASE_URL = ""
chat_id = ""
check_commands_url = []


def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]


def init():
    writeln("Init ...\n")

    global TELEGRAM_ALERT_BASE_URL, chat_id

    # if len(sys.argv) > 1:
    #     need_restart_node = int(sys.argv[1]) == 1

    cmd_url = "unknown"
    if len(sys.argv) > 1:
        TELEGRAM_ALERT_BASE_URL = "https://api.telegram.org/" + sys.argv[1] + "/sendMessage"
    if len(sys.argv) > 2:
        chat_id = sys.argv[2]
    if len(sys.argv) > 3:
        cmd_url = sys.argv[3]
        check_commands_url.append(cmd_url)

    println(
        f'sys_params: {sys.argv[0]} TELEGRAM_ALERT_BASE_URL: {TELEGRAM_ALERT_BASE_URL} chat_id: {chat_id} cmd_url: {cmd_url}')

    run_updater_background()


def fetch_data(url):
    response = requests.get(url)
    response.raise_for_status()  # Проверка на ошибки HTTP
    return response.text


def parse_data(raw_data):
    lines = raw_data.strip().split("\n")
    return [line.split(";") for line in lines]


def writeln(msg):
    sys.stdout.write(msg + "\n")


def println(msg):
    sys.stdout.write(str(datetime.datetime.now()) + ": " + msg + "\n")


def process():
    for commandUrl in check_commands_url:
        println(f'command_url: {commandUrl}')
        raw_data = fetch_data(commandUrl)
        nodes_data = parse_data(raw_data)
        for cmd_name, cmd_check, cmd_restart in nodes_data:
            println(f'cmd_name: {cmd_name} cmd_check:{cmd_check} cmd_restart: {cmd_restart}')
            if cmd_name.startswith("#"): continue
            result = subprocess.run(cmd_check, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            status = result.returncode
            println(f'status: {status}')
            if not status == 0:
                subprocess.run(cmd_restart, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                content = f'{get_ip_address()}\n{cmd_name}'
                println(f'tg_url: {TELEGRAM_ALERT_BASE_URL} chat_id: {chat_id} text: {content}')
                requests.get(url=TELEGRAM_ALERT_BASE_URL, params={'chat_id': chat_id, 'text': content})

    f = open("/root/restarter/restarter/restarter_local.csv", "r")
    lines = f.readlines()
    f.close()
    nodes_data = [line.split(";") for line in lines]

    for cmd_name, cmd_check, cmd_restart in nodes_data:
        println(f'cmd_name: {cmd_name} cmd_check:{cmd_check} cmd_restart: {cmd_restart}')
        if cmd_name.startswith("#"): continue
        result = subprocess.run(cmd_check, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        status = result.returncode
        println(f'status: {status}')
        if not status == 0:
            println(f'cmd_restart: {cmd_restart}')
            subprocess.run(cmd_restart, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            status = result.returncode
            println(f'status: {status}')
            content = f'{get_ip_address()}\n{cmd_name}'
            println(f'tg_url: {TELEGRAM_ALERT_BASE_URL} chat_id: {chat_id} text: {content}')
            requests.get(url=TELEGRAM_ALERT_BASE_URL, params={'chat_id': chat_id, 'text': content})


def run_updater():
    while True:
        process()
        time.sleep(60 * 10)


def run_updater_background():
    writeln("Run background tasks ...\n")
    updater_thread = threading.Thread(target=run_updater)
    updater_thread.start()


def get_sys_info():
    return get_ip_address()


def test(cmd=None):
    writeln("Test mode: ")

    # nodes_data = parse_data("1.Restart Titan(d);sudo docker ps | grep titan > /dev/null 2>&1 && exit 0 || exit 1;sudo docker restart titan")
    # nodes_data = parse_data("#0.Mock(s);exit 1; exit 0")
    # for cmd_name, cmd_check, cmd_restart in nodes_data:
    #     println(f'cmd_name: {cmd_name} cmd_check:{cmd_check} cmd_restart: {cmd_restart}')
    # cmd = "sudo docker-compose -f ~/.spheron/fizz/docker-compose.yml restart"
    cmd = "sudo docker-compose -f /root/.spheron/fizz/docker-compose.yml restart"
    println(f'cmd: {cmd}')
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # result = subprocess.run([cmd], capture_output=True, text=True)
    rcode = result.returncode
    println(f'result.returncode: {rcode}')
    println(f'result.stdout: {result.stdout}')


if __name__ == "__main__":
    # test()
    init()
