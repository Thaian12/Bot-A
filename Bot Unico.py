import requests
import time

# Configurações do Telegram
TELEGRAM_TOKEN = '7519701271:AAG6nCA0ipq-QQGlK9od8R1kaDZtUNkVAh0'
CHAT_ID = '5045138558'
TELEGRAM_API_URL = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
TELEGRAM_UPDATE_URL = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates'

# URLs da API ParaSwap para o par USDT/BRLA
taxa = 1.12 / 100
amount_original = 315000000  # equivalente a 315 USDT, considerando 6 casas decimais
amount_com_taxa = int(amount_original * (1 - taxa))


# URLs das APIs
URL_KUCOIN = "https://api.kucoin.com/api/v1/market/orderbook/level2_20?symbol=USDT-BRL"
URL_BINANCE = "https://api.binance.com/api/v3/depth?symbol=USDTBRL&limit=5"
URL_PARASWAP = f"https://api.paraswap.io/prices/?srcToken=0xc2132D05D31c914a87C6611C10748AEb04B58e8F&destToken=0xE6A537a407488807F0bbeb0038B79004f19DDDFb&amount={amount_com_taxa}&srcDecimals=6&destDecimals=2&side=SELL&network=137&version=5"

# Variáveis globais
preco_manual = None
TAXA_COMPRA_BITOY = 0.0112  # Taxa de 1,12%
withdrawal_fee_kucoin = 2.60  # Taxa de saque KuCoin

# Função para enviar mensagens para o Telegram
def send_telegram_message(message):
    payload = {'chat_id': CHAT_ID, 'text': message, 'parse_mode': 'HTML'}
    response = requests.post(TELEGRAM_API_URL, data=payload)
    if response.status_code != 200:
        print(f"Erro ao enviar mensagem para o Telegram: {response.status_code}")

# Função para formatar números em moeda brasileira
def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# Funções para obter preços de cada exchange
def get_kucoin_order_book():
    response = requests.get(URL_KUCOIN)
    if response.status_code == 200:
        data = response.json()
        if data['code'] == '200000':
            best_bid_price = float(data['data']['bids'][0][0])
            best_bid_quantity = float(data['data']['bids'][0][1])
            best_ask_price = float(data['data']['asks'][0][0])
            best_ask_quantity = float(data['data']['asks'][0][1])
            return best_bid_price, best_bid_quantity, best_ask_price, best_ask_quantity
    return None, None, None, None

def get_binance_order_book():
    response = requests.get(URL_BINANCE)
    if response.status_code == 200:
        data = response.json()
        best_bid_price = float(data['bids'][0][0])
        best_bid_quantity = float(data['bids'][0][1])
        best_ask_price = float(data['asks'][0][0])
        best_ask_quantity = float(data['asks'][0][1])
        return best_bid_price, best_bid_quantity, best_ask_price, best_ask_quantity
    return None, None, None, None

def verificar_preco_paraswap():
    response = requests.get(URL_PARASWAP)
    if response.status_code == 200:
        dados = response.json()
        preco_destino = dados.get('priceRoute', {}).get('destAmount')
        if preco_destino:
            return float(preco_destino) / 10**18
    return None

# Função para verificar preço manual no Telegram
def verificar_preco_manual():
    global preco_manual
    response = requests.get(TELEGRAM_UPDATE_URL)
    if response.status_code == 200:
        updates = response.json().get("result", [])
        if updates:
            last_message = updates[-1].get("message", {}).get("text")
            if last_message and last_message.startswith("/BITOY "):
                try:
                    preco_novo = float(last_message.split(" ")[1])
                    if preco_manual != preco_novo:
                        preco_manual = preco_novo
                        send_telegram_message(f"Preço BITOY atualizado: {formatar_moeda(preco_manual)}")
                except ValueError:
                    send_telegram_message("Erro: formato de preço inválido. Envie como 'BITOY 100.00'.")

