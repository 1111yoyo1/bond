# -*- coding: utf-8 -*-
import urllib2
import httplib
#import numpy as np
import traceback
import re
import sys
import json
import time
import socket
import random
#import pprint


def ReadUrl(url):
    try:
        content = urllib2.urlopen(url).readline()
    except httplib.IncompleteRead as e:
        content = e.partial
        print content
    except socket.error, ex:
        print "Connection error"
        content = None
    except httplib.BadStatusLine as err:
        print "Bad Status Line"
        content = None
    except Exception, e:
        print "Common error, fail to access to %s" % url
        content = None
    return content


def Mail(subject, content):
    import base64
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    mail_server = "smtp.partner.outlook.cn"
    mail_port = 587
    mail_user = "youyou.xu@memblaze.com"
    mail_pass = r'TWVtMjAxODAx'
    to_list = ['<youyou.xu@memblaze.com>', '<k-raik@163.com>']
    s = smtplib.SMTP(mail_server, mail_port)
    s.starttls()
    s.login(mail_user, base64.b64decode(mail_pass))
    msgRoot = MIMEMultipart('related')
    msgRoot['Subject'] = subject
    msg_alternative = MIMEMultipart('alternative')
    msg_alternative.attach(MIMEText(content, 'plain', 'utf-8'))
    msgRoot.attach(msg_alternative)
    s.sendmail(mail_user, to_list, msgRoot.as_string())
    s.close()


class BondObj(object):
    def __init__(self, bondId, market=None, stockId=None, conStockRate=None):
        self.bondId = bondId
        self.market = market
        self.stockId = stockId
        self.conStockRate = conStockRate
        #bondFivePriceUrl = "http://sqt.gtimg.cn/utf8/q=%s%s" % (self.market, self.bondId)
        bondFivePriceUrl = "http://sqt.gtimg.cn/q=%s%s" % (self.market, self.bondId)
        self.bondJsonWebContent = ReadUrl(bondFivePriceUrl)

        #stockFivePriceUrl = "http://sqt.gtimg.cn/utf8/q=%s" % (self.stockId)
        stockFivePriceUrl = "http://qt.gtimg.cn/q=%s" % (self.stockId)
        self.stockJsonWebContent = ReadUrl(stockFivePriceUrl)

    def ToString(self):
        self.output = "Bond Name: %s\n" % unicode(self.bondChineseName, "cp936")
        self.output += "Bond Id: %s\n" % self.bondId
        self.output += "Market: %s\n" % self.market
        self.output += "Stock Name: %s\n" % unicode(self.stockChineseName, "cp936")
        #self.output += unicode(self.stockChineseName, "ISO-8859-1")
        self.output += "Stock Id: %s\n" % self.stockId
        self.output += "stock Converting Rate: %s\n" % self.conStockRate
        if len(self.bondPricesSell) != 0 and len(self.bondPricesBuy) != 0:
            self.output += "Bond Sell Prices: "
            self.output += " ".join(self.bondPricesSell)
            self.output += "\n"
            self.output += "Bond Buy Prices: "
            self.output += " ".join(self.bondPricesBuy)
            self.output += "\n"
            self.output += "Stock Sell prices: "
            self.output += " ".join(self.stockPricesSell)
            self.output += "\n"
            self.output += "Stock Buy prices: "
            self.output += " ".join(self.stockPricesBuy)
            self.output += "\n"
            self.output += "Convert Price Rate: %f\n" % self.overPriceRate
        return self.output

    def Display(self):
        print self.ToString()

    @property
    def bondPricesSell(self):
        bondPricesSell = []
        # bond first 5 price to sell
        if len(self.bondJsonWebContent.split("~")) != 1:  # it's possible to get 'v_pv_none_match="1";\n'
            base = 9
            for i in xrange(0, 9, 2):
                bondPricesSell.append(self.bondJsonWebContent.split("~")[base + i])

        return bondPricesSell

    @property
    def bondPricesBuy(self):
        bondPricesBuy = []
        # bond first 5 price to buy
        if len(self.bondJsonWebContent.split("~")) != 1:  # it's possible to get 'v_pv_none_match="1";\n'
            base = 19
            for i in xrange(0, 9, 2):
                bondPricesBuy.append(self.bondJsonWebContent.split("~")[base + i])
        return bondPricesBuy

    @property
    def bondChineseName(self):
        return self.bondJsonWebContent.split("~")[1]
    
    @property
    def stockChineseName(self):
        return self.stockJsonWebContent.split("~")[1]
    
    @property
    def stockPricesSell(self):
        stockPricesSell = []
        # stock first 5 price to buy
        base = 9
        for i in xrange(0, 9, 2):
            stockPricesSell.append(self.stockJsonWebContent.split("~")[base + i])
        return stockPricesSell

    @property
    def stockPricesBuy(self):
        stockPricesBuy = []
        # stock first 5 price to sell
        base = 19
        for i in xrange(0, 9, 2):
            stockPricesBuy.append(self.stockJsonWebContent.split("~")[base + i])
        return stockPricesBuy

    @property
    def overPriceRate(self):
        try:
            overPriceRate = float(self.bondPricesBuy[0]) / float(float(self.stockPricesSell[0]) * 100 / float(self.conStockRate)) - 1
        except ZeroDivisionError:
            print "hit ZeroDivisionError"
            overPriceRate = -1
        return overPriceRate

    def IsMatch(self):
        if self.overPriceRate < -0.01 and self.overPriceRate > -1:
            return True
        else:
            return False

    def IsValid(self):
        #try:
        self.ToString()
        if (
            self.bondJsonWebContent is None or
            self.stockJsonWebContent is None or
            len(self.bondPricesBuy) == 0 or
            len(self.bondPricesSell) == 0
        ):
            return False
        return True
        # except:
        #     return False


