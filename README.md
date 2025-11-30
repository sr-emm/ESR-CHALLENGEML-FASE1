# Challenge Networking ML

Dentro del repo de Git podrán encontrar todo lo necesario para este challenge.
Dividiéndolo por fases tenemos:

Fase 1
1. Repositorio Git

Se utiliza este repositorio haciendo un link con la aplicación de GitHub Desktop para poder ir modificando los archivos de manera local pero que vayan subiendo a la nube para el control de cambios.
Es una herramienta que no había usado y la verdad está excelente.

2. Frontend de configuración de VLANs

Viendo las opciones que se mencionaron, creo que la mejor es Flask, que al ser web podrá usarse en cualquier dispositivo a futuro.
Luego de muchas iteraciones se llegó a un frontend que cumple con todo lo requerido.

Tiene alguna limitación que a propósito no solucioné, como el borrado de VLANs en el dispositivo. Esto podría ser muy peligroso porque con un botón se podría detener la operativa; por eso, en caso de implementarse, debería tener varios “checks” que permitan estar especialmente seguros de que no va a afectar nada o que el impacto sea reducido.

Descripción general
<img width="1011" height="819" alt="image" src="https://github.com/user-attachments/assets/6d2dd9e6-7214-4737-af63-130b12d434b2" />

La parte de conexión es intuitiva, solicitando los datos para conectarse al equipo: IP, usuario y password.
Luego se puede elegir el protocolo (Telnet o SSH) y el puerto; este último es especialmente útil dado que, al tener los equipos virtualizados, uso puertos muy distintos de los típicos 22/23.
Una vez colocados los datos se puede presionar “Obtener VLANs y Hostname actuales”.

<img width="965" height="515" alt="image" src="https://github.com/user-attachments/assets/d9aa7bc8-8315-4572-b3d3-da87186690f6" />

Con esto se obtienen todos los datos que se configuran y queda un output de los comandos que se ejecutan vía Netmiko:

<img width="981" height="1219" alt="image" src="https://github.com/user-attachments/assets/77817c8e-e36b-4c36-9009-5075217a7155" /> <img width="1028" height="542" alt="image" src="https://github.com/user-attachments/assets/1a1426fa-ebc1-4380-aa04-919f8d4f22da" />

Desde acá se pueden agregar VLANs con el botón “Agregar VLAN”, donde se puede colocar la ID que se prefiera (siempre que sea válida; no admite valores fuera del rango 1–4094) y se permite cambiar los nombres.
Para evitar información innecesaria se omiten las VLAN 1002 a la 1005, dado que son del sistema operativo.

3. Configuración de VLANs

Dentro de la parte de VLANs se puede agregar la que se quiera y la misma va a ser creada con el nombre elegido.

<img width="1020" height="1250" alt="image" src="https://github.com/user-attachments/assets/8c1f8b64-1f5b-4617-967b-f8c29a599541" /> <img width="956" height="534" alt="image" src="https://github.com/user-attachments/assets/97b1da01-1cea-4ce3-adca-21242c349c82" />

Si queremos cambiarle el nombre es tan fácil como editarlo y aplicar de nuevo la configuración:

<img width="1020" height="1242" alt="image" src="https://github.com/user-attachments/assets/f4e1b1b5-dae3-4a76-9ab4-cfa2dcf0214d" /> <img width="971" height="632" alt="image" src="https://github.com/user-attachments/assets/abb888b5-e7be-4eb6-a78d-2b55ac0e29cc" />

La herramienta siempre sobrescribe la configuración actual de VLANs, lo que la hace muy simple pero podría ser contraproducente si se usa sin cuidado.
La ventaja es que es extremadamente fácil cambiar los nombres de todas las VLAN que hagan falta de manera masiva.

Hay un límite de 20 caracteres en el nombre de la VLAN para evitar problemas.

4. Cambio de nombre del switch

Dentro del apartado “Nombre del switch” podemos ver cuál es el actual al obtener la info del equipo:

