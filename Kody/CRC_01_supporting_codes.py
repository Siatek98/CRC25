import pandas as pd
import numpy_financial as npf
from ib_insync import IB, Bond
import random
import re

import random
import re
import time
import pandas as pd
import numpy_financial as npf
from ib_insync import IB, Bond

def format_years(years):
    """
    Zaokrągla liczbę lat do dwóch miejsc.
    Jeśli wynik wynosi dokładnie X.50, zwraca "X i pół roku", w przeciwnym razie "Y.YY lat".
    """
    rounded = round(years, 2)
    if abs(rounded - (int(rounded) + 0.5)) < 1e-6:
        return f"{int(rounded)} i pół roku"
    else:
        return rounded

def get_bond_market_data(ticker_symbol, max_bonds=1000, timeout=60):
    ib = IB()
    client_id = random.randint(1, 9999)
    ib.connect('127.0.0.1', 7497, clientId=client_id)

    bond_data = []
    error_occurred = False

    def on_error(reqId, errorCode, errorString, contract):
        nonlocal error_occurred
        if errorCode == 101:
            print(f"Error 101 (reqId: {reqId}): {errorString}")
            error_occurred = True

    ib.errorEvent += on_error
    start_time = time.time()

    try:
        details = ib.reqContractDetails(Bond(symbol=ticker_symbol))
        if not details:
            print(f"Nie znaleziono obligacji dla {ticker_symbol}")
            return pd.DataFrame()

        details = details[:max_bonds]
        contracts = [detail.contract for detail in details]
        tickers = ib.reqTickers(*contracts)

        elapsed_time = time.time() - start_time
        if elapsed_time > timeout:
            print(f"Osiągnięto limit czasowy ({timeout} sekund) podczas pobierania tickers.")
            return pd.DataFrame()

        today = pd.Timestamp.today()
        for detail, ticker, contract in zip(details, tickers, contracts):
            if error_occurred:
                print("Przerwano działanie ze względu na Error 101.")
                break

            elapsed_time = time.time() - start_time
            if elapsed_time > timeout:
                print(f"Osiągnięto limit czasowy ({timeout} sekund). Przerywam pobieranie.")
                break

            desc = detail.descAppend.strip()
            match = re.match(r'^([^\s]+)\s+(\d+(?:\s+\d+/\d+|\.\d+)?)\s+(\d{2}/\d{2}/\d{2})$', desc)
            if match:
                emitent, kupon_raw, zapadalnosc_raw = match.groups()
                if ' ' in kupon_raw:
                    whole, fraction = kupon_raw.split()
                    numerator, denominator = fraction.split('/')
                    kupon = float(whole) + float(numerator) / float(denominator)
                else:
                    kupon = float(kupon_raw)
                maturity_date = pd.to_datetime(zapadalnosc_raw, format='%m/%d/%y', errors='coerce')
            else:
                emitent, kupon, maturity_date = 'N/A', None, None

            bid, ask = ticker.bid, ticker.ask
            midpoint = (bid + ask) / 2 if bid and ask else None

            if ask and maturity_date and kupon:
                if maturity_date <= today:
                    ytm = None
                    years_to_maturity = 0
                else:
                    years_to_maturity = (maturity_date - today).days / 365.25
                    nper = int(years_to_maturity * 2)
                    face_value = 100
                    coupon_payment = kupon / 100 * face_value / 2
                    if nper <= 0 or ask <= 0:
                        ytm = None
                    else:
                        try:
                            ytm = npf.rate(nper=nper, pmt=coupon_payment, pv=-ask, fv=face_value) * 2 * 100
                            ytm = round(ytm, 4)
                        except Exception:
                            ytm = None
            else:
                ytm = None
                years_to_maturity = None

            if years_to_maturity is not None and years_to_maturity > 0:
                years_str = format_years(years_to_maturity)
            else:
                years_str = None

            bond_data.append({
                "Contract ID": contract.conId,
                "Emitent": emitent,
                "Kupon (%)": kupon,
                "Zapadalność": maturity_date.date() if maturity_date else None,
                "CUSIP": detail.cusip,
                "Exchange": contract.exchange,
                "Min Tick": detail.minTick,
                "Bid": bid,
                "Ask": ask,
                "Midpoint": midpoint,
                "YTM (Ask) [%]": ytm,
                "Lata do wykupu": years_str
            })

        return pd.DataFrame(bond_data)

    finally:
        ib.disconnect()














import pandas as pd
from ib_insync import IB, Bond
import random

def get_bond_historical_data(con_id, duration='1 Y', what_to_show='MIDPOINT'):
    ib = IB()
    ib.connect('127.0.0.1', 7497, clientId=random.randint(1, 100))

    bond = Bond(conId=con_id, exchange='SMART', currency='USD')

    bars = ib.reqHistoricalData(
        bond,
        endDateTime='',
        durationStr=duration,
        barSizeSetting='1 day',
        whatToShow=what_to_show,
        useRTH=True,
        formatDate=1
    )

    data = [{
        'Date': bar.date,
        'Open': bar.open,
        'High': bar.high,
        'Low': bar.low,
        'Close': bar.close
    } for bar in bars]

    ib.disconnect()

    return pd.DataFrame(data)
