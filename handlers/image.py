import os

from agno.media import Image

from agent import agent


def baixar_imagem(bot, message):
    """Baixa a foto enviada no Telegram e devolve o caminho local do arquivo."""
    foto = message.photo[-1]

    arquivo = bot.get_file(foto.file_id)
    dados = bot.download_file(arquivo.file_path)

    os.makedirs("temp", exist_ok=True)
    caminho = os.path.join("temp", f"{foto.file_id}.jpg")

    with open(caminho, "wb") as arquivo_imagem:
        arquivo_imagem.write(dados)

    return caminho


def analisar_imagem(caminho, legenda=None):
    """Envia a imagem para o agente EntendAI resolver o exercício."""
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

    resposta = agent.run(instrucao, images=[Image(filepath=caminho)])

    return resposta.content
