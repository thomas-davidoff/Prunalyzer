import numpy as np
import pandas as pd

import prun_funx

username, auth = input("Enter Username"), input("Enter API authorization hash")
prun_funx.username, prun_funx.auth = username, auth

extractors, infrastructure, production_buildings, all_production_buildings, buildings = prun_funx.parse('buildings', update=True)
materials = prun_funx.parse('materials', update=True)
material_list = [k for k in materials.keys()]
stations, num_stations, station_list = prun_funx.parse('stations', update=True)
prices, prices_df = prun_funx.parse('prices', update=True)
inventory = prun_funx.fetch_inventory(update=True)
recipes = prun_funx.parse('recipes', info=production_buildings)
wf_needs = prun_funx.parse('workforce needs')  # produces a df
building_info = prun_funx.parse('building info', info=all_production_buildings)  # produces a df
workforce = prun_funx.parse('workforce', info=all_production_buildings)  # produces a df
build_cost_matrix = prun_funx.parse('build costs', info=buildings)  # produces a df
#my_production = prun_funx.parse('production',update=False)

'''Will need to find a way to change the station and simultaneously update all prices and dependant calculations!'''
selected_station = 'NC1'
prun_funx.setprices(selected_station, materials, prices)
materials_info = prun_funx.materials_df_create(materials)  # produces a df

profit_df = prun_funx.calc_recipe_profit(recipes, materials, buildings)  # produces a df

'''Create arbitrage_df'''
arbitrage_list = []
for station in station_list:
    start = station
    ends = [s for s in station_list if s != start]
    for end in ends:
        '''create list to convert to pd.Series and append to arbitrage DataFrane
        arbitrage df will have first three columns sharing indexes, with each row representing a unique combination
        of starting and ending exchanges for all materials.

        This could not be accomplished in a list comprehension because of too much variability between the
        material datasets and their relevant prices. For example, the ticker 'CMK.NC1' does not appear in the
        price dictionary when setting prices, and thus does not appear in the prices dictionary. This is because
        when building the prices dictionary I used another dictionary comprehension to create objects out of all
        the materials and could not account for missing/variable values'''
        start_average_array, end_average_array, start_ask_array, end_bid_array = [], [], [], []
        start_supply, end_demand, weight, volume = [], [], [], []

        for m in material_list:
            start_ticker = f'{m}.{start}'
            end_ticker = f'{m}.{end}'
            weight.append(materials[m].weight)
            volume.append(materials[m].volume)

            if start_ticker in prices:
                start_average_array.append(prices[start_ticker].price)
                start_supply.append(prices[start_ticker].supply)
                start_ask_array.append(prices[start_ticker].ask)
            else:
                start_average_array.append(np.nan)
                start_supply.append(np.nan)
                start_ask_array.append(np.nan)
            if end_ticker in prices:
                end_average_array.append(prices[end_ticker].price)
                end_bid_array.append(prices[end_ticker].bid)
                end_demand.append(prices[end_ticker].demand)
            else:
                end_average_array.append(np.nan)
                end_bid_array.append(np.nan)
                end_demand.append(np.nan)

        df_to_add = pd.DataFrame({'start': start,
                                  'end': end,
                                  'material': material_list,
                                  'startAverage': start_average_array,
                                  'startAsk': start_ask_array,
                                  'startSupply':start_supply,
                                  'endAverage': end_average_array,
                                  'endBid': end_bid_array,
                                  'endDemand': end_demand,
                                  'weight':weight,
                                  'volume':volume
                                  })
        arbitrage_list.append(df_to_add)
arbitrage_df = pd.concat(arbitrage_list)
spread_factor = 0.1
volume_factor = 100
cargo_capacity = 500

arbitrage_df['Status'] = 'Normal'
reliability_filter = (arbitrage_df.startAverage * (1-spread_factor) < arbitrage_df.startAsk) & (
            arbitrage_df.startAverage * (1+spread_factor) > arbitrage_df.startAsk) & (
                   arbitrage_df.endAverage * (1-spread_factor) < arbitrage_df.endBid) & (
                   arbitrage_df.endAverage * (1+spread_factor) > arbitrage_df.endBid)
profitable_reliable_filter = reliability_filter & (arbitrage_df['startAsk'] < arbitrage_df['endBid'])
arbitrage_df.loc[~reliability_filter, 'Status'] = 'Off Average'
arbitrage_df.loc[profitable_reliable_filter, 'Status'] = 'ARBITRAGE'
volume_filter = (arbitrage_df.startSupply > volume_factor) & (arbitrage_df.endDemand > volume_factor)

arbitrage_df['Profit'] = arbitrage_df['endBid'] - arbitrage_df['startAsk']
arbitrage_df['ProfitMargin'] = arbitrage_df['Profit'] / arbitrage_df['endBid']
arbitrage_df['ProfitFullCargo'] = arbitrage_df['Profit'] * (cargo_capacity/arbitrage_df['weight'])
volume_profit_filter = volume_filter & (arbitrage_df.Profit > 0)
arbitrage_df = arbitrage_df.loc[volume_profit_filter]
export = True
export_list = {
    'BuildingInfo': building_info,
    'WorkforceInfo': workforce,
    'BuildcostMatrix': build_cost_matrix,
    'MaterialInfo': materials_info,
    'Inventory': inventory,
    'WorkforceNeeds': wf_needs,
    'Profit': profit_df,
    'AllPrices': prices_df,
    'Arbitrage': arbitrage_df
}

if export:
    prun_funx.update_excel(export_list)
