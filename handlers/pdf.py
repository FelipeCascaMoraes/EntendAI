"""
Tudo relacionado a PDFs de exercícios: baixar do Telegram e mandar pro agente.

Segue o mesmo padrão de handlers/image.py, trocando `Image` por `File` — o
agno já sabe formatar um PDF em base64 e mandar pro modelo, do mesmo jeito
que faz com foto.
"""

import os

from agno.media import File

from agent import agent

# Pasta onde os PDFs ficam guardados temporariamente até serem analisados.
PASTA_TEMP = "temp"

MIME_TYPE_PDF = "application/pdf"


def eh_pdf(document):
    """
    Verifica se o documento enviado é um PDF.

    Usamos o mime_type que o próprio Telegram detecta, em vez de olhar só a
    extensão do nome do arquivo — o nome pode vir sem extensão ou "mentindo".
    """
    return document.mime_type == MIME_TYPE_PDF


def baixar_pdf(bot, message):
    """
    Baixa o PDF enviado no Telegram e devolve o caminho local do arquivo.
    """
    documento = message.document

    # get_file devolve os metadados; download_file traz os bytes do arquivo.
    arquivo = bot.get_file(documento.file_id)
    dados = bot.download_file(arquivo.file_path)

    os.makedirs(PASTA_TEMP, exist_ok=True)
    nome = documento.file_name or f"{documento.file_id}.pdf"
    caminho = os.path.join(PASTA_TEMP, f"{documento.file_id}_{nome}")

    # "wb" = write binary, porque PDF não é texto.
    with open(caminho, "wb") as arquivo_pdf:
        arquivo_pdf.write(dados)

    return caminho


def analisar_pdf(caminho, legenda=None, session_id=None, user_id=None):
    """
    Envia o PDF para o agente EntendAI resolver o exercício.

    `legenda` é o texto que o aluno escreveu junto com o arquivo (o caption
    do Telegram) — costuma trazer contexto importante, tipo "só a questão 3".

    `session_id`/`user_id` fazem o PDF entrar na MESMA memória das mensagens
    de texto e das fotos, pelo mesmo motivo de sempre: sem isso o agente
    perde o fio da conversa no próximo follow-up do aluno.
    """
    instrucao = (
        "O aluno enviou um PDF com um exercício ou lista de exercícios. "
        "Leia o conteúdo do arquivo com atenção, identifique o(s) enunciado(s) e "
        "resolva seguindo o formato de resolução passo a passo. "
        "Se houver mais de uma questão no arquivo, resolva todas, numerando-as. "
        "Se o arquivo estiver ilegível, corrompido ou faltar informação, diga "
        "exatamente o que não foi possível ler e peça um novo envio."
    )

    if legenda:
        instrucao += f"\n\nObservação enviada pelo aluno: {legenda}"

    resposta = agent.run(
        instrucao,
        files=[File(filepath=caminho)],
        session_id=session_id,
        user_id=user_id,
    )

    # getattr com valor padrão evita AttributeError caso o retorno mude.
    return getattr(resposta, "content", None)
