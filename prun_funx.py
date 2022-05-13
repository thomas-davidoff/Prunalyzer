import prun_classes
import json
import requests
import pandas as pd
import numpy as np

auth = None
username = None


def fetch_data(keyword, authorization, update=False):
    if update:
        # request headers - json content type and authorization dict
        my_headers = {'Accept': 'application/json', 'Authorization': auth}
        # base_url of API
        base_url = 'https://rest.fnar.net'
        keywords_dict = {
            'buildings': '/building/allbuildings',
            'prices': '/exchange/all',
            'materials': '/material/allmaterials',
            'stations': '/exchange/station',
            'workforce needs': '/global/workforceneeds'
        }
        path = keywords_dict[keyword]
        url = base_url + path
        data = requests.get(url, headers=my_headers).json()
        json_string = json.dumps(data)
        file_title = f'{keyword}.json'
        with open(file_title, 'w') as f:
            f.write(json_string)
    else:
        f = open(f'{keyword}.json')
        data = json.load(f)

    return data


def parse(keyword, update=False, info=None) -> "parses json data (data_to_parse) from API":
    if keyword == 'buildings':
        data = fetch_data(keyword, auth, update=update)
        buildings = {b.ticker: b for b in [prun_classes.Building(b) for b in data]}
        extractors, infrastructure_buildings, production_buildings = classify_buildings(buildings)
        all_production_buildings = merge(extractors, production_buildings)
        return extractors, infrastructure_buildings, production_buildings, all_production_buildings, buildings
    elif keyword == 'materials':
        data = fetch_data(keyword, auth, update=update)
        all_materials = {m.ticker: m for m in [prun_classes.Material(m) for m in data]}
        return all_materials
    elif keyword == 'stations':
        data = fetch_data(keyword, auth, update=update)
        stations = {b.comex_code: b for b in [prun_classes.Station(s) for s in data]}
        num_stations = len(stations)
        station_list = list(stations.keys())
        return stations, num_stations, station_list
    elif keyword == 'prices':
        data = fetch_data(keyword, auth, update=update)
        prices = {p.ticker: p for p in [prun_classes.Price(p) for p in data]}
        return prices
    elif keyword == 'workforce needs':
        data = fetch_data(keyword, auth, update=update)
        wf_needs = {w.workforce_type.lower(): w for w in [prun_classes.WorkforceRequirement(w) for w in data]}
        wf_needs_df = pd.DataFrame([w.needs for w in wf_needs.values()], index=[w for w in wf_needs.keys()])
        wf_needs_df.loc['total'] = wf_needs_df.sum()
        return wf_needs_df
    elif keyword == 'recipes':
        all_recipes = {}
        for building, b in info.items():
            recipes = b.recipes
            for r in recipes:
                recipe_info = prun_classes.Recipe(r)
                recipe_info.building = building
                all_recipes[recipe_info.recipe] = recipe_info
        return all_recipes
    elif keyword == 'building info':
        building_dicts = []
        for building, b in info.items():
            ticker = b.ticker
            num_recipes = len(b.recipes)
            row = {
                'ticker': ticker,
                'name': b.name,
                'expertise': b.expertise.lower(),
                'level': b.level,
                'area': b.area,
                'num_recipes': num_recipes
            }
            building_dicts.append(row)
        building_df = pd.DataFrame(building_dicts).set_index('ticker').sort_values(['level', 'expertise'])
        building_df.level = building_df.level.map(level_dict)
        return building_df
    elif keyword == 'workforce':
        workforce_dicts = []  # will be turned into a df
        for k, b in info.items():
            ticker = b.ticker
            name = b.name
            pioneer = b.pioneer
            settler = b.settler
            technician = b.technician
            engineer = b.engineer
            scientist = b.scientist
            total = np.sum([pioneer, settler, technician, engineer, scientist])
            row = {
                'ticker': ticker,
                'name': name,
                'level': b.level,
                'pioneer': pioneer,
                'settler': settler,
                'technician': technician,
                'engineer': engineer,
                'scientist': scientist,
                'total': total
            }
            workforce_dicts.append(row)

        workforce_df = pd.DataFrame(workforce_dicts).set_index('ticker').sort_values(['level'])
        workforce_df.level = workforce_df.level.map(level_dict)
        return workforce_df
    elif keyword == 'build costs':
        buildcost = {}
        for k, b in info.items():
            bc_df = pd.DataFrame(b.build_costs).set_index('CommodityTicker').drop(['Weight', 'Volume', 'CommodityName'],
                                                                                  axis=1).T
            bc_df = bc_df.to_dict('records')[0]
            buildcost[b.ticker] = bc_df

        """Can access a dataframe of the building material costs by indexing buildcost by ticker"""
        buildcost_df = pd.DataFrame(buildcost).T
        return buildcost_df
    else:
        print('Keyword is not in list.')


