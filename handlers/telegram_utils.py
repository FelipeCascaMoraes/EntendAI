"""
Funções auxiliares para falar com o Telegram sem quebrar o bot.

Por que este arquivo existe:
1) O console do Windows usa a codificação cp1252, que NÃO consegue imprimir
   emojis. Um `print()` com emoji levanta UnicodeEncodeError e derruba o
   handler ANTES de a resposta ser enviada ao aluno.
2) O Telegram recusa mensagens com mais de 4096 caracteres. Uma resolução
   longa passa desse limite e a API devolve erro 400.
3) O Telegram é rígido com formatação. Se o texto tiver um caractere que ele
   interpreta como marcação inválida, ele recusa a mensagem inteira.

Cada função abaixo resolve um desses problemas.
"""

import html
import re

# Limite oficial de caracteres de UMA mensagem no Telegram.
# Usamos um valor um pouco menor para ter folga.
LIMITE_TELEGRAM = 3900


def log(*partes):
    """
    Substituto seguro do `print()`.

    O print normal quebra no Windows quando o texto tem emoji (📚, 💡, ⚠️).
    Aqui trocamos qualquer caractere que o console não aceita por "?", assim
    o log nunca derruba o programa.
    """
    texto = " ".join(str(parte) for parte in partes)
    try:
        print(texto)
    except UnicodeEncodeError:
        # encode/decode com errors="replace" remove os caracteres problemáticos
        print(texto.encode("ascii", errors="replace").decode("ascii"))


def markdown_para_html(texto):
    """
    Converte o Markdown que o agente gera para o HTML que o Telegram entende.

    O agente escreve `**negrito**` (Markdown padrão), mas o Telegram só aceita
    HTML (`<b>negrito</b>`) ou o Markdown dele, que é diferente.

    Ordem importa: primeiro escapamos <, > e & (senão o Telegram acha que é
    uma tag HTML de verdade), depois aplicamos o negrito e o código.
    """
    # 1. Escapa caracteres que têm significado especial em HTML.
    texto = html.escape(texto)

    # 2. **negrito** -> <b>negrito</b>
    #    O `.+?` é "preguiçoso": pega o menor trecho possível entre os **.
    #    re.DOTALL faz o . casar também com quebras de linha.
    texto = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", texto, flags=re.DOTALL)

    # 3. `código` -> <code>código</code>
    texto = re.sub(r"`([^`]+?)`", r"<code>\1</code>", texto)

    return texto


def quebrar_em_partes(texto, limite=LIMITE_TELEGRAM):
    """
    Quebra um texto longo em pedaços que cabem numa mensagem do Telegram.

    Tentamos quebrar em parágrafos (linha em branco) para a leitura não ficar
    estranha. Se um parágrafo sozinho já for maior que o limite, cortamos ele
    "na força" em fatias do tamanho do limite.
    """
    if len(texto) <= limite:
        return [texto]

    partes = []
    atual = ""

    for paragrafo in texto.split("\n\n"):
        # Parágrafo gigante: corta em fatias de tamanho fixo.
        if len(paragrafo) > limite:
            if atual:
                partes.append(atual)
                atual = ""
            for i in range(0, len(paragrafo), limite):
                partes.append(paragrafo[i:i + limite])
            continue

        # +2 por causa do "\n\n" que vamos recolocar entre os parágrafos.
        if len(atual) + len(paragrafo) + 2 > limite:
            partes.append(atual)
            atual = paragrafo
        else:
            atual = f"{atual}\n\n{paragrafo}" if atual else paragrafo

    if atual:
        partes.append(atual)

    return partes


def enviar_resposta(bot, message, texto):
    """
    Envia a resposta ao aluno de forma segura.

    Faz três coisas:
    - garante que existe algum texto para enviar;
    - divide o texto em partes que cabem no limite do Telegram;
    - se o Telegram recusar a formatação HTML, reenvia sem formatação
      (melhor mandar texto "cru" do que não mandar nada).
    """
    if not texto or not texto.strip():
        texto = "Não consegui gerar uma resposta agora. Pode tentar de novo?"

    for parte in quebrar_em_partes(texto):
        try:
            bot.send_message(
                message.chat.id,
                markdown_para_html(parte),
                parse_mode="HTML",
                # Responde à mensagem original só na primeira parte não é
                # necessário; enviar solto deixa a leitura mais limpa.
            )
        except Exception as erro:
            # Plano B: sem formatação nenhuma. Isso quase nunca falha.
            log("Falha ao enviar com HTML, reenviando sem formatação:", erro)
            try:
                bot.send_message(message.chat.id, parte)
            except Exception as erro_final:
                log("Falha definitiva ao enviar mensagem:", erro_final)
