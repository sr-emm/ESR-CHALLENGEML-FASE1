"""
app.py
======
Aplicación Flask para automatizar la configuración de un switch Cisco:

- Conexión por Telnet o SSH (elegible en el frontend)
- Lectura de VLANs actuales (show vlan brief)
- Ignora VLANs 1002–1005 (FDDI/TokenRing)
- Lectura y cambio de hostname
- Aplicación de VLANs + hostname (configuration mode)
- Write memory (save_config)
- Descarga de running-config como archivo .txt
- Envío de running-config a un servidor TFTP (copy run tftp:)
- Regla de negocio: los nombres de VLAN no pueden tener más de 20 caracteres
"""

from flask import Flask, render_template, request, session, make_response
from netmiko import (
    ConnectHandler,
    NetmikoTimeoutException,
    NetmikoAuthenticationException,
)
from datetime import datetime
import re
import time  # usado para pausar entre envíos en el copy run tftp


###############################################################################
# CONFIGURACIÓN BÁSICA DE FLASK
###############################################################################

app = Flask(__name__)

# Clave para manejar sesiones (en un entorno real debería ir en una env var)
app.secret_key = "cambia-esta-clave-para-tu-lab"

# VLANs "legacy" que aparecen siempre y no queremos tocar
IGNORE_VLANS = {"1002", "1003", "1004", "1005"}


###############################################################################
# FUNCIONES AUXILIARES DE NETMIKO / DISPOSITIVO
###############################################################################

def build_device(device_ip, username, password, port, protocol):
    """
    Devuelve el diccionario que Netmiko necesita para conectarse al equipo.

    - protocol: "telnet" o "ssh"
    - device_type cambia según el protocolo
    """
    if protocol == "ssh":
        device_type = "cisco_ios"
    else:
        # Por simplicidad: tratamos todo lo que no sea "ssh" como Telnet
        device_type = "cisco_ios_telnet"

    return {
        "device_type": device_type,
        "host": device_ip,
        "username": username,
        "password": password,
        "secret": password,  # si el enable tiene otra password, habría que separarlo
        "port": port,
    }


def apply_config(vlans, hostname, device_ip, username, password, port, protocol):
    """
    Aplica cambios de configuración al dispositivo:

    - hostname (si viene informado)
    - VLANs (vlan <id> + name <nombre>)

    No guarda la configuración (no hace write memory); eso se maneja con otro botón.
    """
    device = build_device(device_ip, username, password, port, protocol)

    commands = []

    # 1) Cambio de hostname
    if hostname:
        commands.append(f"hostname {hostname}")

    # 2) Definición / actualización de VLANs
    for vlan in vlans:
        vlan_id = vlan["id"]
        vlan_name = vlan["name"]
        commands.extend([
            f"vlan {vlan_id}",
            f"name {vlan_name}",
        ])

    # Si no hay nada para hacer, devolvemos un mensaje
    if not commands:
        return False, "No hay cambios para aplicar (sin hostname ni VLANs)."

    try:
        conn = ConnectHandler(**device)

        # Intentamos entrar a modo enable (por si hace falta)
        try:
            conn.enable()
        except Exception:
            # Si falla enable pero igual estamos en EXEC privilegiado, no pasa nada
            pass

        # Mandamos la lista de comandos en modo configuración
        output = conn.send_config_set(commands)

        conn.disconnect()
        return True, output

    # Manejo de errores “bonito”
    except NetmikoAuthenticationException as e:
        return False, f"Error de autenticación: {e}"
    except NetmikoTimeoutException as e:
        return False, f"Timeout conectando al dispositivo: {e}"
    except Exception as e:
        return False, f"Error inesperado: {e}"