# Funções para checar oportunidades de arbitragem entre exchanges
def check_arbitrage_kucoin_binance():
    kucoin_best_bid_price, _, kucoin_best_ask_price, _ = get_kucoin_order_book()
    binance_best_bid_price, _, binance_best_ask_price, _ = get_binance_order_book()
    
    if kucoin_best_bid_price and binance_best_ask_price and kucoin_best_bid_price > binance_best_ask_price:
        potential_profit_per_usdt = kucoin_best_bid_price - binance_best_ask_price
        trade_quantity = min(binance_best_ask_price, kucoin_best_bid_price)
        total_profit = potential_profit_per_usdt * trade_quantity - withdrawal_fee_kucoin
        percentage_diff = (potential_profit_per_usdt / binance_best_ask_price) * 100
        message = (f"Oportunidade de Arbitragem: Binance / Kucoin\n"
                   f"Compra na Binance: {formatar_moeda(binance_best_ask_price)}\n"
                   f"Venda na KuCoin: {formatar_moeda(kucoin_best_bid_price)}\n"
                   f"Ganho: {formatar_moeda(total_profit)} 💰 ({percentage_diff:.2f}%)")
        send_telegram_message(message)

def check_arbitrage_binance_paraswap():
    preco_paraswap = verificar_preco_paraswap()
    binance_best_bid_price, _, binance_best_ask_price, _ = get_binance_order_book()
    
    if preco_paraswap and binance_best_ask_price:
        diff = abs(preco_paraswap - binance_best_ask_price * 315)
        percentage_diff = (diff / min(preco_paraswap, binance_best_ask_price * 315)) * 100
        if diff >= 5.00:
            message = (f"Oportunidade de Arbitragem: Binance / ParaSwap\n"
                       f"Preço ParaSwap: {formatar_moeda(preco_paraswap)} para 315 USDT\n"
                       f"Preço Binance: {formatar_moeda(binance_best_ask_price * 315)}\n"
                       f"Diferença: {formatar_moeda(diff)} 💰 ({percentage_diff:.2f}%)")
            send_telegram_message(message)

def check_arbitrage_bitoy_binance():
    verificar_preco_manual()
    binance_best_bid_price, _, binance_best_ask_price, _ = get_binance_order_book()
    
    if preco_manual and binance_best_bid_price:
        binance_price = binance_best_bid_price * 315 * (1 - TAXA_COMPRA_BITOY)
        diff = abs(preco_manual * 315 - binance_price)
        percentage_diff = (diff / min(preco_manual * 315, binance_price)) * 100
        if diff >= 5.00:
            message = (f"Oportunidade de Arbitragem: Bitoy / Binance\n"
                       f"Preço Manual: {formatar_moeda(preco_manual * 315)} para 315 USDT\n"
                       f"Preço Binance: {formatar_moeda(binance_price)}\n"
                       f"Diferença: {formatar_moeda(diff)} 💰 ({percentage_diff:.2f}%)")
            send_telegram_message(message)

def check_arbitrage_bitoy_paraswap():
    verificar_preco_manual()
    preco_paraswap = verificar_preco_paraswap()
    
    if preco_manual and preco_paraswap:
        quantidade_usdt_apos_taxa = 315# Aplicando a taxa de compra na quantidade de USDT
        preco_manual_total = preco_manual * quantidade_usdt_apos_taxa
        diff = abs(preco_paraswap - preco_manual_total)
        percentage_diff = (diff / min(preco_paraswap, preco_manual_total)) * 100
        
        if diff >= 5.00:
            message = (f"Oportunidade de Arbitragem: Bitoy / ParaSwap\n"
                       f"Preço Manual Bitoy (após taxa): {formatar_moeda(preco_manual_total)} para {quantidade_usdt_apos_taxa:.2f} USDT\n"
                       f"Preço ParaSwap: {formatar_moeda(preco_paraswap)}\n"
                       f"Diferença: {formatar_moeda(diff)} 💰 ({percentage_diff:.2f}%)")
            send_telegram_message(message)

# Loop principal
def monitorar_precos(intervalo_segundos=60):
    while True:
        check_arbitrage_kucoin_binance()
        check_arbitrage_binance_paraswap()
        check_arbitrage_bitoy_binance()
        check_arbitrage_bitoy_paraswap()
        time.sleep(intervalo_segundos)

# Iniciar monitoramento
monitorar_precos(intervalo_segundos=60)
