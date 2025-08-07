import discord
import csv
import os
import webserver

from decouple import config
from supabase import create_client, Client
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta

# Supabase
supabase: Client = create_client(config("DATABASE_URL"), config("DATABASE_KEY"))

# Inicializar el bot
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=">", intents=intents)
tree = bot.tree

# Embed de información
def get_info_embed():
    embed = discord.Embed(title="INFORMACION", color=discord.Color.yellow())
    embed.set_thumbnail(url=config("BOTAVATAR"))
    embed.add_field(name="Comandos y más cositas", value="El prefijo que tenéis que usar para cualquier comando es: `>`", inline=False)
    embed.add_field(name="/hola o >hola", value="Te saluda el bot", inline=False)
    embed.add_field(name="/addcumple o >addCumple", value="Añade cumpleaños. Formato: `NOMBRE DD-MM-AAAA`", inline=False)
    embed.add_field(name="/deletecumple o >deleteCumple", value="Elimina un cumpleaños. Formato: `NOMBRE`", inline=False)
    embed.add_field(name="/listcumples o >listCumples", value="Lista los cumpleaños", inline=False)
    embed.add_field(name="/cumpleshoy o >cumplesHoy", value="Muestra si hoy es el cumpleaños de alguien", inline=False)
    embed.set_footer(text="Creado por Pchaozz", icon_url=config("MYDISCORDAVATAR"))
    return embed

# ====================
# EVENTO PRINCIPAL
# ====================
@bot.event
async def on_ready():
    print("Bot iniciado correctamente")
    await bot.change_presence(activity=discord.Game(name="Usa /info o >info"))

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
# COMANDOS DE PREFIJO
# ====================
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
            msg = f"🎂 Cumples registrados (última actualización: {last_update}):\n"
            msg += "\n".join(f"{b['name']} - {b['date']}" for b in birthdays)
        else:
            msg = "No hay cumpleaños registrados."
        await ctx.send(msg)
    except Exception as e:
        await ctx.send(f"Error al listar los cumpleaños: {e}")

@bot.command(name="cumplesHoy")
async def birthdays_today(ctx):
    today_str = datetime.today().strftime("%d-%m")
    current_year = datetime.today().year

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
                nombre, fecha = proximo
                await ctx.send(f"No es el cumpleaños de nadie, el próximo cumpleaños es de {nombre} el día {fecha}.")
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
    today_str = datetime.today().strftime("%d-%m")
    current_year = datetime.today().year
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
                nombre, fecha = proximo
                await interaction.response.send_message(f"No es el cumpleaños de nadie, el próximo cumpleaños es de {nombre} el día {fecha}.")
            else:
                await interaction.response.send_message("No es el cumpleaños de nadie, y no hay más cumpleaños registrados.")
    except Exception as e:
        await interaction.response.send_message(f"Error: {e}")


# ====================
# TAREAS PERIÓDICAS
# ====================
@tasks.loop(hours=5)
async def update_database():
    today = datetime.today().strftime("%d-%m-%Y | %H:%M")
    try:
        supabase.table("table_updates").update({"last_update": today}).eq("id", 1).execute()
    except Exception as e:
        print(f"Error al actualizar tabla: {e}")

@tasks.loop(hours=24)
async def check_birthdays():
    await bot.wait_until_ready()
    today_str = datetime.today().strftime("%d-%m")
    current_year = datetime.today().year
    channel = bot.get_channel(765717970055856158)
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
    today = datetime.today().date()  # Solo la fecha
    candidates = []
    for b in birthdays:
        try:
            bdate = datetime.strptime(b["date"], "%d-%m-%Y")
            next_birthday = bdate.replace(year=today.year).date()
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
webserver.keep_alive()
bot.run(config("DISCORD_TOKEN"))
