import numpy as np
from pytz import timezone
from collections import deque

# Features:
# (TODO)
    # 1. ADD SPY/QQQ trend
    # 2. Consider firing signal after crossing signal
    # 4. OR30
    # 5. Optimize Short performance
    # 6. Pivot point
    # 7. Better burst/ttm breakout signal with 5 day high/low (currently suppress too much till 1.005 * high at which
                                                               # point volume could be down already)
# v2.6
    # 1. Smarter KD signal, not limit to exactly monment we see cross,
        
# v2.5
    # 1. Change KD signal and more flexible threashold integrated with volume/price move
    # 2. Small Volumn rate update (remove min * 60 > average_vol)
    # 3. BB resist/support
    # 4. Support level move to 1% - 0.75% for 5 days line
    # 5. Optimized 2/5 signal, handle cases when they are close or even the same
    
# v2.4
    # 1. Enhance log
    # 2. KD parameter from 12,3,3 -> 9,3,3
    # 3. TTM breakout volumn/price filter 
    # 4. Burst filter with more volumn filter
    # 5. Open suppression for TTM and burst signal
    # 6. Add double smooth back for trend-discovery
    # 7. Bias on breaout 0.9925 - 1.005 or Narrow down the range?
    # 8. Add price-spike to KD signal triggering like:
            # and (context.volumn_signal[stock]  <> "Large Volumn"
            # or context.price_move_signal[stock] == "Spike Down")
    
# v2.3
    # 1. SMA -> EMA for trend which is not sensitive
    # 2. Openning volumn signal optimization
    # 3. TTM variable change to 2 and 3 to avoid false positive
    # 4. KD threshold updated.
    # 5. (TODO) Add opening price resist/support
    
# v2.2
    # 1. Optimization on parameters
    # 2. Bug fix
    # 3. Enhanced log

# v2.1
    # 1. TTM optimization which signal support/resist
    # 2. Price/Volumn breakout optimiation which consider support/resist
    # 3. Resist/Support signal suppression, expect see price move before firing signal

# v2.0
    # 1. More optimization on 1,2,5 day support/resist level, reduce notification
    # 2. Refactor logging
    
# v1.9
    # 1. 1,2,5 days Support/Resist level
    # 2. Optimize trend and kd parameter

# v1.8
    # 1. Add Vol filter in TTM squeeze
    # 2. Add price/volumn spike combination
    
# v1.7
    # 1. Add price spike signal
    # 2. Add TTM squeeze
    
# v1.6
    # 1. Add two day breakout
    # 2. Add support/resist notification
    # 3. Optimize volumn indicator

# v1.5
    # 1. Volume signal
    # 2. Break signal fixed

# v1.4
    # 1. Add breakout discovery
    # 2. Add 30-min kd for big reversal
    # 3. Update to EMA for smooth curve

one_min_natr = ta.NATR(timeperiod=15)
five_min_kd = ta.STOCH(fastk_period=45,slowk_period=15,slowk_matype=1,slowd_period=15,slowd_matype=1)
ten_min_kd = ta.STOCH(fastk_period=90,slowk_period=30,slowk_matype=1,slowd_period=30,slowd_matype=1)
one_hour_kd = ta.STOCH(fastk_period=540,slowk_period=180,slowk_matype=1,slowd_period=180,slowd_matype=1)
five_min_sma = ta.EMA(timeperiod=100)
five_min_atr = ta.ATR(timeperiod=100)
five_min_bb = ta.BBANDS(timeperiod=100, nbdevup=2.2, nbdevdn=2.2, matype=1)
two_hour_ma = ta.EMA(timeperiod=105)

def initialize(context):
    context.stocks = [
                      # sid(24), # AAPL
                      # sid(16841), # AMZN
                      # sid(45978), # ATHM
                      # sid(41667), # AWAY
                      # sid(3806), # BIIB
                      # sid(39479), # BIB
                      # sid(17991), # CAR
                      # sid(28016), # CMG
                      # sid(25729), # CTRP
                      # sid(40555), # DANG
                      # sid(44747), # DATA
                      # sid(12959), # DDD
                      # sid(27543), # EXPE
                      # sid(37049), # FAS
                      # sid(42950), # FB
                      # sid(45451), # FEYE
                      # sid(32902), # FSLR
                      # sid(45452), # FUEL
                      # sid(3212), # GILD
                      # sid(9736), # GMCR
                      # sid(42270), # KORS
                      # # sid(46979), # JD
                      # sid(39635), # JKS
                      # # sid(46928), # JMEI
                      # sid(41451), # LNKD
                      # sid(44738), # MKTO
                      # sid(23709), # NFLX
                      # sid(46002), # NMBL
                      # sid(43202), # PANW
                      # sid(19917), # PCLN
                      # sid(41149), # QIHU
                      # sid(45781), # QUNR
                      # sid(41498), # SAVE
                      # sid(43721), # SCTY
                      # sid(40129), # SFUN
                      # sid(42815), # SPLK
                      # sid(38533), # SPXL
                      # sid(12107), # SSYS
                      # sid(37515), # TNA
                      # sid(39214), # TQQQ
                      # sid(42230), # TRIP
                      # sid(39840), # TSLA
                      # sid(45815), # TWTR
                      # sid(27822), # UA
                      # sid(42027), # UBNT
                      # sid(42707), # VIPS
                      # sid(43510), # WDAY
                      # sid(45769), # WUB
                      # sid(27822), # UA
                      # sid(24124), # WYNN
                      sid(42596), # YELP
                      # sid(40562), # YOKU
                      # sid(43647), # YY
                      # sid(41730), # Z
                      # sid(45866), # ZU
                      # 
                      # # Optional
                      # sid(40392), # NOAH
                      # sid(46779), # WB
                      # sid(45902), # WBAI
                      # sid(46876), # TOUR
                      
                      # # Taojin
                      # sid(46680), # TEDU
                      # sid(45797), # CUDA
                      # sid(36628), # GTAT
                      ]
    
    context.brekout_debug_mode = False
    context.volumn_debug_mode = False
    context.kd_debug_model = False
    context.ttm_debug_mode = False
    context.burst_deug_mode = False
    context.price_move_debug_mode = False
    context.trend_debug_mode = False
    
    context.open_suppression = False
    context.warm_up = True
    context.five_min_kd = {}
    context.ten_min_kd = {}
    context.one_hour_kd = {}
    context.five_min_kd_notification = False;
    
    
    context.gap = {}
    context.previous_close = {}
    context.today_open = {}
    context.slope = {}
    context.trend = {}
    context.five_day_range = {}
    context.two_day_range = {}
    context.daily_range = {}
    context.price_history = {}
    context.six_min_vol = {}
    context.thirty_min_vol = {}
    context.six_min_average_vol = {}
    context.volumn_rate = {}
    context.ma_history = {}
    context.volumn_signal = {}
    context.burst_signal = {}
    context.close_price_breakout_signal = {}
    context.close_price_support_signal = {}
    context.close_price_resist_signal = {}
    context.open_price_breakout_signal = {}
    context.open_price_support_signal = {}
    context.open_price_resist_signal = {}
    context.daily_notification = {}
    context.daily_breakout_signal = {}
    context.daily_support_signal = {}
    context.daily_resist_signal = {}
    context.two_day_notification = {}
    context.two_day_breakout_signal = {}
    context.two_day_support_signal = {}
    context.two_day_resist_signal = {}
    context.five_day_notification = {}
    context.five_day_breakout_signal = {}
    context.five_day_support_signal = {}
    context.five_day_resist_signal = {}
    context.bb_support_signal = {}
    context.bb_resist_signal = {}
    context.bb_percent = {}
    context.price_move_signal = {}
    context.squeeze_signal = {}
    for stock in context.stocks:
        context.gap[stock] = False;
        context.previous_close[stock] = 0
        context.today_open[stock] = 0
        context.trend[stock] = None
        context.volumn_signal[stock] = None
        context.burst_signal[stock] = False
        context.close_price_breakout_signal[stock] = None;
        context.close_price_support_signal[stock] = False;
        context.close_price_resist_signal[stock] = False;
        context.open_price_breakout_signal[stock] = None;
        context.open_price_support_signal[stock] = False;
        context.open_price_resist_signal[stock] = False;
        context.daily_notification[stock] = [False, False, False]
        context.daily_breakout_signal[stock] = None;
        context.daily_support_signal[stock] = False
        context.daily_resist_signal[stock] = False
        context.two_day_notification[stock] = [False, False, False]
        context.two_day_breakout_signal[stock] = None;
        context.two_day_support_signal[stock] = False
        context.two_day_resist_signal[stock] = False
        context.five_day_notification[stock] = [False, False, False]
        context.five_day_breakout_signal[stock] = None;
        context.five_day_support_signal[stock] = False
        context.five_day_resist_signal[stock] = False
        context.bb_support_signal[stock] = False
        context.bb_resist_signal[stock] = False
        context.bb_percent[stock] = 0.5
        context.price_move_signal[stock] = None
        context.squeeze_signal[stock] = False
        context.volumn_rate[stock] = 0.2
        context.ma_history[stock] = deque([], 5);
        context.five_day_range[stock] = [99999, 0]
        context.two_day_range[stock] = [99999, 0]
        context.daily_range[stock] = [99999, 0]
        context.five_min_kd[stock] = [50, 50]
        context.ten_min_kd[stock] = [50, 50]
        context.one_hour_kd[stock] = [50, 50]
        context.slope[stock] = None
        context.six_min_vol[stock] = deque([], 6)
        context.thirty_min_vol[stock] = deque([], 30)
        context.six_min_average_vol[stock] = None
        context.price_history[stock] = deque([], 12)  
        
