import sys
from PyQt5.QtWidgets import *
from PyQt5 import uic

# 주식 정보 불러오기
import FinanceDataReader as fdr

# 차트 표시
import matplotlib.pyplot as plt

plt.rc('font', family='gulim') # For Windows

kospi_stocks = fdr.StockListing('KOSPI')
print(kospi_stocks.head())


form_class = uic.loadUiType("stock_search.ui")[0]

def calculate_rsi(data, period=14):  # 내가 원하는 종목의 rsi  값구하기
    delta = data['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period, min_periods=1).mean()
    avg_loss = loss.rolling(window=period, min_periods=1).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi


class WindowClass(QMainWindow, form_class):
    def __init__(self) :
        super().__init__()
        self.setupUi(self)
        for i in kospi_stocks[0:30]["Name"]:
            self.listWidget.addItem(str(i))
        self.listWidget.itemDoubleClicked.connect(self.stock_rsi)

    # 종목 검색 함수 (리스트 위젯에서 종목 눌렀을 때)
    def stock_rsi(self , iteam):
        name = iteam.text()

        code = kospi_stocks.loc[kospi_stocks["Name"] == iteam.text(), "Code"].iloc[0]
        print(code)

        data = fdr.DataReader(code, '2019-1-01', '2024-12-20')
        data['RSI'] = calculate_rsi(data)
        print(data)

        # 차트 그리기
        plt.figure(figsize=(12, 6))
        ax1 = plt.gca()
        ax1.plot(data.index, data['RSI'], label='RSI')
        ax1.axhline(70, color='red', linestyle='--', label='Overbought (70)')
        ax1.axhline(30, color='blue', linestyle='--', label='Oversold (30)')
        ax1.legend(loc='upper left')

        ax2 = ax1.twinx()
        ax2.plot(data.index, data['Close'], color='RED', label='Close Price')
        ax2.set_ylabel('Close Price', color='blue')
        ax2.tick_params(axis='y', labelcolor='blue')
        ax2.set_title(f'{name} Close Price and RSI')
        ax2.legend(loc='upper left')

        plt.show()


if __name__ == "__main__" :
    app = QApplication(sys.argv)
    myWindow = WindowClass()
    myWindow.show()
    app.exec_()