<img width="972" height="155" alt="image" src="https://github.com/user-attachments/assets/9b59c6bb-52fd-4a7e-93a8-fce7192f8716" /> <img width="1026" height="160" alt="image" src="https://github.com/user-attachments/assets/588a54ac-2f2d-40c6-8419-6ba7e37a89b6" />

O podemos cambiarlo y darle “Aplicar cambios en el dispositivo”:

<img width="997" height="996" alt="image" src="https://github.com/user-attachments/assets/2d79ad19-a736-4201-bc22-367b865b662a" /> <img width="992" height="163" alt="image" src="https://github.com/user-attachments/assets/18b59ad0-b6da-4d68-bcf3-d4fdb62db60e" />
5. Guardar configuración

Funciona con un simple write memory al presionar el botón con ese mismo nombre:

<img width="1059" height="1010" alt="image" src="https://github.com/user-attachments/assets/2ae8d636-f159-446a-a909-6e5d48fb5626" />
6. Backup de configuración
6.1 Descargable

Se creó la posibilidad de descargar el archivo con el botón correspondiente.
El archivo incluye un formato de nombre pensado para poder guardar múltiples versiones teniendo un control claro de cuál es la más reciente:

año-mes-dia-horaminutos-hostname.txt

<img width="465" height="69" alt="image" src="https://github.com/user-attachments/assets/58eb6a7d-9161-49af-9742-6b650e5dac57" />

Este archivo se adjunta en el repositorio.

6.2 TFTP

Se utiliza el mismo nombre que en el descargable, pero se debe colocar solo la IP del servidor TFTP en el campo destinado para eso:

<img width="961" height="139" alt="image" src="https://github.com/user-attachments/assets/8c7c5113-0ece-403d-b92f-d0c8d644d13c" /> <img width="992" height="304" alt="image" src="https://github.com/user-attachments/assets/93a9a8fa-c1d6-4781-8323-f3af4fbaddf1" />

Fue necesario colocar un pequeño delay para que esta función funcionara correctamente.

7. Validación de configuración

En cada paso de la configuración se muestra la salida exacta de la consola, lo que permite ver rápidamente si hay algún error.
Como la configuración siempre se sobrescribe al aplicar cambios, no veo un caso donde quede una configuración parcial.
A futuro esto podría mejorarse con una etapa de evaluación de “config actual vs config deseada” y aceptar o rechazar los cambios según se decida.

8. Control de versiones

Se sube la mayor cantidad de información posible para ir documentando todo el proceso y tener un rollback sencillo si fuera necesario.

9. README

Este README documenta el funcionamiento general, la instalación y el flujo de trabajo.

# Instalación
1. Ubicación de archivos

Colocar todos los archivos del proyecto en una misma carpeta.

2. Python y entorno virtual

Instalar Python y crear un entorno virtual.
En mi caso generé algo similar a:

<img width="445" height="33" alt="image" src="https://github.com/user-attachments/assets/47168e3a-2c81-4023-922c-602dc75f4f65" />

(La captura muestra el entorno creado).

3. Instalar Flask (frontend)

Dentro del entorno virtual, instalar Flask:

pip install Flask

<img width="485" height="30" alt="image" src="https://github.com/user-attachments/assets/764a66c4-ea44-4d24-9881-3ae847ea7109" />
4. Instalar Netmiko

En el mismo entorno virtual:

pip install netmiko

<img width="1165" height="44" alt="image" src="https://github.com/user-attachments/assets/fca7ebdd-b9a5-4e8d-8ad9-c3cda8690884" />
5. Ejecutar la aplicación

Cambiarse al folder donde está el script y correr la app con Python:

python .\app.py

<img width="1157" height="34" alt="image" src="https://github.com/user-attachments/assets/791a7863-bb95-4e6d-9248-249fbb3a1ada" />

Es importante que la estructura de carpetas y los nombres de los archivos no se cambien.
Además, dentro de la carpeta ML Challenge está la simulación en GNS3 que se usó para realizar este challenge.
