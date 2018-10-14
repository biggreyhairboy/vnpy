# encoding: UTF-8

"""
15分钟的bar，
5，10，20 三种均线窗口
当5，10在20以上的时候可以做多，当10向上穿越20时开多，当5向下穿越10时平仓。可以反复进行以上步骤。
类似的：
当5，10在20以下的时候可以做空，当10向下穿越20时开空，当5向上穿越10时平仓。可以反复进行以上步骤。
"""

from __future__ import division

from vnpy.trader.vtConstant import EMPTY_STRING, EMPTY_FLOAT
from vnpy.trader.app.ctaStrategy.ctaTemplate import (CtaTemplate,
                                                     BarGenerator,
                                                     ArrayManager)


########################################################################
class Bar15TripleMAStrategy(CtaTemplate):
    """双指数均线策略Demo"""
    className = 'Bar15TripleMAStrategy'
    author = u'Patrick'

    # 策略参数
    fastWindow = 75  # 快速均线参数
    midWindow = 150  # 中速均线参数  15 * 10
    slowWindow = 300  # 慢速均线参数  15 * 20
    initDays = 5  # 初始化数据所用的天数

    #todo 到处详细的下单记录，对照K线进行检验
    #todo 均价考虑成交量
    #todo 考虑其他指标的均线
    #todo 实盘均线数据跑起来
    # # 策略参数
    # fastWindow = 10  # 快速均线参数
    # midWindow = 30  # 中速均线参数  15 * 10
    # slowWindow = 101  # 慢速均线参数  15 * 20
    # initDays = 5  # 初始化数据所用的天数

    # 策略变量
    fastMa0 = EMPTY_FLOAT  # 当前最新的快速EMA
    fastMa1 = EMPTY_FLOAT  # 上一根的快速EMA

    midMa0 = EMPTY_FLOAT
    midMa1 = EMPTY_FLOAT

    slowMa0 = EMPTY_FLOAT
    slowMa1 = EMPTY_FLOAT

    # 参数列表，保存了参数的名称
    paramList = ['name',
                 'className',
                 'author',
                 'vtSymbol',
                 'fastWindow',
                 'midWindow',
                 'slowWindow']

    # 变量列表，保存了变量的名称
    varList = ['inited',
               'trading',
               'pos',
               'fastMa0',
               'fastMa1',
               'midMa0',
               'midMa1',
               'slowMa0',
               'slowMa1']

    # 同步列表，保存了需要保存到数据库的变量名称
    syncList = ['pos']

    # ----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(Bar15TripleMAStrategy, self).__init__(ctaEngine, setting)

        self.bg = BarGenerator(self.onBar)
        self.am = ArrayManager()

        # 注意策略类中的可变对象属性（通常是list和dict等），在策略初始化时需要重新创建，
        # 否则会出现多个策略实例之间数据共享的情况，有可能导致潜在的策略逻辑错误风险，
        # 策略类中的这些可变对象属性可以选择不写，全都放在__init__下面，写主要是为了阅读
        # 策略时方便（更多是个编程习惯的选择）

    # ----------------------------------------------------------------------
    def onInit(self):
        """初始化策略（必须由用户继承实现）"""
        self.writeCtaLog(u'15分钟的三均线策略')

        initData = self.loadBar(self.initDays)
        for bar in initData:
            self.onBar(bar)

        self.putEvent()

    # ----------------------------------------------------------------------
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        self.writeCtaLog(u'15分钟的三均线策略启动')
        self.putEvent()

    # ----------------------------------------------------------------------
    def onStop(self):
        """停止策略（必须由用户继承实现）"""
        self.writeCtaLog(u'15分钟的三均线策略停止')
        self.putEvent()

    # ----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送（必须由用户继承实现）"""
        self.bg.updateTick(tick)

    # ----------------------------------------------------------------------
    def onBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        am = self.am
        am.updateBar(bar)
        if not am.inited:
            return

        # 计算均线
        fastMa = am.sma(self.fastWindow, array=True)
        self.fastMa0 = fastMa[-1]
        self.fastMa1 = fastMa[-2]

        midMa = am.sma(self.midWindow, array=True)
        self.midMa0 = midMa[-1]
        self.midMa1 = midMa[-2]

        slowMa = am.sma(self.slowWindow, array=True)
        self.slowMa0 = slowMa[-1]
        self.slowMa1 = slowMa[-2]

        # 判断买卖
        crossOver  = False
        crossBelow = False
        if self.fastMa0 > self.slowMa0 and self.midMa0 > self.slowMa0:
            # crossOver = True
            crossOver = self.midMa0 > self.slowMa0

        if self.fastMa0 < self.slowMa0 and self.midMa0 < self.slowMa0:
            # crossOver = True
            crossBelow = self.fastMa0 < self.midMa0

        # 所有的委托均以K线收盘价委托（这里有一个实盘中无法成交的风险，考虑添加对模拟市价单类型的支持）
        if crossOver:
            # 如果金叉时手头没有持仓，则直接做多
            if self.pos == 0:
                self.buy(bar.close, 1)
        else:
            # 有多头的话平仓
            if self.pos > 0:
                self.sell(bar.close, 1)

        if crossBelow:
            if self.pos == 0:
                self.short(bar.close, 1)
        else:
            # 有空头的话平仓
            if self.pos < 0:
                self.cover(bar.close, 1)

        # 发出状态更新事件
        self.putEvent()

    # ----------------------------------------------------------------------
    def onOrder(self, order):
        """收到委托变化推送（必须由用户继承实现）"""
        # 对于无需做细粒度委托控制的策略，可以忽略onOrder
        pass

    # ----------------------------------------------------------------------
    def onTrade(self, trade):
        """收到成交推送（必须由用户继承实现）"""
        # 对于无需做细粒度委托控制的策略，可以忽略onOrder
        pass

    # ----------------------------------------------------------------------
    def onStopOrder(self, so):
        """停止单推送"""
        pass