def reset_context(context, data, newDay):
    five_day_low_history = history(bar_count=5, frequency='1d', field='low')
    five_day_high_history = history(bar_count=5, frequency='1d', field='high')
    five_day_volumn_history = history(bar_count=6, frequency='1d', field='volume')
    two_day_low_history = history(bar_count=2, frequency='1d', field='low')
    two_day_high_history = history(bar_count=2, frequency='1d', field='high')

    # Smart Average
    for stock in context.stocks:
        if 2.8 * max(five_day_volumn_history[stock][0 : 5]) > sum(five_day_volumn_history[stock][0 : 5]):
            context.six_min_average_vol[stock] = (sum(five_day_volumn_history[stock][0 : 5])
                                                  - max(five_day_volumn_history[stock][0 : 5]))/260
        else:
            context.six_min_average_vol[stock] = sum(five_day_volumn_history[stock][0 : 5])/325
    
    if newDay:
        for stock in context.stocks:
            context.five_day_range[stock] = [min(five_day_low_history[stock][0 : 4]),
                                             max(five_day_high_history[stock][0 : 4])]
            context.two_day_range[stock] = [two_day_low_history[stock][0],
                                             two_day_high_history[stock][0]]
            context.daily_range[stock] = [99999, 0]
            
            if len(context.price_history[stock]) == 0:
                context.price_history[stock] = deque([data[stock].price] * 12, 12)
                
            # Gap up, reset price history
            if (data[stock].price > 1.015 * list(context.price_history[stock])[-1]
                or data[stock].price < 0.985 * list(context.price_history[stock])[-1]):
                context.price_history[stock] = deque([data[stock].price] * 12, 12)
                context.gap[stock] = True;
              
            context.previous_close[stock] = history(bar_count=2, frequency='1d', field='close_price')[stock][0];
            context.today_open[stock] = data[stock].open_price;
            context.burst_signal[stock] = False
            context.daily_notification[stock] = [False, False, False]
            context.daily_breakout_signal[stock] = None
            context.daily_support_signal[stock] = False
            context.daily_resist_signal[stock] = False
            context.two_day_notification[stock] = [False, False, False]
            context.two_day_breakout_signal[stock] = None
            context.two_day_support_signal[stock] = False
            context.two_day_resist_signal[stock] = False
            context.five_day_notification[stock] = [False, False, False]
            context.five_day_breakout_signal[stock] = None
            context.five_day_support_signal[stock] = False
            context.five_day_resist_signal[stock] = False
            context.six_min_vol[stock] = deque([], 6)
            context.thirty_min_vol[stock] = deque([], 30)
            
            
    else:
        for stock in context.stocks:
            context.five_day_range[stock] = [min(five_day_low_history[stock][0 : 4]),
                                             max(five_day_high_history[stock][0 : 4])]
            context.two_day_range[stock] = [two_day_low_history[stock][0],
                                             two_day_high_history[stock][0]]
            context.daily_range[stock] = [two_day_low_history[stock][1], two_day_high_history[stock][1]]
            context.daily_breakout_signal[stock] = None
            context.two_day_breakout_signal[stock] = None
            context.five_day_breakout_signal[stock] = None
            context.price_history[stock] = deque([data[stock].price] * 12, 12)
        
