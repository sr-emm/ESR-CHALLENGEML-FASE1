# Challenge Networking ML
Dentro del Git podran encontrar todo lo necesario para este challenge. Dividiendolo por fases tenemos

Fase 1:
  1. Repositorio Git
    Se utiliza este repositorio haciendo un link con la aplicacion de Github Desktop para poder ir modificando los archivos de manera local pero que vayan subiendo a la nube para el control de cambios. Una herramienta que no habia usado y esta excelente la verdad.
  2. Frontend de Configuracion de VLANs
    Viendo las opciones que se mencionaron, creo que la mejor es FLASK que al ser web podra usasrse en cualquier dispositivo a futuro. Luego de muchas interacciones se llego a un front end que cumple con todo lo requerido.
    Tiene alguna limitacion que a proposito no solucione como el borrar vlans. Esto podria ser muy peligroso por que podria con un boton detener la operativa, por esto de aplicarse deberia tener varios "checks" que permitan estar especialmente seguros de que no vaya a afectar nada o que el impacto sea reducido.
     Describiendo las opciones tenemos:
<img width="1011" height="819" alt="image" src="https://github.com/user-attachments/assets/6d2dd9e6-7214-4737-af63-130b12d434b2" />
      La parte de conexion es intuitiva soicitando los datos para conexion hacia el mismo. IP, usuario y password. Luego puedes elegir el protocolo (telnet o SSH) y el puerto, este ultimo es especialmente util dado que al tener los equipos virtualizados tengo puertos muy disintos del 22/23. Una vez colocas los datos puedes presionar "Obtener VLANs y Hostname actuales"
     <img width="965" height="515" alt="image" src="https://github.com/user-attachments/assets/d9aa7bc8-8315-4572-b3d3-da87186690f6" />
     Con esto obtienes todos los datos que se configuran y queda un output de los comandos obtenimos por netmiko
     <img width="981" height="1219" alt="image" src="https://github.com/user-attachments/assets/77817c8e-e36b-4c36-9009-5075217a7155" />
     <img width="1028" height="542" alt="image" src="https://github.com/user-attachments/assets/1a1426fa-ebc1-4380-aa04-919f8d4f22da" />

     De aca se pueden agregar VLANs con el boton "Agregar VLAN" donde ahi puedes colocarle la ID que prefieras pero que sea valida (no admite fuera de las 4094) y permite cambiar los nombres. Para evitar informacion innecesaria se omiten las vlan 1002 a la 1005 dado que son del sistema operativo.

  3. Configuracion de VLANs
    Dentro de la parte de VLANs podemos agregar la que queramos y la misma va a ser creada con el nombre elegido.
    <img width="1020" height="1250" alt="image" src="https://github.com/user-attachments/assets/8c1f8b64-1f5b-4617-967b-f8c29a599541" />
    <img width="956" height="534" alt="image" src="https://github.com/user-attachments/assets/97b1da01-1cea-4ce3-adca-21242c349c82" />
    Si queremos cambiarle el nombre es tan facil como hacerlo y aplicar de nuevo la configuraicon:
    <img width="1020" height="1242" alt="image" src="https://github.com/user-attachments/assets/f4e1b1b5-dae3-4a76-9ab4-cfa2dcf0214d" />
    <img width="971" height="632" alt="image" src="https://github.com/user-attachments/assets/abb888b5-e7be-4eb6-a78d-2b55ac0e29cc" />
    La misma esta sobreescribiendo lo actual, esto lo hace bastante simple pero podria ser contraproducente. La ventaja es que extremadamente facil cambiar los nombres a todas las que hagan falta de manera masiva.
    Tiene un limite de 20 caracteres en el nombre de la VLAN para evitar problemas.
  4. Cambio de Nombre del Switch
    Dentro del apartado Nombre del Switch podemos ver cual esta al obtener la info del equipo actualmente
    <img width="972" height="155" alt="image" src="https://github.com/user-attachments/assets/9b59c6bb-52fd-4a7e-93a8-fce7192f8716" />
    <img width="1026" height="160" alt="image" src="https://github.com/user-attachments/assets/588a54ac-2f2d-40c6-8419-6ba7e37a89b6" />
    O cambiarlo y darle aplicar cambios en el dispositivo
    <img width="997" height="996" alt="image" src="https://github.com/user-attachments/assets/2d79ad19-a736-4201-bc22-367b865b662a" />
    <img width="992" height="163" alt="image" src="https://github.com/user-attachments/assets/18b59ad0-b6da-4d68-bcf3-d4fdb62db60e" />
    
  5. Guardar Config
    Funciona con un simple wirte memory al presionar el boton con ese mismo nombre
    <img width="1059" height="1010" alt="image" src="https://github.com/user-attachments/assets/2ae8d636-f159-446a-a909-6e5d48fb5626" />

  6. Backup de Config
    6.1 Descargable
      Se creo la posibilidad de descargar el archivo con el boton correspondiente. El archivo incluye un formato que esta perfectamente diseñado para guardar multiples teniendo un control claro de cual es el mas reciente: año-mes-dia-horaminutos-hostname.txt
      <img width="465" height="69" alt="image" src="https://github.com/user-attachments/assets/58eb6a7d-9161-49af-9742-6b650e5dac57" />
      Se adjunta este archivo en el repositorio
    6.2 TFTP
      Se utiliza el mismo nombre que en el descargable pero se debe colocar la IP en el campo que se destina para eso:
      <img width="961" height="139" alt="image" src="https://github.com/user-attachments/assets/8c7c5113-0ece-403d-b92f-d0c8d644d13c" />
      <img width="992" height="304" alt="image" src="https://github.com/user-attachments/assets/93a9a8fa-c1d6-4781-8323-f3af4fbaddf1" />
      Hubo que colocar un pequeño delay para que funcionara esta funcion. 

  7. Validacion de configuracion
    En cada paso de la configuracion se muestra la salida exacta de la consola, esto hace que si hay un error se pueda visualizar. Al la configuracion siempre sobreescribirse al aplicar cambios, no veo como podria coincidir. Esto podria pasar si se da una etpaa de evaluacion de que esta vs lo que se quiere configurar y aceptar o negar los cambios segun se decida. 
  
  8. Control de Versiones
    Se sube la mayor cantidad de informacion posible para ir documentando todo el proceso y tener facil algun rollback de ser necesario.   
  9. README

INSTALACION
Para instala:
1. Se debe coocar todos los archivos en un carpeta.
2. Se debe instalar python y setear un enviroment. En mi caso genere el siguiente
<img width="445" height="33" alt="image" src="https://github.com/user-attachments/assets/47168e3a-2c81-4023-922c-602dc75f4f65" /> 
3. Dentro del Enviroment: instalar Flask para el Frontend:  pip install Flask
<img width="485" height="30" alt="image" src="https://github.com/user-attachments/assets/764a66c4-ea44-4d24-9881-3ae847ea7109" /> 
 
4. Luego instalar Netmiko:  pip install netmiko
<img width="1165" height="44" alt="image" src="https://github.com/user-attachments/assets/fca7ebdd-b9a5-4e8d-8ad9-c3cda8690884" /> 
 
5. Cambiarse al folder donde esta el scrip y correr con ypthon el app.py: python .\app.py
<img width="1157" height="34" alt="image" src="https://github.com/user-attachments/assets/791a7863-bb95-4e6d-9248-249fbb3a1ada" /> 

Es importante que la esctructura de las carpetas y los nombres de los archivos no se cambien. Ademas, dentro de la carpteta "ML Challenge" esta la simulacion en GNS3 que se uso para realizar este Challenge. 

