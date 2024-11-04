import requests
import time

# URLs da API Binance para o par USDT/BRL
URL_BINANCE = "https://api.binance.com/api/v3/ticker/price?symbol=USDTBRL"

# Configurações do Telegram
TELEGRAM_TOKEN = '7519701271:AAG6nCA0ipq-QQGlK9od8R1kaDZtUNkVAh0'
CHAT_ID = '5045138558'
TELEGRAM_API_URL = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
TELEGRAM_UPDATE_URL = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates'

# Variáveis para armazenar o preço manual atual e o preço anterior
preco_manual = None
preco_manual_anterior = None

# Taxa de 1,12%
TAXA_COMPRA = 0.0112

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

# Função para verificar o preço manual enviado pelo Telegram
def verificar_preco_manual():
    global preco_manual, preco_manual_anterior
    try:
        response = requests.get(TELEGRAM_UPDATE_URL)
        if response.status_code == 200:
            updates = response.json().get("result", [])
            if updates:
                last_message = updates[-1].get("message", {}).get("text")
                if last_message and last_message.startswith("/BITOY "):
                    preco_str = last_message.split(" ")[1]
                    try:
                        preco_novo = float(preco_str)
                        if preco_manual != preco_novo:  # Verifica se o preço mudou
                            preco_manual = preco_novo                       
                            enviar_mensagem_telegram(f"Preço BITOY atualizado: {formatar_moeda(preco_manual)}")
                    except ValueError:
                        print("Erro: formato de preço inválido.")
                        enviar_mensagem_telegram("Erro: formato de preço inválido. Envie como 'BITOY 100.00'.")
    except Exception as e:
        print(f"Ocorreu um erro ao verificar preço manual no Telegram: {e}")

# Função para obter o preço do par USDT/BRL na Binance
def verificar_preco_binance():
    try:
        response = requests.get(URL_BINANCE)
        if response.status_code == 200:
            dados = response.json()
            preco_binance = float(dados['price'])
            print(f"Preço na Binance: {formatar_moeda(preco_binance)} BRL para 1 USDT")
            return preco_binance
        else:
            print(f"Erro na requisição da Binance: {response.status_code}")
    except Exception as e:
        print(f"Ocorreu um erro na Binance: {e}")

# Função para comparar os preços e verificar arbitragem
def comparar_precos():
    global preco_manual
    verificar_preco_manual()  # Checar por novo preço manual a cada verificação

    preco_binance = verificar_preco_binance()
    if preco_manual and preco_binance:
        quantidade_usdt = 315
        preco_manual_total = preco_manual * quantidade_usdt
        quantidade_usdt_com_taxa = quantidade_usdt - (quantidade_usdt * TAXA_COMPRA)
        preco_binance_total = preco_binance * quantidade_usdt_com_taxa
        preco_binance_total_com_taxa = preco_binance_total

        menor_preco = min(preco_manual_total, preco_binance_total_com_taxa)
        maior_preco = max(preco_manual_total, preco_binance_total_com_taxa)
        diferenca_preco = maior_preco - menor_preco
        diferenca_percentual = (diferenca_preco / menor_preco) * 100 if menor_preco > 0 else 0

        preco_manual_formatado = formatar_moeda(preco_manual_total)
        preco_binance_formatado = formatar_moeda(preco_binance_total_com_taxa)

        print(f"Comparação:\n- Preço Manual Total: {preco_manual_formatado} BRL para {quantidade_usdt} USDT")
        print(f"- Preço Binance Total com Taxa: {preco_binance_formatado} BRL para {quantidade_usdt} USDT")
        print(f"- Diferença de Preço: {formatar_moeda(diferenca_preco)} BRL")
        print(f"- Diferença Percentual: {diferenca_percentual:.2f}%")

        if diferenca_preco >= 5.00:
            valor_ganho = diferenca_preco
            if maior_preco == preco_manual_total:
                mensagem = (f"Oportunidade de Arbitragem:📈 \n\n"
                            f"Corretora: Bitoy / Binance\n\n"
                            f"Moeda de Compra: USDT\n"
                            f"Moeda de Venda: BRLA\n\n"
                            f"Comprar na Binance por {preco_binance_formatado}\n"
                            f"Quantidade: {quantidade_usdt_com_taxa} USDT\n\n"
                            f"Vender no preço manual por {formatar_moeda(preco_manual_total)}\n"
                            f"Quantidade: {quantidade_usdt}\n"
                            f"Ganho: {formatar_moeda(valor_ganho)}💰\n"
                            f"ROI: {diferenca_percentual:.2f}%📊")
            else:
                mensagem = (f"Oportunidade de Arbitragem:📈 \n\n"
                            f"Corretora: Bitoy / Binance\n\n"
                            f"Moeda de Compra: USDT\n"
                            f"Moeda de Venda: USDT\n\n"
                            f"Comprar na BITOY por: {formatar_moeda(preco_manual_total)}\n"
                            f"Quantidade: 315 USDT\n\n"
                            f"Vender na Binance por {preco_binance_formatado}\n"
                            f"Quantidade: {quantidade_usdt_com_taxa} USDT\n\n"
                            f"Ganho: {formatar_moeda(valor_ganho)}💰\n"
                            f"ROI: {diferenca_percentual:.2f}%📊")
            print(mensagem)
            enviar_mensagem_telegram(mensagem)
        else:
            print("Nenhuma oportunidade de arbitragem identificada.")

# Loop para monitorar preços e verificar oportunidades de arbitragem
def monitorar_precos(intervalo_segundos=60):
    while True:
        comparar_precos()
        time.sleep(intervalo_segundos)

# Configurar o intervalo de monitoramento e iniciar o bot
monitorar_precos(intervalo_segundos=60)
