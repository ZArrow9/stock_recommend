import yfinance as yf
import twstock as ts
import concurrent.futures
import time
import datetime as dt
import tkinter as tk
from tkinter import ttk
import threading

# INITIALIZE
stock_ids = []
stock_dict = {}
sort_dict = {}
high_risk = [0]*3
high_risk_price = [0]*3
high_risk_name = [0]*3
low_risk = [0]*3
low_risk_price = [0]*3
low_risk_name = [0]*3

window = tk.Tk()
window.title("股票推薦清單")
window.geometry("400x500")

# LOAD FILE
def load_file():
    global stock_ids
    f = open("stock_id.txt","r")
    for i in f.readlines():
        stock_ids.append(i.strip('\n'))
    f.close()

# COLLECT P/E RATIO INFO AND SHOW PROGRESS
progress_count = 0
def find_info(ticker):
    global progress_count
    progress_count += 1
    print("\r資料搜尋進度 (Progress) "+str(int(progress_count/len(stock_ids)*100))+"%",end="")
    find_ticker = str(ticker)+".TW"
    try:
        stock_info = yf.Ticker(find_ticker).info
        return(find_ticker,round(stock_info["trailingPE"],2))
    except Exception as ex:
        return(find_ticker,0)   # invalid value

# GET SPECIFIC STOCK PRICE
def get_price(stock_code):
    today = dt.date.today()
    check_code = stock_code + ".TW"
    check_data = yf.Ticker(check_code).info
    check_price = round(check_data["currentPrice"],2)
    return(check_price)

# GET SPECIFIC STOCK CHINESE NAME
def get_name(stock_code):
    check_code = ts.realtime.get(stock_code)
    chinese_name = check_code['info']['name']
    return(chinese_name)

# SORT BY P/E RATIO
def sort_by_peratio(results):
    global sort_dict
    print("\n資料處理中，請稍後 (Processing Data)")
    for result in results:
        stock_dict[result[0].strip('.TW')] = result[1]
    sort_dict = dict(sorted(stock_dict.items(),key = lambda x:x[1],reverse = True))

# FIND HIGH RISK STOCKS
def find_high():
    global high_risk
    check_count = 0
    for i in range(len(sort_dict)):
        check_ticker = str(list(sort_dict)[i])+".TW"
        try:
            check_history_12d = yf.download(check_ticker, period="12d",progress=False)["Close"].mean()
            check_history_14d = yf.download(check_ticker, period="14d",progress=False)["Close"].mean()
            if (check_history_12d > check_history_14d):
                high_risk[check_count] = list(sort_dict)[i]
                check_count += 1
            if check_count == len(high_risk):
                break
        except Exception as ex:
            pass

# FIND LOW RISK STOCKS
def find_low():
    global low_risk
    check_count = 0
    for i in range(len(sort_dict)-1,-1,-1):
        check_ticker = str(list(sort_dict)[i])+".TW"
        try:
            if (sort_dict[list(sort_dict)[i]] > 0):
                check_history_12d = yf.download(check_ticker, period="12d",progress=False)["Close"].mean()
                check_history_14d = yf.download(check_ticker, period="14d",progress=False)["Close"].mean()
                if (check_history_12d > check_history_14d):
                    low_risk[check_count] = list(sort_dict)[i]
                    check_count += 1
                if check_count == len(low_risk):
                    break
        except Exception as ex:
            pass

# CREATE UI
def create_ui():
    banner = tk.Label(window,text="歡迎使用股票推薦系統",font=("arial",14,"bold"),relief="ridge",width=400,borderwidth=3)
    banner.pack()
    show_time = tk.Label(window,text="系統/查詢時間 (System/Search Time)",font=("arial",12))
    show_time.pack()
    global show_cur_time
    show_cur_time = tk.Label(window,text=0,font=("arial",12))
    show_cur_time.pack()
    tick_time()
    option = tk.Label(window,text="請先選擇資料來源 (Source)",font=("arial",12))
    option.pack()
    url = tk.StringVar()
    yahoo_radbtn = tk.Radiobutton(window,text="Yahoo 股市財經",variable=url,value="https://tw.stock.yahoo.com")
    yahoo_radbtn.pack()
    yahoo_radbtn.select()
    twstock_radbtn = tk.Radiobutton(window,text="TWStock 台灣證券交易所",variable=url,value="https://www.twse.com.tw/")
    twstock_radbtn.pack()
    show_url = tk.Label(window,text="目前選用網址 (URL)",font=("arial",12))
    show_url.pack()
    url_entry = tk.Entry(window,text=url,width=30,state="disable",justify=tk.CENTER)
    url_entry.pack()
    global start_btn
    start_btn = tk.Button(window,text="開始搜尋 (Search)",bg="Yellow",command=start_search)
    start_btn.pack(pady=5)
    show_prog = tk.Label(window,text="搜尋結果 (Result)",font=("arial",12))
    show_prog.pack()

# TICK SYSTEM TIME
def tick_time():
    global next_time
    cur_time = time.strftime("%Y-%m-%d %H:%M:%S")
    if cur_time is not next_time:
        next_time = cur_time
        show_cur_time.config(text = cur_time)
    show_cur_time.after(100,tick_time)
next_time = time.strftime("%Y-%m-%d %H:%M:%S")

# CREATE TABLE
def create_table():
    table = ttk.Treeview(window)
    table['columns'] = ('num', 'name', 'price','risk')

    table.column('#0', width=0, stretch=tk.NO)
    table.column('num', anchor=tk.CENTER, width=120)
    table.column('name', anchor=tk.CENTER, width=80)
    table.column('price', anchor=tk.CENTER, width=120)
    table.column('risk', anchor=tk.CENTER, width=80)

    table.heading('#0', text='', anchor=tk.CENTER)
    table.heading('num', text='股票代碼', anchor=tk.CENTER)
    table.heading('name', text='股票名稱', anchor=tk.CENTER)
    table.heading('price', text='價格', anchor=tk.CENTER)
    table.heading('risk', text='風險', anchor=tk.CENTER)

    table.tag_configure('high_risk', background='lightpink')
    table.tag_configure('low_risk', background='#C1FFC1')

    for i in range(3):
        high_risk_price[i] = get_price(str(high_risk[i]))
        high_risk_name[i] = get_name(str(high_risk[i]))
        table.insert(parent='', 
                     index='end', 
                     iid=i, 
                     text='',
                     values=(str(high_risk[i]), high_risk_name[i],str(round(high_risk_price[i],2)),"高"),
                     tags='high_risk')

    for i in range(3):
        low_risk_price[i]=get_price(str(low_risk[i]))
        low_risk_name[i]=get_name(str(low_risk[i]))
        table.insert(parent='', 
                     index='end', 
                     iid=i+3, 
                     text='',
                     values=(str(low_risk[i]), low_risk_name[i],str(round(low_risk_price[i],2)),"低"),
                     tags='low_risk')
    table.pack()
    print("資料處理完成 (Finished)")

# SEARCH BOTTON EVENT
def start_search():
    start_btn["bg"] = "Gray"
    start_btn["state"] = "disabled"
    load_file()
    threading.Thread(target=start_multithread, daemon=True).start()

# START MULTITHREAD
def start_multithread():
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = executor.map(find_info,stock_ids)
    sort_by_peratio(results)
    find_high()
    find_low()
    window.after(0, create_table)

create_ui()

window.mainloop()
