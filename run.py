from flask import Flask, request, render_template, make_response
from matplotlib import pyplot as plt
from random import randint
import os, glob
from calculator import heatloss_estimate as hl_estimate

app = Flask(__name__)

@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html')

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
        heatpumpcap_17 = float(request.form.get('heatpumpcap_17'))
        heatpumpcap_47 = float(request.form.get('heatpumpcap_47'))

    # calculate heat loss with defined function
        result = hl_estimate(gasuse_total, dhw_monthly, balance_point, furnace_eff, derate, location, heatpumpsize, heatpumpcap_17, heatpumpcap_47)
                    
        m = result[0]
        b = result[1]
        dtemp = result[2]
        heatloss_design = result[3]
        m_hp = result[4]
        b_hp = result[5]
        x_plot = result[6]
        m_list = result[7]
        b_list = result[8]
                    
        # create plots of results
        x = x_plot
        y = m*x+b
        
        fig,ax = plt.subplots(figsize=(10,7))
        ax.plot(x,y,color=step_blue, label='heat loss')

        switchtemp = -99      
        if m_hp > 0:
            y_hp = m_hp*x+b_hp
            switchtemp = (b_hp-b)/(m-m_hp)
            switchtemp = round(switchtemp)
            ax.plot(x,y_hp,color=step_gold, label='custom heat pump capacity')
        else:
            switchtemp = 'None'
            heatpumpcap_17 = 'None'
            heatpumpcap_47 = 'None'

        switchtemp_list = []
        for ml,bl,hp in zip(m_list, b_list, heatpumpsize):
            switch = (bl-b)/(m-ml)
            switchtemp_list.append(round(switch))
            y_list = ml*x+bl
            ax.plot(x,y_list, label=str(hp)+' ton heat pump')
        
        ziplist = zip(switchtemp_list,heatpumpsize)

        ax.set_ylim(0)
        ax.grid(ls='--')
        ax.set_title('Heat Pump Capacity and Estimated Heat Loss', fontsize=19)
        ax.set_xlabel('Outdoor Temperature [\N{DEGREE SIGN}C]', fontsize=16)
        ax.set_ylabel('Heat Loss or Heat Pump Capacity [kBTU/hr]', fontsize=16)
        ax.legend(loc='best', framealpha=0.2, fontsize=12)
        fig.tight_layout()
        value = str(randint(0, 100000))
        heatloss_url=f'static/heatloss{value}.png'
        plt.savefig(heatloss_url,transparent=True)
        plt.close()

    return render_template('calculator_output.html', heatloss_url=heatloss_url, dtemp=dtemp, heatloss_design=round(heatloss_design), gasuse_total=int(gasuse_total), dhw_annual=int(dhw_monthly*12), balance_point=int(balance_point), furnace_eff=furnace_eff, derate=derate, location=location.capitalize(), heatpumpcap_17=heatpumpcap_17, heatpumpcap_47=heatpumpcap_47, switchtemp=switchtemp, heatpumpsize=heatpumpsize, switchlist=switchtemp_list, ziplist=ziplist)

if __name__ == '__main__':
    app.run(debug=True)