def find_signal(context, data):
    moving_average = two_hour_ma(data)
    five_min_sma_data = five_min_sma(data)
    five_min_bb_data = five_min_bb(data)
    five_min_atr_data = five_min_atr(data)
    
    for stock in context.stocks:
        (context.price_history[stock]).append(data[stock].price)
        (context.thirty_min_vol[stock]).append(data[stock].volume)
        (context.six_min_vol[stock]).append(data[stock].volume)
               
        # Find price move signal, (TODO) using data[stock].high/low
        if (data[stock].price > 1.004 * min(context.price_history[stock])
            and data[stock].price >= 0.9975 * max(list(context.price_history[stock])[6:])):
            context.price_move_signal[stock] = "Move Up"
            if (data[stock].price > 1.01 * min(context.price_history[stock])
                and data[stock].price >= 0.998 * max(context.price_history[stock])):
                context.price_move_signal[stock] = "Spike Up"
            
        elif (data[stock].price < 0.996 * max(context.price_history[stock])
              and data[stock].price <= 1.0025 * min(list(context.price_history[stock])[6:])):
            context.price_move_signal[stock] = "Move Down"
            if (data[stock].price < 0.99 * max(context.price_history[stock])
                and data[stock].price <= 1.001 * min(context.price_history[stock])):
                context.price_move_signal[stock] = "Spike Down"
                
        else:
            context.price_move_signal[stock] = None
            
        if context.price_move_debug_mode:
            log.info(str(data[stock].datetime.astimezone(timezone('US/Eastern'))) + "\n"
                     + "Price History: " + str(context.price_history[stock]) + "\n"
                     + "Current Price: " + str(data[stock].price) + "\n"
                     + "Price Move: " + str(context.price_move_signal[stock]) + "\n"
                     + "Burst Signal: " + str(context.burst_signal[stock]) + "\n"
                     + str(stock) + "\n\n\n")
        
        
        # Find volume signal
        if len(context.six_min_vol[stock]) < 6:
            context.volumn_rate[stock] = data[stock].volume/context.six_min_average_vol[stock]
            if (min(context.six_min_vol[stock]) * 12 > context.six_min_average_vol[stock]
                and context.volumn_rate[stock] > 0.4):
                context.volumn_signal[stock] = "Large Volumn"

            elif (context.volumn_rate[stock] < 0.2
                  or min(context.six_min_vol[stock]) * 18 < context.six_min_average_vol[stock]):
                context.volumn_signal[stock] = "Small Volumn"
                # context.burst_signal[stock] = False
                
            else:
                context.volumn_signal[stock] = None 
                
        elif len(context.thirty_min_vol[stock]) < 30:
            context.volumn_rate[stock] = sum(context.six_min_vol[stock])/(5 * context.six_min_average_vol[stock])
            if (min(context.six_min_vol[stock]) * 15 > context.six_min_average_vol[stock] # Ensure steady purchase
                and context.volumn_rate[stock] > 0.4):
                context.volumn_signal[stock] = "Large Volumn"

            elif (context.volumn_rate[stock] < 0.2
                  or min(context.six_min_vol[stock]) * 24 < context.six_min_average_vol[stock]):
                context.volumn_signal[stock] = "Small Volumn"
                # context.burst_signal[stock] = False
                
            else:
                context.volumn_signal[stock] = None                                 
            
        else:
            context.volumn_rate[stock] = float(sum(context.six_min_vol[stock]))/(
                sum(context.thirty_min_vol[stock]) - sum(context.six_min_vol[stock]))
            
            if ((context.volumn_rate[stock] > 0.4
                 or sum(context.six_min_vol[stock]) > 2.5 * context.six_min_average_vol[stock])
                and min(context.six_min_vol[stock]) * 30 > context.six_min_average_vol[stock] # Revisit this
                and sum(context.six_min_vol[stock]) > 1.2 * max(context.six_min_average_vol[stock], 7000)):
                context.volumn_signal[stock] = "Large Volumn"

            elif (context.volumn_rate[stock] < 0.2
                  or sum(context.six_min_vol[stock]) < 0.6 * context.six_min_average_vol[stock]
                  or max(context.six_min_vol[stock]) * 6 < context.six_min_average_vol[stock]
                  # or min(context.six_min_vol[stock]) * 60 < context.six_min_average_vol[stock] Consider to keep this
                  ):
                context.volumn_signal[stock] = "Small Volumn"
                # context.burst_signal[stock] = False
            else:
                context.volumn_signal[stock] = None
            
        if context.volumn_debug_mode:
                log.info(str(data[stock].datetime.astimezone(timezone('US/Eastern'))) + "\n"
                         + "Volumn Signal: " + str(context.volumn_signal[stock]) + "\n"
                         + "Volumn Rate: " + str(context.volumn_rate[stock]) + "\n"
                         + "AVG Vol: " + str(context.six_min_average_vol[stock]) + "\n"
                         + "Volumn Hist: " + str(context.six_min_vol[stock]) + "\n"
                         + "Sum Volumn Ratio: " + str(sum(context.six_min_vol[stock])/
                                                      context.six_min_average_vol[stock]) + "\n"
                         + "Min Volumn Ratio: " + str( min(context.six_min_vol[stock])/
                                                  context.six_min_average_vol[stock])+ "\n\n")
                
        if (context.price_move_signal[stock] == None
            and context.volumn_signal[stock] == "Small Volumn"):
            context.burst_signal[stock] = False        
            
        # Find breakout signal     
        # Daily Breakout
        if (data[stock].price < 1.005 * context.daily_range[stock][0]
              and data[stock].price > 0.995 * context.daily_range[stock][0]):
            
            context.daily_support_signal[stock] = True
            
        elif (data[stock].price < 0.995 * context.daily_range[stock][0]):
            context.daily_breakout_signal[stock] = 'Daily Low'
            context.daily_support_signal[stock] = False
            
            # Signal when volumn is good and price move is fast and daily low is somewhat above two-day low
            # or even below five day low.
            # if (context.volumn_signal[stock] <> "Small Volumn"
                # and context.price_move_signal[stock] == "Spike Down"
                # and (not context.daily_notification[stock][0])):
                # log.info(str(data[stock].datetime.astimezone(timezone('US/Eastern'))) + "\n"
                         # + "Breaking daily low: " + str(stock) + "\n\n")
                # context.daily_notification[stock][0] = True
            
        elif (data[stock].price > 0.995 * context.daily_range[stock][1]
              and data[stock].price < 1.005 * context.daily_range[stock][1]):
              context.daily_resist_signal[stock] = True
            
        elif (data[stock].price > 1.005 * context.daily_range[stock][1]):
            context.daily_breakout_signal[stock] = 'Daily High'
            context.daily_resist_signal[stock] = False
            
            # Signal when volumn is good and price move is fast and daily low is somewhat above two-day low
            # or even below five day low.
            # if (context.volumn_signal[stock] == "Large Volumn"
                # and context.price_move_signal[stock] == "Spike Up"
                # and context.daily_breakout_signal[stock] <> 'Daily High'
                # and (not context.daily_notification[stock][0])):
                # log.info(str(data[stock].datetime.astimezone(timezone('US/Eastern'))) + "\n"
                         # + "Breaking daily high: " + str(stock) + "\n")
                # context.daily_notification[stock][0] = True            
        else:
            # (TODO) Review this to use low/high v.s price?
            if (data[stock].price > 1.0075 * context.daily_range[stock][0]
                and data[stock].price < 0.9925 * context.daily_range[stock][1]):
                context.daily_support_signal[stock] = False
                context.daily_resist_signal[stock] = False
                context.daily_breakout_signal[stock] = None
                context.daily_notification[stock] = [False, False, False]
                
        context.daily_range[stock] = [min([data[stock].low, context.daily_range[stock][0]]),
                               max([data[stock].high, context.daily_range[stock][1]])]
        
        if (data[stock].price > 1.0075 * context.daily_range[stock][0]
            or data[stock].price < 0.9925 * context.daily_range[stock][1]):
            context.daily_breakout_signal[stock] = None
            
        if context.daily_range[stock][0] * 1.015 > context.daily_range[stock][1]:
            context.daily_support_signal[stock] = False
            context.daily_resist_signal[stock] = False
        
                
        # Down side 2/5-Day Breakout signal
        if context.two_day_range[stock][0] == context.five_day_range[stock][0]:
            # Suppress 5 day signal
            context.five_day_support_signal[stock] = False;
            context.five_day_breakout_signal[stock] = None
            
            
        elif context.two_day_range[stock][0] > context.five_day_range[stock][0] * 1.01:
            # Expected case where 2 day support is far away from 5 day support
            if (data[stock].price < 1.0075 * context.two_day_range[stock][0]
                and data[stock].price > 0.995 * context.two_day_range[stock][0]):

                # Determine resist/support base on break signal
                if context.two_day_breakout_signal[stock] == 'Two Day Low':
                    context.two_day_resist_signal[stock] = True

                else:  
                    context.two_day_support_signal[stock] = True
                        
            elif (data[stock].price < 0.995 * context.two_day_range[stock][0]):
                context.two_day_breakout_signal[stock] = 'Two Day Low'
                # Reset after plunge 
                context.two_day_support_signal[stock] = False
                context.two_day_resist_signal[stock] = False
            
                # Signal when volumn is good and price move is fast
                # if (context.volumn_signal[stock] <> "Small Volumn"
                    # and (context.price_move_signal[stock] == "Spike Down"
                         # or context.price_move_signal[stock] == "Move Down")
                    # and context.two_day_range[stock][0] > context.five_day_range[stock][0] * 1.01
                    # and (not context.two_day_notification[stock][0])):
                    # # Revisit this filter
                    # if context.five_day_breakout_signal[stock] <> 'Five Day Low':
                        # log.info(str(data[stock].datetime.astimezone(timezone('US/Eastern'))) + "\n"
                                 # + "Breaking 2-days low: " + str(stock) + "\n\n")
                    # context.two_day_notification[stock][0] = True
                        
            if (data[stock].price < 1.01 * context.five_day_range[stock][0]
                and data[stock].price > 0.9925 * context.five_day_range[stock][0]):

                # Determine resist/support base on break signal
                if context.five_day_breakout_signal[stock] == 'Five Day Low':
                    context.five_day_resist_signal[stock] = True

                else:
                    context.five_day_support_signal[stock] = True

            elif (data[stock].price < 0.9925 * context.five_day_range[stock][0]):
                context.five_day_breakout_signal[stock] = 'Five Day Low'
                # Reset after plunge 
                context.five_day_support_signal[stock] = False
                context.five_day_resist_signal[stock] = False

                # Signal when volumn is good and price move is fast
                # if (context.volumn_signal[stock] <> "Small Volumn"
                    # and (context.price_move_signal[stock] == "Spike Down"
                         # or context.price_move_signal[stock] == "Move Down")
                    # and (not context.five_day_notification[stock][0])):
                    # log.info(str(data[stock].datetime.astimezone(timezone('US/Eastern'))) + "\n"
                             # + "Breaking 5-days low: " + str(stock) + "\n\n")
                    # context.five_day_notification[stock][0] = True   
        
        else:
            # Suppress all signal on the down side
            context.two_day_breakout_signal[stock] = None # (TODO) should I reset this?
            context.two_day_support_signal[stock] = False     
            
        # Up side 2/5-Day Breakout signal
        if context.two_day_range[stock][1] == context.five_day_range[stock][1]:
            # Suppress 5 day signal
            context.five_day_support_signal[stock] = False;
            context.five_day_breakout_signal[stock] = ('Five Day Low'
                                                      if context.two_day_breakout_signal[stock] == 'Five Day Low'
                                                      else None)

        elif context.two_day_range[stock][1] < context.five_day_range[stock][1] * 0.99:
            if (data[stock].price > 0.9925 * context.two_day_range[stock][1]
                  and data[stock].price < 1.005 * context.two_day_range[stock][1]):

                # Determine resist/support base on break signal
                if context.two_day_breakout_signal[stock] == 'Two Day High':
                    context.two_day_support_signal[stock] = True

                else:
                    context.two_day_resist_signal[stock] = True
                    
            elif (data[stock].price > 1.005 * context.two_day_range[stock][1]):
                context.two_day_breakout_signal[stock] = 'Two Day High'
                # Reset after breakout
                context.two_day_support_signal[stock] = False
                context.two_day_resist_signal[stock] = False

                # Signal when volumn is good and price move is fast
                # if (context.volumn_signal[stock] <> "Small Volumn" # (TODO) Should this be not Small?
                    # and (context.price_move_signal[stock] == "Spike Up"
                         # or context.price_move_signal[stock] == "Move Up")
                    # and context.two_day_range[stock][1] < context.five_day_range[stock][1] * 0.99
                    # and (not context.two_day_notification[stock][0])):
                    # if context.five_day_breakout_signal[stock] <> 'Five Day High':  # Revisit this filter
                        # log.info(str(data[stock].datetime.astimezone(timezone('US/Eastern'))) + "\n"
                                 # + "Breaking 2-days high: " + str(stock) + "\n\n")
                    # context.two_day_notification[stock][0] = True

            if (data[stock].price > 0.99 * context.five_day_range[stock][1]
                 and data[stock].price < 1.0075 * context.five_day_range[stock][1]):

                # Determine resist/support base on break signal
                if context.five_day_breakout_signal[stock] == 'Five Day High':
                    context.five_day_support_signal[stock] = True
                    
                else:
                    context.five_day_resist_signal[stock] = True

            elif (data[stock].price > 1.0075 * context.five_day_range[stock][1]):
                context.five_day_breakout_signal[stock] = 'Five Day High'
                context.five_day_support_signal[stock] = False
                context.five_day_resist_signal[stock] = False

                # Signal when volumn is good and price move is fast
                # if (context.volumn_signal[stock] <> "Small Volumn"
                    # and (context.price_move_signal[stock] == "Spike Up"
                         # or context.price_move_signal[stock] == "Move Up")
                    # and (not context.five_day_notification[stock][0])):
                    # log.info(str(data[stock].datetime.astimezone(timezone('US/Eastern'))) + "\n"
                             # + "Breaking 5-days high: " + str(stock) + "\n\n")
                    # context.five_day_notification[stock][0] = True       
                            
        
        else:
            # Suppress all 2 day signal on the up side
            context.two_day_breakout_signal[stock] = ('Two Day Low'
                                                      if context.two_day_breakout_signal[stock] == 'Two Day Low'
                                                      else None)
            context.two_day_resist_signal[stock] = False

        if (data[stock].price > 1.01 * context.two_day_range[stock][0]
            and data[stock].price < 0.99 * context.two_day_range[stock][1]):
            context.two_day_notification[stock] = [False, False, False]
            context.two_day_breakout_signal[stock] = None # (TODO) should I reset this?
            context.two_day_resist_signal[stock] = False
            context.two_day_support_signal[stock] = False
            
        if (data[stock].price > 1.01 * context.five_day_range[stock][0]
                and data[stock].price < 0.99 * context.five_day_range[stock][1]):
                context.five_day_notification[stock] = [False, False, False]
                context.five_day_breakout_signal[stock] = None # (TODO) should I reset this?
                context.five_day_resist_signal[stock] = False
                context.five_day_support_signal[stock] = False
            
        if context.brekout_debug_mode:
            log.info(str(data[stock].datetime.astimezone(timezone('US/Eastern'))) + "\n"
                     + "Daily Range: " + str(context.daily_range[stock]) + "\n"
                     + "Daily Breakout Signal: " + str(context.daily_breakout_signal[stock]) + "\n"
                     + "Daily Support Signal: " + str(context.daily_support_signal[stock]) + "\n"
                     + "Daily Resist Signal: " + str(context.daily_resist_signal[stock]) + "\n"
                     + "Daily Notification Signal: " + str(context.daily_notification[stock]) + "\n"
                     + "2 Day Range: " + str(context.two_day_range[stock]) + "\n"
                     + "2 Day Breakout Signal: " + str(context.two_day_breakout_signal[stock]) + "\n"
                     + "2 Day Support Signal: " + str(context.two_day_support_signal[stock]) + "\n"
                     + "2 Day Resist Signal: " + str(context.two_day_resist_signal[stock]) + "\n"
                     + "2 Day Notification Signal: " + str(context.two_day_notification[stock]) + "\n"
                     + "5 Day Range: " + str(context.five_day_range[stock]) + "\n"
                     + "5 Day Breakout Signal: " + str(context.five_day_breakout_signal[stock]) + "\n"
                     + "5 Day Support Signal: " + str(context.five_day_support_signal[stock]) + "\n"
                     + "5 Day Resist Signal: " + str(context.five_day_resist_signal[stock]) + "\n"
                     + "5 Day Notification Signal: " + str(context.five_day_notification[stock]) + "\n"  
                     + "\n\n")
            
            
        # Find BB support/resist
        context.bb_percent[stock] = (data[stock].price - five_min_bb_data[stock][2])/(five_min_bb_data[stock][0]
                                                                                      - five_min_bb_data[stock][2])
        
        if context.bb_percent[stock] < 0.15:
            context.bb_support_signal[stock] = True
            
        elif context.bb_percent[stock] > 0.85:
            context.bb_resist_signal[stock] = True
                    
        else:
            context.bb_resist_signal[stock] = False
            context.bb_support_signal[stock] = False
            
        # Find trend signal && TTM Trend
        previous_ma = context.ma_history[stock].popleft()
        (context.ma_history[stock]).append(moving_average[stock])
        
        context.slope[stock] = (moving_average[stock] - previous_ma)/ (moving_average[stock] * 5)
        if context.trend_debug_mode:
            log.info(str(data[stock].datetime.astimezone(timezone('US/Eastern'))) + "\n"
                     + "Slope: " + str(context.slope[stock]) + "\n\n")
        if abs(context.slope[stock]) <= 0.00015:
            context.trend[stock] = 'Neutral'
        elif context.slope[stock] > 0.00015:
            context.trend[stock] = 'Bull'
        else:
            context.trend[stock] = 'Bear'
                
        # Find squeeze signal
        upper_band = five_min_sma_data[stock] + 3 * five_min_atr_data[stock]
        lower_band = five_min_sma_data[stock] - 3 * five_min_atr_data[stock]

        if context.ttm_debug_mode:
            log.info(str(data[stock].datetime.astimezone(timezone('US/Eastern'))) + "\n"
                     + str(upper_band) + " : " + str(lower_band) + "\n"
                     + str(five_min_bb_data[stock])
                     + "\n\n")
            
        if (upper_band > five_min_bb_data[stock][0]
            and lower_band < five_min_bb_data[stock][2]
            and five_min_bb_data[stock][0] - five_min_bb_data[stock][2] < 0.85 * (upper_band - lower_band)):
            
            if context.squeeze_signal[stock] == False and context.ttm_debug_mode:
                log.info(str(data[stock].datetime.astimezone(timezone('US/Eastern'))) + "\n"
                     + "TTM Squeeze Start:\n" + str(stock) + "\n\n")
            context.squeeze_signal[stock] = True
            
        elif (context.squeeze_signal[stock] == True
              # and (not context.five_day_resist_signal[stock])
              # and (not context.five_day_support_signal[stock])
              and (not context.open_suppression)
              and (upper_band < five_min_bb_data[stock][0]
                   or lower_band > five_min_bb_data[stock][2])
              and (upper_band < 0.9995 * five_min_bb_data[stock][0]
                   or data[stock].price > upper_band
                   or lower_band > 1.0005 * five_min_bb_data[stock][2]
                   or data[stock].price < lower_band)
              ):
            
            if context.ttm_debug_mode:
                log.info(str(data[stock].datetime.astimezone(timezone('US/Eastern'))) + "\n"
                             + "TTM Squeeze Pending:\n" + str(stock) + "\n"
                             + "Volumn Rate: " + str(context.volumn_rate[stock]) + "\n"
                             + "Volumn Signal: " + str(context.volumn_signal[stock]) + "\n"
                             + "Volumn Detauil:" + str(context.six_min_vol[stock]) + "\n"
                             + "Sum Volumn Ratio: " + str(sum(context.six_min_vol[stock])/
                                                  context.six_min_average_vol[stock]) + "\n"
                             + "Avg Volumn: " + str(context.six_min_average_vol[stock]) + "\n\n")

            if (data[stock].price > upper_band
                and (context.volumn_signal[stock] == "Large Volumn"
                     or context.price_move_signal[stock] == "Spike Up")
                and (context.price_move_signal[stock] == "Move Up"
                     or context.price_move_signal[stock] == "Spike Up")):
                log.info(str(data[stock].datetime.astimezone(timezone('US/Eastern'))) + "\n"
                         + "TTM Squeeze LONG Breakout:\n" + str(stock) + " @" + str(data[stock].price) + "\n"
                         + "Volumn Rate: " + str(context.volumn_rate[stock]) + "\n"
                         + "5 Day Resist Signal: " + ("@" + str(context.five_day_range[stock][1])
                                                      if context.five_day_resist_signal[stock]
                                                      else "False") + "\n"   
                         + "2 Day Resist Signal: " + ("@" + str(context.two_day_range[stock][1])
                                                      if context.two_day_resist_signal[stock]
                                                      else "False") + "\n"
                         + "Daily Resist Signal: " + ("@" + str(context.daily_range[stock][1])
                                                      if context.daily_resist_signal[stock]
                                                      else "False") + "\n"
                         + "\n\n")
                context.squeeze_signal[stock] = False;
                
            elif (data[stock].price < lower_band
                  and (context.volumn_signal[stock] <> "Small Volumn"
                       or context.price_move_signal[stock] == "Spike Down")
                  and (context.price_move_signal[stock] == "Move Down"
                     or context.price_move_signal[stock] == "Spike Down")):
                log.info(str(data[stock].datetime.astimezone(timezone('US/Eastern'))) + "\n"
                         + "TTM Squeeze SHORT Breakout:\n" + str(stock) + " @" + str(data[stock].price) + "\n"
                         + "Volumn Rate: " + str(context.volumn_rate[stock]) + "\n"
                         + "5 Day Support Signal: " + ("@" + str(context.five_day_range[stock][0])
                                                      if context.five_day_support_signal[stock]
                                                      else "False") + "\n"   
                         + "2 Day Support Signal: " + ("@" + str(context.two_day_range[stock][0])
                                                      if context.two_day_support_signal[stock]
                                                      else "False") + "\n"
                         + "Daily Support Signal: " + ("@" + str(context.daily_range[stock][0])
                                                      if context.daily_support_signal[stock]
                                                      else "False") + "\n"
                         + "\n\n")
                context.squeeze_signal[stock] = False;
                
            # Re-visit the threshhold
            elif (upper_band < 0.9975 * five_min_bb_data[stock][0]
                  and lower_band > 1.0025 * five_min_bb_data[stock][2]):
                context.squeeze_signal[stock] = False;
                if context.ttm_debug_mode:
                    log.info(str(data[stock].datetime.astimezone(timezone('US/Eastern'))) + "\n"
                             + "TTM Squeeze Reset:\n" + str(stock) + "\n\n")
            
            else:
                if context.ttm_debug_mode:
                    log.info(str(data[stock].datetime.astimezone(timezone('US/Eastern'))) + "\n"
                             + "TTM Squeeze No Volumn Breakout:\n" + str(stock)
                             + "Volumn Signal: " + str(context.volumn_signal[stock]) + "\n\n")
                    
        if context.burst_deug_mode:
            log.info(str(data[stock].datetime.astimezone(timezone('US/Eastern'))) + "\n"
                     + "Price Move: " + str(context.price_move_signal[stock]) + "\n"
                     + "Volumn Rate: " + str(context.volumn_rate[stock]) + "\n"
                     + "AVG Vol: " + str(context.six_min_average_vol[stock]) + "\n"
                     + "Volumn Hist: " + str(context.six_min_vol[stock]) + "\n"
                     + "Sum Volumn Ratio: " + str(sum(context.six_min_vol[stock])/
                                                  context.six_min_average_vol[stock]) + "\n"
                     + "BB Percent: " + str(context.bb_percent[stock]) + "\n"
                     + "Dail Range: " + str(context.daily_range[stock]) + "\n"
                     + "Daily Breakout Signal: " + str(context.daily_breakout_signal[stock]) + "\n"
                     + "Daily Support Signal: " + str(context.daily_support_signal[stock]) + "\n"
                     + "Daily Resist Signal: " + str(context.daily_resist_signal[stock]) + "\n"
                     + "Daily Notification Signal: " + str(context.daily_notification[stock]) + "\n"
                     + "2 Day Range: " + str(context.two_day_range[stock]) + "\n"
                     + "2 Day Breakout Signal: " + str(context.two_day_breakout_signal[stock]) + "\n"
                     + "2 Day Support Signal: " + str(context.two_day_support_signal[stock]) + "\n"
                     + "2 Day Resist Signal: " + str(context.two_day_resist_signal[stock]) + "\n"
                     + "2 Day Notification Signal: " + str(context.two_day_notification[stock]) + "\n"
                     + "5 Day Range: " + str(context.five_day_range[stock]) + "\n"
                     + "5 Day Breakout Signal: " + str(context.five_day_breakout_signal[stock]) + "\n"
                     + "5 Day Support Signal: " + str(context.five_day_support_signal[stock]) + "\n"
                     + "5 Day Resist Signal: " + str(context.five_day_resist_signal[stock]) + "\n"
                     + "5 Day Notification Signal: " + str(context.five_day_notification[stock]) + "\n"           
                     + "Min Volumn Ratio: " + str( min(context.six_min_vol[stock])/
                                              context.six_min_average_vol[stock])+ "\n\n")
                    
        # Find burst Signal
        if len(context.thirty_min_vol[stock]) < 30:
            if (context.price_move_signal[stock] == "Spike Up"
                and (not context.burst_signal[stock])
                and context.volumn_signal[stock] == "Large Volumn"
                and (not context.open_suppression)
                and (not context.five_day_resist_signal[stock]) # Would like to see signal only after making 5 day-high
                and min(context.six_min_vol[stock]) * 12 > context.six_min_average_vol[stock] # Looking for steady purchase
                ):
                context.burst_signal[stock] = True
                log.info(str(data[stock].datetime.astimezone(timezone('US/Eastern'))) + "\n"
                     + "LONG Large Volumn/Price Burst:\n" + str(stock) + " @" + str(data[stock].price) + "\n"
                     + "BB Percent: " + str(context.bb_percent[stock]) + "\n"
                     + "5 Day Resist Signal: " + ("@" + str(context.five_day_range[stock][1])
                                                  if context.five_day_resist_signal[stock]
                                                  else "False") + "\n"   
                     + "2 Day Resist Signal: " + ("@" + str(context.two_day_range[stock][1])
                                                  if context.two_day_resist_signal[stock]
                                                  else "False") + "\n"
                     + "Daily Resist Signal: " + ("@" + str(context.daily_range[stock][1])
                                                  if context.daily_resist_signal[stock]
                                                  else "False") + "\n"
                     + "Volumn Rate: " + str(context.volumn_rate[stock]) + "\n"
                     + "AVG Vol: " + str(context.six_min_average_vol[stock]) + "\n"
                     + "Volumn Hist: " + str(context.six_min_vol[stock]) + "\n"
                     + "Sum Volumn Ratio: " + str(sum(context.six_min_vol[stock])/
                                                  context.six_min_average_vol[stock]) + "\n"
                     + "Min Volumn Ratio: " + str(min(context.six_min_vol[stock])/
                                                 context.six_min_average_vol[stock])+ "\n"
                     + "\n\n")

                if context.volumn_debug_mode:
                    log.info(str(data[stock].datetime.astimezone(timezone('US/Eastern'))) + "\n"
                             + "Volumn Rate: " + str(context.volumn_rate[stock]) + "\n"
                             + "AVG Vol: " + str(context.six_min_average_vol[stock]) + "\n"
                             + "Volumn Hist: " + str(context.six_min_vol[stock]) + "\n"
                             + "Sum Volumn Ratio: " + str(sum(context.six_min_vol[stock])/
                                                          context.six_min_average_vol[stock]) + "\n"
                             + "Min Volumn Ratio: " + str(min(context.six_min_vol[stock])/
                                                          context.six_min_average_vol[stock])+ "\n\n")


            elif (context.price_move_signal[stock] == "Spike Down"
                  and (not context.open_suppression)
                  # and context.volumn_signal[stock] <> "Small Volumn" # Revisit
                  and context.five_min_kd[stock][0] > 60 # Revisit this filter
                  and (not context.five_day_support_signal[stock]) # Would like to see signal only after making 5 day-high
                  and min(context.six_min_vol[stock]) * 24 < context.six_min_average_vol[stock] # Not expecting steady purchase
                  and context.five_day_breakout_signal[stock] <> "Five Day High"
                  and (not context.burst_signal[stock])):
                context.burst_signal[stock] = True
                log.info(str(data[stock].datetime.astimezone(timezone('US/Eastern'))) + "\n"
                     + "SHORT Large Volumn/Price Burst:\n" + str(stock) + " @" + str(data[stock].price) + "\n"
                     + "BB Percent: " + str(context.bb_percent[stock]) + "\n"
                     + "5 Day Support Signal: " + ("@" + str(context.five_day_range[stock][0])
                                                  if context.five_day_support_signal[stock]
                                                  else "False") + "\n"   
                     + "2 Day Support Signal: " + ("@" + str(context.two_day_range[stock][0])
                                                  if context.two_day_support_signal[stock]
                                                  else "False") + "\n"
                     + "Daily Support Signal: " + ("@" + str(context.daily_range[stock][0])
                                                  if context.daily_support_signal[stock]
                                                  else "False") + "\n"
                     + "Volumn Rate: " + str(context.volumn_rate[stock]) + "\n"
                     + "AVG Vol: " + str(context.six_min_average_vol[stock]) + "\n"
                     + "Volumn Hist: " + str(context.six_min_vol[stock]) + "\n"
                     + "Sum Volumn Ratio: " + str(sum(context.six_min_vol[stock])/
                                                  context.six_min_average_vol[stock]) + "\n"
                     + "Min Volumn Ratio: " + str(min(context.six_min_vol[stock])/
                                                 context.six_min_average_vol[stock])+ "\n"
                     + "\n\n")

                if context.volumn_debug_mode:
                    log.info(str(data[stock].datetime.astimezone(timezone('US/Eastern'))) + "\n"
                             + "Volumn Rate: " + str(context.volumn_rate[stock]) + "\n"
                             + "AVG Vol: " + str(context.six_min_average_vol[stock]) + "\n"
                             + "Volumn Hist: " + str(context.six_min_vol[stock]) + "\n"
                             + "Sum Volumn Ratio: " + str(sum(context.six_min_vol[stock])/
                                                          context.six_min_average_vol[stock]) + "\n"
                             + "Min Volumn Ratio: " + str( min(context.six_min_vol[stock])/
                                                      context.six_min_average_vol[stock])+ "\n\n")
            
        else:
            if (context.price_move_signal[stock] == "Spike Up"
                and (context.volumn_rate[stock] > 0.6
                     or sum(context.six_min_vol[stock]) > 2 * context.six_min_average_vol[stock])
                and (not context.burst_signal[stock])
                and context.volumn_signal[stock] == "Large Volumn"
                and (not context.five_day_resist_signal[stock]) # Would like to see signal only after making 5 day-high
                and min(context.six_min_vol[stock]) * 12 > context.six_min_average_vol[stock] # Looking for steady purchase
                ):
                context.burst_signal[stock] = True
                log.info(str(data[stock].datetime.astimezone(timezone('US/Eastern'))) + "\n"
                     + "LONG Large Volumn/Price Burst:\n" + str(stock) + " @" + str(data[stock].price) + "\n"
                     + "BB Percent: " + str(context.bb_percent[stock]) + "\n"
                     + "5 Day Resist Signal: " + ("@" + str(context.five_day_range[stock][1])
                                                  if context.five_day_resist_signal[stock]
                                                  else "False") + "\n"   
                     + "2 Day Resist Signal: " + ("@" + str(context.two_day_range[stock][1])
                                                  if context.two_day_resist_signal[stock]
                                                  else "False") + "\n"
                     + "Daily Resist Signal: " + ("@" + str(context.daily_range[stock][1])
                                                  if context.daily_resist_signal[stock]
                                                  else "False") + "\n"
                     + "Volumn Rate: " + str(context.volumn_rate[stock]) + "\n"
                     + "AVG Vol: " + str(context.six_min_average_vol[stock]) + "\n"
                     + "Volumn Hist: " + str(context.six_min_vol[stock]) + "\n"
                     + "Sum Volumn Ratio: " + str(sum(context.six_min_vol[stock])/
                                                  context.six_min_average_vol[stock]) + "\n"
                     + "Min Volumn Ratio: " + str(min(context.six_min_vol[stock])/
                                                 context.six_min_average_vol[stock])+ "\n"
                     + "\n\n")

                if context.volumn_debug_mode:
                    log.info(str(data[stock].datetime.astimezone(timezone('US/Eastern'))) + "\n"
                             + "Volumn Rate: " + str(context.volumn_rate[stock]) + "\n"
                             + "AVG Vol: " + str(context.six_min_average_vol[stock]) + "\n"
                             + "Volumn Hist: " + str(context.six_min_vol[stock]) + "\n"
                             + "Sum Volumn Ratio: " + str(sum(context.six_min_vol[stock])/
                                                          context.six_min_average_vol[stock]) + "\n"
                             + "Min Volumn Ratio: " + str( min(context.six_min_vol[stock])/
                                                      context.six_min_average_vol[stock])+ "\n\n")


            elif (context.price_move_signal[stock] == "Spike Down"
                and context.volumn_rate[stock] < 0.4
                and context.five_min_kd[stock][0] > 60 # Revisit this filter
                # and context.volumn_signal[stock] <> "Small Volumn" # Revisit
                and (not context.five_day_support_signal[stock]) # Would like to see signal only after making 5 day-high
                # and min(context.six_min_vol[stock]) * 24 < context.six_min_average_vol[stock] # Not expecting steady purchase, 
                # Revisit this as it is no good for days with volumn burst
                and context.five_day_breakout_signal[stock] <> "Five Day High"
                and (not context.burst_signal[stock])):
                context.burst_signal[stock] = True
                log.info(str(data[stock].datetime.astimezone(timezone('US/Eastern'))) + "\n"
                     + "SHORT Large Volumn/Price Burst:\n" + str(stock) + " @" + str(data[stock].price) + "\n"
                     + "BB Percent: " + str(context.bb_percent[stock]) + "\n"
                     + "5 Day Support Signal: " + ("@" + str(context.five_day_range[stock][0])
                                                  if context.five_day_support_signal[stock]
                                                  else "False") + "\n"   
                     + "2 Day Support Signal: " + ("@" + str(context.two_day_range[stock][0])
                                                  if context.two_day_support_signal[stock]
                                                  else "False") + "\n"
                     + "Daily Support Signal: " + ("@" + str(context.daily_range[stock][0])
                                                  if context.daily_support_signal[stock]
                                                  else "False") + "\n"
                     + "Volumn Rate: " + str(context.volumn_rate[stock]) + "\n"
                     + "AVG Vol: " + str(context.six_min_average_vol[stock]) + "\n"
                     + "Volumn Hist: " + str(context.six_min_vol[stock]) + "\n"
                     + "Sum Volumn Ratio: " + str(sum(context.six_min_vol[stock])/
                                                  context.six_min_average_vol[stock]) + "\n"
                     + "Min Volumn Ratio: " + str(min(context.six_min_vol[stock])/
                                                 context.six_min_average_vol[stock])+ "\n"
                     + "\n\n")

                if context.volumn_debug_mode:
                    log.info(str(data[stock].datetime.astimezone(timezone('US/Eastern'))) + "\n"
                             + "Volumn Rate: " + str(context.volumn_rate[stock]) + "\n"
                             + "AVG Vol: " + str(context.six_min_average_vol[stock]) + "\n"
                             + "Volumn Hist: " + str(context.six_min_vol[stock]) + "\n"
                             + "Sum Volumn Ratio: " + str(sum(context.six_min_vol[stock])/
                                                          context.six_min_average_vol[stock]) + "\n"
                             + "Min Volumn Ratio: " + str( min(context.six_min_vol[stock])/
                                                      context.six_min_average_vol[stock])+ "\n\n")
        


