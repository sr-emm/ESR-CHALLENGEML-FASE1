"""
app.py
======
Backend Refactorizado v2
Mejoras:
- Debug explícito: Muestra en el output qué protocolo y puerto está usando.
- Sanitización de inputs: Fuerza minúsculas en el protocolo.
"""

from flask import Flask, render_template, request, session, make_response
from netmiko import (
    ConnectHandler,
    NetmikoTimeoutException,
    NetmikoAuthenticationException,
)
from datetime import datetime
import re

app = Flask(__name__)
app.secret_key = "lab-secret-key-change-me"

IGNORE_VLANS = {"1002", "1003", "1004", "1005"}

def build_device(device_ip, username, password, port, protocol):
    # Aseguramos que protocol sea string limpio
    protocol = str(protocol).strip().lower()
    
    # Lógica explícita
    if protocol == "ssh":
        device_type = "cisco_ios"
    elif protocol == "telnet":
        device_type = "cisco_ios_telnet"
    else:
        # Fallback por seguridad
        device_type = "cisco_ios"

    return {
        "device_type": device_type,
        "host": device_ip,
        "username": username,
        "password": password,
        "secret": password,
        "port": port,
    }

def fetch_current_data(device_ip, username, password, port, protocol):
    device = build_device(device_ip, username, password, port, protocol)
    debug_info = f"--- DEBUG: Conectando vía {protocol.upper()} al puerto {port} ---\n"
    
    try:
        with ConnectHandler(**device) as conn:
            conn.enable()
            prompt = conn.find_prompt()
            hostname = prompt[:-1] if prompt else "Unknown"
            out_vlan = conn.send_command("show vlan brief")
            
            # Devolvemos el debug + el output real
            return True, {"vlans": parse_vlans_from_show(out_vlan), "hostname": hostname}, debug_info + out_vlan

    except Exception as e:
        return False, None, debug_info + f"FALLO DE CONEXIÓN: {str(e)}"

def apply_config(vlans, hostname, device_ip, username, password, port, protocol):
    device = build_device(device_ip, username, password, port, protocol)
    debug_info = f"--- DEBUG: Aplicando cambios vía {protocol.upper()} ---\n"
    
    commands = []
    if hostname: commands.append(f"hostname {hostname}")
    for vlan in vlans:
        commands.append(f"vlan {vlan['id']}")
        commands.append(f"name {vlan['name']}")

    if not commands: return False, "No hay cambios definidos."

    try:
        with ConnectHandler(**device) as conn:
            conn.enable()
            output = conn.send_config_set(commands)
        return True, debug_info + output
    except Exception as e:
        return False, debug_info + str(e)

def save_mem(device_ip, username, password, port, protocol):
    device = build_device(device_ip, username, password, port, protocol)
    try:
        with ConnectHandler(**device) as conn:
            conn.enable()
            output = conn.save_config()
        return True, f"Protocolo usado: {protocol.upper()}\n" + output
    except Exception as e:
        return False, str(e)

def download_txt(device_ip, username, password, port, protocol):
    device = build_device(device_ip, username, password, port, protocol)
    try:
        with ConnectHandler(**device) as conn:
            conn.enable()
            output = conn.send_command("show running-config")
        return True, output
    except Exception as e:
        return False, str(e)

def upload_tftp_smart(device_ip, username, password, port, protocol, tftp_ip, hostname):
    device = build_device(device_ip, username, password, port, protocol)
    hn = hostname if hostname else "switch-backup"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    filename = f"{timestamp}-{hn}.cfg"

    try:
        with ConnectHandler(**device) as conn:
            conn.enable()
            cmd = f"copy running-config tftp:"
            output = conn.send_command_timing(cmd)
            
            if "Address or name" in output:
                output += conn.send_command_timing(tftp_ip)
            if "Destination filename" in output:
                output += conn.send_command_timing(filename)
            if "confirm" in output or "overwrite" in output:
                 output += conn.send_command_timing("\n")

        return True, output
    except Exception as e:
        return False, str(e)

def parse_vlans_from_show(output):
    vlans = []
    for line in output.splitlines():
        line = line.strip()
        match = re.match(r"^(\d+)\s+(\S+)", line)
        if match:
            v_id, v_name = match.groups()
            if v_id in IGNORE_VLANS: continue
            if len(v_name) > 20: v_name = v_name[:20]
            vlans.append({"id": v_id, "name": v_name})
    return vlans

