# Challenge Networking ML

Creo este Git para concentrar la programacion que requiere el Challenge. La misma debera lograr:
Usando un Frontend:
  - Configurar multiples VLANs especificando ID y nombre
    - VLAN 10: "VLAN_DATOS"
    - VLAN 20: "VLAN_VOZ"
    - VLAN 50: "VLAN_SEGURIDAD"
  - Cambiar nombre del switch
  - Guardar Configuracion
  - Hacer Backup de configuracion
    - El nombre debe incluir: hostname, fecha y hora del backup
  - El script debe validar la configuracion actual del equipo. Alertando en caso de que difiera la config con la implementada en el frontend o en la salida del script

# Realizado
- Se crea un Frontend web que permitira sea compatible con cualquier dispositivo requerido haciendolo mas universal que uno especifico para windows por ejemplo.
- Se le coloca los siguientes datos para acceder al equipo
  - IP
  - User
  - Password
  - Puerto
- 


Pasos realizados:
1. Se hace un resumen de las actividades a realizar dividiendolas por partes y prioridad.
2. Se usa ChatGPT como IA principal en esta fase.
3. Se crea un proyecto dentro de la IA para concentrar la informacion.
4. Se compara los frontend que mencionan en el challenge. Parece que lo mas simple seria flask por ser web

==============================================================================

Manos a la obra:
1. La IA establece instrucciones para trabajar con flask y concentrarse en un paso a la vez.
2. Establece una estructura sencilla:
  2.1. app.py
  2.2. requirements.txt
  2.3. tempaltes (folder)
   2.3.1. index.html
4. Se levanto un ambiente virtual de python en la pc windows, ya tenia Python instalado por lo que fue medio directo.
5. Se instala flask, es la version 3.1.2, los requirements estaban en 3.0.0 por lo que se cambian para ser mas flexibles a "Flask>=3.1.2,<4.0"
6. Se llega a ver la pagina de prueba en localhost:5000 
7. La IA queria establecer las 3 vlan necesarias de forma hardcodeada, pero esto es muy limitante por lo que cambio para uqe la misma permita agregar vlan ID y nombre que se quiera.
<img width="1746" height="480" alt="image" src="https://github.com/user-attachments/assets/6cd22d0b-da96-45d6-bd27-0e58d272a7cd" />

8. Esta version si quieres realizar un cambio, debes de volver a escribir todo de nuevo. Asi que buscare que la informacion permanezca y se pueda editar luego.
9. Ok ahora tiene mas sentido, se pueden editar luego. Esto puede ser util luego cuando se obtenga la informacion del switch al conectarse. Tambien se prueba crear una vlan 5000 para comprobar que tenga sentido, funciona. 
<img width="951" height="827" alt="image" src="https://github.com/user-attachments/assets/d41b81d6-64c1-4f74-8925-c263e2840b6b" />
<img width="351" height="116" alt="image" src="https://github.com/user-attachments/assets/bffee0c4-de05-4a3c-a30e-27a479c6c92b" />

10. Se agregan los archivos al github para tener control de cambios. Se empieza a instalar y configurar netmiko.
11. Se configura en GNS3 un switch IOU L2 para poder establecer las pruebas. Esto hace que deba agregar el puerto para que se conecte al telnet del equipo.
<img width="1078" height="861" alt="image" src="https://github.com/user-attachments/assets/53c6f37b-8b44-4b3e-ac37-67e4da28c192" />
<img width="969" height="879" alt="image" src="https://github.com/user-attachments/assets/0c6ca691-93e5-4533-9235-4a19fa94e5e9" />

12. Se hace cambios para que pueda obtener las vlans creadas y lograr tener una clave persistente para no tener que colocarla cada vez. Esto es por el lab, en produccion se tendria que tener una mejor forma como autenticacion por certificado.

13. Se agregan vlan
