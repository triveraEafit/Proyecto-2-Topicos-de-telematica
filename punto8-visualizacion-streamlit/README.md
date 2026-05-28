# GroupsApp

Aplicacion de mensajeria con:
- registro y login
- grupos
- chat grupal en tiempo real
- mensajes directos 1 a 1
- historial de mensajes
- read receipts en mensajes directos
- carga y descarga de archivos en mensajes directos
- estado online/offline basado en conexiones WebSocket activas

Stack actual:
- Backend: FastAPI + SQLAlchemy + PostgreSQL + WebSocket
- Frontend: React + Vite + Tailwind

## Requisitos

- Python 3.13
- Node 24
- npm 11
- PostgreSQL local o remoto

Versiones probadas en desarrollo:
- Python `3.13.9`
- Node `v24.13.1`
- npm `11.10.0`

## Estructura

- `app/`: backend FastAPI
- `frontend/`: frontend React
- `uploads/`: archivos cargados en mensajes directos
- `requirements.txt`: dependencias de Python

## Dependencias

Backend:

```bash
cd groupsapp-backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Frontend:

```bash
cd groupsapp-backend/frontend
npm ci
```

## Configuracion por entorno

Copia `.env.example` a `.env` y ajusta los valores:

```bash
cp .env.example .env
```

Variables requeridas:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/groupsapp
SECRET_KEY=change-this-secret-before-deploying
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
UPLOAD_DIR=uploads
```

Notas:
- `DATABASE_URL` ya no se deja hardcodeada en el codigo
- `SECRET_KEY` debe cambiarse antes de desplegar
- `UPLOAD_DIR` define la carpeta donde se guardan archivos DM
- las tablas se crean al iniciar el backend
- si vienes de otra rama con un esquema distinto, lo recomendable es recrear la base antes de probar

## Como correr el proyecto

### 1. Backend

```bash
cd groupsapp-backend
source .venv/bin/activate
python -m uvicorn app.main:app --reload
```

Disponible en:
- API: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`

### 2. Frontend

```bash
cd groupsapp-backend/frontend
npm run dev
```

Disponible en:
- App: `http://127.0.0.1:5173`

El frontend usa proxy de Vite para redirigir `/api` a `http://127.0.0.1:8000`, incluyendo WebSocket.

## Como usar la aplicacion

### Registro

Para crear una cuenta:
- ingresa `username`
- ingresa `email`
- ingresa una `password` de minimo 6 caracteres
- confirma la misma password

La app valida:
- password minima de 6 caracteres
- confirmacion igual a la password

### Login

Inicia sesion con:
- `username`
- `password`

### Grupos

Puedes:
- crear un grupo con nombre y descripcion
- unirte a un grupo existente con el ID del grupo
- ver tus grupos cargados desde `GET /groups/my-groups`
- abrir el chat del grupo y enviar mensajes en tiempo real

### Mensajes directos

Puedes:
- abrir un chat directo usando el `username` del otro usuario
- ver historial completo
- marcar mensajes como leidos
- ver conteo de mensajes directos no leidos

### Archivos

Actualmente los archivos funcionan en mensajes directos:
- selecciona un archivo con el boton `Attach`
- el frontend lo envia al endpoint `POST /groups/dm/upload/{username}`
- el backend guarda el archivo en `uploads/`
- el mensaje queda asociado al archivo en la BD
- el receptor puede descargarlo desde el chat

### Online / Offline

El backend mantiene una lista de usuarios online a partir de conexiones WebSocket activas.

Se exponen endpoints para consultar presencia:
- `GET /groups/online-users`
- `GET /groups/user/{user_id}/online`
- `GET /groups/user/by-username/{username}/online`

## Flujo recomendado de prueba

1. Levanta backend y frontend.
2. Registra dos usuarios.
3. Haz login con el primer usuario.
4. Crea un grupo.
5. Abre otra sesion con el segundo usuario.
6. Unete al grupo usando el ID.
7. Prueba chat grupal en dos ventanas o una normal y otra en incognito.
8. Prueba mensajes directos usando el username del otro usuario.
9. Prueba enviar un archivo en un mensaje directo.
10. Descarga el archivo desde el chat receptor.

## Endpoints principales

Auth:
- `POST /users/register`
- `POST /users/login`

Grupos:
- `POST /groups/`
- `POST /groups/{group_id}/join`
- `GET /groups/my-groups`
- `GET /groups/{group_id}/messages`
- `WS /groups/ws/{group_id}?token=JWT`

Mensajes directos:
- `GET /groups/dm/history/{username}`
- `GET /groups/dm/unread`
- `POST /groups/dm/mark-read/{username}`
- `POST /groups/dm/upload/{username}`
- `GET /groups/dm/download/{message_id}?token=JWT`
- `WS /groups/dm/ws/{username}?token=JWT`

## Comandos utiles

Build del frontend:

```bash
cd groupsapp-backend/frontend
npm run build
```

Estado del repo:

```bash
git status
```

Actualizar una rama remota:

```bash
git pull origin <branch>
```

## Limitaciones actuales

- La presencia online depende de conexiones WebSocket activas; no reemplaza un sistema de presencia persistente.
- Los archivos cargados se guardan localmente en `UPLOAD_DIR`; para AWS conviene mover eso a un storage externo.
- Si vas a publicar la app en internet, usa una `SECRET_KEY` fuerte y una `DATABASE_URL` segura desde variables de entorno.

