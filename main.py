#import logging
import datetime
import statistics
from time import sleep

from tkinter import Tk
from tkinter import Label
from tkinter import Button
from tkinter import Entry
from tkinter import ttk
from tkinter import StringVar
from tkinter import messagebox

from alice_blue import TransactionType
from alice_blue import OrderType
from alice_blue import ProductType
from alice_blue import AliceBlue
from alice_blue import LiveFeedType

# Config
username = ''
password = ''
api_secret = ''
twoFA = ''
EMA_CROSS_SCRIP = 'INFY'
BANK_NIFTY_SCRIP = 'BANKNIFTY'
banknifty_nfo_scriptnames = {}
access_token = ''

window=Tk()
var1=StringVar()
var2=StringVar()
quantity=StringVar()

#logging.basicConfig(level=logging.DEBUG)        # Optional for getting debug messages.
# Config

ltp = 0
socket_opened = False
alice = None
def event_handler_quote_update(message):
    global ltp
    ltp = message['ltp']

def open_callback():
    global socket_opened
    socket_opened = True

def buy_signal(ins_scrip, quantity = 25):
    global alice
    return alice.place_order(transaction_type = TransactionType.Buy,
                         instrument = ins_scrip,
                         quantity = quantity,
                         order_type = OrderType.Market,
                         product_type = ProductType.Intraday,
                         price = 0.0,
                         trigger_price = None,
                         stop_loss = None,
                         square_off = None,
                         trailing_sl = None,
                         is_amo = False)

def sell_signal(ins_scrip, quantity=25):
    global alice
    return alice.place_order(transaction_type = TransactionType.Sell,
                         instrument = ins_scrip,
                         quantity = quantity,
                         order_type = OrderType.Market,
                         product_type = ProductType.Intraday,
                         price = 0.0,
                         trigger_price = None,
                         stop_loss = None,
                         square_off = None,
                         trailing_sl = None,
                         is_amo = False)
    
def banknifty_trade(bn_put, bn_call, quantityInt):
    #bn_call = alice.get_instrument_for_fno(symbol = 'BANKNIFTY', expiry_date=datetime.date(2019, 6, 27), is_fut=False, strike=30000, is_CE = True)
    #bn_put = alice.get_instrument_for_fno(symbol = BANK_NIFTY_SCRIP, expiry_date=datetime.date(2020, 10, 15), is_fut=False, strike=17500, is_CE = False)
    #ins_scrip = alice.get_instrument_by_symbol('NSE', EMA_CROSS_SCRIP)
    #sell_signal(bn_put)
    
    buySignalResponse = sell_signal(bn_put, quantityInt)
    sellSignalResponse = sell_signal(bn_call, quantityInt)
    
    orderResponseText = buySignalResponse["message"]
    orderIdText = "Put Order Id: ", str(buySignalResponse["data"]["oms_order_id"]), ", Call Order Id: ",  str(sellSignalResponse["data"]["oms_order_id"])
        
    messagebox.showinfo("Order Details", orderResponseText + '. \n' + ''.join(orderIdText))
    

def getall_banknifty_nfo():
    multiple_underlying = ["BANKNIFTY"]
    matches = alice.search_instruments('NFO', multiple_underlying)
    for nfo_script in matches:
        banknifty_nfo_scriptnames[nfo_script.symbol] = nfo_script
    
