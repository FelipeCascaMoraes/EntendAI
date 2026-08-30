import os

def baixar_imagem(bot, message):

    foto = message.photo[-1]

    arquivo = bot.get_file(foto.file_id)

    dados = bot.download_file(arquivo.file_path)
    os.makedirs("temp", exist_ok=True)
    caminho = os.path.join("temp", f"{arquivo.file_id}.jpg")

    with open(caminho, "wb") as arquivo_imagem:
        arquivo_imagem.write(dados)

    
    
