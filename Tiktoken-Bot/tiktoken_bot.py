import discord
from discord.ext import commands
import tiktoken
import os
from dotenv import load_dotenv
from PIL import Image
import base64
import aiohttp
from io import BytesIO

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

models = ["gpt-3.5-turbo-0301", "gpt-3.5-turbo", "gpt-4", "gpt-4-0314"]

def num_tokens_from_string_model(string: str, model_name: str) -> int:
    encoding = tiktoken.encoding_for_model(model_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

intents = discord.Intents.default()
intents.typing = True
intents.messages = True
intents.presences = False

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    print("------")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        # Do nothing or send a custom message if you want to notify the user
        pass
    else:
        # Log other errors
        print(f"Ignoring exception in command {ctx.command}: {error}")

@bot.command(name="count")
async def token_count(ctx, model_name: str):
    if model_name not in models:
        await ctx.send(f"Invalid model name. Available models: {', '.join(models)}")
        return

    num_tokens = 0

    # Check if there's an attachment (image or txt file)
    if ctx.message.attachments:
        try:
            for i in range(0, len(ctx.message.attachments)):
                attachment = ctx.message.attachments[i]

                if attachment.filename.endswith(".txt"):
                    async with aiohttp.ClientSession() as session:
                        async with session.get(attachment.url) as resp:
                            text_data = await resp.text()
                    num_tokens += num_tokens_from_string_model(text_data, model_name)
                elif attachment.filename.lower().endswith((".png", ".jpg", ".jpeg")):
                    async with aiohttp.ClientSession() as session:
                        async with session.get(attachment.url) as resp:
                            image_data = await resp.read()
                            image = Image.open(BytesIO(image_data))
                            buffered = BytesIO()
                            image.save(buffered, format="PNG")
                            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
                    num_tokens += num_tokens_from_string_model(img_str, model_name)

            await ctx.send(f"Number of tokens in the given attachment(s) for model {model_name}: {num_tokens}")
        except Exception as e:
            await ctx.send(f"Error calculating token count: {e}")

    # Count the tokens in the message content
    message_content = ctx.message.content[len("!count " + model_name + " "):]
    num_tokens = num_tokens_from_string_model(message_content, model_name)
    await ctx.send(f"Number of tokens in the message content for model {model_name}: {num_tokens}")

bot.run(TOKEN)

