import hmac
import hashlib
from easyquant.exchange.util import requests
try:
    from urllib import urlencode

# for python3
except ImportError:
    from urllib.parse import urlencode


ENDPOINT = "https://dapi.binance.com"

BUY = "BUY"
SELL = "SELL"

LIMIT = "LIMIT"
MARKET = "MARKET"

GTC = "GTC"
IOC = "IOC"

options = {}


def set(apiKey, secret):
    """Set API key and secret.

    Must be called before any making any signed API calls.
    """
    options["apiKey"] = apiKey
    options["secret"] = secret

def balance():
    """获取账户余额"""
    data = signedRequest("GET", "/dapi/v1/balance", {})
    if 'msg' in data:
        raise ValueError("Error from exchange: {}".format(data['msg']))
    return data

def depth(symbol, **kwargs):
    """Get order book.

    Args:
        symbol (str)
        limit (int, optional): Default 100. Must be one of 50, 20, 100, 500, 5,
            200, 10.

    """
    params = {"symbol": symbol}
    params.update(kwargs)
    data = request("GET", "/dapi/v1/depth", params)
    return {
        "bids": data["bids"],
        "asks": data["asks"]
    }


def klines(symbol, interval, **kwargs):
    """Get kline/candlestick bars for a symbol.

    Klines are uniquely identified by their open time. If startTime and endTime
    are not sent, the most recent klines are returned.

    Args:
        symbol (str)
        interval (str)
        limit (int, optional): Default 500; max 500.
        startTime (int, optional)
        endTime (int, optional)

    """
    params = {"symbol": symbol, "interval": interval}
    params.update(kwargs)
    data = request("GET", "/dapi/v1/klines", params)
    return data


def position():
    data = signedRequest("GET", "/dapi/v1/positionRisk", {})
    if 'msg' in data:
        raise ValueError("Error from exchange: {}".format(data['msg']))
    return data


def order(symbol, side, order_type, positionSide=None, **kwargs):
    params = {
        "symbol": symbol,
        "side": side,
        "type": order_type,
        "positionSide": positionSide
    }
    params.update(kwargs)
    path = "/dapi/v1/order"
    data = signedRequest("POST", path, params)
    return data


def orderStatus(symbol, **kwargs):
    """Check an order's status.

    Args:
        symbol (str)
        orderId (int, optional)
        origClientOrderId (str, optional)
        recvWindow (int, optional)

    """
    params = {"symbol": symbol}
    params.update(kwargs)
    data = signedRequest("GET", "/dapi/v1/order", params)
    return data


def cancel(symbol, **kwargs):
    """Cancel an active order.

    Args:
        symbol (str)
        orderId (int, optional)
        origClientOrderId (str, optional)
        newClientOrderId (str, optional): Used to uniquely identify this
            cancel. Automatically generated by default.
        recvWindow (int, optional)

    """
    params = {"symbol": symbol}
    params.update(kwargs)
    data = signedRequest("DELETE", "/dapi/v1/order", params)
    return data


def openOrders(symbol, **kwargs):
    """Get all open orders on a symbol.

    Args:
        symbol (str)
        recvWindow (int, optional)

    """
    params = {"symbol": symbol}
    params.update(kwargs)
    data = signedRequest("GET", "/dapi/v1/openOrder", params)
    return data


def allOrders(symbol, **kwargs):
    """Get all account orders; active, canceled, or filled.

    If orderId is set, it will get orders >= that orderId. Otherwise most
    recent orders are returned.

    Args:
        symbol (str)
        orderId (int, optional)
        limit (int, optional): Default 500; max 500.
        recvWindow (int, optional)

    """
    params = {"symbol": symbol}
    params.update(kwargs)
    data = signedRequest("GET", "/dapi/v1/openOrders", params)
    return data


def myTrades(symbol, **kwargs):
    """Get trades for a specific account and symbol.

    Args:
        symbol (str)
        limit (int, optional): Default 500; max 500.
        fromId (int, optional): TradeId to fetch from. Default gets most recent
            trades.
        recvWindow (int, optional)

    """
    params = {"symbol": symbol}
    params.update(kwargs)
    data = signedRequest("GET", "/dapi/v1/userTrades", params)
    return data


def request(method, path, params=None):
    resp = requests.request(method, ENDPOINT + path, params=params)
    data = resp.json()
    # if "msg" in data:
    #     logging.error(data['msg'])
    return data


def signedRequest(method, path, params):
    if "apiKey" not in options or "secret" not in options:
        raise ValueError("Api key and secret must be set")
    timestamp = requests.get("https://api.binance.com/api/v3/time").json()['serverTime']
    query = urlencode(sorted(params.items()))
    query += "&timestamp={}".format(timestamp)
    secret = bytes(options["secret"].encode("utf-8"))
    signature = hmac.new(secret, query.encode("utf-8"),
                         hashlib.sha256).hexdigest()
    query += "&signature={}".format(signature)
    resp = requests.request(method,
                            ENDPOINT + path + "?" + query,
                            headers={"X-MBX-APIKEY": options["apiKey"]})
    data = resp.json()
    # if "msg" in data:
    #     logging.error(data['msg'])
    return data


def formatNumber(x):
    if isinstance(x, float):
        return "{:.8f}".format(x)
    else:
        return str(x)

def get_ticker(symbol):
    params = {"symbol": symbol}
    data = request("GET", "/dapi/v1/ticker/price", params)
    return data


def get_contract_value(symbol):
    result = None
    params = {}
    data = request("GET", "/dapi/v1/exchangeInfo", params)
    for item in data["symbols"]:
        if item["symbol"] == symbol:
            result = int(item["contractSize"])
    return result

def set_leverage(symbol, leverage):
    """设置开仓杠杆倍数"""
    params = {"symbol": symbol,
              "leverage": leverage}
    data = signedRequest("POST", "/dapi/v1/leverage", params)
    return data

def set_side_mode(dualSidePosition):
    """更改持仓模式.变换用户在 所有symbol 合约上的持仓模式：双向持仓或单向持仓。"true"为双向持仓模式；"false"为单向持仓模式"""
    params = {"dualSidePosition": dualSidePosition}
    data = signedRequest("POST", "/dapi/v1/positionSide/dual", params)
    return data

def set_margin_mode(symbol, marginType):
    """变换逐全仓模式.变换用户在指定symbol合约上的保证金模式：逐仓或全仓。
        不同持仓方向上使用相同的保证金模式。双向持仓模式下的逐仓,LONG 与 SHORT使用独立的逐仓仓位。"""
    params = {"symbol": symbol,
              "marginType": marginType}     # 保证金模式 ISOLATED(逐仓), CROSSED(全仓)
    data = signedRequest("POST", "/dapi/v1/marginType", params)
    return data


def listenkeyRequest(method, path, params):
    query = urlencode(sorted(params.items()))
    resp = requests.request(method,
                            ENDPOINT + path + "?" + query,
                            headers={"X-MBX-APIKEY": options["apiKey"]})
    data = resp.json()
    return data


def post_listen_key():
    """生成 Listen Key (USER_STREAM)"""
    params = {}
    path = "/dapi/v1/listenKey"
    data = listenkeyRequest("POST", path, params)
    return data