@app.route("/", methods=["GET", "POST"])
def index():
    vlans = []
    error_msg = None
    success_msg = None
    netmiko_output = None
    
    # Defaults de sesión
    session_data = {k: session.get(k, "") for k in ["device_ip", "username", "port", "hostname", "protocol", "tftp_server"]}
    password = session.get("device_password", "")
    
    # Si la sesión está vacía, forzamos defaults seguros
    if not session_data["protocol"]: session_data["protocol"] = "ssh"
    if not session_data["port"]: session_data["port"] = 22

    if request.method == "POST":
        action = request.form.get("action")
        
        # Leemos el protocolo explícitamente y lo limpiamos
        raw_protocol = request.form.get("protocol", "ssh")
        clean_protocol = raw_protocol.strip().lower()

        form_data = {
            "device_ip": request.form.get("device_ip", "").strip(),
            "username": request.form.get("username", "").strip(),
            "port": request.form.get("port", "").strip(),
            "hostname": request.form.get("hostname", "").strip(),
            "protocol": clean_protocol,
            "tftp_server": request.form.get("tftp_server", "").strip()
        }
        
        form_pass = request.form.get("password", "")
        if form_pass: 
            password = form_pass
            session["device_password"] = password
            
        for k, v in form_data.items():
            session[k] = v
        
        try:
            port_int = int(form_data["port"])
        except:
            port_int = 22 if clean_protocol == "ssh" else 23

        # Lógica de aplicación de VLANs
        if action == "apply":
            ids = request.form.getlist("vlan_id")
            names = request.form.getlist("vlan_name")
            vlans = [{"id": i, "name": n} for i, n in zip(ids, names) if i and i not in IGNORE_VLANS]

        # Dispatcher
        if not form_data["device_ip"]:
             error_msg = "Falta IP del dispositivo."
        
        elif action == "fetch_all":
            ok, data, raw_out = fetch_current_data(
                form_data["device_ip"], form_data["username"], password, port_int, clean_protocol
            )
            if ok:
                vlans = data["vlans"]
                session["hostname"] = data["hostname"]
                form_data["hostname"] = data["hostname"]
                success_msg = "Datos leídos correctamente."
                netmiko_output = raw_out
            else:
                error_msg = f"Error conectando: {raw_out}"

        elif action == "apply":
            ok, out = apply_config(
                vlans, form_data["hostname"], 
                form_data["device_ip"], form_data["username"], password, port_int, clean_protocol
            )
            if ok:
                success_msg = "Cambios aplicados."
                netmiko_output = out
            else:
                error_msg = f"Error aplicando: {out}"

        elif action == "save_config":
            ok, out = save_mem(
                form_data["device_ip"], form_data["username"], password, port_int, clean_protocol
            )
            if ok:
                success_msg = "Configuración guardada."
                netmiko_output = out
            else:
                error_msg = out

        elif action == "download_config":
            ok, out = download_txt(
                form_data["device_ip"], form_data["username"], password, port_int, clean_protocol
            )
            if ok:
                response = make_response(out)
                response.headers["Content-Type"] = "text/plain"
                fn = f"backup-{form_data['hostname'] or 'switch'}.txt"
                response.headers["Content-Disposition"] = f"attachment; filename={fn}"
                return response
            else:
                error_msg = out

        elif action == "tftp_upload":
            if not form_data["tftp_server"]:
                error_msg = "Falta IP del servidor TFTP."
            else:
                ok, out = upload_tftp_smart(
                    form_data["device_ip"], form_data["username"], password, port_int, clean_protocol,
                    form_data["tftp_server"], form_data["hostname"]
                )
                if ok:
                    success_msg = "Backup TFTP completado."
                    netmiko_output = out
                else:
                    error_msg = f"Error TFTP: {out}"

        return render_template(
            "index.html",
            vlans=vlans,
            device_ip=form_data["device_ip"],
            username=form_data["username"],
            port=form_data["port"],
            hostname=form_data["hostname"],
            protocol=form_data["protocol"], # Pasamos el protocolo limpio de vuelta al template
            tftp_server=form_data["tftp_server"],
            password_value=password,
            error_msg=error_msg,
            success_msg=success_msg,
            netmiko_output=netmiko_output
        )

    # GET REQUEST
    return render_template(
        "index.html",
        vlans=[],
        device_ip=session_data["device_ip"],
        username=session_data["username"],
        port=session_data["port"],
        hostname=session_data["hostname"],
        protocol=session_data["protocol"],
        tftp_server=session_data["tftp_server"],
        password_value=password
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)