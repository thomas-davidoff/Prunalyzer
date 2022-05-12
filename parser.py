import requests
import json
import numpy as np
import pandas as pd


class Building(object):
    def __init__(self, data):
        self.recipes = data['Recipes']
        self.build_costs = data['BuildingCosts']
        self.name = data['Name']
        self.ticker = data['Ticker']
        self.expertise = data['Expertise']
        self.pioneer = data['Pioneers']
        self.settler = data['Settlers']
        self.technician = data['Technicians']
        self.engineer = data['Engineers']
        self.scientist = data['Scientists']
        self.area = data['AreaCost']
        self.username_submitted = data['UserNameSubmitted']
        self.timestamp = data['Timestamp']
        self.production_building = len(self.recipes) > 0
        self.level = np.max(np.nonzero([self.pioneer, self.settler, self.technician, self.engineer,
                                        self.scientist])) if self.production_building is True else np.nan


class Recipe(object):
    def __init__(self, recipe_dict):
        self.building = None  # assign building later
        self.recipe = recipe_dict['RecipeName']
        self.duration = recipe_dict['DurationMs'] / 1000
        self.outputs = None
        split = self.recipe.split(' = ')
        if len(split) != 2:
            self.inputs = np.empty(0)
            self.iq = np.empty(0)
            outs = [y.split('x') for y in self.recipe[2:].split(' ')]
            self.oq = [int(z[0]) for z in outs]
            self.outputs = [z[1] for z in outs]
        else:
            ins = [y.split('x') for y in split[0].split(' ')]
            outs = [y.split('x') for y in split[1].split(' ')]
            self.iq = [int(z[0]) for z in ins]
            self.inputs = [z[1] for z in ins]
            self.oq = [int(z[0]) for z in outs]
            self.outputs = [z[1] for z in outs]
        self.num_inputs = len(self.inputs)
        self.num_outputs = len(self.outputs)
        self.cogs = None
        self.revenue = None
        self.profit = None
        self.profit_margin = None


class Material(object):
    def __init__(self, material_dict):
        self.category = material_dict['CategoryName']
        self.category_id = material_dict['CategoryId']
        self.name = material_dict['Name']
        self.mat_id = material_dict['MatId']
        self.ticker = material_dict['Ticker']
        self.weight = material_dict['Weight']
        self.volume = material_dict['Volume']
        self.username_submitted = material_dict['UserNameSubmitted']
        self.timestamp = material_dict['Timestamp']
        '''assign the following attributes when you have price data'''
        self.mm_buy = None
        self.mm_sell = None
        self.price = None
        self.ask_count = None
        self.ask = None
        self.supply = None
        self.bid_count = None
        self.bid = None
        self.demand = None


class Station(object):
    def __init__(self, data):
        self.nat_id = data['NaturalId']
        self.name = data['Name']
        self.sys_id = data['SystemId']
        self.sys_nat_id = data['SystemNaturalId']
        self.commission_time = data['CommisionTimeEpochMs']
        self.comex_id = data['ComexId']
        self.comex_code = data['ComexCode']
        self.warehouse_id = data['WarehouseId']
        self.country_id = data['CountryId']
        self.country_code = data['CountryCode']
        self.country_name = data['CountryName']
        self.currency_num = data['CurrencyNumericCode']
        self.currency_code = data['CurrencyCode']
        self.currency_name = data['CurrencyName']
        self.currency_decimals = data['CurrencyDecimals']
        self.governor_id = data['GovernorId']
        self.governor_username = data['GovernorUserName']
        self.governor_corp_id = data['GovernorCorporationId']
        self.governor_corp_name = data['GovernorCorporationName']
        self.governor_corp_code = data['GovernorCorporationCode']
        self.username_submitted = data['UserNameSubmitted']
        self.timestamp = data['Timestamp']


# create function to merge two dictionaries without updating original dicts
def merge(d1, d2):
    py = {**d1, **d2}
    return py


# create function to map dictionary values from key value
def vec_translate(a, my_dict):
    return np.vectorize(my_dict.__getitem__)(a)


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
            'workforce_needs': '/global/workforceneeds'
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


def fetch_inventory(a_username, api_authentication, update=False):
    f = 'inventory.csv'
    if update:
        url = f'https://rest.fnar.net/csv/inventory?apikey={api_authentication}&username={a_username}'
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


def search_price(material_ticker):
    return all_materials[material_ticker].price


def get_local_price(material_ticker, selected_station):
    station_index = sorted(stations).index(selected_station)
    prices = price_data[station_index::num_stations]
    '''above code will create a new list of dictionaries only pertaining to the selected station,
    by setting the step-size to the number of unique exchanges in the game, and the start index
    at the first occurance of the selected station - its alphabetical'''
    for price in prices:
        if price['MaterialTicker'] == material_ticker:
            all_materials[material_ticker].mm_buy = price['MMBuy']
            all_materials[material_ticker].mm_sell = price['MMSell']
            all_materials[material_ticker].price = price['PriceAverage']
            all_materials[material_ticker].ask_count = price['AskCount']
            all_materials[material_ticker].ask = price['Ask']
            all_materials[material_ticker].supply = price['Supply']
            all_materials[material_ticker].bid_count = price['BidCount']
            all_materials[material_ticker].bid = price['Bid']
            all_materials[material_ticker].demand = price['Demand']