def crude_sma_trade_triggers():
    global socket_opened
    minute_close = []
    ins_scrip = alice.get_instrument_by_symbol('MCX', 'CRUDEOIL OCT FUT')
    #ins_scrip = alice.get_instrument_by_symbol('NSE', 'INFY')
    
    print('Before Socket Start')
    alice.start_websocket(subscribe_callback=event_handler_quote_update,
                          socket_open_callback=open_callback,
                          run_in_background=True)
    print('Before Socket Open')
    while(socket_opened==False):    # wait till socket open & then subscribe
        pass
    print('Socket Open Successful')
    alice.subscribe(ins_scrip, LiveFeedType.COMPACT)
    
    print('After Subscribe!')
    current_signal = ''
    print(datetime.datetime.now().second)
    while True:
        if(datetime.datetime.now().second == 0):
            minute_close.append(ltp)
            print("Crude Last traded price -> " + str(ltp))
            if(len(minute_close) > 9):
                sma_5 = statistics.mean(minute_close[-3:])
                sma_20 = statistics.mean(minute_close[-9:])
                if(current_signal != 'buy'):
                    if(sma_5 > sma_20):
                        #buy_signal(ins_scrip)
                        print("Buy CRUDE at -> " + str(ltp))
                        current_signal = 'buy'
                if(current_signal != 'sell'):
                    if(sma_5 < sma_20):
                        #sell_signal(ins_scrip)
                        print("Sell CRUDE at -> " + str(ltp))
                        current_signal = 'sell'
            sleep(1)
        sleep(0.2)  # sleep for 200ms
 
def onTriggerClick():
    banknifty_trade(banknifty_nfo_scriptnames.get(var1.get()), banknifty_nfo_scriptnames.get(var2.get()), int(quantity.get()))

def launchUI():
  
    window.geometry("600x200")
    window.title("Market Master")
    quantity.set('25')
    
    # label text for title 
    Label(window,text="Bank Nifty Trading Terminal",relief="solid",bg="orange",width=30,font=("arial",20,"bold")).place(x=50,y=5)
      
    Label(window,text="Select Put Script",width=20,font=("arial",10,"bold")).place(x=77,y=60)
    drop1=ttk.Combobox(window,textvar=var1,value=tuple(banknifty_nfo_scriptnames))
    drop1.current(0)
    drop1.config(width=30)
    drop1.place(x=300,y=60)
    
    Label(window,text="Select Call Script",width=20,font=("arial",10,"bold")).place(x=77,y=90)
    drop2=ttk.Combobox(window,textvar=var2,value=tuple(banknifty_nfo_scriptnames)) 
    drop2.current(0)
    drop2.config(width=30)
    drop2.place(x=300,y=90)
    
    Label(window,text="Input Quantity",width=20,font=("arial",10,"bold")).place(x=77,y=120)
    quantityEntry=Entry(window, textvariable = quantity, width=33)
    quantityEntry.place(x=300,y=120)
    
    Button(window,text="Trigger Trade",relief="solid",width=10,bg="red",fg="white", command=onTriggerClick).place(x=200,y=160)
    Button(window, text="Close", relief="solid",width=10, bg="red", fg="white", command=window.destroy).place(x=300,y=160)
    
    window.mainloop()    
    
def main():
    global socket_opened
    global alice
    global username
    global password
    global twoFA
    global api_secret
    global EMA_CROSS_SCRIP
    global BANK_NIFTY_SCRIP
    global banknifty_nfo_scriptnames
    global access_token
    global var1
    global var2
    global socket_opened
    global quantity
    
    access_token = "W8cjsykLHoMLxLGT-7jMd_lE99cgPtXfIWBaLLE0A7E.b33Zz69ZBvgo_7VLZcKwoqsw9Bbk2hJvRkB9X0J4Etg"
    if(access_token is None or access_token == ''):
        print("Getting a fresh token")
        access_token = AliceBlue.login_and_get_access_token(username=username, password=password, twoFA=twoFA,  api_secret=api_secret)
        print(access_token)

    #Initialze AliceBlue Object
    alice = AliceBlue(username=username, password=password, access_token=access_token, master_contracts_to_download=['NFO'])
    
    #print(alice.get_balance()) # get balance / margin limits
    #print(alice.get_profile()) # get profile
    #print(alice.get_daywise_positions()) # get daywise positions
    #print(alice.get_netwise_positions()) # get netwise positions
    #print(alice.get_holding_positions()) # get holding positions
    
    getall_banknifty_nfo()
    launchUI()
    #banknifty_trade()
    #crude_sma_trade_triggers()
    
    print("End!!")
   
if(__name__ == '__main__'):
    main()