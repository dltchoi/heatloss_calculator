def heatloss_estimate (gasuse_total, dhw_monthly, balance_point, furnace_eff, derate, location, heatpumpsize, heatpumpcap_17, heatpumpcap_47):
    import pandas as pd
    import numpy as np
    import math

    estimate_2021=[]
    # import weather data and specify design temperature based on location
    if location == 'toronto':
        toronto_2021 = pd.read_csv("static/2021_toronto_weather.csv",parse_dates=['date_time_local'])
        toronto_2021 = toronto_2021.set_index('date_time_local')
        estimate_2021 = toronto_2021.copy()
        dtemp = -17
    elif location == 'london':
        london_2021 = pd.read_csv("static/2021_london_weather.csv",parse_dates=['date_time_local'])
        london_2021 = london_2021.set_index('date_time_local')
        estimate_2021 = london_2021.copy()
        dtemp = -18
    elif location == 'niagara':
        niagarafalls_2021 = pd.read_csv("static/2021_niagarafalls_weather.csv",parse_dates=['date_time_local'])
        niagarafalls_2021 = niagarafalls_2021.set_index('date_time_local')
        estimate_2021 = niagarafalls_2021.copy()
        dtemp = -16
    
    # standard heat pump performance data points 
    m_15 = (18-10)/(8.3+8.3)
    b_15 = 18-(m_15*8.3)
    m_2 = (23.2-12.6)/(8.3+8.3)
    b_2 = 23.2-(m_2*8.3)
    m_25 = (28.4-16.2)/(8.3+8.3)
    b_25 = 28.4-(m_25*8.3)
    m_3 = (32.8-19)/(8.3+8.3)
    b_3 = 32.8-(m_3*8.3)
    m_35 = (40-24)/(8.3+8.3)
    b_35 = 40-(m_35*8.3)
    m_4 = (44.5-28)/(8.3+8.3)
    b_4 = 44.5-(m_4*8.3)
    m_5 = (59-36)/(8.3+8.3)
    b_5 = 59-(m_5*8.3)

    # gather data based on user heat pump size selections
    m_list = []
    b_list = []
    for i in heatpumpsize:
        if float(i) == 1.5:
            m_list.append(m_15)
            b_list.append(b_15)
        elif float(i) == 2:
            m_list.append(m_2)
            b_list.append(b_2)
        elif float(i) == 2.5:
            m_list.append(m_25)
            b_list.append(b_25)
        elif float(i) == 3:
            m_list.append(m_3)
            b_list.append(b_3)
        elif float(i) == 3.5:
            m_list.append(m_35)
            b_list.append(b_35)
        elif float(i) == 4:
            m_list.append(m_4)
            b_list.append(b_4)
        elif float(i) == 5:
            m_list.append(m_5)
            b_list.append(b_5)

    # import heat pump capacities based on user input
    m_hp = (heatpumpcap_47-heatpumpcap_17)/(8.3+8.3)
    b_hp = heatpumpcap_47-(m_hp*8.3)

    # calculate annual gas use from furnace
    dhw_annual = dhw_monthly*12
    gasuse_annual = gasuse_total - dhw_annual
    
    # define variables and state first heat loss guess
    heatloss_guess = 10 # kBtu/hr - first guess of heat loss at -15C (not a reasonable guess, but a relatively low value to reduce runtime)
    gas_estimate_total = 0
    
    # loop through different heat loss estimates until annual usage estimate is close to the user input
    while int(gas_estimate_total) < gasuse_annual*(1+(derate/100)):
        heatloss_guess += 1
        # estimate heat loss slope and intercept with each guess
        m = (heatloss_guess - 0)/(-15 - balance_point)
        b = 0 - (m * balance_point)
    
    # estimate hourly heat loss based on weather data
        heatloss = []
        for x in estimate_2021.temperature:
            if x > balance_point:
                heatloss.append(0)
            else:
                heatloss.append(m * x + b)
        estimate_2021['heatloss'] = heatloss
        estimate_2021['gas_m3'] = estimate_2021.heatloss * (1/3.41) * (1/10.5) * (1/(furnace_eff/100))
    
    # calculate total annual estimated gas use
        gas_estimate_total = estimate_2021.gas_m3.sum()

        if int(gas_estimate_total) == gasuse_annual*(1+(derate/100)):
            break
    
    # calculate design heat loss 
    heatloss_design = (m * dtemp) + b

    # create output variables for plotting
    x_plot = np.linspace(-30,30,10)
    
    return [m, b, dtemp, heatloss_design, m_hp, b_hp, x_plot, m_list, b_list]