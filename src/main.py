import discord
import csv
import os
import webserver

from decouple import config
from supabase import create_client, Client
from discord.ext import commands, tasks
from datetime import datetime

#COSAS DE LA BASE DE DATOS 

supabase: Client = create_client(os.getenv("DATABASE_URL"), os.getenv("DATABASE_KEY"))

#Inicializar el bot con el prefijo (>)
bot = commands.Bot(command_prefix=">", intents=discord.Intents.all())

# Archivo CSV donde se guardan los cumpleaños
#CSV_FILE = 'birthdays.csv'

#Este evento sirve para avisar cuando el bot ha acabado de levantarse
@bot.event
async def on_ready():
    print("Bot iniciado correctamente")
    await bot.change_presence(activity=discord.Game(name="Usa >info para ver mis comandos!")) # Cambia el estado del bot al iniciar

    if not update_database.is_running():
        update_database.start() # Inicia el bucle de actualización de la base de datos

    if not check_birthdays.is_running():
        check_birthdays.start() # Inicia el bucle de comprobación de cumpleaños

#SOBRE LOS @bot.command()  
#Si dentro de los partensesis haces un aliases con contenido 
#por ejemplo =["hola", "/o"] puedes hacer un diccionario con posibles opciones para triggerear lo mismo
#o tambien puedes hacer name="nombre" para que no usar el nombre de la funcion e usar uno diferente a ella

#Este comando sirve para añadir un cumpleaños
@bot.command(name="addCumple")
async def add_birthday(ctx, name: str, date: str):
    try:
        # Verifica el formato de la fecha
        datetime.strptime(date, "%d-%m-%Y")

        # Inserta el nuevo cumpleaños en la base de datos
        supabase.table("birthdays").insert({"name": name, "date": date}).execute()
        await ctx.send(f"Cumpleaños de {name} agregado para el {date}.")
    except ValueError:
        await ctx.send("El formato de la fecha es incorrecto. Usa DD-MM-AAAA.")
    except Exception as e:
        await ctx.send(f"Error al agregar el cumpleaños: {e}")


#Este comando sirve para eliminar un cumpleaños      
@bot.command(name="deleteCumple")
async def delete_birthday(ctx, name: str):
    try:
        # Elimina el cumpleaños de la base de datos
        supabase.table("birthdays").delete().eq("name", name).execute()
        await ctx.send(f"Cumpleaños de {name} eliminado.")
    except Exception as e:
        await ctx.send(f"Error al eliminar el cumpleaños: {e}")

#Este comando te lista todos los cumpleaños
@bot.command(name="listCumples")
async def list_birthdays(ctx):
    try:
        # Obtiene todos los cumpleaños de la base de datos
        response = supabase.table("birthdays").select("*").execute()
        birthdays = response.data

        # Obtiene la última fecha de actualización de la tabla table_updates
        update_response = supabase.table("table_updates").select("last_update").eq("id", 1).execute()
        last_update = update_response.data[0]['last_update'] if update_response.data else "Desconocido"

        if birthdays:
            response_message = f"Cumpleaños registrados (última comprobación: {last_update}): \n"
            for birthday in birthdays:
                response_message += f"{birthday['name']} - {birthday['date']} \n"
            await ctx.send(response_message)
        else:
            await ctx.send(f"No hay cumpleaños registrados (última comprobación: {last_update}).")
    except Exception as e:
        await ctx.send(f"Error al listar los cumpleaños: {e}")
        
@tasks.loop(hours=5)
async def update_database():
    
    # Para evitar que la base de datos entre en reposo, actualizo cada 5h la ultima vez que se hace un check de los cumpleaños
    date = datetime.today()
    today = datetime.today().strftime("%d-%m-%Y | %H:%M")

    try:
        supabase.table("table_updates").update({"last_update": today}).eq("id", 1).execute()
    except Exception as e:
        print(f"Error al actualizar la tabla de actualizaciones: {e}")
    
        