def fetch_current_vlans(device_ip, username, password, port, protocol):
    """
    Ejecuta 'show vlan brief' y parsea la salida para obtener una lista
    de VLANs en el formato:

        [{"id": "10", "name": "USERS"}, ...]

    Ignora las VLANs 1002–1005.
    """
    device = build_device(device_ip, username, password, port, protocol)

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
    Parseo simple de la salida de 'show vlan brief'.

    - Toma solo líneas que empiezan con dígito
    - Usa espacios en blanco como separador
    - El primer campo es el VLAN ID y el segundo el nombre
    - Ignora los VLAN IDs en IGNORE_VLANS
    - El nombre se corta a máximo 20 caracteres (regla de negocio)
    """
    vlans = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        if not line[0].isdigit():  # descarta encabezados, etc.
            continue

        parts = re.split(r"\s+", line)
        if len(parts) < 2:
            continue

        vlan_id = parts[0]
        vlan_name = parts[1]

        if not vlan_id.isdigit():
            continue

        if vlan_id in IGNORE_VLANS:
            # Saltamos VLANs legacy (FDDI / TokenRing)
            continue

        # Regla: máximo 20 caracteres en nombre de VLAN
        if len(vlan_name) > 20:
            vlan_name = vlan_name[:20]

        vlans.append({"id": vlan_id, "name": vlan_name})

    return vlans


def fetch_hostname(device_ip, username, password, port, protocol):
    """
    Obtiene el hostname actual del dispositivo ejecutando:

        show running-config | include ^hostname
    """
    device = build_device(device_ip, username, password, port, protocol)

    try:
        conn = ConnectHandler(**device)

        try:
            conn.enable()
        except Exception:
            pass

        output = conn.send_command("show running-config | include ^hostname")
        conn.disconnect()

        hostname = parse_hostname_from_output(output)
        return True, hostname, output

    except NetmikoAuthenticationException as e:
        return False, "", f"Error de autenticación: {e}"
    except NetmikoTimeoutException as e:
        return False, "", f"Timeout conectando al dispositivo: {e}"
    except Exception as e:
        return False, "", f"Error inesperado: {e}"


def parse_hostname_from_output(output):
    """
    Extrae el hostname de una salida que contenga líneas del tipo:

        hostname MI_SWITCH
    """
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("hostname "):
            parts = line.split()
            if len(parts) >= 2:
                return parts[1]
    return ""


def save_config_only(device_ip, username, password, port, protocol):
    """
    Llama a 'save_config()' de Netmiko, que normalmente ejecuta:

        write memory
    o
        copy running-config startup-config

    según el tipo de dispositivo.
    """
    device = build_device(device_ip, username, password, port, protocol)

    try:
        conn = ConnectHandler(**device)

        try:
            conn.enable()
        except Exception:
            pass

        try:
            output = conn.save_config()
        except Exception:
            # Si por alguna razón save_config falla, devolvemos un mensaje genérico
            output = "No se pudo ejecutar save_config automáticamente (probá manualmente 'write memory')."

        conn.disconnect()
        return True, output

    except NetmikoAuthenticationException as e:
        return False, f"Error de autenticación: {e}"
    except NetmikoTimeoutException as e:
        return False, f"Timeout conectando al dispositivo: {e}"
    except Exception as e:
        return False, f"Error inesperado: {e}"


def fetch_full_config(device_ip, username, password, port, protocol):
    """
    Devuelve la running-config completa usando:

        show running-config

    Esta salida se usa para descargarla como archivo .txt.
    """
    device = build_device(device_ip, username, password, port, protocol)

    try:
        conn = ConnectHandler(**device)

        try:
            conn.enable()
        except Exception:
            pass

        output = conn.send_command("show running-config")
        conn.disconnect()
        return True, output

    except NetmikoAuthenticationException as e:
        return False, f"Error de autenticación: {e}"
    except NetmikoTimeoutException as e:
        return False, f"Timeout conectando al dispositivo: {e}"
    except Exception as e:
        return False, f"Error inesperado: {e}"


def upload_config_tftp(device_ip, username, password, port, protocol, tftp_ip, hostname):
    """
    Envía la running-config a un servidor TFTP ejecutando:

        copy running-config tftp:

    - Solo se pide la IP del servidor TFTP.
    - El nombre del archivo se genera con el mismo formato que la descarga:

        Año-Mes-Dia-horaMinuto-Hostname.txt
        (por ejemplo: 2025-11-29-2218-SWITCH_AUTOMATIZADO.txt)

    Implementado con write_channel / read_channel para controlar bien el diálogo.
    """
    tftp_ip = tftp_ip.strip()

    # Validación simple de IP (no chequea rangos 0-255, solo formato x.x.x.x)
    if not re.match(r"^\d{1,3}(\.\d{1,3}){3}$", tftp_ip):
        return False, "IP de TFTP inválida. Ejemplo: 192.168.1.100"

    # Si no tenemos hostname, inventamos uno genérico
    hn = hostname if hostname else "device"

    now = datetime.now()
    # Mismo formato que el nombre del archivo descargado, sin guion entre hora y minuto
    tftp_filename = f"{now.year:04d}-{now.month:02d}-{now.day:02d}-{now.hour:02d}{now.minute:02d}-{hn}.txt"

    device = build_device(device_ip, username, password, port, protocol)

    try:
        conn = ConnectHandler(**device)

        try:
            conn.enable()
        except Exception:
            pass

        output = ""

        # 1) Lanzamos el comando "copy running-config tftp:"
        conn.write_channel("copy running-config tftp:\n")
        time.sleep(1)
        out = conn.read_channel()
        output += out

        # 2) Respondemos con la IP del servidor TFTP
        conn.write_channel(tftp_ip + "\n")
        time.sleep(1)
        out = conn.read_channel()
        output += out

        # 3) Respondemos con el nombre de archivo destino
        conn.write_channel(tftp_filename + "\n")
        time.sleep(1)
        out = conn.read_channel()
        output += out

        # 4) Si aparece un prompt de confirmación [confirm], mandamos ENTER extra
        if "[confirm]" in out.lower() or "confirm" in out.lower():
            conn.write_channel("\n")
            time.sleep(1)
            out = conn.read_channel()
            output += out

        conn.disconnect()
        return True, output

    except NetmikoAuthenticationException as e:
        return False, f"Error de autenticación: {e}"
    except NetmikoTimeoutException as e:
        return False, f"Timeout conectando al dispositivo: {e}"
    except Exception as e:
        return False, f"Error inesperado: {e}"


###############################################################################
# RUTA PRINCIPAL DE FLASK (INDEX)
###############################################################################

@app.route("/", methods=["GET", "POST"])
def index():
    """
    Controlador principal de la app.

    Maneja tanto el GET (carga inicial del formulario) como el POST,
    donde se ejecutan las distintas acciones:

    - fetch_all       → Leer VLANs + hostname
    - save_config     → Write memory
    - download_config → Descargar running-config como .txt
    - tftp_upload     → copy running-config tftp:
    - apply           → Aplicar VLANs + hostname
    """

    # Recuperamos valores "persistentes" desde la sesión (si existen)
    device_ip = session.get("device_ip", "")
    username = session.get("username", "")
    stored_password = session.get("device_password", "")
    port = session.get("port", 23)
    hostname = session.get("hostname", "")
    protocol = session.get("protocol", "telnet")  # valor por defecto: telnet
    tftp_server = session.get("tftp_server", "")

    # Variables que se usan para renderizar el template
    vlans = []
    error_msg = None
    success_msg = None
    netmiko_output = None

    # Para manejar el campo password en el formulario
    password = ""
    password_for_field = stored_password

    # -------------------------------------------------------------------------
    # SI LLEGA UN POST (el usuario tocó algún botón del formulario)
    # -------------------------------------------------------------------------
    if request.method == "POST":
        # Acción solicitada por el usuario (botón presionado)
        # Valores posibles: apply, fetch_all, save_config, download_config, tftp_upload
        action = request.form.get("action", "apply")

        # Leemos los campos que vienen del formulario
        form_ip = request.form.get("device_ip", "").strip()
        form_user = request.form.get("username", "").strip()
        form_pass = request.form.get("password", "")
        form_port = request.form.get("port", "").strip()
        form_hostname = request.form.get("hostname", "").strip()
        form_protocol = request.form.get("protocol", "").strip().lower()
        form_tftp_server = request.form.get("tftp_server", "").strip()

        # Actualizamos valores en memoria con lo que venga del formulario
        if form_ip:
            device_ip = form_ip
        if form_user:
            username = form_user

        # Protocolo (telnet / ssh)
        if form_protocol in ("telnet", "ssh"):
            protocol = form_protocol

        # Puerto: si está vacío, ponemos el default según protocolo
        if form_port:
            try:
                port = int(form_port)
            except ValueError:
                port = 23 if protocol == "telnet" else 22
        else:
            port = 23 if protocol == "telnet" else 22

        # Hostname: si viene info nueva, la guardamos
        if form_hostname:
            hostname = form_hostname

        # Límite backend de 20 caracteres
        if hostname and len(hostname) > 20:
            hostname = hostname[:20]

        # Password:
        # - si la escribe, actualizamos
        # - si la deja en blanco, usamos la almacenada en sesión
        if form_pass:
            password = form_pass
        else:
            password = stored_password

        # Servidor TFTP (solo IP)
        if form_tftp_server:
            tftp_server = form_tftp_server

        # Guardamos todos estos datos en la sesión para no tener que reescribirlos
        session["device_ip"] = device_ip
        session["username"] = username
        session["port"] = port
        session["hostname"] = hostname
        session["protocol"] = protocol
        session["tftp_server"] = tftp_server
        if password:
            session["device_password"] = password

        # Valor que se mostrará en el campo password (lo que tengamos guardado)
        password_for_field = password

        # ---------------------------------------------------------------------
        # Parseamos las VLANs que vengan del formulario
        # (se usan cuando se presiona "Aplicar cambios en el dispositivo")
        # ---------------------------------------------------------------------
        vlan_ids = request.form.getlist("vlan_id")
        vlan_names = request.form.getlist("vlan_name")

        for vid, vname in zip(vlan_ids, vlan_names):
            vid = vid.strip()
            vname = vname.strip()

            if not vid:
                continue
            if vid in IGNORE_VLANS:
                # Por si alguien quiere meter a mano una VLAN 1002–1005, la ignoramos
                continue
            if not vname:
                vname = f"VLAN_{vid}"

            # Regla: máximo 20 caracteres en el nombre de VLAN (seguridad backend)
            if len(vname) > 20:
                vname = vname[:20]

            vlans.append({"id": vid, "name": vname})

        # ---------------------------------------------------------------------
        # Validación básica de conexión
        # ---------------------------------------------------------------------
        # Validación real de IP en backend
        ip_regex = r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
        if not re.match(ip_regex, device_ip):
            error_msg = "La IP del dispositivo no es válida."
        else:
            # -----------------------------------------------------------------
            # Acción: Leer VLANs + hostname (fetch_all)
            # -----------------------------------------------------------------
            if action == "fetch_all":
                ok_vlans, vlans_from_device, out_vlans = fetch_current_vlans(
                    device_ip=device_ip,
                    username=username,
                    password=password,
                    port=port,
                    protocol=protocol,
                )
                ok_host, hostname_from_device, out_host = fetch_hostname(
                    device_ip=device_ip,
                    username=username,
                    password=password,
                    port=port,
                    protocol=protocol,
                )

                msgs_ok = []
                msgs_err = []

                if ok_vlans:
                    vlans = vlans_from_device
                    msgs_ok.append("VLANs leídas correctamente.")
                else:
                    msgs_err.append(f"Error leyendo VLANs: {vlans_from_device}")

                if ok_host:
                    if hostname_from_device:
                        hostname = hostname_from_device
                        session["hostname"] = hostname
                    msgs_ok.append("Hostname leído correctamente.")
                else:
                    msgs_err.append(f"Error leyendo hostname: {hostname_from_device}")

                if msgs_ok:
                    success_msg = " ".join(msgs_ok)
                if msgs_err:
                    error_msg = " ".join(msgs_err)

                # Construimos una salida combinada para mostrar en el textarea
                netmiko_output = ""
                if out_vlans:
                    netmiko_output += "=== show vlan brief ===\n" + out_vlans
                if out_host:
                    netmiko_output += "\n\n=== hostname ===\n" + out_host

            # -----------------------------------------------------------------
            # Acción: Write memory (save_config)
            # -----------------------------------------------------------------
            elif action == "save_config":
                ok, output = save_config_only(
                    device_ip=device_ip,
                    username=username,
                    password=password,
                    port=port,
                    protocol=protocol,
                )
                if ok:
                    success_msg = "Configuración guardada en el dispositivo."
                    netmiko_output = output
                else:
                    error_msg = output

            # -----------------------------------------------------------------
            # Acción: Descargar running-config como .txt (download_config)
            # -----------------------------------------------------------------
            elif action == "download_config":
                ok, cfg_output = fetch_full_config(
                    device_ip=device_ip,
                    username=username,
                    password=password,
                    port=port,
                    protocol=protocol,
                )
                if not ok:
                    # En este caso, cfg_output contiene el mensaje de error
                    error_msg = cfg_output
                else:
                    # Determinamos el hostname a usar en el nombre del archivo
                    hn = hostname or parse_hostname_from_output(cfg_output) or "device"
                    now = datetime.now()
                    filename = f"{now.year:04d}-{now.month:02d}-{now.day:02d}-{now.hour:02d}{now.minute:02d}-{hn}.txt"

                    # Devolvemos una respuesta HTTP que fuerza la descarga del archivo
                    response = make_response(cfg_output)
                    response.headers["Content-Type"] = "text/plain"
                    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
                    return response

            # -----------------------------------------------------------------
            # Acción: Subir running-config a TFTP (tftp_upload)
            # -----------------------------------------------------------------
            elif action == "tftp_upload":
                if not tftp_server:
                    error_msg = "Debes especificar la IP del servidor TFTP (ej: 192.168.1.100)."
                else:
                    # Si no tenemos hostname, intentamos leerlo para usarlo en el nombre del archivo
                    if not hostname:
                        ok_host, hostname_from_device, _ = fetch_hostname(
                            device_ip=device_ip,
                            username=username,
                            password=password,
                            port=port,
                            protocol=protocol,
                        )
                        if ok_host and hostname_from_device:
                            hostname = hostname_from_device
                            session["hostname"] = hostname

                    ok, output = upload_config_tftp(
                        device_ip=device_ip,
                        username=username,
                        password=password,
                        port=port,
                        protocol=protocol,
                        tftp_ip=tftp_server,
                        hostname=hostname,
                    )
                    if ok:
                        success_msg = f"Configuración enviada al servidor TFTP {tftp_server}."
                        netmiko_output = output
                    else:
                        error_msg = output

            # -----------------------------------------------------------------
            # Acción por defecto: aplicar VLANs + hostname (apply)
            # -----------------------------------------------------------------
            else:  # action == "apply"
                if len(vlans) == 0 and not hostname:
                    error_msg = "No hay cambios para aplicar (ni VLANs ni hostname)."
                else:
                    ok, output = apply_config(
                        vlans=vlans,
                        hostname=hostname,
                        device_ip=device_ip,
                        username=username,
                        password=password,
                        port=port,
                        protocol=protocol,
                    )
                    if ok:
                        success_msg = "Configuración aplicada correctamente (VLANs/hostname)."
                        netmiko_output = output
                    else:
                        error_msg = output

    # -------------------------------------------------------------------------
    # Renderizamos la plantilla con todos los datos recopilados
    # -------------------------------------------------------------------------
    return render_template(
        "index.html",
        vlans=vlans,
        device_ip=device_ip,
        username=username,
        port=port,
        hostname=hostname,
        protocol=protocol,
        tftp_server=tftp_server,
        password_value=password_for_field,
        error_msg=error_msg,
        success_msg=success_msg,
        netmiko_output=netmiko_output,
    )


###############################################################################
# LANZAR LA APLICACIÓN (solo en modo desarrollo)
###############################################################################

if __name__ == "__main__":
    # host="0.0.0.0" → accesible desde otras máquinas de la red
    app.run(host="0.0.0.0", port=5000, debug=True)
