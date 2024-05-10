import google.generativeai as genai
import json
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import datetime
import threading
import time
import requests
from bs4 import BeautifulSoup
import speech_recognition as sr

datahora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")

# Configuração do Spotify
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id='CLIENT-ID-SPOTIFY',
                                               client_secret='CLIENT-SECRET-SPOTIFY',
                                               redirect_uri='http://localhost:8888/callback',
                                               scope='user-read-playback-state,user-modify-playback-state'))

# Pegar temperatura atual em Brasília
def get_temperature_in_brasilia():
    url = "https://weather.com/pt-BR/clima/hoje/l/BRXX0043:1:BR?Goto=Redirected"
    
    try:
        # Faz a requisição GET para a página
        response = requests.get(url)
        
        # Verifica se a requisição foi bem-sucedida
        if response.status_code == 200:
            # Parseia o conteúdo HTML da página
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Encontra o elemento span com a classe "CurrentConditions--tempValue--MHmYY"
            temperature_element = soup.find("span", class_="CurrentConditions--tempValue--MHmYY")
            
            # Verifica se o elemento foi encontrado
            if temperature_element:
                # Extrai o texto da temperatura e remove o símbolo de grau
                temperature = temperature_element.text.replace('°', '')
                return temperature
            else:
                return "Não foi possível encontrar a temperatura atual em Brasília."
        else:
            return f"Erro ao fazer a requisição: {response.status_code}"
    except Exception as e:
        return f"Ocorreu um erro ao tentar obter a temperatura: {str(e)}"

# Função para obter o tempo atual
def get_current_time():
    current_time = datetime.datetime.now()
    return current_time.strftime("%d/%m/%Y %H:%M:%S")

# Função para tocar uma música no Spotify
def search_and_play_song(song_name):
    try:
        results = sp.search(q=song_name, limit=1, type='track')
        if results['tracks']['total'] > 0:
            uri = results['tracks']['items'][0]['uri']
            sp.start_playback(uris=[uri])
            return f"Tocando a música {song_name} no Spotify."
        else:
            return f"Desculpe, não consegui encontrar a música {song_name} no Spotify."
    except spotipy.exceptions.SpotifyException as e:
        if "Player command failed: No active device found, reason: NO_ACTIVE_DEVICE" in str(e):
            return "Não consegui encontrar dispositivos para reproduzir suas músicas."
        else:
            print(f"Erro ao tentar tocar a música: {e}")
            return f"Erro ao tentar tocar a música: {e}"

# Função para realizar ações no Spotify
def search_and_play(song_name, query_type):
    if query_type == 'song':
        return search_and_play_song(song_name)
    elif query_type == 'playlist':
        return search_and_play_playlist(song_name)
    elif query_type == 'artist':
        return search_and_play_artist(song_name)
    elif query_type == 'current_song':
        return get_current_song()
    else:
        return "Tipo de consulta não suportado."

# Função para tocar uma playlist no Spotify
def search_and_play_playlist(playlist_name):
    try:
        results = sp.search(q=playlist_name, limit=1, type='playlist')
        if results['playlists']['total'] > 0:
            uri = results['playlists']['items'][0]['uri']
            sp.start_playback(context_uri=uri)
            return f"Tocando a playlist {playlist_name} no Spotify."
        else:
            return f"Desculpe, não consegui encontrar a playlist {playlist_name} no Spotify."
    except spotipy.exceptions.SpotifyException as e:
        if "Player command failed: No active device found, reason: NO_ACTIVE_DEVICE" in str(e):
            return "Não consegui encontrar dispositivos para reproduzir suas músicas."
        else:
            print(f"Erro ao tentar tocar a playlist: {e}")
            return f"Erro ao tentar tocar a playlist: {e}"

# Função para tocar as principais músicas de um artista no Spotify
def search_and_play_artist(artist_name):
    try:
        results = sp.search(q=artist_name, limit=1, type='artist')
        if results['artists']['total'] > 0:
            artist_id = results['artists']['items'][0]['id']
            top_tracks = sp.artist_top_tracks(artist_id)
            if len(top_tracks['tracks']) > 0:
                uri = top_tracks['tracks'][0]['uri']
                sp.start_playback(uris=[uri])
                return f"Tocando as principais músicas de {artist_name} no Spotify."
            else:
                return f"Desculpe, não consegui encontrar músicas populares para o artista {artist_name} no Spotify."
        else:
            return f"Desculpe, não consegui encontrar o artista {artist_name} no Spotify."
    except spotipy.exceptions.SpotifyException as e:
        if "Player command failed: No active device found, reason: NO_ACTIVE_DEVICE" in str(e):
            return "Não consegui encontrar dispositivos para reproduzir suas músicas."
        else:
            print(f"Erro ao tentar tocar músicas do artista: {e}")
            return f"Erro ao tentar tocar músicas do artista: {e}"