## Despliegue

Para desplegar esta aplicacion en AWS, lo minimo recomendado es:

1. mover credenciales y secretos a variables de entorno
2. usar una base PostgreSQL administrada
3. configurar almacenamiento persistente para archivos
4. asegurar soporte de WebSocket en el balanceador o proxy
5. corregir la validacion real de password en login

### AWS EC2 (Lab)

Si en el laboratorio solo van a usar EC2, esta app tambien puede correr completa en una sola instancia:

- PostgreSQL local en la EC2
- backend FastAPI en la EC2
- frontend compilado en la EC2
- Nginx en la EC2
- archivos en `UPLOAD_DIR` dentro de la EC2

Eso es valido para demo o clase. No es la mejor opcion para persistencia de largo plazo.

#### 1. Lanzar la instancia

Recomendado:
- AMI: Amazon Linux 2023
- tipo: `t3.micro` o `t3.small`
- puertos abiertos:
  - `80` para la app
  - `22` solo desde tu IP, o usar EC2 Instance Connect
- no abras `5432` si PostgreSQL va a vivir dentro de la misma EC2

#### 2. Instalar paquetes

```bash
sudo dnf update -y
sudo dnf install -y git nginx gcc postgresql15 postgresql15-server python3.11 python3.11-pip python3.11-devel nodejs24 nodejs24-npm
```

#### 3. Inicializar PostgreSQL

En Amazon Linux 2023, segun el paquete instalado, el comando puede ser uno de estos:

```bash
command -v postgresql-setup
command -v postgresql-15-setup
```

Usa el que exista:

```bash
sudo postgresql-setup --initdb
```

o

```bash
sudo postgresql-15-setup initdb
```

Luego:

```bash
sudo systemctl enable --now postgresql
sudo systemctl status postgresql
```

#### 4. Crear la BD local

```bash
sudo -u postgres psql
```

Dentro de `psql`:

```sql
CREATE USER groupsapp_user WITH PASSWORD 'TU_PASSWORD';
CREATE DATABASE groupsapp OWNER groupsapp_user;
\q
```

#### 5. Clonar el repo

```bash
cd /home/ec2-user
git clone https://github.com/triveraEafit/groupsapp-backend.git
cd groupsapp-backend
git checkout main
git pull origin main
```

#### 6. Crear `.env`

```bash
cp .env.example .env
mkdir -p /home/ec2-user/groupsapp-backend/uploads
nano .env
```

Ejemplo:

```env
DATABASE_URL=postgresql://groupsapp_user:TU_PASSWORD@127.0.0.1:5432/groupsapp
SECRET_KEY=pon_una_secret_key_larga_y_random
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
UPLOAD_DIR=/home/ec2-user/groupsapp-backend/uploads
```

Puedes generar una secret con:

```bash
openssl rand -hex 32
```

#### 7. Instalar backend

```bash
cd /home/ec2-user/groupsapp-backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### 8. Compilar frontend

```bash
cd /home/ec2-user/groupsapp-backend/frontend
npm-24 ci
npm-24 run build
```

#### 9. Probar backend manualmente

```bash
cd /home/ec2-user/groupsapp-backend
source .venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Verifica en otra terminal:

```bash
curl http://127.0.0.1:8000/
```

#### 10. Crear servicio `systemd`

```bash
sudo tee /etc/systemd/system/groupsapp.service > /dev/null <<'EOF'
[Unit]
Description=GroupsApp FastAPI
After=network.target postgresql.service

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/groupsapp-backend
ExecStart=/home/ec2-user/groupsapp-backend/.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now groupsapp
sudo systemctl status groupsapp
```

#### 11. Publicar frontend con Nginx

```bash
sudo mkdir -p /var/www/groupsapp
sudo cp -r /home/ec2-user/groupsapp-backend/frontend/dist/* /var/www/groupsapp/
```

Config:

```bash
sudo tee /etc/nginx/conf.d/groupsapp.conf > /dev/null <<'EOF'
map $http_upgrade $connection_upgrade {
    default upgrade;
    '' close;
}

server {
    listen 80;
    server_name _;

    root /var/www/groupsapp;
    index index.html;

    client_max_body_size 25M;

    location / {
        try_files $uri /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_read_timeout 600s;
    }
}
EOF
```

```bash
sudo nginx -t
sudo systemctl enable --now nginx
sudo systemctl restart nginx
```

#### 12. Probar la app

Abre:

```text
http://IP_PUBLICA_EC2
```

Prueba:

1. register
2. login
3. crear grupo
4. join group
5. chat grupal
6. DM
7. subida de archivos

#### 13. Logs utiles

```bash
sudo systemctl status groupsapp
sudo journalctl -u groupsapp -n 200 --no-pager
sudo journalctl -u nginx -n 200 --no-pager
```

#### 14. Persistencia

Esta estrategia sirve bien para laboratorio, pero recuerda:

- si la instancia se detiene y vuelve a iniciar, un volumen EBS normalmente conserva datos
- si la instancia se termina, puedes perder la BD local y los archivos

Por eso, para algo mas serio:

1. usa RDS para PostgreSQL
2. mueve archivos a S3
3. agrega HTTPS y dominio