def make_decision(context, data):
    one_min_natr_data = one_min_natr(data)
    five_min_kd_data = five_min_kd(data)
    ten_min_kd_data = ten_min_kd(data)
    # one_hour_kd_data = one_hour_kd(data)
    one_hour_kd_data = one_hour_kd(data)
    
    for stock in context.stocks:
        if context.kd_debug_model:
            log.info(str(data[stock].datetime.astimezone(timezone('US/Eastern'))) + "\n"
                     + "Trend: " + str(context.trend[stock]) + "\n"
                     + "Price Move: " + str(context.price_move_signal[stock]) + "\n"
                     + "5-min KD: " + str(five_min_kd_data[stock]) + "\n"
                     + "10-min KD: " + str(ten_min_kd_data[stock]) + "\n"
                     + "60-min KD: " + str(one_hour_kd_data[stock]) + "\n"
                     + "NATR: " + str(one_min_natr_data[stock]) + "\n"
                     + "BB Percent: " + str(context.bb_percent[stock]) + "\n"
                     + "Volumn Rate: " + str(context.volumn_rate[stock]) + "\n"
                     + "Volumn Signal: " + str(context.volumn_signal[stock]) + "\n"
                     + "Burst Signal: " + str(context.burst_signal[stock]) + "\n"
                     + "Dail Range: " + str(context.daily_range[stock]) + "\n"
                     + "Daily Breakout Signal: " + str(context.daily_breakout_signal[stock]) + "\n"
                     + "Daily Support Signal: " + str(context.daily_support_signal[stock]) + "\n"
                     + "Daily Resist Signal: " + str(context.daily_resist_signal[stock]) + "\n"
                     + "2 Day Range: " + str(context.two_day_range[stock]) + "\n"
                     + "2 Day Breakout Signal: " + str(context.two_day_breakout_signal[stock]) + "\n"
                     + "2 Day Support Signal: " + str(context.two_day_support_signal[stock]) + "\n"
                     + "2 Day Resist Signal: " + str(context.two_day_resist_signal[stock]) + "\n"
                     + "5 Day Range: " + str(context.five_day_range[stock]) + "\n"
                     + "5 Day Breakout Signal: " + str(context.five_day_breakout_signal[stock]) + "\n"
                     + "5 Day Support Signal: " + str(context.five_day_support_signal[stock]) + "\n"
                     + "5 Day Resist Signal: " + str(context.five_day_resist_signal[stock]) + "\n"
                     + "\n\n")
            
        if context.five_day_breakout_signal[stock] == None:
            if context.trend[stock] == None:
                pass
            
            elif context.trend[stock] == 'Neutral':
                if ((five_min_kd_data[stock][0] < 30
                     or (five_min_kd_data[stock][0] > 50 and
                         (context.price_move_signal[stock] == "Spike Up"
                          or context.volumn_signal[stock] == "Large Volumn"))
                     or (five_min_kd_data[stock][0] > 50 and
                         context.five_day_support_signal[stock]))
                    and five_min_kd_data[stock][0] > context.five_min_kd[stock][0]
                    and five_min_kd_data[stock][0] > five_min_kd_data[stock][1]
                    and context.five_min_kd[stock][0] < context.five_min_kd[stock][1]
                    and one_min_natr_data[stock] > 0.15
                    and context.bb_percent[stock] < 0.4
                    and context.price_move_signal[stock] <> "Move Down"
                    and context.price_move_signal[stock] <> "Spike Down"
                    and ((context.volumn_signal[stock] == "Large Volumn"
                          and context.price_move_signal[stock] == "Move Up")
                         or context.price_move_signal[stock] == "Spike Up"
                         or context.daily_support_signal[stock]
                         or context.two_day_support_signal[stock]
                         or context.five_day_support_signal[stock])
                    and context.volumn_signal[stock] <> "Small Volumn"):
                    log.info(str(data[stock].datetime.astimezone(timezone('US/Eastern'))) + "\n"
                             + "LONG: " + str(stock) + " @" + str(data[stock].price) + "\n"
                             + "Trend: " + str(context.trend[stock]) + "\n"
                             + "Price Move: " + str(context.price_move_signal[stock]) + "\n"
                             + "5-min KD: " + str(five_min_kd_data[stock][0]) + "\n"
                             + "NATR: " + str(one_min_natr_data[stock]) + "\n"
                             + "Daily Support Signal: " + str(context.daily_support_signal[stock]) + "\n"
                             + "2 Day Support Signal: " + str(context.two_day_support_signal[stock]) + "\n"
                             + "5 Day Support Signal: " + str(context.five_day_support_signal[stock]) + "\n"
                             + "Volumn Signal: " + str(context.volumn_signal[stock]) + "\n" 
                             + "\n\n")

                elif ((five_min_kd_data[stock][0] > 70
                       or (five_min_kd_data[stock][0] > 50 and
                           context.price_move_signal[stock] == "Spike Down")
                       or (five_min_kd_data[stock][0] > 50 and
                           context.five_day_resist_signal[stock]))
                    and five_min_kd_data[stock][0] < context.five_min_kd[stock][0]
                    and five_min_kd_data[stock][0] < five_min_kd_data[stock][1]
                    and context.five_min_kd[stock][0] > context.five_min_kd[stock][1]
                    and one_min_natr_data[stock] > 0.15
                    and context.bb_percent[stock] > 0.6
                    and context.price_move_signal[stock] <> "Move Up"
                    and context.price_move_signal[stock] <> "Spike Up"
                    and (context.volumn_signal[stock] <> "Large Volumn"
                         or (context.price_move_signal[stock] == "Spike Down"
                             or context.price_move_signal[stock] == "Move Down"))
                    and (context.daily_resist_signal[stock]
                         or context.two_day_resist_signal[stock]
                         or context.five_day_resist_signal[stock]
                         or context.price_move_signal[stock] == "Spike Down")):
                    log.info(str(data[stock].datetime.astimezone(timezone('US/Eastern'))) + "\n"
                             + "SHORT: " + str(stock) + " @" + str(data[stock].price) + "\n"
                             + "Trend: " + str(context.trend[stock]) + "\n"
                             + "Price Move: " + str(context.price_move_signal[stock]) + "\n"
                             + "5-min KD: " + str(five_min_kd_data[stock][0]) + "\n"
                             + "NATR: " +str(one_min_natr_data[stock]) + "\n"
                             + "Daily Resist Signal: " + str(context.daily_resist_signal[stock]) + "\n"
                             + "2 Day Resist Signal: " + str(context.two_day_resist_signal[stock]) + "\n"
                             + "5 Day Resist Signal: " + str(context.five_day_resist_signal[stock]) + "\n"
                             + "Volumn Signal: " + str(context.volumn_signal[stock]) + "\n"
                             + "\n\n")

            elif context.trend[stock] == 'Bull':
                if ((five_min_kd_data[stock][0] < 50
                     or (five_min_kd_data[stock][0] < 60
                           and (context.price_move_signal[stock] == "Spike Up"
                                or context.volumn_signal[stock] == "Large Volumn")))
                    and five_min_kd_data[stock][0] > context.five_min_kd[stock][0]
                    and five_min_kd_data[stock][0] > five_min_kd_data[stock][1]
                    and context.five_min_kd[stock][0] < context.five_min_kd[stock][1]
                    and one_min_natr_data[stock] > 0.15
                    and context.bb_percent[stock] < 0.4
                    and context.price_move_signal[stock] <> "Move Down"
                    and context.price_move_signal[stock] <> "Spike Down"
                    and ((context.volumn_signal[stock] == "Large Volumn"
                          and context.price_move_signal[stock] == "Move Up")
                         or context.price_move_signal[stock] == "Spike Up"
                         or context.daily_support_signal[stock]
                         or context.two_day_support_signal[stock]
                         or context.five_day_support_signal[stock])
                    and context.volumn_signal[stock] <> "Small Volumn"): # Consider remove this
                    log.info(str(data[stock].datetime.astimezone(timezone('US/Eastern'))) + "\n"
                             + "LONG: " + str(stock) + " @" + str(data[stock].price) + "\n"
                             + "Trend: " + str(context.trend[stock]) + "\n"
                             + "Price Move: " + str(context.price_move_signal[stock]) + "\n"
                             + "5-min KD: " + str(five_min_kd_data[stock][0]) + "\n"
                             + "NATR: " + str(one_min_natr_data[stock]) + "\n"
                             + "Daily Support Signal: " + str(context.daily_support_signal[stock]) + "\n"
                             + "2 Day Support Signal: " + str(context.two_day_support_signal[stock]) + "\n"
                             + "5 Day Support Signal: " + str(context.five_day_support_signal[stock]) + "\n"
                             + "Volumn Signal: " + str(context.volumn_signal[stock]) + "\n"
                             + "\n\n")

                elif ((ten_min_kd_data[stock][0] > 70
                       or (ten_min_kd_data[stock][0] > 50 and
                           context.price_move_signal[stock] == "Spike Down"))
                    and ten_min_kd_data[stock][0] < context.ten_min_kd[stock][0]
                    and ten_min_kd_data[stock][0] < ten_min_kd_data[stock][1]
                    and context.ten_min_kd[stock][0] > context.ten_min_kd[stock][1]
                    and one_min_natr_data[stock] > 0.15
                    and context.bb_percent[stock] > 0.4
                    and (context.price_move_signal[stock] == "Move Down"
                         or context.price_move_signal[stock] == "Spike Down")
                    # and (context.volumn_signal[stock] <> "Large Volumn"
                         # or context.price_move_signal[stock] == "Spike Down")
                    and (context.daily_resist_signal[stock]
                         or context.two_day_resist_signal[stock]
                         or context.five_day_resist_signal[stock]
                         or context.price_move_signal[stock] == "Spike Down")):
                    log.info(str(data[stock].datetime.astimezone(timezone('US/Eastern'))) + "\n"
                             + "SHORT ON DIVERGENCE: " + str(stock) + " @" + str(data[stock].price) + "\n"
                             + "Trend: " + str(context.trend[stock]) + "\n"
                             + "Price Move: " + str(context.price_move_signal[stock]) + "\n"
                             + "10-min KD: " + str(ten_min_kd_data[stock][0]) + "\n"
                             + "NATR: " +str(one_min_natr_data[stock]) + "\n"
                             + "Daily Resist Signal: " + str(context.daily_resist_signal[stock]) + "\n"
                             + "2 Day Resist Signal: " + str(context.two_day_resist_signal[stock]) + "\n"
                             + "5 Day Resist Signal: " + str(context.five_day_resist_signal[stock]) + "\n"
                             + "Volumn Signal: " + str(context.volumn_signal[stock]) + "\n"
                             + "\n\n")
                    
                elif ((five_min_kd_data[stock][0] > 60
                       or (five_min_kd_data[stock][0] > 40
                           and context.price_move_signal[stock] == "Spike Down"))
                    and five_min_kd_data[stock][0] < context.five_min_kd[stock][0]
                    and five_min_kd_data[stock][0] < five_min_kd_data[stock][1]
                    and context.five_min_kd[stock][0] > context.five_min_kd[stock][1]
                    and one_min_natr_data[stock] > 0.15
                    and context.bb_percent[stock] > 0.6
                    and context.price_move_signal[stock] <> "Move Up"
                    and context.price_move_signal[stock] <> "Spike Up"
                    and (context.volumn_signal[stock] <> "Large Volumn"
                         or (context.price_move_signal[stock] == "Spike Down"
                             or context.price_move_signal[stock] == "Move Down"))
                    and context.five_day_resist_signal[stock]):
                    log.info(str(data[stock].datetime.astimezone(timezone('US/Eastern'))) + "\n"
                             + "SHORT on 5 Day Resist: " + str(stock) + " @" + str(data[stock].price) + "\n"
                             + "Trend: " + str(context.trend[stock]) + "\n"
                             + "Price Move: " + str(context.price_move_signal[stock]) + "\n"
                             + "5-min KD: " + str(five_min_kd_data[stock][0]) + "\n"
                             + "NATR: " +str(one_min_natr_data[stock]) + "\n"
                             + "Daily Resist Signal: " + str(context.daily_resist_signal[stock]) + "\n"
                             + "2 Day Resist Signal: " + str(context.two_day_resist_signal[stock]) + "\n"
                             + "5 Day Resist Signal: " + str(context.five_day_resist_signal[stock]) + "\n"
                             + "Volumn Signal: " + str(context.volumn_signal[stock]) + "\n"
                             + "\n\n")
                    
            else:
                if ((ten_min_kd_data[stock][0] < 30
                     or (ten_min_kd_data[stock][0] < 50
                           and (context.price_move_signal[stock] == "Spike Up"
                                or context.volumn_signal[stock] == "Large Volumn")))
                    and ten_min_kd_data[stock][0] > context.ten_min_kd[stock][0]
                    and ten_min_kd_data[stock][0] > ten_min_kd_data[stock][1]
                    and context.ten_min_kd[stock][0] < context.ten_min_kd[stock][1]
                    and one_min_natr_data[stock] > 0.15
                    and context.bb_percent[stock] < 0.6
                    and (context.price_move_signal[stock] == "Move Up"
                         or context.price_move_signal[stock] == "Spike Up")
                    and ((context.volumn_signal[stock] == "Large Volumn"
                          and context.price_move_signal[stock] == "Move Up")
                         or context.price_move_signal[stock] == "Spike Up"
                         or context.daily_support_signal[stock]
                         or context.two_day_support_signal[stock]
                         or context.five_day_support_signal[stock])
                    and context.volumn_signal[stock] <> "Small Volumn"): # Consider remove this
                    log.info(str(data[stock].datetime.astimezone(timezone('US/Eastern'))) + "\n"
                             + "LONG ON DIVERGENCE: " + str(stock) + " @" + str(data[stock].price) + "\n"
                             + "Trend: " + str(context.trend[stock]) + "\n"
                             + "Price Move: " + str(context.price_move_signal[stock]) + "\n"
                             + "10-min KD: " + str(ten_min_kd_data[stock][0]) + "\n"
                             + "NATR: " + str(one_min_natr_data[stock]) + "\n"
                             + "Daily Support Signal: " + str(context.daily_support_signal[stock]) + "\n"
                             + "2 Day Support Signal: " + str(context.two_day_support_signal[stock]) + "\n"
                             + "5 Day Support Signal: " + str(context.five_day_support_signal[stock]) + "\n"
                             + "Volumn Signal: " + str(context.volumn_signal[stock]) + "\n"
                             + "\n\n")
        
                elif ((five_min_kd_data[stock][0] > 50
                       or (five_min_kd_data[stock][0] > 40
                           and context.price_move_signal[stock] == "Spike Down"))
                    and five_min_kd_data[stock][0] < context.five_min_kd[stock][0]
                    and five_min_kd_data[stock][0] < five_min_kd_data[stock][1]
                    and context.five_min_kd[stock][0] > context.five_min_kd[stock][1]
                    and one_min_natr_data[stock] > 0.15
                    and context.bb_percent[stock] > 0.6
                    and context.price_move_signal[stock] <> "Move Up"
                    and context.price_move_signal[stock] <> "Spike Up"
                    and (context.volumn_signal[stock] <> "Large Volumn"
                         or (context.price_move_signal[stock] == "Spike Down"
                             or context.price_move_signal[stock] == "Move Down"))
                    and (context.daily_resist_signal[stock]
                         or context.two_day_resist_signal[stock]
                         or context.five_day_resist_signal[stock]
                         or context.price_move_signal[stock] == "Spike Down")):
                    log.info(str(data[stock].datetime.astimezone(timezone('US/Eastern'))) + "\n"
                             + "SHORT: " + str(stock) + " @" + str(data[stock].price) + "\n"
                             + "Trend: " + str(context.trend[stock]) + "\n"
                             + "Price Move: " + str(context.price_move_signal[stock]) + "\n"
                             + "5-min KD: " + str(five_min_kd_data[stock][0]) + "\n"
                             + "NATR: " +str(one_min_natr_data[stock]) + "\n"
                             + "Daily Resist Signal: " + str(context.daily_resist_signal[stock]) + "\n"
                             + "2 Day Resist Signal: " + str(context.two_day_resist_signal[stock]) + "\n"
                             + "5 Day Resist Signal: " + str(context.five_day_resist_signal[stock]) + "\n"
                             + "Volumn Signal: " + str(context.volumn_signal[stock]) + "\n"
                             + "\n\n")
                    
                elif ((five_min_kd_data[stock][0] < 40
                       or (five_min_kd_data[stock][0] < 60
                           and (context.price_move_signal[stock] == "Spike Up"
                                or context.volumn_signal[stock] == "Large Volumn")))
                    and five_min_kd_data[stock][0] > context.five_min_kd[stock][0]
                    and five_min_kd_data[stock][0] > five_min_kd_data[stock][1]
                    and context.five_min_kd[stock][0] < context.five_min_kd[stock][1]
                    and one_min_natr_data[stock] > 0.15
                    and context.bb_percent[stock] < 0.4
                    and context.price_move_signal[stock] <> "Move Down"
                    and context.price_move_signal[stock] <> "Spike Down"
                    and context.five_day_support_signal[stock]
                    and context.volumn_signal[stock] <> "Small Volumn"):
                    log.info(str(data[stock].datetime.astimezone(timezone('US/Eastern'))) + "\n"
                             + "LONG on 5 Day Support: " + str(stock) + " @" + str(data[stock].price) + "\n"
                             + "Trend: " + str(context.trend[stock]) + "\n"
                             + "Price Move: " + str(context.price_move_signal[stock]) + "\n"
                             + "5-min KD: " + str(five_min_kd_data[stock][0]) + "\n"
                             + "NATR: " + str(one_min_natr_data[stock]) + "\n"
                             + "Daily Support Signal: " + str(context.daily_support_signal[stock]) + "\n"
                             + "2 Day Support Signal: " + str(context.two_day_support_signal[stock]) + "\n"
                             + "5 Day Support Signal: " + str(context.five_day_support_signal[stock]) + "\n"
                             + "Volumn Signal: " + str(context.volumn_signal[stock]) + "\n" 
                             + "\n\n")

        # Five day low
        elif context.five_day_breakout_signal[stock] == "Five Day Low":              
            # if ((one_hour_kd_data[stock][0] < 30
                     # or (one_hour_kd_data[stock][0] < 50
                           # and (context.price_move_signal[stock] == "Spike Up"
                                # or context.volumn_signal[stock] == "Large Volumn")))
                # and one_hour_kd_data[stock][0] > one_hour_kd_data[stock][1]
                # and context.one_hour_kd[stock][0] < context.one_hour_kd[stock][1]
                # and one_min_natr_data[stock] > 0.15
                # and context.bb_percent[stock] < 0.7
                # and context.trend[stock] <> 'Bear' # Revist this filter
                # and (context.price_move_signal[stock] == "Spike Up"
                     # or context.price_move_signal[stock] == "Move Up")
                # and context.volumn_signal[stock]  <> "Small Volumn"
                # and ((not context.five_day_resist_signal[stock]) # Consider previous support becomes resist
                     # or ((context.price_move_signal[stock] == "Spike Up"
                          # or context.price_move_signal[stock] == "Move Up")
                         # and context.volumn_signal[stock]  == "Large Volumn"))
                # and (context.volumn_signal[stock]  == "Large Volumn"
                     # or context.price_move_signal[stock] == "Spike Up")):
                # log.info(str(data[stock].datetime.astimezone(timezone('US/Eastern'))) + "\n"
                         # + "LONG on Five Day Low: " + str(stock) + " @" + str(data[stock].price) + "\n"
                         # + "Trend: " + str(context.trend[stock]) + "\n"
                         # + "Price Move: " + str(context.price_move_signal[stock]) + "\n"
                         # + "60-min KD: " + str(one_hour_kd_data[stock][0]) + "\n"
                         # + "NATR: " + str(one_min_natr_data[stock]) + "\n"
                         # + "Volumn Signal: " + str(context.volumn_signal[stock]) + "\n"
                         # + "Daily Support Signal: " + str(context.daily_support_signal[stock]) + "\n"
                         # + "\n\n")
                
            # elif ((five_min_kd_data[stock][0] < 30
                   # or (five_min_kd_data[stock][0] < 50
                           # and (context.price_move_signal[stock] == "Spike Up"
                                # or context.volumn_signal[stock] == "Large Volumn")))
                  # and five_min_kd_data[stock][0] > context.five_min_kd[stock][0]
                  # and five_min_kd_data[stock][0] > five_min_kd_data[stock][1]
                  # and context.five_min_kd[stock][0] < context.five_min_kd[stock][1]
                  # and one_min_natr_data[stock] > 0.15
                  # and context.bb_percent[stock] < 0.5
                  # and context.daily_support_signal[stock]
                  # and not context.five_day_resist_signal[stock]
                  # and not context.two_day_resist_signal[stock]
                  # and ((not context.five_day_resist_signal[stock]) # Consider previous support becomes resist
                       # or ((context.price_move_signal[stock] == "Spike Up"
                            # or context.price_move_signal[stock] == "Move Up")
                           # and context.volumn_signal[stock]  == "Large Volumn"))
                  # and context.volumn_signal[stock] <> "Small Volumn" # Consider remove this
                  # and (context.price_move_signal[stock] == "Move Up"
                       # or context.price_move_signal[stock] == "Spike Up")
                  # and (context.volumn_signal[stock] == "Large Volumn"
                       # or context.price_move_signal[stock] == "Spike Up")):
                # log.info(str(data[stock].datetime.astimezone(timezone('US/Eastern'))) + "\n"
                         # + "LONG on Daily Support: " + str(stock) + " @" + str(data[stock].price) + "\n"
                         # + "Trend: " + str(context.trend[stock]) + "\n"
                         # + "Price Move: " + str(context.price_move_signal[stock]) + "\n"
                         # + "5-min KD: " + str(five_min_kd_data[stock][0]) + "\n"
                         # + "NATR: " + str(one_min_natr_data[stock]) + "\n"
                         # + "Volumn Signal: " + str(context.volumn_signal[stock]) + "\n"
                         # + "\n\n")
                            
            if ((one_hour_kd_data[stock][0] < 30
                     or (one_hour_kd_data[stock][0] < 50
                           and (context.price_move_signal[stock] == "Spike Up"
                                or context.volumn_signal[stock] == "Large Volumn")))
                and one_hour_kd_data[stock][0] > one_hour_kd_data[stock][1]
                and context.one_hour_kd[stock][0] < context.one_hour_kd[stock][1]
                and one_min_natr_data[stock] > 0.15
                and context.bb_percent[stock] < 0.7
                and context.volumn_signal[stock]  <> "Small Volumn"
                and ((not context.five_day_resist_signal[stock]) # Consider previous support becomes resist
                     or ((context.price_move_signal[stock] == "Spike Up"
                          or context.price_move_signal[stock] == "Move Up")
                         and context.volumn_signal[stock]  == "Large Volumn"))):
                log.info(str(data[stock].datetime.astimezone(timezone('US/Eastern'))) + "\n"
                         + "LONG on Five Day Low: " + str(stock) + " @" + str(data[stock].price) + "\n"
                         + "Trend: " + str(context.trend[stock]) + "\n"
                         + "Price Move: " + str(context.price_move_signal[stock]) + "\n"
                         + "60-min KD: " + str(one_hour_kd_data[stock][0]) + "\n"
                         + "NATR: " + str(one_min_natr_data[stock]) + "\n"
                         + "Volumn Signal: " + str(context.volumn_signal[stock]) + "\n"
                         + "Daily Support Signal: " + str(context.daily_support_signal[stock]) + "\n"
                         + "\n\n")

            # Revisit this and add more filter?
            elif ((five_min_kd_data[stock][0] > 60
                   or (five_min_kd_data[stock][0] > 40
                       and context.price_move_signal[stock] == "Spike Down"))
                and five_min_kd_data[stock][0] < context.five_min_kd[stock][0]
                and five_min_kd_data[stock][0] < five_min_kd_data[stock][1]
                and context.five_min_kd[stock][0] > context.five_min_kd[stock][1]
                and context.bb_percent[stock] > 0.5
                and one_min_natr_data[stock] > 0.15
                and (context.volumn_signal[stock]  <> "Large Volumn"
                     or (context.price_move_signal[stock] == "Spike Down"
                         or context.price_move_signal[stock] == "Move Down"))
                and context.daily_resist_signal[stock]
                and not context.five_day_support_signal[stock]
                and not context.two_day_support_signal[stock]):
                log.info(str(data[stock].datetime.astimezone(timezone('US/Eastern'))) + "\n"
                         + "SHORT on Daily Resist: " + str(stock) + " @" + str(data[stock].price) + "\n"
                         + "Trend: " + str(context.trend[stock]) + "\n"
                         + "Price Move: " + str(context.price_move_signal[stock]) + "\n"
                         + "5-min KD: " + str(five_min_kd_data[stock][0]) + "\n"
                         + "NATR: " +str(one_min_natr_data[stock]) + "\n"
                         + "Volumn Signal: " + str(context.volumn_signal[stock]) + "\n"
                         + "\n\n")

        # Five Day High
        else:              
            # if ((one_hour_kd_data[stock][0] > 70
                     # or (one_hour_kd_data[stock][0] > 50
                         # and context.price_move_signal[stock] == "Spike Down"))
                # and one_hour_kd_data[stock][0] < one_hour_kd_data[stock][1]
                # and context.one_hour_kd[stock][0] > context.one_hour_kd[stock][1]
                # and one_min_natr_data[stock] > 0.15
                # and context.bb_percent[stock] > 0.3
                # and ((not context.five_day_support_signal[stock]) # Consider previous resist becomes support
                     # or context.price_move_signal[stock] == "Spike Down")
                # and context.trend[stock] <> 'Bull' # Revisit this filter
                # # and (context.volumn_signal[stock]  <> "Large Volumn"
                     # # or context.price_move_signal[stock] == "Spike Down")
                # and (context.price_move_signal[stock] == "Move Down"
                     # or context.price_move_signal[stock] == "Spike Down")):
                # log.info(str(data[stock].datetime.astimezone(timezone('US/Eastern'))) + "\n"
                         # + "SHORT on Five Day High: " + str(stock) + " @" + str(data[stock].price) + "\n"
                         # + "Trend: " + str(context.trend[stock]) + "\n"
                         # + "Price Move: " + str(context.price_move_signal[stock]) + "\n"
                         # + "60-min KD: " + str(one_hour_kd_data[stock][0]) + "\n"
                         # + "NATR: " + str(one_min_natr_data[stock]) + "\n"
                         # + "Volumn Rate: " + str(context.volumn_rate[stock]) + "\n"
                         # + "Volumn Signal: " + str(context.volumn_signal[stock]) + "\n"
                         # + "Daily Resist Signal: " + str(context.daily_resist_signal[stock]) + "\n"
                         # + "\n\n")
            
            # elif ((five_min_kd_data[stock][0] > 70
                   # or (five_min_kd_data[stock][0] > 50
                       # and context.price_move_signal[stock] == "Spike Down"))
                # and five_min_kd_data[stock][0] < context.five_min_kd[stock][0]
                # and five_min_kd_data[stock][0] < five_min_kd_data[stock][1]
                # and context.five_min_kd[stock][0] > context.five_min_kd[stock][1]
                # and one_min_natr_data[stock] > 0.15
                # and context.bb_percent[stock] > 0.5
                # and context.daily_resist_signal[stock]
                # and not context.five_day_support_signal[stock]
                # and not context.two_day_support_signal[stock]
                # and ((not context.five_day_support_signal[stock]) # Consider previous resist becomes support
                     # or context.price_move_signal[stock] == "Spike Down")
                # # and (context.volumn_signal[stock]  <> "Large Volumn"
                     # # or context.price_move_signal[stock] == "Spike Down")
                # and (context.trend[stock] <> 'Bull'
                     # or context.price_move_signal[stock] == "Spike Down")
                # and (context.price_move_signal[stock] == "Move Down"
                     # or context.price_move_signal[stock] == "Spike Down")):
                # log.info(str(data[stock].datetime.astimezone(timezone('US/Eastern'))) + "\n"
                         # + "SHORT on Daily Resist: " + str(stock) + " @" + str(data[stock].price) + "\n"
                         # + "Trend: " + str(context.trend[stock]) + "\n"
                         # + "Price Move: " + str(context.price_move_signal[stock]) + "\n"
                         # + "5-min KD: " + str(five_min_kd_data[stock][0]) + "\n"
                         # + "NATR: " +str(one_min_natr_data[stock]) + "\n"
                         # + "Volumn Signal: " + str(context.volumn_signal[stock]) + "\n"
                         # + "\n\n")
                            
            if ((one_hour_kd_data[stock][0] > 70
                     or (one_hour_kd_data[stock][0] > 50
                         and context.price_move_signal[stock] == "Spike Down"))
                and one_hour_kd_data[stock][0] < one_hour_kd_data[stock][1]
                and context.one_hour_kd[stock][0] > context.one_hour_kd[stock][1]
                and one_min_natr_data[stock] > 0.15
                and context.bb_percent[stock] > 0.3
                and ((not context.five_day_support_signal[stock]) # Consider previous resist becomes support
                     or context.price_move_signal[stock] == "Spike Down")
                and context.trend[stock] <> 'Bull' # Revisit this filter
                # and (context.volumn_signal[stock]  <> "Large Volumn"
                     # or context.price_move_signal[stock] == "Spike Down")
                and (context.price_move_signal[stock] == "Move Down"
                     or context.price_move_signal[stock] == "Spike Down")):
                log.info(str(data[stock].datetime.astimezone(timezone('US/Eastern'))) + "\n"
                         + "SHORT on Five Day High: " + str(stock) + " @" + str(data[stock].price) + "\n"
                         + "Trend: " + str(context.trend[stock]) + "\n"
                         + "Price Move: " + str(context.price_move_signal[stock]) + "\n"
                         + "60-min KD: " + str(one_hour_kd_data[stock][0]) + "\n"
                         + "NATR: " + str(one_min_natr_data[stock]) + "\n"
                         + "Volumn Rate: " + str(context.volumn_rate[stock]) + "\n"
                         + "Volumn Signal: " + str(context.volumn_signal[stock]) + "\n"
                         + "Daily Resist Signal: " + str(context.daily_resist_signal[stock]) + "\n"
                         + "\n\n")
            
            elif ((five_min_kd_data[stock][0] < 40
                   or (five_min_kd_data[stock][0] < 60
                           and (context.price_move_signal[stock] == "Spike Up"
                                or context.volumn_signal[stock] == "Large Volumn")))
                  and five_min_kd_data[stock][0] > context.five_min_kd[stock][0]
                  and five_min_kd_data[stock][0] > five_min_kd_data[stock][1]
                  and context.five_min_kd[stock][0] < context.five_min_kd[stock][1]
                  and context.bb_percent[stock] < 0.5
                  and one_min_natr_data[stock] > 0.15
                  and context.volumn_signal[stock]  <> "Small Volumn"
                  and context.daily_support_signal[stock]
                  and not context.five_day_resist_signal[stock]
                  and not context.two_day_resist_signal[stock]):
                log.info(str(data[stock].datetime.astimezone(timezone('US/Eastern'))) + "\n"
                         + "LONG on Daily Support: " + str(stock) + " @" + str(data[stock].price) + "\n"
                         + "Trend: " + str(context.trend[stock]) + "\n"
                         + "Price Move: " + str(context.price_move_signal[stock]) + "\n"
                         + "5-min KD: " + str(five_min_kd_data[stock][0]) + "\n"
                         + "NATR: " +str(one_min_natr_data[stock]) + "\n"
                         + "Volumn Signal: " + str(context.volumn_signal[stock]) + "\n"
                         + "\n\n")
        
        context.five_min_kd[stock] = five_min_kd_data[stock]
        context.ten_min_kd[stock] = ten_min_kd_data[stock]
        context.one_hour_kd[stock] = one_hour_kd_data[stock]

