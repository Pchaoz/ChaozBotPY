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
    print("Bot inciado correctamente")
    check_birthdays.start() #Comprueba si hay algun cumpleaños al iniciarse

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
        
# Comprobacion diaria que comprueba si es el cumpleaños de alguien
@tasks.loop(hours=24)
async def check_birthdays():
    # Para evitar que la base de datos entre en reposo, actualizo cada 24h la ultima vez que se hace un check de los cumpleaños
    date = datetime.today()
    today = datetime.today().strftime("%d-%m-%Y | %H:%M")

    try:
        supabase.table("table_updates").update({"last_update": today}).eq("id", 1).execute()
    except Exception as e:
        print(f"Error al actualizar la tabla de actualizaciones: {e}")

    current_year = date.year  # Obtiene el año en el que estamos
    channel = bot.get_channel(765717970055856158)  # La ID del canal para notificar el cumpleaños

    if channel is None:
        print("Error: No se pudo encontrar el canal.")
        return

    try:
        # Obtiene todos los cumpleaños de la base de datos
        response = supabase.table("birthdays").select("*").execute()
        birthdays = response.data

        # Comprueba si hay algún cumpleaños hoy
        birthday_found = False
        for birthday in birthdays:
            birth_date = datetime.strptime(birthday['date'], "%d-%m-%Y")
            birth_day_month = birth_date.strftime('%d-%m')
            if birth_day_month == today:
                birthday_found = True
                age = current_year - birth_date.year
                try:
                    await channel.send(f"@everyone ¡Hoy es el cumpleaños de {birthday['name']}! 🎉 Cumple {age} años.")
                except discord.errors.Forbidden:
                    print(f"No tengo permisos para enviar mensajes o mencionar a todos en el canal {channel.name}.")
                except Exception as e:
                    print(f"Error al enviar mensaje: {e}")

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
    
    
#Basicamente intenta conectar al bot usando el token del ENV
webserver.keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))