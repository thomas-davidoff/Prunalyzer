import prun_classes
import json
import requests
import pandas as pd
import numpy as np

auth = None
username = None


def fetch_data(keyword, update=False):
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
            'workforce needs': '/global/workforceneeds',
            'production': f'/production/{username}',
            'planet_resources': '/rain/planetresources',
            'planet_names':'/planet/allplanets'
        }
        path = keywords_dict[keyword]
        url = base_url + path
        data = requests.get(url, headers=my_headers).json()
        json_string = json.dumps(data)
        file_title = f'example_data/{keyword}.json'
        with open(file_title, 'w') as f:
            f.write(json_string)
    else:
        f = open(f'example_data/{keyword}.json')
        data = json.load(f)

    return data


def parse(keyword, update=False, info=None) -> "parses json data (data_to_parse) from API":
    if keyword == 'buildings':
        data = fetch_data(keyword, update=update)
        buildings = {b.ticker: b for b in [prun_classes.Building(b) for b in data]}
        extractors, infrastructure_buildings, production_buildings = classify_buildings(buildings)
        all_production_buildings = merge(extractors, production_buildings)
        return extractors, infrastructure_buildings, production_buildings, all_production_buildings, buildings
    elif keyword == 'materials':
        data = fetch_data(keyword, update=update)
        all_materials = {m.ticker: m for m in [prun_classes.Material(m) for m in data]}
        material_list = [k for k in all_materials.keys()]
        return all_materials, material_list
    elif keyword == 'stations':
        data = fetch_data(keyword, update=update)
        stations = {b.comex_code: b for b in [prun_classes.Station(s) for s in data]}
        num_stations = len(stations)
        station_list = list(stations.keys())
        return stations, num_stations, station_list
    elif keyword == 'prices':
        data = fetch_data(keyword, update=update)
        price_df = pd.DataFrame(data).set_index('MaterialTicker')
        prices = {p.ticker: p for p in [prun_classes.Price(p) for p in data]}  # ticker includes exchange code
        return prices, price_df
    elif keyword == 'workforce needs':
        data = fetch_data(keyword, update=update)
        wf_needs = {w.workforce_type.lower(): w for w in [prun_classes.WorkforceRequirement(w) for w in data]}
        wf_needs_df = pd.DataFrame([w.needs for w in wf_needs.values()], index=[w for w in wf_needs.keys()])
        wf_needs_df.loc['total'] = wf_needs_df.sum()
        return wf_needs_df
    elif keyword == 'recipes':
        all_recipes = {}
        for building, b in info.items():  # info is production_buildings dict
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
    elif keyword == 'planet_resources':
        resources_data = fetch_data(keyword, update=update)
        name_dict = {p['PlanetNaturalId']:p['PlanetName'] for p in fetch_data('planet_names',update=update)}
        ids = [p['Planet'] for p in resources_data]
        names = [name_dict[p] for p in ids]
        resources = [p['Ticker'] for p in resources_data]
        types = [p['Type'] for p in resources_data]
        factors = [p['Factor'] for p in resources_data]
        pr = pd.DataFrame({
            'natural_id':ids,
            'name':names,
            'resource':resources,
            'type': types,
            'factor': factors,
        }).set_index('natural_id')
        pr['per_day'] = np.where(pr['type']=='GASEOUS',pr['factor']*60,pr['factor']*70)
        return pr
    elif keyword == 'production':
        data = fetch_data('production', update=update)
        placeholder = 'my production will be here soon'
        return placeholder
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
        mat_cx = material_ticker + station_string
        try:
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
            material_dict[material_ticker].price = np.nan
            material_dict[material_ticker].mm_buy = np.nan
            material_dict[material_ticker].mm_sell = np.nan
            material_dict[material_ticker].ask_count = np.nan
            material_dict[material_ticker].ask = np.nan
            material_dict[material_ticker].supply = np.nan
            material_dict[material_ticker].bid_count = np.nan
            material_dict[material_ticker].bid = np.nan
            material_dict[material_ticker].demand = np.nan


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
        o_mm = np.array([material_dict[o].mm_buy for o in outputs if material_dict[o].mm_buy is not None])
        if len(o_mm) > 0:
            min_mm = np.nanmin(o_mm)
        else:
            min_mm = np.nan
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
            'duration (s)': duration,
            'mmbid': min_mm
        }

        dfrows.append(row)

    profit_df = pd.DataFrame(dfrows).set_index('recipe').sort_values(['level', 'output demand (min)', 'profit'],
                                                                     ascending=[True, False, False])
    profit_df.level = profit_df.level.map(level_dict)
    return profit_df


def fetch_inventory(update=False):
    f = 'example_data/inventory.csv'
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
def update_excel(dfs_to_write, file_name) -> 'Sends to excel':
    with pd.ExcelWriter(file_name, engine='xlsxwriter') as writer:
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


def find_arbitrage(station_list, material_list,materials,prices):
    print('Creating material arbitrage df')
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
                                      'startSupply': start_supply,
                                      'endAverage': end_average_array,
                                      'endBid': end_bid_array,
                                      'endDemand': end_demand,
                                      'weight': weight,
                                      'volume': volume
                                      })
            arbitrage_list.append(df_to_add)
    arbitrage_df = pd.concat(arbitrage_list)
    spread_factor = 0.1
    volume_factor = 100
    cargo_capacity = 500

    arbitrage_df['Status'] = 'Normal'
    reliability_filter = (arbitrage_df.startAverage * (1 - spread_factor) < arbitrage_df.startAsk) & (
            arbitrage_df.startAverage * (1 + spread_factor) > arbitrage_df.startAsk) & (
                                 arbitrage_df.endAverage * (1 - spread_factor) < arbitrage_df.endBid) & (
                                 arbitrage_df.endAverage * (1 + spread_factor) > arbitrage_df.endBid)
    profitable_reliable_filter = reliability_filter & (arbitrage_df['startAsk'] < arbitrage_df['endBid'])
    arbitrage_df.loc[~reliability_filter, 'Status'] = 'Off Average'
    arbitrage_df.loc[profitable_reliable_filter, 'Status'] = 'ARBITRAGE'
    volume_filter = (arbitrage_df.startSupply > volume_factor) & (arbitrage_df.endDemand > volume_factor)

    arbitrage_df['Profit'] = arbitrage_df['endBid'] - arbitrage_df['startAsk']
    arbitrage_df['ProfitMargin'] = arbitrage_df['Profit'] / arbitrage_df['endBid']
    arbitrage_df['ProfitFullCargo'] = arbitrage_df['Profit'] * (cargo_capacity / arbitrage_df['weight'])
    volume_profit_filter = volume_filter & (arbitrage_df.Profit > 0)
    arbitrage_df = arbitrage_df.loc[volume_profit_filter]
    return arbitrage_df