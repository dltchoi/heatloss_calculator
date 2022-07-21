def heatloss_estimate (gasuse_total, dhw_annual, balance_point, furnace_eff, derate, location, heatpumpsize):
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
    
    # import heat pump capacities based on size selected
    if heatpumpsize == '1.5':
        m_hp = (18-10)/(8.3+8.3)
        b_hp = 18-(m_hp*8.3)
    elif heatpumpsize =='2':
        m_hp = (23.2-12.6)/(8.3+8.3)
        b_hp = 23.2-(m_hp*8.3)
    elif heatpumpsize =='3':
        m_hp = (32.8-19)/(8.3+8.3)
        b_hp = 32.8-(m_hp*8.3)
    elif heatpumpsize =='4':
        m_hp = (44.5-28)/(8.3+8.3)
        b_hp = 44.5-(m_hp*8.3)
    elif heatpumpsize =='5':
        m_hp = (59-36)/(8.3+8.3)
        b_hp = 59-(m_hp*8.3)

    # calculate annual gas use from furnace
    gasuse_annual = gasuse_total - dhw_annual
    
    # define variables and state first heat loss guess
    heatloss_guess = 10 # kBtu/hr - first guess of heat loss at -15C (not a reasonable guess, but a relatively low value to reduce runtime)
    gas_estimate_total = 0
    
    # loop through different heat loss estimates until annual usage estimate is close to the user input
    while int(gas_estimate_total) < gasuse_annual*(1+derate):
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
        estimate_2021['gas_m3'] = estimate_2021.heatloss * (1/3.41) * (1/10.5) * (1/furnace_eff)
    
    # calculate total annual estimated gas use
        gas_estimate_total = estimate_2021.gas_m3.sum()

        if int(gas_estimate_total) == gasuse_annual*(1+derate):
            break
    
    # calculate design heat loss 
    heatloss_design = (m * dtemp) + b

    # create output variables for plotting
    x_plot = np.linspace(-20,20,10)
    
    
    return [m, b, gas_estimate_total, dtemp, heatloss_design, m_hp, b_hp, x_plot]