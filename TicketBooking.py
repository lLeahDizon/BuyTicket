import requests
import traceback
import msvcrt
import Station_Parse
import os
from datetime import datetime
from prettytable import PrettyTable
from splinter.browser import Browser
from time import sleep
from urllib3.exceptions import InsecureRequestWarning


# 数据处理+显示
class Trains_demo():
    # 初始化
    def __init__(self, raw_trains, option):
        # headers='车次 车站 时间 历时 商务/特等座 一等座 二等座 高级软卧 软卧 动卧 硬卧 软座 硬座 无座 其他'.split()
        self.headers = '车次 车站 时间 历时 商务/特等座 一等座 二等座 高级软卧 软卧 动卧 硬卧 软座 硬座 无座'.split()
        self.raw_trains = raw_trains
        self.option = option

    # 获取出发和到达站
    def get_from_to_station_name(self, data_list):
        self.from_station_name = data_list[6]
        self.to_station_name = data_list[7]
        self.from_to_station_name = Station_Parse.parse_station().disparse(
            self.from_station_name) + '-->' + Station_Parse.parse_station().disparse(self.to_station_name)
        return self.from_to_station_name

    # 获得出发和到达时间
    def get_start_arrive_time(self, data_list):
        self.start_arrive_time = data_list[8] + '-->' + data_list[9]
        return self.start_arrive_time

    # 解析trains数据(与headers依次对应)
    def parse_trains_data(self, data_list):
        return {
            'trips': data_list[3],
            'from_to_station_name': self.get_from_to_station_name(data_list),
            'start_arrive_time': self.get_start_arrive_time(data_list),
            'duration': data_list[10],
            'business_premier_seat': data_list[32] or '--',
            'first_class_seat': data_list[31] or '--',
            'second_class_seat': data_list[30] or '--',
            'senior_soft_sleep': data_list[21] or '--',
            'soft_sleep': data_list[23] or '--',
            'move_sleep': data_list[33] or '--',
            'hard_sleep': data_list[28] or '--',
            'soft_seat': data_list[24] or '--',
            'hard_seat': data_list[29] or '--',
            'no_seat': data_list[26] or '--',
        }

    # 判断是否需要显示
    def need_show(self, data_list):
        trips = data_list[3]
        initial = trips[0].lower()
        if 'a' in self.option:
            return trips
        else:
            return (initial in self.option)

    # 数据显示
    def show_train_data(self):
        self.demo = PrettyTable()
        self.demo._set_field_names(self.headers)
        for self.train in self.raw_trains:
            self.data_list = self.train.split('|')
            if self.need_show(self.data_list):
                self.values_row = []
                self.parsed_train_data = self.parse_trains_data(self.data_list)
                self.values_row.append(self.parsed_train_data['trips'])
                self.values_row.append(self.parsed_train_data['from_to_station_name'])
                self.values_row.append(self.parsed_train_data['start_arrive_time'])
                self.values_row.append(self.parsed_train_data['duration'])
                self.values_row.append(self.parsed_train_data['business_premier_seat'])
                self.values_row.append(self.parsed_train_data['first_class_seat'])
                self.values_row.append(self.parsed_train_data['second_class_seat'])
                self.values_row.append(self.parsed_train_data['senior_soft_sleep'])
                self.values_row.append(self.parsed_train_data['soft_sleep'])
                self.values_row.append(self.parsed_train_data['move_sleep'])
                self.values_row.append(self.parsed_train_data['hard_sleep'])
                self.values_row.append(self.parsed_train_data['soft_seat'])
                self.values_row.append(self.parsed_train_data['hard_seat'])
                self.values_row.append(self.parsed_train_data['no_seat'])
                self.demo.add_row(self.values_row)
        print(self.demo)


