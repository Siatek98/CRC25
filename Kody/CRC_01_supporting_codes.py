import pandas as pd
import numpy_financial as npf
from ib_insync import IB, Bond
import random
import re


def get_bond_market_data(ticker_symbol):
    ib = IB()
    ib.connect('127.0.0.1', 7497, clientId=random.randint(1, 100))

    details = ib.reqContractDetails(Bond(symbol=ticker_symbol))
    bond_data = []

    for detail in details:
        contract = detail.contract
        desc = detail.descAppend.strip()

        match = re.match(r'^([^\s]+)\s+(\d+(?:\s+\d+/\d+|\.\d+)?)\s+(\d{2}/\d{2}/\d{2})$', desc)
        if match:
            emitent = match.group(1)
            kupon_raw = match.group(2)
            zapadalnosc_raw = match.group(3)

            if ' ' in kupon_raw:
                whole, fraction = kupon_raw.split()
                numerator, denominator = fraction.split('/')
                kupon = float(whole) + float(numerator) / float(denominator)
            else:
                kupon = float(kupon_raw)

            maturity_date = pd.to_datetime(zapadalnosc_raw, format='%m/%d/%y', errors='coerce')
        else:
            emitent, kupon, maturity_date = 'N/A', None, None

        ticker = ib.reqMktData(contract, '', False, False)

        # konieczne odczekanie, aż dane spłyną
        ib.sleep(2)

        bid = ticker.bid if ticker.bid else None
        ask = ticker.ask if ticker.ask else None
        midpoint = (bid + ask) / 2 if bid and ask else None

        if ask and maturity_date and kupon:
            today = pd.Timestamp.today()
            years_to_maturity = (maturity_date - today).days / 365.25
            face_value = 100
            coupon_payment = kupon / 100 * face_value / 2

            try:
                ytm = npf.rate(
                    nper=int(years_to_maturity * 2),
                    pmt=coupon_payment,
                    pv=-ask,
                    fv=face_value
                ) * 2 * 100
                ytm = round(ytm, 4)
            except:
                ytm = None
        else:
            ytm = None

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
            "YTM (Ask) [%]": ytm
        })

    ib.disconnect()

    return pd.DataFrame(bond_data)





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
