import discord
import re
import random

from decouple import config
from supabase import create_client, Client
from discord.ext import commands, tasks
from discord import app_commands

# Fechas / horas
from datetime import datetime, date, time, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError 

# ====================
# FUNCION EXTRAER NOMBRE DE GIF
# ====================
def extraer_nombre_gif(url):
    match = re.search(r'([\w-]+\.gif)', url)
    return match.group(1) if match else None

# ====================
# SUPABASE
# ====================
supabase: Client = create_client(config("DATABASE_URL"), config("DATABASE_KEY"))

# ====================
# OWNER
# ====================
OWNER_ID = 690680552629469184

def es_admin(ctx):
    return (
        ctx.author.id == OWNER_ID or 
        ctx.author.guild_permissions.administrator
    )

# ====================
# GIF BLACKLIST CACHE
# ====================
gif_blacklist_cache = []

def load_gif_blacklist():
    global gif_blacklist_cache
    try:
        response = supabase.table("gif_blacklist").select("*").execute()
        gif_blacklist_cache = [row["gif_value"].strip() for row in response.data]
        print(f"[GIF] Blacklist cargada: {len(gif_blacklist_cache)} elementos")
    except Exception as e:
        print(f"[GIF] Error cargando blacklist: {e}")

# ====================
# CANALES DONDE FILTRAR
# ====================
GIF_FILTER_CHANNELS = [
    int(ch.strip())
    for ch in config("GIF_FILTER_CHANNELS", default="").split(",")
    if ch.strip()
]

# ====================
# CONFIGURACIÓN / BOT
# ====================
def _load_tz():
    tzname = config("TIMEZONE", default="Europe/Madrid")
    try:
        return ZoneInfo(tzname)
    except ZoneInfoNotFoundError:
        try:
            import tzdata
            return ZoneInfo(tzname)
        except Exception:
            print(f"[WARN] No se encontró tzdata para '{tzname}'. Usando la zona local del sistema.")
            return datetime.now().astimezone().tzinfo or timezone.utc

TZ = _load_tz()

def now_local() -> datetime:
    return datetime.now(TZ)

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix=">", intents=intents, help_command=None)
tree = bot.tree

# ====================
# EVENTO PRINCIPAL
# ====================
@bot.event
async def on_ready():
    print("Bot iniciado correctamente")
    await bot.change_presence(activity=discord.Game(name="Usa /info o >info"))

    load_gif_blacklist()

    if not update_database.is_running():
        update_database.start()

    if not check_birthdays.is_running():
        check_birthdays.start()

    try:
        await tree.sync()
        print("Slash commands sincronizados correctamente.")
    except Exception as e:
        print(f"Error al sincronizar slash commands: {e}")

# ====================
# EMBED INFORMACIÓN
# ====================
def get_info_embed():
    embed = discord.Embed(
        title="Lista de comandos",
        description="El prefijo es: `>` o también puedes usar los slash commands `/`",
        color=discord.Color.yellow()
    )
    embed.set_thumbnail(url=config("BOTAVATAR", default="https://cdn.discordapp.com/avatars/1199687784437387365/a_6e2eff574f64daa0df8bc5211ad533b3.gif"))

    # Cumples
    embed.add_field(name="🎂 Cumpleaños", value=(
        "`/addcumple` o `>addCumple` → Añade cumpleaños. Formato: `NOMBRE DD-MM-AAAA`\n"
        "`/deletecumple` o `>deleteCumple` → Elimina un cumpleaños. Formato: `NOMBRE`\n"
        "`/listcumples` o `>listCumples` → Lista todos los cumpleaños registrados\n"
        "`/cumpleshoy` o `>cumplesHoy` → Muestra si hoy es el cumple de alguien"
    ), inline=False)

    # Admin
    embed.add_field(name="🛠️ Administración", value=(
        "`>banporid <id> [motivo]` → Banear usuario por ID (solo Owner)\n"
        "`>unbanporid <id>` → Desbanear usuario por ID (solo Owner)\n"
        "`>resetSlash` → Elimina todos los slash commands (solo Owner)\n"
        "`>reiniciarCumples` → Reinicia la tarea de cumpleaños (solo Owner)"
    ), inline=False)

    # Info
    embed.add_field(name="🤑 Otros", value=(
        "`/hola` o `>hola` → El bot te saluda\n"
        "`/info` o `>info` → Muestra este mensaje de ayuda"
    ), inline=False)

    embed.set_footer(text="Creado por Pchaozz", icon_url=config("MYDISCORDAVATAR", default="https://cdn.discordapp.com/avatars/690680552629469184/a_cb2b335c021d301da0cb883fe38b3eb4.gif"))
    return embed


