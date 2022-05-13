import prun_funx

username, auth = input("Enter Username"), input("Enter API authorization hash")
prun_funx.username, prun_funx.auth = username, auth

extractors, infrastructure, production_buildings, all_production_buildings, buildings = prun_funx.parse('buildings')
materials = prun_funx.parse('materials')
stations, num_stations, station_list = prun_funx.parse('stations')
prices = prun_funx.parse('prices', update=False)
inventory = prun_funx.fetch_inventory(update=False)
recipes = prun_funx.parse('recipes', info = production_buildings)
wf_needs = prun_funx.parse('workforce needs') # produces a df
building_info = prun_funx.parse('building info', info = production_buildings) # produces a df
workforce = prun_funx.parse('workforce', info = all_production_buildings) # produces a df
build_cost_matrix = prun_funx.parse('build costs', info = buildings) # produces a df
materials_info = prun_funx.materials_df_create(materials)

'''Will need to find a way to change the station and simultaneously update all prices and dependant calculations!'''
selected_station = 'NC1'
prun_funx.setprices(selected_station, materials, prices)

profit_df = prun_funx.calc_recipe_profit(recipes, materials, buildings)

export = True
export_list = {
    'BuildingInfo': building_info,
    'WorkforceInfo': workforce,
    'BuildcostMatrix': build_cost_matrix,
    'MaterialInfo': materials_info,
    'Inventory': inventory
}

if export:
    prun_funx.update_excel(export_list)