def handle_data(context, data):
    if context.warm_up:
        indicators = [one_hour_kd(data)[sid(8554)][0],
                   ten_min_kd(data)[sid(8554)][0],
                   five_min_kd(data)[sid(8554)][0],
                   two_hour_ma(data)[sid(8554)],
                   one_min_natr(data)[sid(8554)],
                   five_min_atr(data)[sid(8554)],
                   five_min_sma(data)[sid(8554)],
                   five_min_bb(data)[sid(8554)][0]]
        
        for stock in context.stocks:
            if stock in data:
                (context.thirty_min_vol[stock]).append(data[stock].volume)
                (context.six_min_vol[stock]).append(data[stock].volume)
                (context.price_history[stock]).append(data[stock].price)
                (context.ma_history[stock]).append(two_hour_ma(data)[stock])
                 
        for i in indicators:
            if np.isnan(i):
                return
        context.warm_up = False
        reset_context(context, data, False)
        log.info(str(data[sid(37515)].datetime.astimezone(timezone('US/Eastern'))) + "\n" + 
                         "Warming up Finish" + "\n\n")
    
    else:
        current_datetime = get_datetime()
        if current_datetime.hour == 13 and current_datetime.minute == 31:
            reset_context(context, data, True)
            
        if current_datetime.hour == 13 and current_datetime.minute <= 44:
            context.open_suppression = True;
        else:
            context.open_suppression = False;

        find_signal(context, data)
        make_decision(context, data)