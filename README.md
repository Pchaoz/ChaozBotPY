# 🤖 KaosBot

> Bot multifunción para Discord desarrollado en Python con `discord.py` y persistencia de datos en **Supabase**.

---

## ✨ Funcionalidades

- 🎂 **Gestión de cumpleaños** — Registra, elimina y consulta cumpleaños. Aviso automático diario.
- 🚫 **Filtro de GIFs** — Blacklist de GIFs que se eliminan automáticamente en canales configurados.
- 🛠️ **Herramientas de administración** — Ban/unban por ID, gestión de slash commands.
- ⚡ **Slash commands** — Todos los comandos principales disponibles también como `/comando`.

---

## 🛠️ Tecnologías

| Tecnología | Uso |
|---|---|
| Python 3.10+ | Lenguaje principal |
| [discord.py](https://discordpy.readthedocs.io/) | API de Discord |
| [Supabase](https://supabase.com/) | Base de datos (PostgreSQL) |
| [python-decouple](https://pypi.org/project/python-decouple/) | Variables de entorno |

---

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/Pchaoz/ChaozBotPY.git
cd ChaozBotPY
```

### 2. Instalar dependencias

El proyecto incluye un `requirements.txt` con las versiones exactas:

```bash
pip install -r requirements.txt
```

```
discord.py==2.4.0
python-decouple==3.8
supabase==2.13.0
tzdata==2025.1
```

### 3. Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
DISCORD_TOKEN=tu_token_aqui
DATABASE_URL=https://xxxx.supabase.co
DATABASE_KEY=tu_api_key_aqui
OWNER_ID=tu_id_de_discord
TIMEZONE=Europe/Madrid
BOTAVATAR=https://url-del-avatar-del-bot.gif
MYDISCORDAVATAR=https://url-de-tu-avatar.gif

# IDs de canales donde se filtra GIFs (separados por comas, sin espacios)
GIF_FILTER_CHANNELS=765717970055856158,973193910547542057,1138932431022473276,1405643983941799989

# Canal donde se anuncian los cumpleaños
BIRTHDAY_CHANNEL_ID=765717970055856158
```

### 4. Configurar Supabase

Crea las siguientes tablas en tu proyecto de Supabase:

**`birthdays`**
```sql
create table birthdays (
  id bigint primary key generated always as identity,
  name text not null,
  date text not null
);
```

**`gif_blacklist`**
```sql
create table gif_blacklist (
  id bigint primary key generated always as identity,
  gif_value text not null
);
```

**`table_updates`**
```sql
create table table_updates (
  id bigint primary key,
  last_update text
);
-- Inserta el registro inicial
insert into table_updates (id, last_update) values (1, 'N/A');
```

### 5. Ejecutar el bot

```bash
python main.py
```

---

## 📋 Comandos

### 🎂 Cumpleaños

| Comando | Slash | Descripción |
|---|---|---|
| `>addCumple <nombre> <fecha>` | `/addcumple` | Añade un cumpleaños. Fecha en formato `DD-MM-AAAA` |
| `>deleteCumple <nombre>` | `/deletecumple` | Elimina el cumpleaños de una persona |
| `>listCumples` | `/listcumples` | Lista todos los cumpleaños registrados |
| `>cumplesHoy` | `/cumpleshoy` | Muestra si hoy hay cumpleaños o cuándo es el próximo |

### 🚫 Filtro de GIFs *(solo admins)*

| Comando | Descripción |
|---|---|
| `>filtrargif <nombre.gif>` | Añade un GIF a la lista negra |
| `>quitargif <nombre.gif>` | Elimina un GIF de la lista negra |
| `>listargifs` | Muestra todos los GIFs bloqueados |

### 🛠️ Administración *(solo Owner)*

| Comando | Descripción |
|---|---|
| `>banporid <id> [motivo]` | Banea un usuario por su ID |
| `>unbanporid <id>` | Desbanea un usuario por su ID |
| `>resetSlash` | Elimina y re-sincroniza los slash commands |
| `>reiniciarCumples` | Reinicia la tarea periódica de cumpleaños |

### 🤖 Generales

| Comando | Slash | Descripción |
|---|---|---|
| `>hola` | `/hola` | El bot te saluda |
| `>info` | `/info` | Muestra la lista de comandos |

---

## ⚙️ Configuración de Canales

Todos los IDs de canal se gestionan desde el `.env`, sin tocar el código:

```env
# Canales donde se aplica el filtro de GIFs (separados por comas)
GIF_FILTER_CHANNELS=765717970055856158,973193910547542057,1138932431022473276,1405643983941799989

# Canal donde el bot anuncia los cumpleaños
BIRTHDAY_CHANNEL_ID=765717970055856158
```

El bot los carga automáticamente al iniciar:

```python
# GIF_FILTER_CHANNELS se parsea como lista de enteros desde el .env
# BIRTHDAY_CHANNEL_ID se usa en la tarea check_birthdays
```

---

## 🔐 Permisos

| Nivel | Acceso |
|---|---|
| **Owner** | Todos los comandos sin restricción |
| **Administrador del servidor** | Comandos de gestión de GIFs |
| **Usuario general** | Comandos de cumpleaños, hola e info |

---

## 🔄 Tareas Automáticas

| Tarea | Frecuencia | Descripción |
|---|---|---|
| `update_database` | Cada 5 horas | Actualiza el registro de última actualización en Supabase |
| `check_birthdays` | Diaria a las 00:00 | Comprueba y anuncia cumpleaños del día |

---

## 📁 Estructura del Proyecto

```
.
├── src/
│   └── main.py          # Código principal del bot
├── .gitignore
├── ChaozBotPY.code-workspace
├── requirements.txt     # Dependencias con versiones fijas
├── .env                 # Variables de entorno (no subir a git)
└── README.md
```

---

## 📝 Notas

- La caché de GIFs se carga al iniciar el bot. Los cambios hechos directamente en Supabase sin usar los comandos requieren reinicio.
- Los slash commands pueden tardar hasta **1 hora** en propagarse globalmente tras sincronizarse.
- Si `tzdata` no está disponible en el sistema, el bot usa la zona horaria local como fallback.

---

## 👤 Autor

**Pchaozz** — [Discord](https://discord.com/)

---

## 📄 Licencia

Este proyecto es de uso privado. Contacta al autor para más información.
