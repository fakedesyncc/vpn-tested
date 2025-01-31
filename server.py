import json
import logging
import subprocess
from flask import Flask, render_template, request, jsonify
from threading import Thread, Lock

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
active_connections = {}
config_lock = Lock()

CONFIG_TEMPLATES = {
    "socks5": {
        "inbounds": [{
            "listen": "127.0.0.1",
            "port": 1080,
            "protocol": "socks",
            "settings": {"auth": "noauth", "udp": True}
        }],
        "outbounds": [{
            "protocol": "freedom",
            "tag": "direct"
        }]
    },
    "vless": {
        "inbounds": [{
            "listen": "127.0.0.1",
            "port": 1080,
            "protocol": "socks",
            "settings": {"auth": "noauth", "udp": True}
        }],
        "outbounds": [{
            "protocol": "vless",
            "settings": {
                "vnext": [{
                    "address": None,
                    "port": None,
                    "users": [{"id": None, "flow": "xtls-rprx-vision"}]
                }]
            },
            "streamSettings": {
                "network": "tcp",
                "security": "reality",
                "realitySettings": {
                    "serverName": None,
                    "publicKey": None,
                    "fingerprint": "chrome"
                }
            }
        }]
    }
}

class ConnectionManager:
    def __init__(self):
        self.process = None
        self.connection_type = None
        self.config = None

    def start_connection(self, conn_type, config):
        with config_lock:
            self.stop_connection()
            config_file = f"config_{conn_type}.json"
            with open(config_file, 'w') as f:
                json.dump(config, f)
            
            self.process = subprocess.Popen(
                ['xray', 'run', '-c', config_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )
            Thread(target=self.log_output).start()
            self.connection_type = conn_type
            self.config = config

    def stop_connection(self):
        if self.process:
            self.process.terminate()
            self.process = None

    def log_output(self):
        while self.process and self.process.poll() is None:
            line = self.process.stdout.readline()
            if line:
                logging.info(f"[Xray] {line.decode().strip()}")

manager = ConnectionManager()

@app.route('/')
def index():
    return render_template('control_panel.html')

@app.route('/connect', methods=['POST'])
def connect():
    try:
        data = request.json
        conn_type = data['type']
        config = CONFIG_TEMPLATES[conn_type].copy()

        if conn_type == "socks5":
            config['outbounds'][0]['settings'] = {
                "servers": [{
                    "address": data['host'],
                    "port": int(data['port'])
                }]
            }
        elif conn_type == "vless":
            config['outbounds'][0]['settings']['vnext'][0].update({
                "address": data['host'],
                "port": int(data['port'])
            })
            config['outbounds'][0]['settings']['vnext'][0]['users'][0]['id'] = data['uuid']
            config['outbounds'][0]['streamSettings']['realitySettings'].update({
                "serverName": data['sni'],
                "publicKey": data['public_key']
            })

        manager.start_connection(conn_type, config)
        return jsonify({"status": "connected", "type": conn_type})

    except Exception as e:
        logging.error(str(e))
        return jsonify({"status": "error", "message": str(e)})

@app.route('/disconnect', methods=['POST'])
def disconnect():
    try:
        manager.stop_connection()
        return jsonify({"status": "disconnected"})
    except Exception as e:
        logging.error(str(e))
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)