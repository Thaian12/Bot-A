import requests
import time

# URLs da API ParaSwap para o par USDT/BRLA
taxa = 1.12 / 100
amount_original = 315000000  # equivalente a 315 USDT, considerando 6 casas decimais
amount_com_taxa = int(amount_original * (1 - taxa))

# Atualizando a URL com o valor modificado
URL_PARASWAP = f"https://api.paraswap.io/prices/?srcToken=0xc2132D05D31c914a87C6611C10748AEb04B58e8F&destToken=0xE6A537a407488807F0bbeb0038B79004f19DDDFb&amount={amount_com_taxa}&srcDecimals=6&destDecimals=2&side=SELL&network=137&version=5"

# Configurações do Telegram
TELEGRAM_TOKEN = '7519701271:AAG6nCA0ipq-QQGlK9od8R1kaDZtUNkVAh0'
CHAT_ID = '5045138558'
TELEGRAM_API_URL = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
TELEGRAM_GET_UPDATES_URL = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates'

# Variáveis globais para armazenar o preço manual e controlar a mensagem de confirmação
preco_manual = None
mensagem_enviada = False
confirmacao_preco_atualizada = False  # Controle para evitar envio duplicado

# Função para formatar números como moeda brasileira
def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# Função para enviar mensagem para o Telegram
def enviar_mensagem_telegram(mensagem):
    try:
        payload = {'chat_id': CHAT_ID, 'text': mensagem}
        requests.post(TELEGRAM_API_URL, data=payload)
    except Exception as e:
        print(f"Ocorreu um erro ao enviar mensagem para o Telegram: {e}")

# Função para verificar novas mensagens no Telegram e atualizar o preço manual
def verificar_comando_telegram():
    global preco_manual, mensagem_enviada, confirmacao_preco_atualizada
    try:
        response = requests.get(TELEGRAM_GET_UPDATES_URL)
        if response.status_code == 200:
            updates = response.json().get('result', [])
            for update in updates:
                message = update.get('message', {})
                chat_id = message.get('chat', {}).get('id')
                text = message.get('text')
                if chat_id == int(CHAT_ID) and text and text.startswith('/preço'):
                    try:
                        novo_preco = float(text.split()[1])
                        if novo_preco != preco_manual:  # Verifica se o preço mudou
                            preco_manual = novo_preco
                            mensagem_enviada = False  # Reinicia a flag quando o preço é atualizado
                            confirmacao_preco_atualizada = False  # Reinicia a confirmação
                    except (IndexError, ValueError):
                        enviar_mensagem_telegram("Comando inválido. Use o formato: /preço <valor>")
        else:
            print(f"Erro ao obter mensagens do Telegram: {response.status_code}")
    except Exception as e:
        print(f"Ocorreu um erro ao verificar comandos do Telegram: {e}")

# Função para enviar confirmação de atualização do preço manual
def enviar_confirmacao_preco_atualizado():
    global confirmacao_preco_atualizada
    if preco_manual is not None and not confirmacao_preco_atualizada:
        enviar_mensagem_telegram(f"Preço manual atualizado para: {formatar_moeda(preco_manual)}")
        confirmacao_preco_atualizada = True  # Marca a confirmação como enviada

# Função para obter o preço do par USDT/BRLA na ParaSwap
def verificar_preco_paraswap():
    try:
        response = requests.get(URL_PARASWAP)
        if response.status_code == 200:
            dados = response.json()
            preco_destino = dados.get('priceRoute', {}).get('destAmount')
            if preco_destino:
                preco_destino_formatado = float(preco_destino) / 10**18
                preco_formatado = formatar_moeda(preco_destino_formatado)
                print(f"Preço na ParaSwap: {preco_formatado} BRLA para {amount_com_taxa / 10**6} USDT")
                return preco_destino_formatado
            else:
                print("Não foi possível obter o preço na ParaSwap.")
        else:
            print(f"Erro na requisição da ParaSwap: {response.status_code}")
    except Exception as e:
        print(f"Ocorreu um erro na ParaSwap: {e}")

# Função para comparar os preços obtidos e calcular a diferença
def comparar_precos():
    global mensagem_enviada
    preco_paraswap = verificar_preco_paraswap()
    if preco_paraswap and preco_manual:
        # Ajuste para calcular o preço manual sem a taxa
        preco_manual_sem_taxa = preco_manual * amount_original / 10**6  # Total em BRL para 315 USDT sem taxa

        maior_preco = max(preco_paraswap, preco_manual_sem_taxa)
        menor_preco = min(preco_paraswap, preco_manual_sem_taxa)
        diferenca_preco = maior_preco - menor_preco

        diferenca_percentual = (diferenca_preco / menor_preco) * 100 if menor_preco > 0 else 0

        preco_manual_sem_taxa_formatado = formatar_moeda(preco_manual_sem_taxa)

        print(f"Comparação:\n- ParaSwap: {formatar_moeda(preco_paraswap)} BRLA para {amount_com_taxa / 10**6} USDT")
        print(f"- Manual (sem taxa): {preco_manual_sem_taxa_formatado} BRL para {amount_com_taxa / 10**6} USDT")
        print(f"- Diferença de Preço: {formatar_moeda(diferenca_preco)} BRL")
        print(f"- Diferença Percentual: {diferenca_percentual:.2f}%")

        if diferenca_preco >= 5.00 and not mensagem_enviada:
            valor_ganho = diferenca_preco
            if maior_preco == preco_paraswap:
                mensagem = (f"Oportunidade de Arbitragem:📈 \n\n"
                            f"Corretora: BITOY / 1NCH\n\n"
                            f"Moeda de Compra: USDT\n"
                            f"Moeda de Venda: BRLA\n\n"
                            f"Comprar na Bitoy por: {preco_manual_sem_taxa_formatado}\n"
                            f"Quantidade: {amount_original / 10**6} USDT\n\n"
                            f"Vender na 1nch por: {formatar_moeda(preco_paraswap)}\n"
                            f"Quantidade: {amount_com_taxa / 10**6} USDT\n\n"
                            f"Ganho: {formatar_moeda(valor_ganho)}💰\n"
                            f"Ganho: {diferenca_percentual:.2f}%📊")
            else:
                mensagem = (f"Oportunidade de Arbitragem: \n\n"
                            f"Comprar na ParaSwap por: {formatar_moeda(preco_paraswap)}\n"
                            f"Vender manualmente por: {preco_manual_sem_taxa_formatado}\n\n"
                            f"Valor Ganho: {formatar_moeda(valor_ganho)}🟢")
            print(mensagem)
            enviar_mensagem_telegram(mensagem)
            mensagem_enviada = True  # Marca a mensagem como enviada
        else:
            print("Nenhuma oportunidade de arbitragem identificada.")

# Loop para verificar e comparar os preços periodicamente
def monitorar_precos(intervalo_segundos=10):
    while True:
        verificar_comando_telegram()  # Verifica comandos no Telegram
        enviar_confirmacao_preco_atualizado()  # Envia confirmação de preço atualizado
        comparar_precos()
        time.sleep(intervalo_segundos)

# Configurar o intervalo de monitoramento e iniciar o bot
monitorar_precos(intervalo_segundos=60)