def InTradingTime():
    InTradingTime = False
    parsed = time.strptime(time.ctime())
    if parsed.tm_hour > 8 and parsed.tm_hour < 15:
        InTradingTime = True
    else:
        print "not in trading time, current time\n", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    return InTradingTime


def main():

    ignoreList = ["127009", "113020", "110050", "110040", "128020"]

    timeLast = time.time()
    timeItvl = 60
    delay = 1

    while True:
        if not InTradingTime():
            delay = 60
        else:
            delay = 1
            localtime = time.strftime('%Y-%m-%d', time.localtime(time.time()))
            filename = "bondOuput_%s.txt" % localtime
            monitorList = []
            with open("bondwatchList.txt", "r") as f:
                monitorList = map(lambda x: x.strip(), f.readlines())
            #print monitorList

            try:
                bondToStockUrl = "https://www.jisilu.cn/data/cbnew/cb_list/"
                #originJsonWebContent = urllib2.urlopen(bondToStockUrl).readline()
                originJsonWebContent = ReadUrl(bondToStockUrl)
                if originJsonWebContent is None:
                    continue
                # try:
                #     originJsonWebContent = urllib2.urlopen(bondToStockUrl).readline()
                # except httplib.IncompleteRead as e:
                #     originJsonWebContent = e.partial
                #     print originJsonWebContent
                # except socket.error, ex:
                #     print "Connection error:"
                # except httplib.BadStatusLine as err:
                #     print "Bad Status Line"
                # except Exception, e:
                #     print "Common error, fail to access to %s" % bondToStockUrl

                originalDict = json.loads(originJsonWebContent)
                pageList = originalDict.get("rows", [])

                bondObjList = []
                for page in pageList:
                    bond_idContentList = page.get("cell", [])
                    bondId = bond_idContentList.get("bond_id", [])
                    market = bond_idContentList.get("market", [])
                    stockId = bond_idContentList.get("stock_id", [])
                    if len(market) == 0:
                        market = stockId[0:2]
                    conStockRate = bond_idContentList.get("convert_price", [])
                    bondObj = BondObj(bondId, market=market, stockId=stockId, conStockRate=conStockRate)
                    if bondObj.IsValid():
                        bondObjList.append(bondObj)
            except:
                print "Issues occurred when accessing website or generating obj..., retry in 1 minutes"
                print traceback.format_exc()
                time.sleep(60)
                continue

            matched = []
            with open(filename, "a") as f:
                print "total bond: %s " % len(bondObjList)
                f.write("total bond: %s " % len(bondObjList))
                localtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
                f.write(localtime + "\n")
                for bondObj in bondObjList:
                    print "processing bond %s" % bondObj.bondId
                    bondObj.Display()
                    if bondObj.IsMatch():
                        if bondObj.bondId in monitorList:
                            matched.append(bondObj)
                            f.write(bondObj.output.encode("utf-8"))
                            f.write("\n")
                            #Mail("get exchangable bond %s\n" % bondObj.bondId, bondObj.output)
                            if bondObj.bondId not in ignoreList:
                                print "get exchangable bond %s" % bondObj.bondId
                                f.write("get exchangable bond %s\n" % bondObj.bondId)
                                timeStart = time.time()
                                if timeStart - timeLast >= timeItvl:
                                    timeLast = timeStart
                                    Mail("get exchangable bond %s\n" % bondObj.bondId, bondObj.output)
                f.write("\n")

                print "matched bond: %s " % len(matched)
                f.write("matched bond: %s \n" % len(matched))
        time.sleep(delay)

if __name__ == "__main__":
    main()