# 车票查询
class Query_Ticket(object):
    # 初始化
    def __init__(self, ticket_option, from_station, to_station, date):
        # 请求地址的模板
        self.url_template = (
            'https://kyfw.12306.cn/otn/leftTicket/query{}?leftTicketDTO.'
            'train_date={}&'
            'leftTicketDTO.from_station={}&'
            'leftTicketDTO.to_station={}&'
            'purpose_codes=ADULT'
        )
        self.ticket_option = ticket_option
        self.from_station = from_station
        self.to_station = to_station
        self.date = date

    # 获得请求地址
    def request_url1(self):
        return (self.url_template.format('A', self.date, self.from_station, self.to_station))

    def request_url2(self):
        return (self.url_template.format('Z', self.date, self.from_station, self.to_station))

    # 查询车票
    def query(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'}
        self.res = requests.get(self.request_url1(), headers=self.headers, verify=False)
        try:
            self.trains = self.res.json()['data']['result']
        except:
            self.res = requests.get(self.request_url2(), headers=self.headers, verify=False)
            self.trains = self.res.json()['data']['result']
        Trains_demo(self.trains, self.ticket_option).show_train_data()


# 抢票
class Buy_Tickets(object):
    # 初始化
    def __init__(self, username, passwd, order, passengers, dtime, starts, ends):
        self.username = username
        self.passwd = passwd
        # 车次，0代表所有车次
        self.order = order
        # 乘客名
        self.passengers = passengers
        # 起始地和终点
        self.starts = starts
        self.ends = ends
        # 日期
        self.dtime = dtime
        self.login_url = 'https://kyfw.12306.cn/otn/login/init'
        self.initMy_url = 'https://kyfw.12306.cn/otn/view/index.html'
        self.ticket_url = 'https://kyfw.12306.cn/otn/leftTicket/init'
        self.driver_name = 'chrome'
        self.executable_path = 'C:\\Users\\Lemon\\AppData\\Local\\Programs\\Python\\Python37\\Scripts\\chromedriver.exe'

    # 登录
    def login(self):
        self.driver.visit(self.login_url)
        self.driver.fill('loginUserDTO.user_name', self.username)
        # sleep(1)
        self.driver.fill('userDTO.password', self.passwd)
        # sleep(1)
        print('请输入验证码...')
        while True:
            if self.driver.url != self.initMy_url:
                sleep(1)
            else:
                break

    # 买票
    def start_buy(self):
        self.driver = Browser(driver_name=self.driver_name, executable_path=self.executable_path)
        self.driver.driver.set_window_size(700, 500)
        self.login()
        self.driver.visit(self.ticket_url)
        try:
            print('开始购票...')
            # 加载查询信息
            self.driver.cookies.add({'_jc_save_fromStation': self.starts})
            self.driver.cookies.add({'_jc_save_toStation': self.ends})
            self.driver.cookies.add({'_jc_save_fromDate': self.dtime})
            self.driver.reload()
            count = 0
            if self.order != '0':
                self.order = int(self.order)
                while self.driver.url == self.ticket_url:
                    self.driver.find_by_text('查询').click()
                    count += 1
                    print('第%d次点击查询...' % count)
                    try:
                        self.driver.find_by_text('预订')[self.order - 1].click()
                        sleep(1.5)
                    except Exception as e:
                        print(e)
                        print('预订失败...')
                        continue
            else:
                while self.driver.url == self.ticket_url:
                    self.driver.find_by_text('查询').click()
                    count += 1
                    print('第%d次点击查询...' % count)
                    try:
                        for i in self.driver.find_by_text('预订'):
                            i.click()
                            sleep(1)
                    except Exception as e:
                        print(e)
                        print('预订失败...')
                        continue
            print('开始预订...')
            sleep(1)
            print('开始选择用户...')
            for p in self.passengers:
                self.driver.find_by_text(p).last.click()
                sleep(0.5)
                if p[-1] == ')':
                    self.driver.find_by_id('dialog_xsertcj_ok').click()
            print('提交订单...')
            sleep(1)
            self.driver.find_by_id('submitOrder_id').click()
            sleep(2)
            print('确认选座...')
            self.driver.find_by_id('qr_submit_id').click()
            print('预订成功...')
            content = '恭喜您抢票成功，请在半小时内完成支付！！！'
            _ = os.system('mshta vbscript:createobject("sapi.spvoice").speak("%s")(window.close)' % content)
        except Exception as e:
            print(e)


# 主程序
class main():
    def __init__(self):
        print('\n')
        print('*' * 50)

        print('查询车票余量请输入:query\n抢票请输入:buy\n退出请输入:exit')
        print('*' * 50)
        while True:
            self.select = input('query or buy or exit：')
            # 查询功能
            if self.select == 'query':
                print('选项(可多选)：\na-全部\ng-高铁\nd-动车\nk-快速\nt-特快\nz-直达')
                self.ticket_option = input('请选择查询的车次类型：')
                self.from_station = input('请输入出发地：')
                self.to_station = input('请输入目的地：')

                print('日期输入格式year-month-day，如2019-01-01')
                self.date = input('请输入查询日期：')
                self.from_station = Station_Parse.parse_station().parse(self.from_station)
                self.to_station = Station_Parse.parse_station().parse(self.to_station)
                if self.from_station is None or self.to_station is None:
                    print('请输入有效的车站名...')
                    continue
                try:
                    if datetime.strptime(self.date, '%Y-%m-%d') < datetime.now():
                        raise ValueError
                except:
                    print('请输入有效日期...')
                    continue
                try:
                    Query_Ticket(self.ticket_option, self.from_station, self.to_station, self.date).query()
                except Exception as e:
                    print(e)
                    print('something wrong!')
                    continue
            # 抢票功能
            elif self.select == 'buy':
                self.username = input('请输入用户名：\n')
                print('请输入密码：')
                try:
                    self.password = self.pwd_input().strip()
                except:
                    self.password = input('版本问题密码明文输入：')
                print('\n输入说明：数字0代表任意班次，数字1代表全部车次查询结果的第一个，数字2代表第二个以此类推。')
                self.order = input('请输入班次：\n')

                print('请逐个输入需要购票的乘客名，输入完成后请输入finished.')

                print('普通票输入例如：张三，学生票输入例如：张三(学生)')
                self.passengers = []
                while True:
                    self.passenger = input('name or finished.')
                    if self.passenger == 'finished':
                        break
                    else:
                        self.passengers.append(self.passenger)
                self.starts = input('请输入出发地：')
                self.ends = input('请输入目的地：')

                print('日期输入格式year-month-day，如2019-01-01')
                self.dtime = input('请输入抢票日期：')
                try:
                    self.starts = self.Get_Cookies()[0] + '%2C' + Station_Parse.parse_station().parse(self.starts)
                    self.ends = self.Get_Cookies()[1] + '%2C' + Station_Parse.parse_station().parse(self.ends)
                except:
                    print('请输入有效车站名...')
                    continue
                try:
                    if datetime.strptime(self.dtime, '%Y-%m-%d') < datetime.now():
                        raise ValueError
                except:
                    print('请输入有效日期...')
                    continue
                try:
                    Buy_Tickets(self.username, self.password, self.order, self.passengers, self.dtime, self.starts,
                                self.ends).start_buy()
                except:
                    print('发生了不可描述的错误，可能与你的非法输入(如班次)有关')
            # 退出功能
            elif self.select == 'exit':
                break
            else:
                print('输入内容错误，请重新输入！！！')

    # 密码输入，cmd命令行下运行显示*号
    def pwd_input(self):
        self.chars = []
        while True:
            self.newChar = msvcrt.getch().decode(encoding='utf-8')
            # 回车键，输入结束
            if self.newChar in "\r\n":
                break
            # 退格键
            elif self.newChar == '\b':
                if self.chars:
                    del self.chars[-1]
                    # 光标回退一格
                    msvcrt.putch("\b".encode(encoding='utf-8'))
                    # 输出一个空格覆盖原来的星号
                    msvcrt.putch(" ".encode(encoding='utf-8'))
                    # 光标退回一格准备接受新的输入
                    msvcrt.putch("\b".encode(encoding='utf-8'))
            else:
                self.chars.append(self.newChar)
                msvcrt.putch("*".encode(encoding='utf-8'))
        return ("".join(self.chars))

    # 中文转Unicode
    def to_unicode(self, string):
        self.uni = ''
        for s in string:
            self.uni += hex(ord(s)).upper().replace('0X', '%u')
        return self.uni

    # 将起始地和终点转化为相应的Cookies
    def Get_Cookies(self):
        return [self.to_unicode(self.starts), self.to_unicode(self.ends)]

    # 验证码
    def verification_code(self):
        self.vcode_position = ['51,44', '113,44', '176,44', '275,51', '261,129', '181,111', '38,116', '93,115']
        position = input('请输入验证码的位置')
        data_vcode_position = []
        for point in position:
            data_vcode_position.append(self.vcode_position[int(point)])
        data_point = ','.join(data_vcode_position)


if __name__ == '__main__':
    main()