def classify_buildings(building_list):
    """ Separates building objects into production buildings,
    non-production buildings(infrastructure buildings), and extractor buildings.
    Extractor building recipes have to be treated differently, so their recipes should not
    be added to the recipe collection df later """
    extractor_buildings = {}
    inf_buildings = {}
    prod_buildings = {}

    for building_ticker, b in building_list.items():
        if len(b.recipes) == 1:
            extractor_buildings[building_ticker] = b
        elif b.production_building:
            prod_buildings[building_ticker] = b
        else:
            inf_buildings[building_ticker] = b
    return extractor_buildings, inf_buildings, prod_buildings


# create function to merge two dictionaries without updating original dicts
def merge(d1, d2):
    py = {**d1, **d2}
    return py


def setprices(station, material_dict, price_dict):
    station_string = f'.{station}'

    for material_ticker, material_object in material_dict.items():
        try:
            mat_cx = material_ticker + station_string
            material_dict[material_ticker].price = price_dict[mat_cx].price
            material_dict[material_ticker].mm_buy = price_dict[mat_cx].mm_buy
            material_dict[material_ticker].mm_sell = price_dict[mat_cx].mm_sell
            material_dict[material_ticker].ask_count = price_dict[mat_cx].ask_count
            material_dict[material_ticker].ask = price_dict[mat_cx].ask
            material_dict[material_ticker].supply = price_dict[mat_cx].supply
            material_dict[material_ticker].bid_count = price_dict[mat_cx].bid_count
            material_dict[material_ticker].bid = price_dict[mat_cx].bid
            material_dict[material_ticker].demand = price_dict[mat_cx].demand
        except:
            print(f'Could not find {mat_cx} in price_dict')


'''Level dict below is used to translate the level number to the corresponding title'''
level_dict = {
    0: 'pioneer',
    1: 'settler',
    2: 'technician',
    3: 'engineer',
    4: 'scientist'
}


