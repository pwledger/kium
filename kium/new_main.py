import sys
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtMultimedia import QSound, QMediaPlayer, QMediaContent
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QUrl

from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QClipboard  # 복사

from collections import deque
from datetime import datetime
import time

import atexit
import csv

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(300, 300, 800, 600)
        self.setWindowTitle("Kiwoom 조건식 완성 및 알림")

        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.ocx.OnEventConnect.connect(self._handler_login)
        self.ocx.OnReceiveConditionVer.connect(self._handler_condition_load)
        self.ocx.OnReceiveRealCondition.connect(self._handler_real_condition)
        self.ocx.OnReceiveTrCondition.connect(self._handler_tr_condition)
        self.ocx.OnReceiveTrData.connect(self._handler_tr_data)
        self.ocx.OnReceiveRealData.connect(self._handler_real_data)

        self.CommConnect()

        self.buy_stock_dict = {}
        self.today_buy = {}
        self.execution_price = None  # 체결 가격 저장용

        btn1 = QPushButton("Condition Down")
        btn2 = QPushButton("Condition List")
        btn3 = QPushButton("Condition Send")
        btn4 = QPushButton("Sell All")  # 일괄 매도 버튼
        btn5 = QPushButton("값 설정")

        self.listWidget = QListWidget()
        self.price_data = {}
        self.rsiListWidget = QListWidget()
        self.rsiList30under = QListWidget()
        self.rsiList30today = QListWidget()
        self.today_tran = QListWidget()
        # 알람 표시
        self.last_shown_message = None  # 마지막으로 표시된 메시지를 기록
        self.message_timestamp = 0  # 마지막 메시지의 타임스탬프를 기록
        self.alert_timer = QTimer(self)  # 타이머 설정
        self.alert_timer.setSingleShot(True)  # 타이머가 한 번만 실행되도록 설정
        self.last_saved_time = 0

        # Layouts
        main_layout = QVBoxLayout()
        button_layout = QHBoxLayout()
        list_layout = QHBoxLayout()
        input_layout = QHBoxLayout()

        # 입력창 시간
        self.input_field_time = QLineEdit(self)
        input_layout.addWidget(QLabel("시간"))
        self.input_field_time.setText("09:10")
        input_layout.addWidget(self.input_field_time)

        self.input_field_price = QLineEdit(self)
        input_layout.addWidget(QLabel("매수가격(원)"))
        self.input_field_price.setText("1000000")
        input_layout.addWidget(self.input_field_price)

        self.input_field_quantity = QLineEdit(self)
        input_layout.addWidget(QLabel("매수주 0이면 가격 :"))
        self.input_field_quantity.setText("1")
        input_layout.addWidget(self.input_field_quantity)

        self.input_field_tick = QLineEdit(self)
        input_layout.addWidget(QLabel("틱 (120 ,60)"))
        self.input_field_tick.setText("60")
        input_layout.addWidget(self.input_field_tick)

        self.input_field_count = QLineEdit(self)
        input_layout.addWidget(QLabel("종목당 거래 횟수"))
        self.input_field_count.setText("2")
        input_layout.addWidget(self.input_field_count)

        self.input_field_eran_rate = QLineEdit(self)
        input_layout.addWidget(QLabel("수익률"))
        self.input_field_eran_rate.setText("4")
        input_layout.addWidget(self.input_field_eran_rate)

        self.input_field_loss_rate = QLineEdit(self)
        input_layout.addWidget(QLabel("손절률"))
        self.input_field_loss_rate.setText("3")
        input_layout.addWidget(self.input_field_loss_rate)

        input_layout.addWidget(btn5)

        # Add buttons to button layout
        button_layout.addWidget(btn1)
        button_layout.addWidget(btn2)
        button_layout.addWidget(btn3)
        button_layout.addWidget(btn4)  # 일괄 매도 버튼 추가

        # Add lists to list layout with titles
        vertical_layout_left = QVBoxLayout()
        self.label = QLabel("Stock Codes")
        vertical_layout_left.addWidget(self.label)
        vertical_layout_left.addWidget(self.listWidget)

        vertical_layout_right = QVBoxLayout()
        vertical_layout_right.addWidget(QLabel("RSI Values"))
        vertical_layout_right.addWidget(self.rsiListWidget)

        vertical_layout_right1 = QVBoxLayout()
        vertical_layout_right1.addWidget(QLabel("RSI stock and time"))
        vertical_layout_right1.addWidget(self.rsiList30under)

        vertical_layout_right2 = QVBoxLayout()
        vertical_layout_right2.addWidget(QLabel("today RSI"))
        vertical_layout_right2.addWidget(self.rsiList30today)

        vertical_layout_right3 = QVBoxLayout()
        vertical_layout_right3.addWidget(QLabel("today buy sell"))
        vertical_layout_right3.addWidget(self.today_tran)

        list_layout.addLayout(vertical_layout_left)
        list_layout.addLayout(vertical_layout_right)
        list_layout.addLayout(vertical_layout_right1)
        list_layout.addLayout(vertical_layout_right2)
        list_layout.addLayout(vertical_layout_right3)

        # Add sub-layouts to main layout
        main_layout.addLayout(input_layout)
        main_layout.addLayout(button_layout)
        main_layout.addLayout(list_layout)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # event
        btn1.clicked.connect(self.GetConditionLoad)
        btn2.clicked.connect(self.GetConditionNameList)
        btn3.clicked.connect(self.send_condition)
        btn4.clicked.connect(self.sell_all_stocks)  # 일괄 매도 버튼 클릭 이벤트 연결
        btn5.clicked.connect(self.set_conditon_price)

        self.media_player = QMediaPlayer()

        # Queue for managing stock price requests
        self.stock_queue = deque()
        self.price_data = {}  # Dictionary to store price data for each stock
        self.price_data120 = {}
        self.timer = QTimer()
        self.timer.timeout.connect(self.process_queue)
        self.timer.start(200)  # Process queue every 200ms

        # 메세지
        self.msg_boxes = []

        # 시스템 종료 했을 떄 기록
        self.today_ris = []

        # Connect the itemClicked signal to the slot
        self.rsiList30under.itemClicked.connect(self.display_rsi_history)

        self.purchase_time_h = 9
        self.purchase_time_m = 10
        self.purchase_price = 1000000
        self.purchase_count = 60
        self.purchase_tick = 2
        self.purchase_loss_rate = 4
        self.purchase_earn_rate = 3
        self.purchase_quantity = 1
    def CommConnect(self):
        self.ocx.dynamicCall("CommConnect()")

    def GetLoginInfo(self, tag):
        result = self.ocx.dynamicCall("GetLoginInfo(QString)", tag)
        print(result)
        return result.split(';')[:-1]  # 계좌번호 리스트 반환

    def _handler_login(self, err_code):  # 로그인
        print("handler login", err_code)

    def _handler_condition_load(self, ret, msg):  # 조건 로드
        print("handler condition load", ret, msg)
        # 계좌번호 가져오기
        self.accounts = self.GetLoginInfo("ACCNO")  # 계좌번호 리스트 가져오기
        self.account = self.accounts[1]  # 첫 번째 계좌 사용
        print("사용할 계좌", self.account)
    def _handler_real_condition(self, code, type, cond_name, cond_index):  # 실시간
        if type == "D":
            item_count = self.listWidget.count()
            for i in range(item_count):
                item = self.listWidget.item(i)  # i 번째 항목 가져오기
                if item.text() == code:  # 항목의 텍스트가 code와 일치하는지 확인
                    row = i
                    break
            self.listWidget.takeItem(row)  # 해당 인덱스의 항목 삭제
        elif type == "I":
            item = QListWidgetItem(code)
            self.listWidget.addItem(item)  # ui 목록에 추가하는 법
            if code not in self.price_data:
                self.price_data[code] = deque(maxlen=120)
                self.request_real_time_data(code)
            if code not in self.price_data120:
                self.price_data120[code] = deque(maxlen=120)
        self.label.setText(f"Stock Codes {self.listWidget.count()}")

    def _handler_tr_condition(self, sCrNo, strCodeList, strConditionName, nIndex, nNext):
        print(strCodeList, strConditionName)
        self.update_list_widget(strCodeList)

    def _handler_tr_data(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext, data_len, err_code, msg1, msg2):
        if sRQName == "opt10001_req":
            current_price = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0,
                                                 "현재가").strip()
            stock_code = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0,
                                              "종목코드").strip()
            self.price_data[stock_code] = [[float(current_price), 0]]
            self.price_data120[stock_code] = [[float(current_price), 0]]
            print(self.price_data)
    def _handler_real_data(self, code, real_type, real_data):
        if real_type == "주식체결":
            print(".", end="")
            tick_price = self.ocx.dynamicCall("GetCommRealData(QString, int)", code, 10).strip()
            volume = self.ocx.dynamicCall("GetCommRealData(QString, int)", code, 15)  # 거래량
            self.price_data[code].append([float(tick_price), volume])

            self.sell_time(code, tick_price)
            if len(self.price_data[code]) >= self.purchase_tick:  # 틱 값 조절 부분
                r = self.price_data[code].pop()
                self.price_data120[code].append(r)
                self.price_data[code] = deque(maxlen=121)

            if len(self.price_data120[code]) >= 14:
                rsi = self.calculate_rsi_one(code)
                self.update_rsi_list_widget(code, rsi, tick_price)
                self.price_data120[code].popleft()

    def copy_to_clipboard(self, button, message, msg_box):
        if button.text() == "OK":
            # 클립보드에 메시지 복사
            clipboard = QApplication.clipboard()
            clipboard.setText(message)

    def request_stock_price(self, code):
        self.ocx.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.ocx.dynamicCall("CommRqData(QString, QString, int, QString)", "opt10001_req", "opt10001", 0, "2000")

    def request_real_time_data(self, code):
        self.ocx.dynamicCall("SetRealReg(QString, QString, QString, QString)", "0101", code, "20", "1")

    def process_queue(self):
        if self.stock_queue and not self.ocx.dynamicCall(
                "GetCommDataEx()"):  # Ensure no current request is being processed
            code = self.stock_queue.popleft()
            self.request_stock_price(code)
    def GetConditionLoad(self):
        self.ocx.dynamicCall("GetConditionLoad()")
        # Set the media content
        url = QUrl.fromLocalFile("alert.mp3")  # Replace with the path to your sound file
        self.media_player.setMedia(QMediaContent(url))
        # Play the sound
        self.media_player.play()

    def GetConditionNameList(self):
        data = self.ocx.dynamicCall("GetConditionNameList()")
        conditions = data.split(";")[:-1]
        for condition in conditions:
            index, name = condition.split('^')
            print(index, name)
        self.index = index
        self.name = name

    def SendCondition(self, screen, cond_name, cond_index, search):
        ret = self.ocx.dynamicCall("SendCondition(QString, QString, int, int)", screen, cond_name, cond_index, search)
        print(ret)

    def send_condition(self):
        self.SendCondition("100", self.name, self.index, 1) 


    def display_rsi_history(self, item):
        self.rsiList30today.clear()
        stock_code = item.text()
        history = [entry for entry in self.today_ris if entry[1] == stock_code]
        for entry in history:
            self.rsiList30today.addItem(f"{entry[0]} : {entry[1]} : {entry[2]}")

    def buy_stock(self, account, code, qty, price):
        # SendOrder 매수 함수 호출
        order_result = self.ocx.dynamicCall(
            "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
            [
                "매수주문",  # 요청 이름
                "1000",  # 화면 번호 (4자리 임의 숫자)
                account,  # 계좌번호
                1,  # 주문유형 (1: 신규 매수, 2: 신규 매도)
                code,  # 종목코드
                qty,  # 주문 수량
                price,  # 주문 가격 (0이면 시장가 주문)
                "03",  # 거래구분 (00: 지정가, 03: 시장가)
                ""  # 원주문번호 (정정/취소 주문시 필요, 신규주문시 공백)
            ]
        )
        return order_result

    def sell_stock(self, account, code, qty, price):
        # SendOrder 매수 함수 호출
        order_result = self.ocx.dynamicCall(
            "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
            [
                "매수주문",  # 요청 이름
                "1000",  # 화면 번호 (4자리 임의 숫자)
                account,  # 계좌번호
                2,  # 주문유형 (1: 신규 매수, 2: 신규 매도)
                code,  # 종목코드
                qty,  # 주문 수량
                price,  # 주문 가격 (0이면 시장가 주문)
                "03",  # 거래구분 (00: 지정가, 03: 시장가)
                ""  # 원주문번호 (정정/취소 주문시 필요, 신규주문시 공백)
            ]
        )
        return order_result

    def sell_all_stocks(self):
        # 보유 중인 모든 종목을 일괄 매도하는 함수
        for stock_code, details in list(self.buy_stock_dict.items()):
            qty = details[0]  # 보유 수량
            price = 0  # 시장가로 매도
            print(f"매도 주문: 종목 코드={stock_code}, 수량={qty}")
            self.sell_stock(self.account, stock_code, qty, price)
            del self.buy_stock_dict[stock_code]  # 매도 후 해당 종목 삭제
        print("모든 종목 매도 완료")
    def set_conditon_price(self):
        self.purchase_time_h = int(self.input_field_time.text()[0:2])
        self.purchase_time_m = int(self.input_field_time.text()[3:5])
        self.purchase_price = int(self.input_field_price.text())
        self.purchase_count = int(self.input_field_count.text())
        self.purchase_tick = int(self.input_field_tick.text())
        self.purchase_loss_rate = int(self.input_field_loss_rate.text())
        self.purchase_earn_rate = int(self.input_field_eran_rate.text())
        self.purchase_quantity = int(self.input_field_quantity.text())
        print(self.purchase_time_h, self.purchase_time_m, self.purchase_price, self.purchase_count, self.purchase_tick)
        print(self.purchase_loss_rate, self.purchase_earn_rate)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())