# ====================
# FILTRO AUTOMÁTICO DE GIFS
# ====================
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    #print(f"[DEBUG] Mensaje en {message.channel.id}: {message.content}")

    contiene_gif = False
    gif_name = None

    # ====================
    # ADJUNTOS
    # ====================
    for attachment in message.attachments:
        if attachment.filename.lower().endswith(".gif"):
            contiene_gif = True
            gif_name = attachment.filename

    # ====================
    # LINKS
    # ====================
    urls = re.findall(r'(https?://[^\s]+)', message.content)

    for url in urls:
        if ".gif" in url:
            contiene_gif = True
            gif_name = extraer_nombre_gif(url)

    # ====================
    # EMBEDS
    # ====================
    for embed in message.embeds:
        if embed.url and ".gif" in embed.url:
            contiene_gif = True
            gif_name = extraer_nombre_gif(embed.url)

    # DEBUG
    if gif_name:
        print(f"[GIF DETECTADO] {gif_name}")

    # ====================
    # OWNER
    # ====================
    if message.author.id == OWNER_ID:

        if contiene_gif and gif_name and gif_name in gif_blacklist_cache:
            await message.delete()

        await bot.process_commands(message)
        return

    # ====================
    # FILTRO POR CANALES
    # ====================
    if GIF_FILTER_CHANNELS:
        if message.channel.id not in GIF_FILTER_CHANNELS:
            await bot.process_commands(message)
            return

    # ====================
    # FILTRADO NORMAL
    # ====================
    if contiene_gif and gif_name:
        print(f"[CHECK] '{gif_name.strip()}' vs {gif_blacklist_cache}")
        if gif_name.strip() in gif_blacklist_cache:
            try:
                print(f"[GIF BLOQUEADO] {gif_name}")
                await message.delete()
            except Exception as e:
                print(f"[GIF ERROR] {e}")

    await bot.process_commands(message)


# ====================
# COMANDOS GIF
# ====================

@bot.command(name="filtrargif")
async def filtrar_gif(ctx, *, url: str):

    if not es_admin(ctx):
        await ctx.send("No tienes permisos ❌")
        return

    if url in gif_blacklist_cache:
        await ctx.send("Ese GIF ya está en la blacklist ⚠️")
        return

    try:
        supabase.table("gif_blacklist").insert({
            "gif_value": url
        }).execute()

        gif_blacklist_cache.append(url)

        await ctx.send("GIF añadido a la blacklist 🚫")

    except Exception as e:
        await ctx.send(f"Error: {e}")


@bot.command(name="quitargif")
async def quitar_gif(ctx, *, url: str):

    if not es_admin(ctx):
        await ctx.send("No tienes permisos ❌")
        return

    try:
        supabase.table("gif_blacklist").delete().eq("gif_value", url).execute()

        if url in gif_blacklist_cache:
            gif_blacklist_cache.remove(url)

        await ctx.send("GIF eliminado de la blacklist ✅")

    except Exception as e:
        await ctx.send(f"Error: {e}")


