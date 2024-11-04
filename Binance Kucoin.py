import requests
import time

# Configurações do Telegram
TELEGRAM_TOKEN = '7519701271:AAG6nCA0ipq-QQGlK9od8R1kaDZtUNkVAh0'
CHAT_ID = '5045138558'

# Função para enviar mensagens para o Telegram
def send_telegram_message(message):
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'  # Para formatar a mensagem em HTML (opcional)
    }
    response = requests.post(telegram_url, json=payload)
    if response.status_code != 200:
        print(f"Erro ao enviar mensagem para o Telegram: {response.status_code}")

# Função para obter o livro de ordens completo na KuCoin para o par USDT/BRL
def get_kucoin_order_book():
    kucoin_url = "https://api.kucoin.com/api/v1/market/orderbook/level2_20?symbol=USDT-BRL"
    response = requests.get(kucoin_url)
    if response.status_code == 200:
        data = response.json()
        if data['code'] == '200000':
            best_bid_price = float(data['data']['bids'][0][0])  # Melhor preço de compra
            best_bid_quantity = float(data['data']['bids'][0][1])  # Quantidade na melhor ordem de compra
            best_ask_price = float(data['data']['asks'][0][0])  # Melhor preço de venda
            best_ask_quantity = float(data['data']['asks'][0][1])  # Quantidade na melhor ordem de venda
            return best_bid_price, best_bid_quantity, best_ask_price, best_ask_quantity
    else:
        print(f"Erro ao obter livro de ordens da KuCoin: {response.status_code}")
    return None, None, None, None

# Função para obter o livro de ordens completo na Binance para o par USDT/BRL
def get_binance_order_book():
    binance_url = "https://api.binance.com/api/v3/depth?symbol=USDTBRL&limit=5"
    response = requests.get(binance_url)
    if response.status_code == 200:
        data = response.json()
        best_bid_price = float(data['bids'][0][0])  # Melhor preço de compra
        best_bid_quantity = float(data['bids'][0][1])  # Quantidade na melhor ordem de compra
        best_ask_price = float(data['asks'][0][0])  # Melhor preço de venda
        best_ask_quantity = float(data['asks'][0][1])  # Quantidade na melhor ordem de venda
        return best_bid_price, best_bid_quantity, best_ask_price, best_ask_quantity
    else:
        print(f"Erro ao obter livro de ordens da Binance: {response.status_code}")
    return None, None, None, None

# Função para verificar oportunidade de arbitragem
def check_arbitrage_opportunity():
    # Taxa de saque da KuCoin
    withdrawal_fee = 2.60  # R$ 2,60

    # Obter dados para USDT/BRL em ambas as corretoras
    kucoin_best_bid_price, kucoin_best_bid_qty, kucoin_best_ask_price, kucoin_best_ask_qty = get_kucoin_order_book()
    binance_best_bid_price, binance_best_bid_qty, binance_best_ask_price, binance_best_ask_qty = get_binance_order_book()

    # Verificar se dados foram obtidos
    if None in [kucoin_best_bid_price, kucoin_best_bid_qty, kucoin_best_ask_price, kucoin_best_ask_qty,
                binance_best_bid_price, binance_best_bid_qty, binance_best_ask_price, binance_best_ask_qty]:
        print("Erro ao obter dados de uma das corretoras. Tentando novamente.")
        return

    # Exibir os preços e quantidades das melhores ordens de compra/venda
    print("\n--- Monitoramento USDT/BRL ---")
    print("KuCoin - USDT/BRL")
    print("Melhor Preço de Compra:", kucoin_best_bid_price, "Quantidade:", kucoin_best_bid_qty)
    print("Melhor Preço de Venda:", kucoin_best_ask_price, "Quantidade:", kucoin_best_ask_qty)

    print("\nBinance - USDT/BRL")
    print("Melhor Preço de Compra:", binance_best_bid_price, "Quantidade:", binance_best_bid_qty)
    print("Melhor Preço de Venda:", binance_best_ask_price, "Quantidade:", binance_best_ask_qty)

    # Determinar o valor menor entre as melhores ordens de compra e venda
    if kucoin_best_bid_price > binance_best_ask_price:
        trade_quantity = min(binance_best_ask_qty, kucoin_best_bid_qty)
        potential_profit_per_usdt = kucoin_best_bid_price - binance_best_ask_price
        total_potential_profit = potential_profit_per_usdt * trade_quantity - withdrawal_fee  # Abatendo a taxa
        applied_value = binance_best_ask_price * trade_quantity  # Valor aplicado na arbitragem
        percentage_difference = (potential_profit_per_usdt / binance_best_ask_price) * 100

        message = f"Oportunidade de Arbitragem:📈\n\n"
        message += f"Corretora: Binance / Kucoin\n\n"
        message += f"Moeda de Compra: USDT\n"
        message += f"Moeda de Venda: USDT\n\n"
        message += f"Comprar na Binance por R$ {binance_best_ask_price}\n"
        message += f"Quantidade <b>{trade_quantity} USDT</b>\n\n"
        message += f"Vender na KuCoin por R$ {kucoin_best_bid_price}\n"
        message += f"Quantidade <b>{trade_quantity} USDT</b>\n\n"
        message += f"Valor: <b>R$ {applied_value:.2f}</b>\n"
        message += f"Ganho: <b>R$ {total_potential_profit:.2f}💰</b>\n"
        message += f"Diferença: <b>{percentage_difference:.2f}%📊</b>\n"
        
        print(message)
        send_telegram_message(message)  # Enviar mensagem para o Telegram

    

# Loop de monitoramento a cada 30 segundos
while True:
    check_arbitrage_opportunity()
    # Aguardar 30 segundos antes da próxima consulta
    time.sleep(30)