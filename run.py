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
    for filename in glob.glob("static/heatloss*"): #removes any files in the directory beginningwith example
        os.remove(filename)
    #Colour
    step_blue = "#00a3af"
    step_gold = "#f8a81d"
    
    # get user inputs
    if request.method=='POST':
        gasuse_total = float(request.form.get('gasuse_total'))
        dhw_annual = float(request.form.get('dhw_annual'))
        balance_point = float(request.form.get('balance_point'))
        furnace_eff = float(request.form.get('furnace_eff'))
        derate = float(request.form.get('derate'))
        location = request.form.get('location')
        heatpumpsize = request.form.get('heatpumpsize')

    # calculate heat loss with defined function
        result = hl_estimate(gasuse_total, dhw_annual, balance_point, furnace_eff, derate, location, heatpumpsize)
                    
        if result[2] <= 0: #No Solution
            html_page = render_template('error.html')
        else:
            m = result[0]
            b = result[1]
            gas_estimate_total = result[2]
            dtemp = result[3]
            heatloss_design = result[4]
            m_hp = result[5]
            b_hp = result[6]
            x_plot = result[7]
                    
            # create plots of results
            x = x_plot
            y = m*x+b
            y2 = m_hp*x+b_hp
            fig,ax = plt.subplots(figsize=(6,4))
            ax.plot(x,y,color=step_blue, label='heat loss')
            ax.plot(x,y2,color=step_gold, label='heat pump capacity')
            ax.set_ylim(0)
            ax.grid(ls='--')
            ax.set_title('Standard Heat Pump Capacity and Estimated Heat Loss')
            ax.set_xlabel('Outdoor Temperature [$^{o}$C]')
            ax.set_ylabel('Heat Loss or Heat Pump Capacity [kBtu/hr]')
            ax.legend()
            fig.tight_layout()
            value = str(randint(0, 100000))
            heatloss_url=f'static/heatloss{value}.png'
            plt.savefig(heatloss_url,transparent=True)
            plt.close()

            # calculate switchover temperature for heat pump size selected
            switchtemp = (b_hp-b)/(m-m_hp)
                
    return render_template('calculator_output.html', heatloss_url=heatloss_url, gas_estimate_total=int(gas_estimate_total), dtemp=dtemp, heatloss_design=round(heatloss_design), gasuse_total=int(gasuse_total), dhw_annual=int(dhw_annual), balance_point=int(balance_point), furnace_eff=furnace_eff, derate=int(derate*100), location=location, heatpumpsize=heatpumpsize, switchtemp=round(switchtemp))

if __name__ == '__main__':
    app.run(debug=True)