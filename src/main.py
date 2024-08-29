import discord
import csv

from dotenv import load_dotenv
from decouple import config
from discord.ext import commands, tasks
from datetime import datetime

bot = commands.Bot(command_prefix=".", intents=discord.Intents.all())

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
    today = datetime.today().strftime('%d-%m-%Y')
    channel = bot.get_channel(1138968277360582757) #La ID del canal en el que hara la noticia
    
    try:
        with open(CSV_FILE, 'r') as file:
            reader = csv.reader(file)
            birthdays = list(reader)
        for name, date in birthdays:
            if date == today:
                await channel.send(f"¡Hoy es el cumpleaños de {name} @everywone!")
            
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
    embeded_msg = discord.Embed(title="INFORMACION", description="Pues no se, la descripcion", color=discord.Color.yellow())
    embeded_msg.set_thumbnail(url=ctx.message.author.avatar)
    embeded_msg.add_field(name="test", value="valor", inline=False)
    embeded_msg.set_image(url=ctx.guild.icon)
    embeded_msg.set_footer(text="Creado por Pchaozz", icon_url=ctx.author.avatar)
    await ctx.send(embed=embeded_msg)    
    
    
#Basicamente intenta conectar al bot usando el token del ENV
bot.run(config("TOKEN"))