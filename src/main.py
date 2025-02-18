import discord
import csv
import os
import webserver

from decouple import config
from discord.ext import commands, tasks
from datetime import datetime


bot = commands.Bot(command_prefix=">", intents=discord.Intents.all())

# Archivo CSV donde se guardan los cumpleaños
CSV_FILE = 'birthdays.csv'

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
        #Primero se comprueba que el formato sea el correcto
        datetime.strptime(date, "%d-%m-%Y")
        #Se guarda el cumpleaños en un CSV 
        with open(CSV_FILE, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([name, date])
            
            #Si se guarda con exito envia un mensaje indicando que ha funcionado
            await ctx.send(f"Cumpleaños de {name} agregado para el {date}.")
        
    except ValueError:
        await ctx.send("El formato de la fecha es incorrecto. Usa DD-MM-AAAA.")

#Este comando sirve para eliminar un cumpleaños      
@bot.command(name="deleteCumple")
async def delete_birthday(ctx, name: str):
    try:
        with open(CSV_FILE, 'r') as file:
            reader = csv.reader(file)
            birthdays = list(reader)

        # Filtra los cumpleaños para excluir el que se desea eliminar
        new_birthdays = [row for row in birthdays if row[0].lower() != name.lower()]

        #Si lo encuentra lo substituye por una linea en blanco
        if len(new_birthdays) < len(birthdays):
            with open(CSV_FILE, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(new_birthdays)
            await ctx.send(f"Cumpleaños de {name} eliminado.")
        else:
            await ctx.send(f"No se encontró un cumpleaños para {name}.")
    except FileNotFoundError:
        await ctx.send("No hay cumpleaños registrados.")
        
  
#Este comando te lista todos los cumpleaños
@bot.command(name="listCumples")
async def list_birthdays(ctx):
    try:
        with open(CSV_FILE, 'r') as file:
            reader = csv.reader(file)
            birthdays = list(reader)
        if birthdays:
            response = "Cumpleaños registrados: \n"
            #Por cada cumple en el CSV lo agrega al string con la respuesta final
            for name, date in birthdays:
                response += f"{name} - {date} \n"
            await ctx.send(response)
        else:
            await ctx.send("No hay cumpleaños registrados.")
            
    except FileNotFoundError:
        await ctx.send("No hay cumpleaños registrados.")

#Comprobacion diaria que comprueba si es el cumpleaños de alguien
@tasks.loop(hours=24)
async def check_birthdays():
    today = datetime.today().strftime('%d-%m')  # Obtiene solo día y mes de hoy
    current_year = datetime.today().year  # Obtiene el año en el que estamos
    channel = bot.get_channel(765717970055856158)  # La ID del canal para notificar el cumpleaños
    
    try:
        with open(CSV_FILE, 'r') as file:
            reader = csv.reader(file)
            birthdays = list(reader)
        for name, date in birthdays:
            # Se extrae solo el dia y el mes
            birth_date = datetime.strptime(date, "%d-%m-%Y")
            birth_day_month = birth_date.strftime('%d-%m')
            
            if birth_day_month == today:
                age = current_year - birth_date.year
                try:
                    # Menciona a todos y envía el mensaje
                    await channel.send(f"¡Hoy es el cumpleaños de {name}! 🎉 Cumple {age} años. @everyone ")
                except discord.errors.Forbidden:
                    # Si el bot no tiene permisos para menionar a todo el mundo envia este mensaje en vez de la felicitacion
                    print(f"No tengo permisos para enviar mensajes o mencionar a todos en el canal {channel.name}.")
                except Exception as e:
                    print(f"Error al enviar mensaje: {e}")
    except FileNotFoundError:
        print("No se encontró el archivo de cumpleaños.")
        
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