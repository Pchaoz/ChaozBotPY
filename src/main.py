import discord

from dotenv import load_dotenv
from decouple import config
from discord.ext import commands

bot = commands.Bot(command_prefix=".", intents=discord.Intents.all())

#Este evento sirve para avisar cuando el bot ha acabado de levantarse
@bot.event
async def on_ready():
    print("Bot inciado correctamente")

#SOBRE LOS @bot.command()  
#Si dentro de los partensesis haces un aliases con contenido 
#por ejemplo =["hola", "/o"] puedes hacer un diccionario con posibles opciones para triggerear lo mismo
#o tambien puedes hacer name="nombre" para que no usar el nombre de la funcion e usar uno diferente a ella

#Este comando te dice hola mencionandote
@bot.command(name="hola") 
async def hi(ctx):
    await ctx.send(f"Holiwis {ctx.author.mention}")
    
@bot.command(name="que")
async def repeatuser(ctx):
    await ctx.send(f"Has dicho {ctx}")

#INFO DEL BOT
@bot.command(name="info")
async def description(ctx):
    embeded_msg = discord.Embed(title="INFORMACION", description="Pues no se, la descripcion", color=discord.Color.yellow())
    embeded_msg.add_field(name="test", value="valor", inline=False)
    embeded_msg.set_image(url=ctx.guild.icon)
    embeded_msg.set_footer(text="Creado por Pchaozz")
    await ctx.send(embed=embeded_msg)    
    
    
#Basicamente intenta conectar al bot usando el token del ENV
bot.run(config("TOKEN"))