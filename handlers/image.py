"""
Tudo relacionado a fotos de exercícios: baixar do Telegram e mandar pro agente.
"""

import os

from agno.media import Image

from agent import agent

# Pasta onde as fotos ficam guardadas temporariamente até serem analisadas.
PASTA_TEMP = "temp"


def baixar_imagem(bot, message):
    """
    Baixa a foto enviada no Telegram e devolve o caminho local do arquivo.

    O Telegram manda a MESMA foto em várias resoluções, da menor para a maior.
    Por isso pegamos `message.photo[-1]`: o último item é a maior resolução,
    que é a que o modelo consegue ler melhor.
    """
    foto = message.photo[-1]

    # get_file devolve os metadados; download_file traz os bytes da imagem.
    arquivo = bot.get_file(foto.file_id)
    dados = bot.download_file(arquivo.file_path)

    os.makedirs(PASTA_TEMP, exist_ok=True)
    caminho = os.path.join(PASTA_TEMP, f"{foto.file_id}.jpg")

    # "wb" = write binary, porque imagem não é texto.
    with open(caminho, "wb") as arquivo_imagem:
        arquivo_imagem.write(dados)

    return caminho


def analisar_imagem(caminho, legenda=None, session_id=None, user_id=None):
    """
    Envia a imagem para o agente EntendAI resolver o exercício.

    `legenda` é o texto que o aluno escreveu junto com a foto (o caption do
    Telegram). Ele costuma trazer contexto importante, tipo "só a questão 3".

    `session_id`/`user_id` fazem a foto entrar na MESMA memória das mensagens
    de texto. Sem eles, o aluno mandaria a foto e, ao perguntar depois
    "não entendi a questão 3", o agente não saberia de qual lista se trata.
    """
    instrucao = (
        "O aluno enviou a foto de um exercício. "
        "Leia a imagem com atenção, identifique o enunciado e resolva o exercício "
        "seguindo o formato de resolução passo a passo. "
        "Se houver mais de uma questão na imagem, resolva todas, numerando-as. "
        "Se a imagem estiver ilegível ou faltar informação, diga exatamente o que não "
        "foi possível ler e peça uma nova foto."
    )

    if legenda:
        instrucao += f"\n\nObservação enviada pelo aluno: {legenda}"

    resposta = agent.run(
        instrucao,
        images=[Image(filepath=caminho)],
        session_id=session_id,
        user_id=user_id,
    )

    # getattr com valor padrão evita AttributeError caso o retorno mude.
    return getattr(resposta, "content", None)
