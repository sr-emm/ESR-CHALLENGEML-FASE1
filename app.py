from flask import Flask, render_template, request, session
from netmiko import (
    ConnectHandler,
    NetmikoTimeoutException,
    NetmikoAuthenticationException,
)
import re

app = Flask(__name__)
IGNORE_VLANS = {"1002", "1003", "1004", "1005"}

# SOLO LAB – en algo real, esto debería ir en una variable de entorno
app.secret_key = "cambia-esta-clave-para-tu-lab"


def apply_vlan_config(vlans, device_ip, username, password, port, device_type="cisco_ios_telnet"):
    """
    Aplica configuración de VLANs en el dispositivo Cisco.
    """
    device = {
        "device_type": device_type,  # "cisco_ios" si usás SSH
        "host": device_ip,
        "username": username,
        "password": password,
        "secret": password,   # si el enable es distinto, cambiá esto
        "port": port,
    }

    commands = []
    for vlan in vlans:
        vlan_id = vlan["id"]
        vlan_name = vlan["name"]

        commands.extend([
            f"vlan {vlan_id}",
            f"name {vlan_name}",
        ])

    try:
        conn = ConnectHandler(**device)

        # Intentar enable
        try:
            conn.enable()
        except Exception:
            pass

        output = conn.send_config_set(commands)

        try:
            output += "\n" + conn.save_config()
        except Exception:
            output += "\n(No se pudo ejecutar save_config automáticamente)"

        conn.disconnect()
        return True, output

    except NetmikoAuthenticationException as e:
        return False, f"Error de autenticación: {e}"
    except NetmikoTimeoutException as e:
        return False, f"Timeout conectando al dispositivo: {e}"
    except Exception as e:
        return False, f"Error inesperado: {e}"


def fetch_current_vlans(device_ip, username, password, port, device_type="cisco_ios_telnet"):
    """
    Ejecuta 'show vlan brief' y devuelve una lista de VLANs parseadas.
    """
    device = {
        "device_type": device_type,
        "host": device_ip,
        "username": username,
        "password": password,
        "secret": password,
        "port": port,
    }

    try:
        conn = ConnectHandler(**device)

        try:
            conn.enable()
        except Exception:
            pass

        output = conn.send_command("show vlan brief")
        conn.disconnect()

        vlans = parse_vlans_from_show(output)
        return True, vlans, output

    except NetmikoAuthenticationException as e:
        return False, [], f"Error de autenticación: {e}"
    except NetmikoTimeoutException as e:
        return False, [], f"Timeout conectando al dispositivo: {e}"
    except Exception as e:
        return False, [], f"Error inesperado: {e}"


def parse_vlans_from_show(output):
    """
    Parseo simple de 'show vlan brief'.
    Ignora las VLANs 1002-1005 (FDDI/TokenRing).
    """
    vlans = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        if not line[0].isdigit():
            continue

        parts = re.split(r"\s+", line)
        if len(parts) < 2:
            continue

        vlan_id = parts[0]
        vlan_name = parts[1]

        if not vlan_id.isdigit():
            continue

        # Ignorar VLANs legacy 1002-1005
        if vlan_id in IGNORE_VLANS:
            continue

        vlans.append({"id": vlan_id, "name": vlan_name})

    return vlans


@app.route("/", methods=["GET", "POST"])
def index():
    # Valores iniciales desde sesión (para no reescribir todo cada vez)
    device_ip = session.get("device_ip", "")
    username = session.get("username", "")
    stored_password = session.get("device_password", "")
    port = session.get("port", 23)

    vlans = []
    error_msg = None
    success_msg = None
    netmiko_output = None

    password = ""          # lo que llega del form
    password_for_field = ""  # lo que vamos a mostrar en el input (última usada)

    if request.method == "POST":
        action = request.form.get("action", "apply")  # "apply" o "fetch"

        # Datos de conexión (si el form trae algo, pisa lo de sesión)
        form_ip = request.form.get("device_ip", "").strip()
        form_user = request.form.get("username", "").strip()
        form_pass = request.form.get("password", "")
        form_port = request.form.get("port", "").strip()

        if form_ip:
            device_ip = form_ip
        if form_user:
            username = form_user

        if form_port:
            try:
                port = int(form_port)
            except ValueError:
                port = 23

        # Password: si el usuario escribe una, se actualiza;
        # si la deja vacía, usamos la que está guardada en sesión
        if form_pass:
            password = form_pass
        else:
            password = stored_password

        # Guardar en sesión para próximas veces
        session["device_ip"] = device_ip
        session["username"] = username
        session["port"] = port
        if password:
            session["device_password"] = password

        password_for_field = password  # esto rellena el input password

        # VLANs del form (para acción "apply"; para "fetch" se sobrescriben)
        vlan_ids = request.form.getlist("vlan_id")
        vlan_names = request.form.getlist("vlan_name")

        for vid, vname in zip(vlan_ids, vlan_names):
            vid = vid.strip()
            vname = vname.strip()

            if not vid:
                continue

            # Ignorar VLANs 1002–1005 aunque el usuario las ingrese
            if vid in IGNORE_VLANS:
                continue

            if not vname:
                vname = f"VLAN_{vid}"

            vlans.append({"id": vid, "name": vname})

        if not device_ip or not username or not password:
            error_msg = "Faltan datos de conexión (IP, usuario o password)."
        else:
            if action == "fetch":
                # Leer VLANs actuales del equipo
                ok, vlans_from_device, output = fetch_current_vlans(
                    device_ip=device_ip,
                    username=username,
                    password=password,
                    port=port,
                    device_type="cisco_ios_telnet",  # "cisco_ios" si usás SSH
                )
                if ok:
                    vlans = vlans_from_device
                    success_msg = "VLANs leídas correctamente del dispositivo."
                    netmiko_output = output
                else:
                    error_msg = output

            else:  # action == "apply"
                if len(vlans) == 0:
                    error_msg = "No se cargó ninguna VLAN válida."
                else:
                    ok, output = apply_vlan_config(
                        vlans=vlans,
                        device_ip=device_ip,
                        username=username,
                        password=password,
                        port=port,
                        device_type="cisco_ios_telnet",  # "cisco_ios" si usás SSH
                    )
                    if ok:
                        success_msg = "Configuración de VLANs aplicada correctamente."
                        netmiko_output = output
                    else:
                        error_msg = output
    else:
        # GET: mostrar última password usada (si existe)
        password_for_field = stored_password

    return render_template(
        "index.html",
        vlans=vlans,
        device_ip=device_ip,
        username=username,
        port=port,
        password_value=password_for_field,
        error_msg=error_msg,
        success_msg=success_msg,
        netmiko_output=netmiko_output,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