@bot.command(name="listargifs")
async def listar_gifs(ctx):

    if not es_admin(ctx):
        await ctx.send("No tienes permisos ❌")
        return

    if not gif_blacklist_cache:
        await ctx.send("La blacklist está vacía 📭")
        return

    msg = "🚫 **GIFs bloqueados:**\n"
    msg += "\n".join(f"- {gif}" for gif in gif_blacklist_cache[:50])

    if len(gif_blacklist_cache) > 50:
        msg += "\n... (demasiados para mostrar)"

    await ctx.send(msg)

# ====================
# COMANDOS DE PREFIJO
# ====================
@bot.command(name="resetSlash")
async def clear_slash(ctx):
    if ctx.author.id != int(config("OWNER_ID")):
        await ctx.send("No tienes permiso para esto.")
        return
    bot.tree.clear_commands(guild=None)
    await bot.tree.sync()
    await ctx.send("Todos los slash commands eliminados. Reinicia el bot para registrar solo los nuevos.")

@bot.command(name="info")
async def info_command(ctx):
    await ctx.send(embed=get_info_embed())

@bot.command(name="addCumple")
async def add_birthday(ctx, name: str, date: str):
    try:
        datetime.strptime(date, "%d-%m-%Y")
        supabase.table("birthdays").insert({"name": name, "date": date}).execute()
        await ctx.send(f"Cumpleaños de {name} agregado para el {date}.")
    except ValueError:
        await ctx.send("El formato de la fecha es incorrecto. Usa DD-MM-AAAA.")
    except Exception as e:
        await ctx.send(f"Error al agregar el cumpleaños: {e}")

@bot.command(name="deleteCumple")
async def delete_birthday(ctx, name: str):
    try:
        supabase.table("birthdays").delete().eq("name", name).execute()
        await ctx.send(f"Cumpleaños de {name} eliminado.")
    except Exception as e:
        await ctx.send(f"Error al eliminar el cumpleaños: {e}")

@bot.command(name="listCumples")
async def list_birthdays(ctx):
    try:
        response = supabase.table("birthdays").select("*").execute()
        birthdays = response.data
        update_response = supabase.table("table_updates").select("last_update").eq("id", 1).execute()
        last_update = update_response.data[0]['last_update'] if update_response.data else "Desconocido"

        if birthdays:

            def parse_fecha(f):
                if isinstance(f, (datetime, date)):
                    return f
                return datetime.strptime(f, "%d-%m-%Y")

            birthdays.sort(key=lambda x: parse_fecha(x['date']).strftime("%m-%d"))

            msg = f"🎂 Cumples registrados (última actualización: {last_update}):\n"
            msg += "\n".join(f"{b['name']} - {b['date']}" for b in birthdays)
        else:
            msg = "No hay cumpleaños registrados."
        await ctx.send(msg)
    except Exception as e:
        await ctx.send(f"Error al listar los cumpleaños: {e}")

@bot.command(name="cumplesHoy")
async def birthdays_today(ctx):
    today_str = now_local().strftime("%d-%m")
    current_year = now_local().year

    try:
        birthdays = supabase.table("birthdays").select("*").execute().data
        found = False
        msg = "🎉 **Cumpleaños de hoy:**\n"
        for b in birthdays:
            bdate = datetime.strptime(b["date"], "%d-%m-%Y")
            if bdate.strftime("%d-%m") == today_str:
                age = current_year - bdate.year
                msg += f"🎂 {b['name']} cumple {age} años\n"
                found = True

        if found:
            await ctx.send(msg)
        else:
            proximo = get_next_birthday(birthdays)
            if proximo:
                nombre, fecha, dias = proximo
                texto_dias = "mañana" if dias == 1 else f"en {dias} días"
                await ctx.send(f"No es el cumpleaños de nadie, el próximo cumpleaños es de {nombre} el día {fecha} ({texto_dias}).")
            else:
                await ctx.send("No es el cumpleaños de nadie, y no hay más cumpleaños registrados.")
    except Exception as e:
        await ctx.send(f"Error al comprobar cumpleaños: {e}")

