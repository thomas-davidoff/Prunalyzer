import prun_funx

username, auth = input("Enter Username"), input("Enter API authorization hash")
prun_funx.username, prun_funx.auth = username, auth
reload = True

extractors, infrastructure, production_buildings, all_production_buildings, buildings = prun_funx.parse('buildings',
                                                                                                        update=reload)
materials, material_list = prun_funx.parse('materials', update=reload)
stations, num_stations, station_list = prun_funx.parse('stations', update=reload)
prices, prices_df = prun_funx.parse('prices', update=reload)
inventory = prun_funx.fetch_inventory(update=reload)
wf_needs = prun_funx.parse('workforce needs', update=reload)  # produces a df
planet_resources = prun_funx.parse('planet_resources', update=reload)

recipes = prun_funx.parse('recipes', info=production_buildings)
building_info = prun_funx.parse('building info', info=all_production_buildings)  # produces a df
workforce = prun_funx.parse('workforce', info=all_production_buildings)  # produces a df
build_cost_matrix = prun_funx.parse('build costs', info=buildings)  # produces a df

# my_production = prun_funx.parse('production',update=False)

selected_station = 'NC1'
print('setting prices to selected station')
prun_funx.setprices(selected_station, materials, prices)
materials_info = prun_funx.materials_df_create(materials)  # produces a df
print('analyzing all recipe profit')
profit_df = prun_funx.calc_recipe_profit(recipes, materials, buildings)  # produces a df

'''Create arbitrage_df'''
print('Analyzing material arbitrage')

arbitrage_df = prun_funx.find_arbitrage(station_list,material_list,materials,prices)

print('creating specific station price dataframes')
# Create just NC1 df for import to rain sheet
nc1_df = prices_df.loc[prices_df['ExchangeCode'] == 'NC1'].reset_index().sort_values('MaterialTicker').set_index(
    'MaterialTicker')
ai1_df = prices_df.loc[prices_df['ExchangeCode'] == 'AI1'].reset_index().sort_values('MaterialTicker').set_index(
    'MaterialTicker')

print('exporting data to excel...')
export = True
filename = 'example_data/all_data.xlsx'
export_list = {
    'BuildingInfo': building_info,
    'WorkforceInfo': workforce,
    'BuildCostMatrix': build_cost_matrix,
    'MaterialInfo': materials_info,
    'Inventory': inventory,
    'WorkforceNeeds': wf_needs,
    'Profit': profit_df,
    'AllPrices': prices_df,
    'Arbitrage': arbitrage_df,
    'NC1Prices': nc1_df,
    'AI1Prices': ai1_df
}

if export:
    prun_funx.update_excel(export_list, filename)

print('Done!')
