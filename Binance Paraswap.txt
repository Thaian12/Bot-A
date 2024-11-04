import requests
import time

# URLs da API ParaSwap e Binance para o par USDT/BRL
URL_PARASWAP = "https://api.paraswap.io/prices/?srcToken=0xc2132D05D31c914a87C6611C10748AEb04B58e8F&destToken=0xE6A537a407488807F0bbeb0038B79004f19DDDFb&amount=315000000&srcDecimals=6&destDecimals=2&side=SELL&network=137&version=5"
URL_BINANCE = "https://api.binance.com/api/v3/ticker/price?symbol=USDTBRL"

# Configurações do Telegram
TELEGRAM_TOKEN = '7519701271:AAG6nCA0ipq-QQGlK9od8R1kaDZtUNkVAh0'
CHAT_ID = '5045138558'
TELEGRAM_API_URL = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'

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

# Função para obter o preço do par USDT/BRLA na ParaSwap
def verificar_preco_paraswap():
    try:
        response = requests.get(URL_PARASWAP)
        if response.status_code == 200:
            dados = response.json()
            # Extrair o preço da resposta JSON
            preco_destino = dados.get('priceRoute', {}).get('destAmount')
            if preco_destino:
                # Ajustar o valor dividindo por 10**18
                preco_destino_formatado = float(preco_destino) / 10**18
                # Formatando o preço
                preco_formatado = formatar_moeda(preco_destino_formatado)
                print(f"Preço na ParaSwap: {preco_formatado} BRLA para 315 USDT")
                return preco_destino_formatado
            else:
                print("Não foi possível obter o preço na ParaSwap.")
        else:
            print(f"Erro na requisição da ParaSwap: {response.status_code}")
    except Exception as e:
        print(f"Ocorreu um erro na ParaSwap: {e}")

# Função para obter o preço do par USDT/BRL na Binance
def verificar_preco_binance():
    try:
        response = requests.get(URL_BINANCE)
        if response.status_code == 200:
            dados = response.json()
            # Obter o preço do par USDT/BRL
            preco_binance = float(dados['price'])
            # Formatando o preço
            preco_formatado = formatar_moeda(preco_binance)
            print(f"Preço na Binance: {preco_formatado} BRL para 1 USDT")
            return preco_binance
        else:
            print(f"Erro na requisição da Binance: {response.status_code}")
    except Exception as e:
        print(f"Ocorreu um erro na Binance: {e}")

# Função para comparar os preços obtidos e calcular diferença
def comparar_precos():
    preco_paraswap = verificar_preco_paraswap()
    preco_binance = verificar_preco_binance()
    if preco_paraswap and preco_binance:
        preco_binance_315 = preco_binance * 315  # Converter para 315 USDT
        
        # Calcular diferença de preço
        maior_preco = max(preco_paraswap, preco_binance_315)
        menor_preco = min(preco_paraswap, preco_binance_315)
        diferenca_preco = maior_preco - menor_preco
        
        # Calcular diferença percentual
        if menor_preco > 0:
            diferenca_percentual = (diferenca_preco / menor_preco) * 100
        else:
            diferenca_percentual = 0  # Evitar divisão por zero
        
        preco_binance_315_formatado = formatar_moeda(preco_binance_315)
        
        print(f"Comparação:\n- ParaSwap: {formatar_moeda(preco_paraswap)} BRLA para 315 USDT")
        print(f"- Binance: {preco_binance_315_formatado} BRL para 315 USDT")
        print(f"- Diferença de Preço: {formatar_moeda(diferenca_preco)} BRL")
        print(f"- Diferença Percentual: {diferenca_percentual:.2f}%")
        
        # Verificar oportunidade de arbitragem
        if diferenca_preco >= 5.00:
            valor_ganho = diferenca_preco
            if maior_preco == preco_paraswap:
                mensagem = (f"Oportunidade de Arbitragem:📈 \n\n"
                            f"Corretora: Binance / 1NCH\n\n"
                            f"Moeda de Compra: USDT\n"
                            f"Moeda de Venda: BRLA\n\n"
                            f"Comprar na Binance por {preco_binance_315_formatado}\n"
                            f"Quantidade: 315 USDT\n\n"
                            f"Vender na ParaSwap por {formatar_moeda(preco_paraswap)}\n"
                            f"Quantidade: 315 USDT\n\n"
                            f"Valor:  {preco_binance_315_formatado}\n"
                            f"Ganho: {formatar_moeda(valor_ganho)}💰\n"
                            f"Ganho: {diferenca_percentual:.2f}%📊")
            else:
                mensagem = (f"Oportunidade de Arbitragem: \n\n"
                            f"Comprar na ParaSwap por {formatar_moeda(preco_paraswap)}\n"
                            f"Vender na Binance por {preco_binance_315_formatado}\n\n"
                            f"Valor Ganho: {formatar_moeda(valor_ganho)}🟢")
            print(mensagem)
            enviar_mensagem_telegram(mensagem)  # Enviar mensagem para o Telegram
        else:
            print("Nenhuma oportunidade de arbitragem identificada.")

# Loop para verificar e comparar os preços periodicamente
def monitorar_precos(intervalo_segundos=10):  # Alterado para 10 segundos
    while True:
        comparar_precos()
        time.sleep(intervalo_segundos)

# Configurar o intervalo de monitoramento e iniciar o bot
monitorar_precos(intervalo_segundos=10)  # Verifica a cada 10 segundos
