#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time       : 2017/6/21 下午4:23
# @Author     : Vilson Yuan
# @File       : check_marathon_port.py
# @Description :
import json
import os
import re
import subprocess
import time
import requests

LOG_FILE = '/var/log/marathon-lb-dumplicate_port'


def check_conflict_port(logger, config):
    conflict_msg = []
    # status, resp = commands.getstatusoutput("netstat -antlp|grep LISTEN")

    for line in config.splitlines():
        if line.startswith("frontend") and re.findall(r'frontend [^0-9]+_[0-9]+$', line):
            port = line[line.rfind("_") + 1:]
            check_port(logger, port)


def check_port(logger, port):
    pro = subprocess.Popen("/sbin/lsof -i:%s -P -sTCP:LISTEN|grep -v COMMAND|grep -v haproxy" % port,
                           stdout=subprocess.PIPE, shell=True)
    stdout, stderr = pro.communicate()
    if stderr:
        logger.debug("error start command 'netstat -antlp|grep LISTEN'")
        return

    if stdout:  # conflict
        msg = stdout.splitlines()
        conflict_msg = []
        for line in msg:
            item = line.split()
            conflict_msg.append("conflict: %s %s" % (item[0], item[1]))
            alarm(logger, os.getenv("HOST"))
        write_file(conflict_msg)


def kill_pid(logger, pid):
    pro = subprocess.Popen("kill -9 %s" % pid, stdout=subprocess.PIPE, shell=True)
    stdout, stderr = pro.communicate()
    if stderr:
        logger.error("kill failed %s" % pid)
        return


def alarm(logger, host, url="http://10.3.15.198:1988/v1/push"):
    data = [{
        "metric": "marathon-lb-check",
        "endpoint": host,
        "timestamp": int(time.time()),
        "step": 60,
        "value": 90,
        "counterType": "GAUGE",
        "tags": ""
    }]
    try:
        resp = requests.post(url, data=json.dumps(data), headers={"Content-Type": "application/json"})
        logger.debug("alarm - %s", resp.text)
    except Exception as e:
        logger.error("failed to alram: %s", str(e))


def write_file(msg):
    with open(LOG_FILE, 'w+') as fp:
        fp.writelines(msg)
