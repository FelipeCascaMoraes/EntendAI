import telebot
import os
from dotenv import load_dotenv  

load_dotenv()  

telegram_api_key = os.getenv("TELEGRAM_API_KEY")
nvidia_api_key = os.getenv("NVIDIA_API_KEY")

if not telegram_api_key:
    print("TELEGRAM_API_KEY não encontrado no arquivo .env")


if not nvidia_api_key:
    print("NVIDIA_API_KEY não encontrado no arquivo .env")

bot = telebot.TeleBot(telegram_api_key)

@bot.message_handler(commands=['start'])
def mensagem_bot(mensagem):
    bot.reply_to(mensagem, "Olá! Eu sou o EntendAI, seu assistente de IA. Como posso ajudá-lo hoje?")

print('Bot iniciado. Aguardando mensagens...')
bot.polling()