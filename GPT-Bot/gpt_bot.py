import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
import openai

load_dotenv()

data = {
    'GPT_API_KEY': os.getenv('GPT_API_KEY'),
    'DISCORD_BOT_TOKEN': os.getenv('DISCORD_BOT_TOKEN')
}
openai.api_key = data['GPT_API_KEY']

curr_model = "gpt-4"
prompt_per_price = 0.03
response_per_price = 0.06

if curr_model == "gpt-3.5-turbo":
    prompt_price = 0.002
    response_price = 0.002

context_tokens = 0
total_tokens = 0

intents = discord.Intents.default()
intents.typing = True
intents.message_content = True
intents.presences = False
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}!')
    print("------")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        # Do nothing or send a custom message if you want to notify the user
        pass
    else:
        # Log other errors
        print(f"Ignoring exception in command {ctx.command}: {error}")

@bot.command(name='gpt')
async def generate_gpt_response(ctx, *, prompt):
    global context_tokens, total_tokens

    response, response_info, token_usage = await generate_response(ctx, prompt)
    response_tokens = token_usage['completion_tokens']
    prompt_tokens = token_usage['prompt_tokens']
    total_tokens += token_usage['total_tokens']
    context_tokens += total_tokens

    # calculate prices for prompt tokens and response tokens
    prompt_price = round(prompt_tokens/1000 * prompt_per_price, 4)
    response_price = round(response_tokens/1000 * response_per_price, 4)
    total_price = round(prompt_price+response_price, 4)

    # format the response with the desired information
    formatted_response = f"{response}\n\nPrompt tokens: {prompt_tokens}, price: ${prompt_price}\nResponse tokens: {response_tokens}, price: ${response_price}\nTotal tokens: {total_tokens}, price: ${total_price}\nTotal tokens in chat history: {context_tokens}\nmodel: {curr_model}"

    await ctx.send(formatted_response)

async def generate_response(ctx, prompt):
    try:
        messages = [{"role": "user", "content": prompt}]
        
        if ctx.message.attachments:
            for attachment in ctx.message.attachments:
                image_bytes = await attachment.read()
                messages.append({"role": "user", "content": {"image": image_bytes}})
        
        response = openai.ChatCompletion.create(
            model=curr_model,
            max_tokens=2048,
            n=1,
            messages=messages
        )

        response_text = response['choices'][0]['message']['content'].strip()
        response_info = f"Prompt: {prompt}\n\nResponse: {response_text}"
        token_usage = response['usage']
        return response_text, response_info, token_usage
    except openai.error.APIError as e:
        #Handle API error here, e.g. retry or log
        print(f"OpenAI API returned an API Error: {e}")
        pass
    except openai.error.APIConnectionError as e:
        #Handle connection error here
        print(f"Failed to connect to OpenAI API: {e}")
        pass
    except openai.error.RateLimitError as e:
        #Handle rate limit error (we recommend using exponential backoff)
        print(f"OpenAI API request exceeded rate limit: {e}")
        pass

bot.run(data['DISCORD_BOT_TOKEN'])