def setprices(station):
    selected_station = station
    for material_ticker, material_object in all_materials.items():
        get_local_price(material_ticker, selected_station)


def buildlist(building_list):
    buildcost_list = []
    for building_ticker in building_list:
        x = buildcost[building_ticker]
        x['building'] = building_ticker
        buildcost_list.append(x)

    df = pd.DataFrame(buildcost_list).set_index('building')
    df.loc['total'] = df.sum()
    price_list = []
    for item in list(df.columns):
        price_list.append(all_materials[item].price)

    df.loc['price/unit'] = price_list
    df.loc['total price'] = np.multiply(df.loc['total'], df.loc['price/unit'])
    total_cost = df.loc['total price'].sum()
    print(total_cost)
    return df

def configure_user():
    user = input('Enter your in-game username.\n')
    authorization_key = input('Enter your authorization key for the FIO REST API')
    print('User has been configured')
    return  user, authorization_key

# api authorization hash

username, auth = configure_user()
print('Setting authorization hash and username')
print('Fetching building data from API...')
building_data = fetch_data('buildings', update=True)
print('Success')
materials_data = fetch_data('materials', update=True)
price_data = fetch_data('prices', update=True)
station_data = fetch_data('stations', update=True)
workforce_needs_data = fetch_data('workforce_needs', update=True)

# create inventory df
inventory_df = fetch_inventory(username, auth, update=True)

# parse and classify all building data
buildings = {b.ticker: b for b in [Building(b) for b in building_data]}
extractors, infrastructure_buildings, production_buildings = classify_buildings(buildings)
all_production_buildings = merge(extractors, production_buildings)

# parse all material data
all_materials = {m.ticker: m for m in [Material(m) for m in materials_data]}

# parse all exchange station data, and count the number of active stations
stations = {b.comex_code: b for b in [Station(s) for s in station_data]}
num_stations = len(station_data)

# set prices for selected station as attributes of materials
setprices('NC1')

# create df for materials
materials_df = pd.DataFrame([[mat.ticker, mat.name, mat.ask, mat.ask_count, mat.bid, mat.bid_count, mat.category,
                              mat.category_id, mat.demand, mat.mat_id, mat.mm_buy, mat.mm_sell, mat.price, mat.supply,
                              mat.timestamp, mat.volume, mat.weight] for mat in all_materials.values()],
                            columns=['ticker', 'name', 'ask', 'ask_count', 'bid', 'bid_count', 'category',
                                     'category_id', 'demand', 'mat_id', 'mm_buy', 'mm_sell', 'price', 'supply',
                                     'timestamp', 'volume', 'weight']).set_index('ticker')

# all_recipes contains only *production* recipes - not the three recipes used by EXT, RIG, and COL
# all_recipes will serve as the data for recipe parsing
recipes = {}  # for further parsing
building_dicts = []  # to be turned into a dataframe
level_dict = {
    0: 'pioneer',
    1: 'settler',
    2: 'technician',
    3: 'engineer',
    4: 'scientist'
}
'''Create recipes dictionary (for further parsing), and the list of building dictionaries for info'''
for k, b in production_buildings.items():
    ticker = b.ticker
    b_recipes = b.recipes
    recipes[ticker] = b_recipes
    num_recipes = len(b_recipes)
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

'''create objects for all recipes, with attributes listed in  the recipe_info class'''
all_recipes = {}
for b, building_recipes in recipes.items():
    for r in building_recipes:
        info = Recipe(r)
        info.building = b
        all_recipes[info.recipe] = info

workforce_dicts = []  # will be turned into a df
for k, b in all_production_buildings.items():
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

"""
buildcost is formatted as a dictionary, with the layout as follows:
    key - building ticker
    value - list of dictionaries that each contain the keys:
        'CommodityName'
        'CommodityTicker'
        'Weight'
        'Volume'
        'Amount'
        """
buildcost = {}
for k, b in buildings.items():
    bc_df = pd.DataFrame(b.build_costs).set_index('CommodityTicker').drop(['Weight', 'Volume', 'CommodityName'],
                                                                          axis=1).T
    bc_df = bc_df.to_dict('records')[0]
    buildcost[b.ticker] = bc_df

"""Can access a dataframe of the building material costs by indexing buildcost by ticker"""
buildcost_df = pd.DataFrame(buildcost).T

dfrows = []
for k, v in all_recipes.items():
    iq, oq, inputs, outputs, num_inputs, num_outputs = v.iq, v.oq, v.inputs, v.outputs, v.num_inputs, v.num_outputs
    input_prices = np.array([search_price(i) for i in inputs])
    output_prices = [search_price(i) for i in outputs]

    o_demand = np.array([all_materials[o].demand for o in outputs])
    mindemand = np.min(o_demand)
    if num_inputs > 0:
        i_supply = np.array([all_materials[i].supply for i in inputs])
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
    buildinglevel = buildings[building].level
    buildingexpertise = buildings[building].expertise
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

export_list = {
    'BuildingInfo': building_df,
    'WorkforceInfo': workforce_df,
    'BuildcostMatrix': buildcost_df,
    'RecipeProfits': profit_df,
    'MaterialInfo': materials_df,
    'Inventory': inventory_df
}

update_excel(export_list)