# Comprobacion diaria que comprueba si es el cumpleaños de alguien
@tasks.loop(hours=24)
async def check_birthdays():
    date = datetime.today()
    today_str = date.strftime("%d-%m")
    current_year = date.year

    channel = bot.get_channel(765717970055856158)  # Reemplazar esto por algo dinámico en el futuro

    if channel is None:
        print("Error: No se pudo encontrar el canal.")
        return

    try:
        # Obtiene todos los cumpleaños de la base de datos
        response = supabase.table("birthdays").select("*").execute()
        birthdays = response.data
        
        # Verifica si hoy es el cumpleaños de alguien
        birthday_found = False
        for birthday in birthdays:
            birth_date = datetime.strptime(birthday['date'], "%d-%m-%Y")
            birth_day_month = birth_date.strftime('%d-%m')

            if birth_day_month == today_str:
                birthday_found = True
                age = current_year - birth_date.year
                try:
                    await channel.send(f"@everyone ¡Hoy es el cumpleaños de {birthday['name']}! 🎉 Cumple {age} años.")
                except discord.errors.Forbidden:
                    print(f"No tengo permisos para enviar mensajes o mencionar a todos en el canal {channel.name}.")
                except Exception as e:
                    print(f"Error al enviar mensaje: {e}")
        #Si no es el cumpleaños de nadie, lo avisa
        if not birthday_found:
            await channel.send("Hoy no es el cumpleaños de nadie.")
    except Exception as e:
        print(f"Error al comprobar cumpleaños: {e}")

        
#Este comando te dice hola mencionandote
@bot.command(name="hola")
async def hi(ctx):
    await ctx.send(f"Holiwis {ctx.author.mention}")
    
#Comando de prueba para repita el mensaje del usuario pero sin el prefijo W.I.P
@bot.command(name="que")
async def repeatuser(ctx):
    print(ctx.message.content)
    base_msg = ctx.message.content
    

#INFO DEL BOT
@bot.command(name="info")
async def description(ctx):
    embeded_msg = discord.Embed(title="INFORMACION", description=f"Comandos y mas cositas. El prefijo que teneis que usar para cualquier comando es: >", color=discord.Color.yellow())
    embeded_msg.set_thumbnail(url=os.getenv("BOTAVATAR"))
    embeded_msg.add_field(name=">hola", value="Te saluda el bot de vuelta, totalmente de forma amigable", inline=False)
    embeded_msg.add_field(name=">addCumple", value="Añade un cumpleaños, formato a usar el comando -> NOMBRE DD-MM-AAAA", inline=False)
    embeded_msg.add_field(name=">deleteCumple", value="Elimina un cumpleaños, formato a usar el comando -> NOMBRE", inline=False)
    embeded_msg.add_field(name=">listCumples", value="Lista todos los cumpleaños en un mensaje normal de texto", inline=False)
    embeded_msg.set_footer(text="Creado por Pchaozz", icon_url=os.getenv("MYDISCORDAVATAR"))
    await ctx.send(embed=embeded_msg)    
    
@bot.command(name="banporid")
async def ban_user_by_id(ctx, user_id: int, *, reason: str = "No se especificó motivo."):
    ID_AUTORIZADO = 690680552629469184

    if ctx.author.id != ID_AUTORIZADO:
        await ctx.send(" No tienes permiso para usar este comando.")
        return

    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.ban(user, reason=reason)
        await ctx.send(f"Usuario con ID `{user_id}` ha sido baneado. Motivo: {reason}")
    except discord.Forbidden:
        await ctx.send("No tengo permisos suficientes para banear a ese usuario.")
    except discord.NotFound:
        await ctx.send("No se encontró un usuario con esa ID.")
    except Exception as e:
        await ctx.send(f"Error inesperado: {e}")

@bot.command(name="unbanporid")
async def unban_user_by_id(ctx, user_id: int):
    ID_AUTORIZADO = 690680552629469184

    if ctx.author.id != ID_AUTORIZADO:
        await ctx.send("No tienes permiso para usar este comando.")
        return

    try:
        user = await bot.fetch_user(user_id)
        bans = [ban async for ban in ctx.guild.bans()]


        for ban_entry in bans:
            if ban_entry.user.id == user_id:
                await ctx.guild.unban(ban_entry.user)
                await ctx.send(f"Usuario `{ban_entry.user}` ha sido desbaneado.")
                return

        await ctx.send("Ese usuario no está baneado en este servidor.")
    except discord.Forbidden:
        await ctx.send("No tengo permisos suficientes para desbanear a ese usuario.")
    except Exception as e:
        await ctx.send(f"Error inesperado: {e}")


    
    
#Basicamente intenta conectar al bot usando el token del ENV
webserver.keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))