def calc_recipe_profit(recipe_dict, material_dict, building_dict) -> 'Creates a DataFrame of profits for all recipes':
    dfrows = []
    for k, v in recipe_dict.items():
        iq, oq, inputs, outputs, num_inputs, num_outputs = v.iq, v.oq, v.inputs, v.outputs, v.num_inputs, v.num_outputs
        input_prices = np.array([material_dict[i].price for i in inputs])
        output_prices = [material_dict[i].price for i in outputs]
        o_demand = np.array([material_dict[o].demand for o in outputs])
        mindemand = np.min(o_demand)
        if num_inputs > 0:
            i_supply = np.array([material_dict[i].supply for i in inputs])
            minsupply = np.min(i_supply)
        else:
            minsupply = 0
        duration = v.duration
        duration_h = duration / 3600

        input_totals = np.multiply(input_prices, iq) if num_inputs > 0 else 0
        output_totals = np.multiply(output_prices, oq)
        cogs = np.sum(input_totals)
        revenue = np.sum(output_totals)
        profit = revenue - cogs
        profitmargin = profit / revenue

        # set new information as an attribute of the recipe
        v.cogs = cogs
        v.revenue = revenue
        v.profit = profit
        v.profit_margin = profitmargin

        # set additional information for building and the building level
        building = v.building
        buildinglevel = building_dict[building].level
        buildingexpertise = building_dict[building].expertise
        inputlist = ', '.join(inputs) if num_inputs > 0 else ''
        outputlist = ', '.join(outputs)

        row = {
            'cogs': cogs,
            'revenue': revenue,
            'profit': profit,
            'profitmargin': profitmargin,
            'profit/hr': profit / duration_h,
            'recipe': k if num_inputs > 0 else ' ' + k,
            'building': building,
            'level': buildinglevel,
            'expertise': buildingexpertise.lower(),
            'input(s)': inputlist,
            'output(s)': outputlist,
            'output demand (min)': mindemand,
            'input_supply (min)': minsupply,
            'num_inputs': num_inputs,
            'num_outputs': num_outputs,
            'duration (s)': duration
        }

        dfrows.append(row)

    profit_df = pd.DataFrame(dfrows).set_index('recipe').sort_values(['level', 'output demand (min)', 'profit'],
                                                                     ascending=[True, False, False])
    profit_df.level = profit_df.level.map(level_dict)
    return profit_df


def fetch_inventory(update=False):
    f = 'inventory.csv'
    if update:
        url = f'https://rest.fnar.net/csv/inventory?apikey={auth}&username={username}'
        my_headers = {'Accept': 'application/csv'}
        data = requests.get(url, headers=my_headers)
        data = data.content

        csv_file = open(f, 'wb')
        csv_file.write(data)
        csv_file.close()
        data = pd.read_csv(f).set_index('Ticker')
    else:
        data = pd.read_csv(f).set_index('Ticker')

    return data

# function to simulate excel auto-fit columns
def get_col_widths(dataframe):
    # First we find the maximum length of the index column
    idx_max = max([len(str(s)) for s in dataframe.index.values] + [len(str(dataframe.index.name))])
    # Then, we concatenate this to the max of the lengths of column name and its values for each column, left to right
    return [idx_max] + [max([len(str(s)) for s in dataframe[col].values] + [len(col)]) for col in dataframe.columns]


# function to save data to excel
def update_excel(dfs_to_write) -> 'Sends to excel':
    with pd.ExcelWriter("all_info.xlsx", engine='xlsxwriter') as writer:
        for df_name, df in dfs_to_write.items():
            df.to_excel(writer, sheet_name=df_name, index=True)
            worksheet = writer.sheets[df_name]
            (max_row, max_col) = df.shape
            column_settings = [{'header': column} for column in df.columns]
            column_settings.insert(0, {'header': df.index.name})
            # Add the Excel table structure. Pandas will add the data.
            worksheet.add_table(0, 0, max_row, max_col,
                                {'columns': column_settings, 'style': 'Table Style Light 1', 'name': df_name})
            # Make the columns wider for clarity.
            worksheet.set_column(0, max_col - 1, 12)
            for i, width in enumerate(get_col_widths(df)):
                worksheet.set_column(i, i, width + 2.5)

def materials_df_create(mat_dict):
    return pd.DataFrame([[mat.ticker, mat.name, mat.ask, mat.ask_count, mat.bid, mat.bid_count, mat.category,
                                  mat.category_id, mat.demand, mat.mat_id, mat.mm_buy, mat.mm_sell, mat.price,
                                  mat.supply,
                                  mat.timestamp, mat.volume, mat.weight] for mat in mat_dict.values()],
                                columns=['ticker', 'name', 'ask', 'ask_count', 'bid', 'bid_count', 'category',
                                         'category_id', 'demand', 'mat_id', 'mm_buy', 'mm_sell', 'price', 'supply',
                                         'timestamp', 'volume', 'weight']).set_index('ticker')