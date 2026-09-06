"""
Ponto de entrada do EntendAI no Telegram.

Este arquivo só cuida da "porta de entrada": recebe a mensagem do aluno,
decide qual handler chama, e devolve a resposta. Toda a inteligência está
em agent.py e o tratamento de imagem em handlers/image.py.

ATENÇÃO à ORDEM dos handlers: o pyTelegramBotAPI testa os handlers na ordem
em que foram registrados e usa o PRIMEIRO que casar. Por isso os handlers
específicos (comandos, foto, documento) vêm ANTES do handler genérico de
texto, que fica sempre por último.
"""

import os
import time

import telebot
from dotenv import load_dotenv

from agent import agent
from handlers.image import baixar_imagem, analisar_imagem
from handlers.telegram_utils import log, enviar_resposta

load_dotenv()

telegram_api_key = os.getenv("TELEGRAM_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

# Antes o código só avisava e seguia em frente — aí o bot subia quebrado.
# Agora ele para na hora, com uma mensagem clara do que falta.
if not telegram_api_key:
    raise SystemExit("TELEGRAM_API_KEY não encontrado no arquivo .env")

if not openai_api_key:
    raise SystemExit("OPENAI_API_KEY não encontrado no arquivo .env")

bot = telebot.TeleBot(telegram_api_key)


MENSAGEM_ERRO_GENERICA = (
    "Tive um problema para processar sua mensagem agora. "
    "Pode tentar enviar de novo?"
)


# ---------------------------------------------------------------------------
# 1) Comandos (/start e /ajuda) — precisam vir primeiro
# ---------------------------------------------------------------------------
@bot.message_handler(commands=["start", "ajuda"])
def start(message):
    enviar_resposta(
        bot,
        message,
        "Olá! Eu sou o **EntendAI**, seu tutor educacional.\n\n"
        "Você pode:\n"
        "• escrever o exercício em texto;\n"
        "• mandar uma **foto** da questão;\n"
        "• pedir só uma **dica** se quiser tentar sozinho;\n"
        "• dizer *não entendi* que eu explico de outro jeito.",
    )


# ---------------------------------------------------------------------------
# 2) Fotos
# ---------------------------------------------------------------------------
@bot.message_handler(content_types=["photo"])
def receber_imagem(message):
    caminho = None
    try:
        # "typing..." aparece para o aluno enquanto o modelo pensa.
        bot.send_chat_action(message.chat.id, "typing")

        caminho = baixar_imagem(bot, message)
        resposta = analisar_imagem(
            caminho,
            legenda=message.caption,
            session_id=str(message.chat.id),
            user_id=str(message.from_user.id),
        )

        log("Resposta do agente (imagem) gerada com sucesso.")
        enviar_resposta(bot, message, resposta)

    except Exception as erro:
        # log seguro: nunca quebra por causa de emoji/acentos no console.
        log("Erro ao analisar imagem:", repr(erro))
        enviar_resposta(
            bot,
            message,
            "Não consegui ler essa imagem. Tente enviar novamente com mais "
            "luz e foco, ou digite o enunciado em texto.",
        )
    finally:
        # Apaga o arquivo temporário mesmo se deu erro no meio do caminho.
        if caminho and os.path.exists(caminho):
            try:
                os.remove(caminho)
            except OSError as erro:
                log("Não consegui apagar o arquivo temporário:", repr(erro))


# ---------------------------------------------------------------------------
# 3) Tipos que ainda não sabemos tratar
#    Sem este handler, o aluno mandava um áudio/PDF e o bot ficava MUDO,
#    porque nenhum handler casava com a mensagem.
# ---------------------------------------------------------------------------
@bot.message_handler(
    content_types=["document", "voice", "audio", "video", "video_note", "sticker"]
)
def tipo_nao_suportado(message):
    enviar_resposta(
        bot,
        message,
        "Por enquanto eu entendo apenas **texto** e **fotos** de exercícios. "
        "Manda o enunciado escrito ou tira uma foto da questão. 🙂",
    )


# ---------------------------------------------------------------------------
# 4) Texto comum — SEMPRE o último handler registrado
# ---------------------------------------------------------------------------
@bot.message_handler(func=lambda message: True, content_types=["text"])
def responder(message):
    try:
        bot.send_chat_action(message.chat.id, "typing")

        # session_id/user_id são ESSENCIAIS: eles separam a memória de cada
        # aluno. Sem isso, todo mundo cairia na mesma conversa e um aluno
        # veria o contexto do outro.
        resposta = agent.run(
            message.text,
            session_id=str(message.chat.id),
            user_id=str(message.from_user.id),
        )

        # `resposta.content` pode vir None se o modelo não retornar texto.
        conteudo = getattr(resposta, "content", None)
        log("Resposta do agente gerada. Tamanho:", len(conteudo or ""))

        enviar_resposta(bot, message, conteudo)

    except Exception as erro:
        # Sem este try/except, qualquer falha (timeout da OpenAI, cota,
        # erro de rede) fazia o handler morrer em silêncio: o aluno não
        # recebia NADA. Era exatamente esse o comportamento observado.
        log("Erro ao responder mensagem de texto:", repr(erro))
        enviar_resposta(bot, message, MENSAGEM_ERRO_GENERICA)


def iniciar():
    """
    Mantém o bot no ar mesmo quando a internet oscila.

    O `infinity_polling` reconecta sozinho na maioria dos casos, MAS ele morre
    quando a conexão com a api.telegram.org estoura o tempo limite
    (`ReadTimeout`) ou quando um handler levanta uma exceção que ele repassa.
    Quando isso acontece, o processo simplesmente encerra e o bot fica offline
    sem ninguém perceber.

    Este laço garante que, se o polling cair, esperamos alguns segundos e
    começamos de novo — em vez de deixar o bot morto.
    """
    while True:
        try:
            log("EntendAI está online e pronto para ajudar!")
            # timeout: quanto esperamos por uma resposta da API.
            # long_polling_timeout: quanto a API segura a conexão aberta
            # esperando chegar mensagem nova.
            bot.infinity_polling(timeout=30, long_polling_timeout=30)

            # Se o infinity_polling retornar sem erro, foi encerramento normal.
            break

        except Exception as erro:
            log("Polling caiu, reiniciando em 5s. Motivo:", repr(erro))
            time.sleep(5)


if __name__ == "__main__":
    try:
        iniciar()
    except KeyboardInterrupt:
        # Ctrl+C no terminal: encerra limpo, sem cuspir traceback feio.
        log("EntendAI encerrado pelo usuário.")