@bot.command(name="reiniciarCumples")
async def restart_check_birthdays(ctx):
    if ctx.author.id != int(config("OWNER_ID")):
        return await ctx.send("No tienes permiso para usar este comando.")
    try:
        if check_birthdays.is_running():
            check_birthdays.cancel()
        check_birthdays.start()
        await ctx.send("Tarea de cumpleaños reiniciada.")
    except RuntimeError as e:
        await ctx.send(f"Error al reiniciar: {e}")

@bot.command(name="banporid")
async def ban_user_by_id(ctx, user_id: int, *, reason: str = "No se especificó motivo."):
    if ctx.author.id != int(config("OWNER_ID")):
        return await ctx.send("No tienes permiso para usar este comando.")
    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.ban(user, reason=reason)
        await ctx.send(f"Usuario `{user_id}` baneado. Motivo: {reason}")
    except discord.Forbidden:
        await ctx.send("No tengo permisos suficientes para banear.")
    except discord.NotFound:
        await ctx.send("Usuario no encontrado.")
    except Exception as e:
        await ctx.send(f"Error inesperado: {e}")

@bot.command(name="unbanporid")
async def unban_user_by_id(ctx, user_id: int):
    if ctx.author.id != int(config("OWNER_ID")):
        return await ctx.send("No tienes permiso para usar este comando.")
    try:
        bans = [ban async for ban in ctx.guild.bans()]
        for ban in bans:
            if ban.user.id == user_id:
                await ctx.guild.unban(ban.user)
                return await ctx.send(f"Usuario `{ban.user}` desbaneado.")
        await ctx.send("Ese usuario no está baneado.")
    except discord.Forbidden:
        await ctx.send("No tengo permisos para desbanear.")
    except Exception as e:
        await ctx.send(f"Error inesperado: {e}")

# ====================
# COMANDOS SLASH
# ====================
@tree.command(name="hola", description="Te saluda el bot")
async def slash_hi(interaction: discord.Interaction):
    await interaction.response.send_message(f"Holiwis {interaction.user.mention}")

@tree.command(name="info", description="Muestra información del bot")
async def slash_info(interaction: discord.Interaction):
    await interaction.response.send_message(embed=get_info_embed())

@tree.command(name="addcumple", description="Añade un cumpleaños")
@app_commands.describe(name="Nombre de la persona", date="Fecha en formato DD-MM-AAAA")
async def slash_addcumple(interaction: discord.Interaction, name: str, date: str):
    try:
        datetime.strptime(date, "%d-%m-%Y")
        supabase.table("birthdays").insert({"name": name, "date": date}).execute()
        await interaction.response.send_message(f"Cumpleaños de {name} agregado para el {date}.")
    except ValueError:
        await interaction.response.send_message("Formato incorrecto. Usa DD-MM-AAAA.")
    except Exception as e:
        await interaction.response.send_message(f"Error: {e}")

@tree.command(name="deletecumple", description="Elimina un cumpleaños")
@app_commands.describe(name="Nombre a eliminar")
async def slash_deletecumple(interaction: discord.Interaction, name: str):
    try:
        supabase.table("birthdays").delete().eq("name", name).execute()
        await interaction.response.send_message(f"Cumpleaños de {name} eliminado.")
    except Exception as e:
        await interaction.response.send_message(f"Error: {e}")

@tree.command(name="listcumples", description="Lista todos los cumpleaños")
async def slash_listcumples(interaction: discord.Interaction):
    try:
        response = supabase.table("birthdays").select("*").execute()
        birthdays = response.data
        update_response = supabase.table("table_updates").select("last_update").eq("id", 1).execute()
        last_update = update_response.data[0]['last_update'] if update_response.data else "Desconocido"

        if birthdays:
            msg = f"🎂 Cumples registrados (última actualización: {last_update}):\n"
            msg += "\n".join(f"{b['name']} - {b['date']}" for b in birthdays)
        else:
            msg = "No hay cumpleaños registrados."
        await interaction.response.send_message(msg)
    except Exception as e:
        await interaction.response.send_message(f"Error: {e}")