# Função para obter a música atualmente tocando no Spotify
def get_current_song():
    try:
        current_playback = sp.current_playback()
        if current_playback is not None and 'item' in current_playback:
            song_name = current_playback['item']['name']
            return f"A música atualmente tocando é: {song_name}."
        else:
            return "Não está tocando nenhuma música no momento."
    except spotipy.exceptions.SpotifyException as e:
        if str(e) == "http status: 404, code:-1 - https://api.spotify.com/v1/me/player/play: Player command failed: No active device found, reason: NO_ACTIVE_DEVICE":
            return "Não consegui encontrar dispositivos para reproduzir suas músicas."
        else:
            print(f"Erro ao tentar obter a música atualmente tocando: {e}")
            return f"Erro ao tentar obter a música atualmente tocando: {e}"

# Função para criar um lembrete
def criar_lembrete(data, hora, texto):
    lembrete = {
        "data": data,
        "hora": hora,
        "texto": texto
    }
    with open("lembretes.json", "a", encoding='utf-8') as file:
        file.write(json.dumps(lembrete) + '\n')

# Função para verificar lembretes
def verificar_lembretes():
    while True:
        with open("lembretes.json", "r", encoding='utf-8') as file:
            lines = file.readlines()
        with open("lembretes.json", "w", encoding='utf-8') as file:
            for line in lines:
                lembrete = json.loads(line)
                if lembrete.get('data') is None or lembrete.get('hora') is None or lembrete.get('texto') is None:
                    continue  # Pula a linha se algum campo estiver faltando
                data_lembrete = datetime.datetime.strptime(lembrete['data'] + ' ' + lembrete['hora'], "%d/%m/%Y %H:%M:%S")
                diff = data_lembrete - datetime.datetime.now()
                if diff.days == 0 and diff.seconds < 3600:
                    print(f"\nLembrete para o dia {lembrete['data']}, sobre: {lembrete['texto']}\n")
                else:
                    file.write(line)  # Escreve a linha de volta no arquivo se não precisar ser removida
        time.sleep(60)  # Verifica a cada minuto
        
# Thread para verificar lembretes
lembretes_thread = threading.Thread(target=verificar_lembretes)
lembretes_thread.start()

