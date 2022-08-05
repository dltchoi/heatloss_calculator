def heatloss_estimate (gasuse_total, dhw_monthly, balance_point, furnace_eff, hl_derate, location, heatpumpsize, heatpumpcap_17_c1, heatpumpcap_47_c1, heatpumpcap_17_c2, heatpumpcap_47_c2, heatpumpcap_17_c3, heatpumpcap_47_c3, hp_derate):
    import pandas as pd
    import numpy as np
    import math
    from datetime import datetime
    import datetime

    estimate_2021=[]
    # import weather data and specify design temperature based on location
    if location == 'toronto':
        estimate_2021 = pd.read_csv("static/2021_toronto_weather.csv",parse_dates=['date_time_local'])
        estimate_2021 = estimate_2021.set_index('date_time_local')
        estimate_2021 = estimate_2021.copy()
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
    elif location == 'sudbury':
        sudbury_2021 = pd.read_csv("static/2021_sudbury_weather.csv",parse_dates=['date_time_local'])
        sudbury_2021 = sudbury_2021.set_index('date_time_local')
        estimate_2021 = sudbury_2021.copy()
        dtemp = -25
    
    # standard heat pump performance data points
    hp_derate = hp_derate/100 # convert heat pump derate
    m_15 = ((18-10)*hp_derate)/(8.3+8.3)
    b_15 = (18*hp_derate)-(m_15*8.3)
    m_2 = ((23.2-12.6)*hp_derate)/(8.3+8.3)
    b_2 = (23.2*hp_derate)-(m_2*8.3)
    m_25 = ((28.4-16.2)*hp_derate)/(8.3+8.3)
    b_25 = (28.4*hp_derate)-(m_25*8.3)
    m_3 = ((32.8-19)*hp_derate)/(8.3+8.3)
    b_3 = (32.8*hp_derate)-(m_3*8.3)
    m_35 = ((40-24)*hp_derate)/(8.3+8.3)
    b_35 = (40*hp_derate)-(m_35*8.3)
    m_4 = ((44.5-28)*hp_derate)/(8.3+8.3)
    b_4 = (44.5*hp_derate)-(m_4*8.3)
    m_5 = ((59-36)*hp_derate)/(8.3+8.3)
    b_5 = (59*hp_derate)-(m_5*8.3)

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

    # import heat pump capacities and capacity derate based on user input
    if (heatpumpcap_17_c1 > 0) & (heatpumpcap_47_c1 > 0):
        m_hp_1 = ((heatpumpcap_47_c1-heatpumpcap_17_c1)*hp_derate)/(8.3+8.3)
        b_hp_1 = (heatpumpcap_47_c1*hp_derate)-(m_hp_1*8.3)
    else:
        m_hp_1 = -999
        b_hp_1 = -999
    
    if (heatpumpcap_17_c2 > 0) & (heatpumpcap_47_c2 > 0):
        m_hp_2 = ((heatpumpcap_47_c2-heatpumpcap_17_c2)*hp_derate)/(8.3+8.3)
        b_hp_2 = (heatpumpcap_47_c2*hp_derate)-(m_hp_2*8.3)
    else:
        m_hp_2 = -999
        b_hp_2 = -999

    if (heatpumpcap_17_c3 > 0) & (heatpumpcap_47_c3 > 0):
        m_hp_3 = ((heatpumpcap_47_c3-heatpumpcap_17_c3)*hp_derate)/(8.3+8.3)
        b_hp_3 = (heatpumpcap_47_c3*hp_derate)-(m_hp_3*8.3)
    else:
        m_hp_3 = -999
        b_hp_3 = -999

    # calculate annual gas use from furnace
    dhw_annual = dhw_monthly*12
    gasuse_annual = gasuse_total - dhw_annual
    
    # define variables and state first heat loss guess
    heatloss_guess = 10 # kBtu/hr - first guess of heat loss at -15C (not a reasonable guess, but a relatively low value to reduce runtime)
    gas_estimate_total = 0
    
    # loop through different heat loss estimates until annual usage estimate is close to the user input
    while int(gas_estimate_total) < gasuse_annual*(1+(hl_derate/100)):
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

        if int(gas_estimate_total) == gasuse_annual*(1+(hl_derate/100)):
            break

    # calculate total annual heat loss (needed for histogram plot)
    heatloss_annual = estimate_2021.heatloss.sum()

    # calculate design heat loss 
    heatloss_design = (m * dtemp) + b

    # create output variables for plotting
    x_plot = np.linspace(-30,balance_point,20)
    x_std = np.linspace(-15,balance_point,20)

    # create dataframe for plotting heat load distribution histogram
    bin_midpoints = np.arange(-29.5,balance_point,1)
    hours = []
    load = []
    for mid_point in bin_midpoints:
        hour_count = 0
        load_sum = 0
        for temp,hl in zip(estimate_2021['temperature'],estimate_2021['heatloss']):
            if (temp >= (mid_point - 0.5)) & (temp < mid_point + 0.5):
                hour_count = hour_count + 1
                load_sum = load_sum + hl
        hours.append(hour_count)
        load.append(load_sum)
    hours_dict = {
        'temp':bin_midpoints,
        'hours': hours,
        'load':load}
    heatload_dist = pd.DataFrame(hours_dict)
    # calculate heat load required in GJ
    # multiply number of hours by kBTU/hr load to get kBTU then convert to GJ using a factor of 0.001055
    heatload_dist['GJ'] = heatload_dist.hours*heatload_dist.load*0.001055    
    heatload_dist['kbtu'] = heatload_dist.hours*heatload_dist.load

    return [m, b, dtemp, heatloss_design, m_hp_1, b_hp_1, m_hp_2, b_hp_2, m_hp_3, b_hp_3, x_plot, x_std, m_list, b_list, heatloss_annual, estimate_2021, heatload_dist]