@tree.command(name="cumpleshoy", description="Verifica si hoy es el cumpleaños de alguien")
async def slash_cumpleshoy(interaction: discord.Interaction):
    today_str = now_local().strftime("%d-%m")
    current_year = now_local().year
    try:
        birthdays = supabase.table("birthdays").select("*").execute().data
        found = False
        msg = "🎉 **Cumples de hoy:**\n"
        for b in birthdays:
            bdate = datetime.strptime(b["date"], "%d-%m-%Y")
            if bdate.strftime("%d-%m") == today_str:
                age = current_year - bdate.year
                msg += f"🎂 {b['name']} cumple {age} años\n"
                found = True

        if found:
            await interaction.response.send_message(msg)
        else:
            proximo = get_next_birthday(birthdays)
            if proximo:
                nombre, fecha, dias = proximo
                texto_dias = "mañana" if dias == 1 else f"en {dias} días"
                await interaction.response.send_message(f"No es el cumpleaños de nadie, el próximo cumpleaños es de {nombre} el día {fecha} ({texto_dias}).")
            else:
                await interaction.response.send_message("No es el cumpleaños de nadie, y no hay más cumpleaños registrados.")
    except Exception as e:
        await interaction.response.send_message(f"Error: {e}")

# ====================
# TAREAS PERIÓDICAS
# ====================
@tasks.loop(hours=5)
async def update_database():
    # Guardamos la hora local en la tabla de control
    today = now_local().strftime("%d-%m-%Y | %H:%M")
    try:
        supabase.table("table_updates").update({"last_update": today}).eq("id", 1).execute()
    except Exception as e:
        print(f"Error al actualizar tabla: {e}")

# Aviso diario a una hora fija local (09:00). Ajusta la hora si quieres.
@tasks.loop(time=time(0, 0, tzinfo=TZ))
async def check_birthdays():
    await bot.wait_until_ready()
    today_str = now_local().strftime("%d-%m")
    current_year = now_local().year
    channel = bot.get_channel(int(config("BIRTHDAY_CHANNEL_ID")))
    if not channel:
        print("Canal no encontrado")
        return
    try:
        birthdays = supabase.table("birthdays").select("*").execute().data
        found = False
        for b in birthdays:
            if datetime.strptime(b['date'], "%d-%m-%Y").strftime("%d-%m") == today_str:
                age = current_year - datetime.strptime(b['date'], "%d-%m-%Y").year
                await channel.send(f"@everyone Hoy es el cumple de {b['name']}! 🎉 ({age} años)")
                found = True
        if not found:
            proximo = get_next_birthday(birthdays)
            if proximo:
                nombre, fecha, dias = proximo
                texto_dias = "mañana" if dias == 1 else f"en {dias} días"
                await channel.send(f"No es el cumpleaños de nadie. El próximo cumpleaños es de {nombre} el día {fecha} ({texto_dias}).")
            else:
                await channel.send("No es el cumpleaños de nadie, y no hay más cumpleaños registrados.")
    except Exception as e:
        print(f"Error al comprobar cumpleaños: {e}")

# ====================
# OTRAS FUNCIONES
# ====================
def get_next_birthday(birthdays):
    # Trabajamos siempre en fecha local
    today = now_local().date()
    candidates = []
    for b in birthdays:
        try:
            bdate = datetime.strptime(b["date"], "%d-%m-%Y")
            # Cumple del año actual
            next_birthday = bdate.replace(year=today.year).date()
            # Si ya pasó, movemos al año siguiente
            if next_birthday < today:
                next_birthday = next_birthday.replace(year=today.year + 1)
            days_until = (next_birthday - today).days
            candidates.append((days_until, next_birthday, b["name"]))
        except Exception:
            continue
    if not candidates:
        return None
    days_until, next_birthday, name = min(candidates, key=lambda x: x[0])
    return name, next_birthday.strftime("%d-%m"), days_until

# ====================
# EJECUCIÓN
# ====================
bot.run(config("DISCORD_TOKEN"))
