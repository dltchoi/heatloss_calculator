from traceback import format_list
from flask import Flask, request, render_template, make_response
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
from random import randint
import os, glob
from calculator import heatloss_estimate as hl_estimate

app = Flask(__name__)

@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html')

@app.route("/aboutus")
def aboutus():
    return render_template('aboutus.html')

@app.route("/contact")
def contact():
    return render_template('contact.html')

@app.route("/methodology")
def methodology():
    return render_template('methodology.html')

@app.route("/error")
def error():
    return render_template('error.html')

@app.route("/calculator")
def calculator():
    return render_template('calculator.html')

@app.route("/calculator_output", methods=["GET","POST"])
def calculator_output():
    for filename in glob.glob("static/heatloss*"): #removes any files in the directory beginning with example
        os.remove(filename)
    for filename in glob.glob("static/heatenergy*"):
        os.remove(filename)
    for filename in glob.glob("static/customheatenergy*"): 
        os.remove(filename)
    for filename in glob.glob("static/heatdist*"): 
        os.remove(filename)

    #Colour
    step_blue = "#00a3af"
    step_gold = "#f8a81d"
    
    # get user inputs
    if request.method=='POST':
        gasuse_total = float(request.form.get('gasuse_total'))
        dhw_monthly = float(request.form.get('dhw_monthly'))
        balance_point = float(request.form.get('balance_point'))
        furnace_eff = float(request.form.get('furnace_eff'))
        derate = float(request.form.get('derate'))
        location = request.form.get('location')
        heatpumpsize = request.form.getlist('heatpumpsize')
        heatpumpcap_17_c1 = float(request.form.get('heatpumpcap_17_c1'))
        heatpumpcap_47_c1 = float(request.form.get('heatpumpcap_47_c1'))
        heatpumpcap_17_c2 = float(request.form.get('heatpumpcap_17_c2'))
        heatpumpcap_47_c2 = float(request.form.get('heatpumpcap_47_c2'))
        heatpumpcap_17_c3 = float(request.form.get('heatpumpcap_17_c3'))
        heatpumpcap_47_c3 = float(request.form.get('heatpumpcap_47_c3'))
        mintemp_c1 = float(request.form.get('mintemp_c1'))
        mintemp_c2 = float(request.form.get('mintemp_c2'))
        mintemp_c3 = float(request.form.get('mintemp_c3'))
        hp_derate = float(request.form.get('hp_derate'))
        derate_c1 = float(request.form.get('derate_c1'))
        derate_c2 = float(request.form.get('derate_c2'))
        derate_c3 = float(request.form.get('derate_c3'))

    # calculate heat loss with defined function
        result = hl_estimate(gasuse_total, dhw_monthly, balance_point, furnace_eff, derate, location, heatpumpsize, heatpumpcap_17_c1, heatpumpcap_47_c1, heatpumpcap_17_c2, heatpumpcap_47_c2, heatpumpcap_17_c3, heatpumpcap_47_c3, hp_derate, derate_c1, derate_c2, derate_c3)
                    
        m = result[0]
        b = result[1]
        dtemp = result[2]
        heatloss_design = result[3]
        m_hp_1 = result[4]
        b_hp_1 = result[5]
        m_hp_2 = result[6]
        b_hp_2 = result[7]
        m_hp_3 = result[8]
        b_hp_3 = result[9]
        x_plot = result[10]
        x_std = result[11]
        m_list = result[12]
        b_list = result[13]
        heatloss_annual = result[14]
        estimate_2021 = result[15]
        heatload_dist = result[16]
        gasuse_annual = result[17]
        derate_c1 = result[18]
        derate_c2 = result[19]
        derate_c3 = result[20]
        location_name = result[21]
                    
        # create plots of results
        x = x_plot
        x1 = np.linspace(mintemp_c1,balance_point,20)
        x2 = np.linspace(mintemp_c2,balance_point,20)
        x3 = np.linspace(mintemp_c3,balance_point,20)
        y = m*x+b
        # building load plot
        fig,ax = plt.subplots(figsize=(10,7))
        ax.plot(x,y,color='red', linewidth=2, label='Heat loss')

        # calculate total annual heating load for 2021
        GJ_total = heatload_dist.GJ.sum()
        kbtu_total = heatload_dist.kbtu.sum()

        switchtemp_1 = -999
        switchtemp_2 = -999
        switchtemp_3 = -999
        # create list of temperatures for the custom input values
        ctemps = [-8.3,8.3]
        if m_hp_1 > 0:
            # calculate heat pump capacity curve
            y_hp = m_hp_1*x1+b_hp_1
            # calculate switchover temperature
            switchtemp_1 = (b_hp_1-b)/(m-m_hp_1)
            switchtemp_1 = round(switchtemp_1)
            # calculate heat pump capacity below switchover temperature (for electric back-up scenario)

            # add heat pump performance capacity to building load plot
            ax.plot(x1,y_hp, label='Custom heat pump capacity - 1')

            # calculate heat pump capacity below switchover temperature (for electric back-up scenario)
            e_req_list1 = []
            e_hp_list1 = []
            for e in heatload_dist.temp:
                if mintemp_c1 < e < switchtemp_1:
                    e_y = m*e+b
                    e_y_hp = m_hp_1*e+b_hp_1
                elif e < mintemp_c1:
                    e_y = m*e+b
                    e_y_hp = 0
                elif e > switchtemp_1:
                    e_y = 0
                    e_y_hp = 0
                e_cap = e_y - e_y_hp
                # capacity needed to top up heat pump below switchover temp
                e_req_list1.append(e_cap)
                # heat pump capacity below switchover temp
                e_hp_list1.append(e_y_hp)
            
            # convert from kbtu/hr to kbtu
            heatload_dist['e_hp_belowswitch'] = e_hp_list1*heatload_dist.hours*heatload_dist.hours
            heatload_dist['e_req_belowswitch'] = e_req_list1*heatload_dist.hours*heatload_dist.hours
            # calculate percentage of heating required above and below switchover temperature for furnace backup scenario
            p_hp = round((heatload_dist.loc[heatload_dist.temp >= switchtemp_1].GJ.sum()/GJ_total)*100)
            p_f = 100 - p_hp
            # calculate percentage of heating provided by heat pump and elec resistance
            p_e = round((heatload_dist.e_req_belowswitch.sum()/kbtu_total)*100)
            p_ehp = round((heatload_dist.e_hp_belowswitch.sum()/kbtu_total)*100) + p_hp

            # create a list of parameters to display on output page
            caps_c1 = [heatpumpcap_17_c1,heatpumpcap_47_c1]
            curve1 = zip(caps_c1,ctemps)
            curve1_result = zip([switchtemp_1],[p_hp],[p_ehp])
        else:
            switchtemp_1 = 'None'
            curve1 = []
            curve1_result = []
        
        if m_hp_2 > 0:
            y_hp = m_hp_2*x2+b_hp_2
            switchtemp_2 = (b_hp_2-b)/(m-m_hp_2)
            switchtemp_2 = round(switchtemp_2)
            # add heat pump performance capacity to building load plot
            ax.plot(x2,y_hp, label='Custom heat pump capacity - 2')

            # calculate heat pump capacity below switchover temperature (for electric back-up scenario)
            e_req_list2 = []
            e_hp_list2 = []
            for e in heatload_dist.temp:
                if mintemp_c2 < e < switchtemp_2:
                    e_y = m*e+b
                    e_y_hp = m_hp_2*e+b_hp_2
                elif e < mintemp_c2:
                    e_y = m*e+b
                    e_y_hp = 0
                elif e > switchtemp_2:
                    e_y = 0
                    e_y_hp = 0
                e_cap = e_y - e_y_hp
                # capacity needed to top up heat pump below switchover temp
                e_req_list2.append(e_cap)
                # heat pump capacity below switchover temp
                e_hp_list2.append(e_y_hp)
            
            # convert from kbtu/hr to kbtu
            heatload_dist['e_hp_belowswitch'] = e_hp_list2*heatload_dist.hours*heatload_dist.hours
            heatload_dist['e_req_belowswitch'] = e_req_list2*heatload_dist.hours*heatload_dist.hours

            # calculate percentage of heating required above and below switchover temperature
            p_hp = round((heatload_dist.loc[heatload_dist.temp >= switchtemp_2].GJ.sum()/GJ_total)*100)
            p_f = 100 - p_hp
            # calculate percentage of heating provided by heat pump and elec resistance
            p_e = round((heatload_dist.e_req_belowswitch.sum()/kbtu_total)*100)
            p_ehp = round((heatload_dist.e_hp_belowswitch.sum()/kbtu_total)*100) + p_hp
            
            # create a list of parameters to display on output page
            caps_c2 = [heatpumpcap_17_c2,heatpumpcap_47_c2]
            curve2 = zip(caps_c2,ctemps)
            curve2_result = zip([switchtemp_2],[p_hp],[p_ehp])
        else:
            switchtemp_2 = []
            curve2 = []
            curve2_result = []

        if m_hp_3 > 0:
            # calculate heat pump capacity curve
            y_hp = m_hp_3*x3+b_hp_3
            # calculate switchover temperature
            switchtemp_3 = (b_hp_3-b)/(m-m_hp_3)
            switchtemp_3 = round(switchtemp_3)

            # add heat pump performance capacity to building load plot
            ax.plot(x3,y_hp, label='Custom heat pump capacity - 3')

            # calculate heat pump capacity below switchover temperature (for electric back-up scenario)
            e_req_list3 = []
            e_hp_list3 = []
            for e in heatload_dist.temp:
                if mintemp_c3 < e < switchtemp_3:
                    e_y = m*e+b
                    e_y_hp = m_hp_3*e+b_hp_3
                elif e < mintemp_c3:
                    e_y = m*e+b
                    e_y_hp = 0
                elif e > switchtemp_3:
                    e_y = 0
                    e_y_hp = 0
                e_cap = e_y - e_y_hp
                # capacity needed to top up heat pump below switchover temp
                e_req_list3.append(e_cap)
                # heat pump capacity below switchover temp
                e_hp_list3.append(e_y_hp)
            
            # convert from kbtu/hr to kbtu
            heatload_dist['e_hp_belowswitch'] = e_hp_list3*heatload_dist.hours*heatload_dist.hours
            heatload_dist['e_req_belowswitch'] = e_req_list3*heatload_dist.hours*heatload_dist.hours
            # calculate percentage of heating required above and below switchover temperature for furnace back-up scenario
            p_hp = round((heatload_dist.loc[heatload_dist.temp >= switchtemp_3].kbtu.sum()/kbtu_total)*100)
            p_f = 100 - p_hp
            # calculate percentage of heating provided by heat pump and elec resistance
            p_e = round((heatload_dist.e_req_belowswitch.sum()/kbtu_total)*100)
            p_ehp = round((heatload_dist.e_hp_belowswitch.sum()/kbtu_total)*100) + p_hp
            
            # create a list of parameters to display on output page
            caps_c3 = [heatpumpcap_17_c3,heatpumpcap_47_c3]
            curve3 = zip(caps_c3,ctemps)
            curve3_result = zip([switchtemp_3],[p_hp],[p_ehp])
        else:
            switchtemp_3 = []
            curve3 = []
            curve3_result = []

        switchtemp_list = []
        e_req_list = []
        e_hp_list = []
        f_frac_list = []
        hp_frac_list = []
        e_frac_list = []
        ehp_frac_list = []

        for ml,bl,hp in zip(m_list, b_list, heatpumpsize):
            # calculate switchover temperatures for heat pump sizes selected from available options
            switch = (bl-b)/(m-ml)
            switch = round(switch)
            switchtemp_list.append(switch)
            # calculate heat pump capacity curve for each heat pump size selected
            y_list = ml*x_std+bl
            # plots the capacity curve(s)
            ax.plot(x_std,y_list, label=str(hp)+' ton heat pump')
            # calculate heat pump capacity below switchover temperature (for electric back-up scenario)
            e_req_list = []
            e_hp_list = []
            for e in heatload_dist.temp:
                if -15 <= e < switch:
                    e_y = m*e+b
                    e_y_hp = ml*e+bl
                elif e < -15:
                    e_y = m*e+b
                    e_y_hp = 0
                elif e > switch:
                    e_y = 0
                    e_y_hp = 0
                e_req = e_y - e_y_hp
                # capacity needed to top up heat pump below switchover temp
                e_req_list.append(e_req)
                # heat pump capacity below switchover temp
                e_hp_list.append(e_y_hp)

            # convert heat pump capacity and required heating from kbtu/hr to kbtu
            heatload_dist['e_hp_belowswitch'] = e_hp_list*heatload_dist.hours*heatload_dist.hours
            heatload_dist['e_req_belowswitch'] = e_req_list*heatload_dist.hours*heatload_dist.hours

            # calculate percentage of heating required above and below switchover temperature for furnace back-up scenario
            p_hp = round((heatload_dist.loc[heatload_dist.temp >= switch].kbtu.sum()/kbtu_total)*100)
            p_f = 100 - p_hp
            f_frac_list.append(p_f)
            hp_frac_list.append(p_hp)
            # calculate percentage of heating provided by heat pump and elec resistance
            p_ehp = round((heatload_dist.e_hp_belowswitch.sum()/kbtu_total)*100) + p_hp
            p_e = round((heatload_dist.e_req_belowswitch.sum()/kbtu_total)*100)
            e_frac_list.append(p_e)
            ehp_frac_list.append(p_ehp)

        # zip together heat pump parameters to display on output page
        ziplist = zip(switchtemp_list,heatpumpsize,hp_frac_list,ehp_frac_list)

        ax.set_ylim(0)
        ax.grid(ls='--')
        ax.set_title('Heat Pump Capacity and Estimated Heat Loss', fontsize=19)
        ax.set_xlabel('Outdoor Temperature [\N{DEGREE SIGN}C]', fontsize=17)
        ax.set_ylabel('Heat Loss or Heat Pump Capacity [kBTU/hr]', fontsize=17)
        ax.legend(loc='best', framealpha=0.2, fontsize=12)
        fig.tight_layout()
        value = str(randint(0, 100000))
        heatloss_url=f'static/heatloss{value}.png'
        plt.savefig(heatloss_url,transparent=True)
        plt.close()

        # create histogram plot of outdoor temperature and annual heating required
        fig4,ax4 = plt.subplots(figsize=(10,7))
        ax4.bar(heatload_dist.loc[heatload_dist.temp < balance_point].temp,(heatload_dist.loc[heatload_dist.temp < balance_point].kbtu/kbtu_total)*100, color = step_blue,)
        ax4.grid()
        ax4.set_title('Average Annual Heating Load Distribution (2017 - 2021)', fontsize=19)
        ax4.set_ylabel('Fraction of Annual Heating Required (%)', fontsize=17)
        ax4.set_xlabel('Outdoor Temperature [\N{DEGREE SIGN}C]', fontsize=17)
        fig4.tight_layout()
        value = str(randint(0, 100000))
        heatdist_url=f'static/heatdist{value}.png'
        plt.savefig(heatdist_url,transparent=True)
        plt.close()

    return render_template('calculator_output.html', heatloss_url=heatloss_url, heatdist_url=heatdist_url, dtemp=dtemp, heatloss_design=round(heatloss_design), gasuse_total=int(gasuse_total), dhw_annual=int(dhw_monthly*12), balance_point=int(balance_point), furnace_eff=furnace_eff, derate=round(derate), hp_derate=round(hp_derate), derate_c1=derate_c1, derate_c2=derate_c2, derate_c3=derate_c3, heatpumpsize=heatpumpsize, switchlist=switchtemp_list, curve1=curve1, curve2=curve2, curve3=curve3, curve1_result=curve1_result, curve2_result=curve2_result, curve3_result=curve3_result, ziplist=ziplist, gasuse_annual=round(gasuse_annual), location_name=location_name)

if __name__ == '__main__':
    app.run(debug=True)