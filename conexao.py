import telebot
import os
from dotenv import load_dotenv  
from agent import agent
from handlers.image import baixar_imagem

load_dotenv()  

telegram_api_key = os.getenv("TELEGRAM_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

if not telegram_api_key:
    print("TELEGRAM_API_KEY não encontrado no arquivo .env")

if not openai_api_key:
    print("OPENAI_API_KEY não encontrado no arquivo .env")

bot = telebot.TeleBot(telegram_api_key)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Olá! Eu sou o EntendAI, seu tutor educacional. Envie-me um exercício e eu vou ajudá-lo a entender como resolvê-lo passo a passo.")

@bot.message_handler(func=lambda message: True)
def responder(message):
    response = agent.run(message.text)
    print("Resposta do agente:", response.content)
    bot.reply_to(message, response.content)

@bot.message_handler(content_types=["photo"])
def receber_imagem(message):
    caminho = baixar_imagem(bot, message)

    bot.reply_to(
        message,
        f"Imagem recebida! Salvei em: {caminho}"
    )

print('EntendAI está online e pronto para ajudar!')
bot.infinity_polling()