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
import logging
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
    to_list = ['<youyou.xu@memblaze.com>']
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


class LogBuilder(object):
    """ build  a logger"""

    _singleton = None

    def __new__(cls, *args,**kwargs):
        if not cls._singleton:
            cls._singleton = super(LogBuilder, cls).__new__(cls, *args, **kwargs)
        else:
            def initPass(self,*args,**kwargs):
                pass
            cls.__init__ = initPass
        return cls._singleton

    def __init__(self, filename):
        self.fileName = filename
        self.logLevel = logging.INFO
        self.logFormatter = '%(asctime)s %(levelname)s %(message)s'
        self.setup()

    def setup(self):
        logger = logging.getLogger(__name__)
        logger.setLevel(self.logLevel)
        formatter = logging.Formatter(self.logFormatter)
        hdlr = logging.FileHandler(self.fileName)
        hdlr.setFormatter(formatter)
        logger.addHandler(hdlr)

        hdlr2 = logging.StreamHandler(sys.stdout)
        hdlr2.setFormatter(formatter)
        logger.addHandler(hdlr2)
        self.mapLogger(logger)
        self.logger = logger
        return logger

    def mapLogger(self, logger):
        """map the logger to support legacy code"""
        logger.Debug = logger.debug
        logger.Info = logger.info
        logger.Warning = logger.warning
        logger.Error = logger.error
        logger.Critical = logger.critical


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

    def SimpleInfoToString(self):
        self.output = "Bond Id: %s, " % self.bondId
        self.output += "Bond Name: %s, " % unicode(self.bondChineseName, "cp936")
        self.output += "Convert Price Rate: %f" % self.overPriceRate
        return self.output

    def Display(self, logger=None):
        if logger is None:
            print self.ToString()
        else:
            logger.Info(self.ToString())

    def DisplaySimple(self, logger=None):
        if logger is None:
            print self.SimpleInfoToString()
        else:
            logger.Info(self.SimpleInfoToString())

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
        inTradingTime = InTradingTime()
        if not inTradingTime:
            delay = 60
        else:
            delay = 1
        print "sleep %d seconds" % delay
        if inTradingTime:
            targetBond = sys.argv[1] if len(sys.argv) == 2 else ""
            localtime = time.strftime('%Y-%m-%d', time.localtime(time.time()))
            filename = "bondOuput%s_%s_2.txt" % (targetBond, localtime)
            log = LogBuilder(filename)
            logger = log.logger

            monitorList = []
            with open("bondwatchList.txt", "r") as f:
                monitorList = map(lambda x: x.strip(), f.readlines())

                try:
                    bondToStockUrl = "https://www.jisilu.cn/data/cbnew/cb_list/"
                    originJsonWebContent = ReadUrl(bondToStockUrl)
                    if originJsonWebContent is None:
                        continue

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
                        if len(sys.argv) == 2:
                            if targetBond == bondId:
                                bondObjList.append(bondObj)
                        else:
                            if bondObj.IsValid():
                                bondObjList.append(bondObj)
                except:
                    logger.Info("Issues occurred when accessing website or generating obj..., retry in 1 minutes")
                    logger.Info(traceback.format_exc())
                    time.sleep(60)
                    continue

                matched = []
                with open(filename, "a") as f:
                    if len(sys.argv) == 2:
                        for bondObj in bondObjList:
                            bondObj.DisplaySimple(logger)
                    else:
                        logger.Info("total bond: %s " % len(bondObjList))
                        localtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
                        logger.Info(localtime + "\n")
                        for bondObj in bondObjList:
                            logger.Info("processing bond %s" % bondObj.bondId)
                            bondObj.Display()
                            if bondObj.IsMatch():
                                if bondObj.bondId in monitorList:
                                    matched.append(bondObj)
                                    logger.Info(bondObj.ToString())
                                    if bondObj.bondId not in ignoreList:
                                        logger.Info("get exchangable bond %s\n" % bondObj.bondId)
                                        timeStart = time.time()
                                        if timeStart - timeLast >= timeItvl:
                                            timeLast = timeStart
                                        Mail("get exchangable bond %s\n" % bondObj.bondId, bondObj.output)
                        logger.Info("matched bond: %s" % len(matched))
        time.sleep(delay)

if __name__ == "__main__":
    main()