# Função principal do assistente virtual
def assistente():
    genai.configure(api_key="CHAVE-API-GEMINI")
    model = genai.GenerativeModel('gemini-1.0-pro-latest')
    chat = model.start_chat(history=[])

    while True:
        # Cria um reconhecedor de fala
        recognizer = sr.Recognizer()
        print("Ouvindo...")
        # Usa o microfone como fonte de áudio
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source) 
            # Escuta o áudio
            audio = recognizer.listen(source)
        try:
            # Usa o Google Speech Recognition para reconhecer a fala
            textin = recognizer.recognize_google(audio, language='pt-BR')
            print("Você disse: ")
            mensagem = textin

            texto = """
                Seu nome é Gemini, um assistente virtual. Seu objetivo é ajudar seu dono(a) no dia a dia. 
                Converse de forma natural e descontraída, como um ser humano.
                Aja como se você tivesse alto conhecimento sobre os mais diversos assuntos. Sendo eles principalmente tecnologia, eletrônica, programação, etc.               
                TODAS AS SUAS RESPOSTAS DEVEM SEGUIR À RISCA A NORMA DA LÍNGUA PORTUGUESA. Não utilize caracteres especiais para tornar o texto bonito ou mais legível, pois o usuário não verá o texto.
                Seu texto será sintetizado em fala, e para que a fala fique com uma pronúncia clara, é necessário que o texto esteje limpo.

                Todas as suas respostas passam por um sistema que analisa mensagens JSON para poder saber qual ação executar. 
                No dia a dia, o usuário pode pedir pra você executar diferentes ações, você deve analisar as ações existentes, e qual delas está sendo requisitada pelo usuário.
                Adapte sua resposta JSON conforme a ação.

                Ao retornar uma resposta, você deve SEMPRE retornar a mensagem no formato JSON, exemplo de formatação que deve se seguida:
                Na variável type, se você for apenas responder com texto, deixe "text", e na resposta, escreva sua resposta.
                {
                "type": "text",
                "resposta": "Sua resposta"
                }

                DIFERENTES AÇÕES COM FORMATAÇÕES JSON EXISTENTES:
                DESLIGAR SISTEMA:
                Se o usuário se despedir, falar para desligar, ou algo similar, você deve retornar o seguinte JSON:
                {
                "type": "system_status",
                "status": off, 
                "resposta": "Resposta dizendo qual foi a ação realizada, se você desligou ou ligou o servidor."
                }

                TOCAR MÚSICA NO SPOTIFY:
                Se o usuário pedir para tocar uma música, playlist ou artista no Spotify, você deve retornar o seguinte JSON:
                {
                "type": "spotify_action",
                "query_type": "song/playlist/artist", # Determine com base na mensagem do usuário se é song, playlist ou artist
                "query_name": "nome da música, playlist ou artista",
                "resposta": "Resposta relacionada à ação executada."
                }

                OBTER MÚSICA ATUALMENTE TOCANDO:
                Se o usuário perguntar qual música está tocando no momento, você deve retornar o seguinte JSON:
                {
                "type": "spotify_action",
                "query_type": "current_song",
                "resposta": "Resposta relacionada à ação executada."
                }

                CRIAR LEMBRETE:
                Se o usuário pedir para criar um lembrete, com uma data/hora e uma descrição, você deve retornar o seguinte JSON SOMENTE SE TIVER TODAS AS INFORMAÇÕES:
                {
                "type": "create_reminder",            # NENHUMA DAS INFORMAÇÕES PODEM FICAR NULAS, PEÇA PARA O USUÁRIO FORNECER TODAS! NÃO DESOBEDEÇA ESSA ORDEM!
                "hora": "Hora do lembrete ",  # Arrume a hora fornecida para ficar no formato (HH:MM:SS)
                "data": "Data do lembrete ", # Arrume a data fornecida pra ficar no formato (DD/MM/AAAA)
                "desc": "Descrição sobre o lembrete",           
                "resposta": "Resposta relacionada à ação executada."
                }
                MOSTRAR LEMBRETES:
                Se o usuário pedir pra você falar quais os lembretes criados, você deve retornar o seguinte JSON:
                {
                "type": "show_reminders",
                "resposta": "Um momento.."
                }
                OBTER TEMPERATURA:
                Se o usuário perguntar qual a temperatura atual, você deve retornar o seguinte JSON:
                {
                "type": "get_temp",
                "resposta": None
                }
                """
            
            texto += f"INFORMAÇÕES IMPORTANTES\nData/Hora: {datahora}"

            prompt = texto + mensagem
            response = chat.send_message(prompt)
            resposta_json = json.loads(response.text)
            response_type = resposta_json.get('type')

            if response_type == "text":
                print("Gemini: ", resposta_json['resposta'], "\n")
                    
            elif response_type == "system_status":
                print("Gemini: ", resposta_json['resposta'], "\n")
                status = resposta_json.get('status')
                if status == 'off':
                    break

            elif response_type == 'spotify_action':
                query_type = resposta_json.get('query_type')
                if query_type == 'current_song':
                    print(get_current_song())
                    break

                else:
                    query_name = resposta_json.get('query_name', '')
                    resposta = search_and_play(query_name, query_type)
                    print("Gemini: ", resposta, "\n")

            elif response_type == "create_reminder":
                print("Gemini: ", resposta_json['resposta'])
                data = resposta_json['data']
                hora = resposta_json['hora']
                texto_lembrete = resposta_json['desc']
                criar_lembrete(data, hora, texto_lembrete)
                break

            elif response_type == 'show_reminders':
                with open("lembretes.json", "r", encoding='utf-8') as file:
                    lines = file.readlines()
                    for i in lines:
                        lembrete = json.loads(i)
                        horario = lembrete.get('hora')
                        data = lembrete.get('data')
                        desc = lembrete.get('texto')
                        print(f"Lembrete {i}\n{data} | {horario} - {desc}")
                break

            elif response_type == "get_temp":
                temperatura = get_temperature_in_brasilia()
                print(f"Gemini: A temperatura atual em Brasília é de {temperatura}°C")
                break

        except sr.UnknownValueError:
            print("Não foi possível entender a fala.")
        except sr.RequestError as e:
            print("Erro ao acessar o serviço de reconhecimento de fala; {0}".format(e))

# Cria um reconhecedor de fala
recognizer = sr.Recognizer()
    
# Usa o microfone como fonte de áudio
with sr.Microphone() as source:
    recognizer.adjust_for_ambient_noise(source) 
    # Escuta o áudio
    print("Hibernando...")
    audio = recognizer.listen(source)
try:
    # Usa o Google Speech Recognition para reconhecer a fala
    texto = recognizer.recognize_google(audio, language='pt-BR')
    print("Você disse: ", texto)
    if 'assistente' in texto.lower():
        assistente()
except sr.UnknownValueError:
    None
except sr.RequestError as e:
    print("Erro ao acessar o serviço de reconhecimento de fala; {0}".format(e))
