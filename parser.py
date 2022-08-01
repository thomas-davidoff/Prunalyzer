import requests
import pandas as pd
import streamlit as st
import numpy as np
import io
import time
import json
import streamlit_funx as sf
from datetime import datetime

current_time = time.time() * 1000


class FioEndpoint(object):
    def __init__(self, name, endpoint, access, func, type):
        print(f'Creating object for FioEndpoint ({name}) @ location: ({endpoint})')
        self.name = name
        self.url = 'https://rest.fnar.net' + endpoint
        self.access = access
        self.parsing_function = func
        self.type = type
        self.last_update = None
        self.data = None
        print('Done.')

    def fetch(self, query=None):
        global destination
        if 'username_placeholder' in self.url:
            url = self.url.replace('username_placeholder', destination['FIO Authorization']['ign'])
            if 'query_placeholder' in url:
                url = url.replace('query_placeholder', query)
        else:
            url = self.url
            if 'query_placeholder' in url:
                url = url.replace('query_placeholder', query)

        print(f'running FioEndpoint.fetch() @ {url}')

        if self.access == 'public':
            headers = {'Accept': f'application/{self.type}'}
        elif self.access == 'private':
            auth = destination['FIO Authorization']['AuthToken']
            headers = {'Accept': f'application/{self.type}', 'Authorization': auth}

        if self.type == 'json':
            data = requests.get(url, headers=headers)
            if data.status_code == 200:
                print('Data successfully fetched.')
                self.data = data.json()
            else:
                print(f'Error. Status code: {data.status_code}')
        elif self.type == 'csv':
            data = requests.get(url, headers=headers)
            url_data = data.content
            raw_content = url_data.decode('utf-8')
            content = io.StringIO(raw_content)
            df = pd.read_csv(content)

            if data.status_code == 200:
                print('Data successfully fetched.')
                self.data = df
            else:
                print(f'Error. status code: {data.status_code}')

        destination['FIO Endpoints'][self.name] = self

    def parse(self):
        if self.parsing_function is not None:
            return self.parsing_function(self.data, self.name)
        else:
            pass

    def fetch_and_parse(self):
        self.fetch()
        self.parse()


class Material(object):
    def __init__(self, datum):
        global destination
        self.matId = datum['MaterialId']
        self.category = datum['CategoryName']
        self.categoryId = datum['CategoryId']
        self.name = datum['Name']
        self.ticker = datum['Ticker']
        self.weight = datum['Weight']
        self.volume = datum['Volume']

    def getInfo(self):
        station = destination['price_source'].lower()
        query = destination['cost_method'].lower()
        price = getattr(self, f'{station}_{query}')
        if price is None:
            possible_methods = ['bid', 'ask', 'avg']
            for method in possible_methods:
                price = getattr(self, f'{station}_{method}')
                if price != None:
                    return price
            if price is None:
                possible_stations = destination['exchange_codes']
                for station in possible_stations:
                    price = getattr(self, f'{station}_avg')
                    if price != None:
                        return price
        if price is None:
            price = 1000000
        else:
            return price


class Building(object):
    def __init__(self, datum):
        self.recipes = [r['BuildingRecipeId'] for r in datum['Recipes']]
        self.build_costs = datum['BuildingCosts']
        self.name = datum['Name']
        self.ticker = datum['Ticker']
        self.expertise = datum['Expertise']

        self.workforce = {
            'pioneer': datum['Pioneers'],
            'settler': datum['Settlers'],
            'technician': datum['Technicians'],
            'engineer': datum['Engineers'],
            'scientist': datum['Scientists']
        }

        self.area = datum['AreaCost']
        self.username_submitted = datum['UserNameSubmitted']
        self.timestamp = datum['Timestamp']
        self.production_building = len(self.recipes) > 0
        self.level = np.max(np.nonzero(list(self.workforce.values()))) if self.production_building is True else np.nan
        self.hab = self.name.startswith('habitation')
        self.planetary = self.name.startswith('planetary')

    def get_wf_cost(self):
        current_source = [destination['price_source'], destination['cost_method']]
        try:
            assert(self.wf_cost['source'] == current_source)
            return self.wf_cost['value']
        except (AttributeError, AssertionError):
            wf_cost = destination['workforce_needs'].get_costs()
            self.wf_cost = {
                'value':round(sum(list(self.workforce.values()) * wf_cost), 2),
                'source':current_source
            }
            return self.wf_cost['value']


class Planet(object):
    def __init__(self, datum):
        global destination
        self.name = datum['PlanetName']
        self.nat_id = datum['PlanetNaturalId']
        self.sys = datum['SystemId']

        self.gravity = datum['Gravity']
        self.temperature = datum['Temperature']
        self.pressure = datum['Pressure']
        self.surface = datum['Surface']
        self.fertility = np.nan if datum['Fertility'] == -1 else round(datum['Fertility'] * (10 / 33), 2) * 100

        build_requirements = [m['MaterialTicker'] for m in datum['BuildRequirements']]
        specials = ['MCG', 'AEF', 'SEA', 'HSE', 'INS', 'TSH', 'MGC', 'BL']
        building_materials = {}
        for mat in specials:
            if mat in build_requirements:
                building_materials[mat] = True
            else:
                building_materials[mat] = False
        self.building_materials = building_materials

        self.has_local_market = datum['HasLocalMarket']
        self.has_cogc = datum['HasChamberOfCommerce']
        self.cogc_status = datum['COGCProgramStatus']
        self.production_fees = datum['ProductionFees']

        cogc_programs = datum['COGCPrograms']

        if len(cogc_programs) > 0:
            program_starts = [program['StartEpochMs'] for program in cogc_programs]
            program_starts.remove(max(program_starts))
            self.last_cogc = cogc_programs[program_starts.index(max(program_starts))]['ProgramType']
        else:
            self.last_cogc = None

        self.faction = datum['FactionCode']
        self.population = datum['PopulationId']
        self.governor = datum['GovernorUserName']
        self.governor_corp = datum['GovernorCorporationCode']

        self.resources = datum['Resources']
        for resource in self.resources:
            resource['Ticker'] = destination['mat_dict'][resource['MaterialId']].lower()
            del resource['MaterialId']
            if resource['ResourceType'] == 'GASEOUS':
                per_day = resource['Factor'] * 60
                resource['Factor'] *= 100
                resource['Rate Per Day'] = int(per_day * (10 ** 2)) / (10 ** 2)
                resource['Building'] = 'COL'
            elif resource['ResourceType'] == 'LIQUID':
                per_day = resource['Factor'] * 70
                resource['Factor'] *= 100
                resource['Rate Per Day'] = int(per_day * (10 ** 2)) / (10 ** 2)
                resource['Building'] = 'RIG'
            elif resource['ResourceType'] == 'MINERAL':
                per_day = resource['Factor'] * 70
                resource['Factor'] *= 100
                resource['Rate Per Day'] = int(per_day * (10 ** 2)) / (10 ** 2)
                resource['Building'] = 'EXT'

        self.num_resources = len(self.resources)


class PlanetProduction(object):
    def __init__(self, data):
        self.data = data
        orders = []

        planet_buildings = []

        for building in data:

            building_orders = building['Orders']
            building_ticker = get_build_ticker(building['Type'])
            condition = str(int(building['Condition'] * 100)) + '%',
            efficiency = str(int(building['Efficiency'] * 100)) + '%',
            quantity = building['Capacity']

            planet_buildings.append(dict(
                ticker=building_ticker,
                condition=condition[0],
                efficiency=efficiency[0],
                quantity=quantity,
                expertise=destination['buildings'][building_ticker].expertise
            ))
            for order in building_orders:
                inputs = {m['MaterialTicker']: m['MaterialAmount'] for m in order['Inputs']}
                outputs = {m['MaterialTicker']: m['MaterialAmount'] for m in order['Outputs']}

                if len(inputs) == 0 and len(outputs) == 0:
                    pass
                else:

                    in_string = ' '.join([f'{value}x{key}' for key, value in inputs.items()])
                    out_string = ' '.join([f'{value}x{key}' for key, value in outputs.items()])
                    recipe = ' => '.join([in_string, out_string])

                    order_info = {
                        'recipe': recipe,
                        'recurring': order['Recurring'],
                        'production_fee': order['ProductionFee'],
                        'time_created': order['CreatedEpochMs'],
                        'start_time': order['StartedEpochMs'],
                        'completion_time': order['CompletionEpochMs'],
                        'duration': order['DurationMs'],
                        'progress': order['CompletedPercentage'],
                        'building': building_ticker,
                        'building_slots': quantity

                    }

                    orders.append(order_info)
        df = pd.DataFrame(orders)

        df['started'] = pd.notnull(df['start_time'])

        building_orders = []

        for building in set(df['building'].values):
            all_orders = df[df['building'] == building].sort_values('completion_time')
            num_waiting = len(all_orders[all_orders['started'] == False])
            num_in_progress = len(all_orders) - num_waiting
            completion_timing = list(all_orders['completion_time'])
            start_timing = list(all_orders['start_time'])[:num_in_progress] + completion_timing[0:num_waiting]
            all_orders['start_time'] = start_timing
            all_orders['completion_time'] = all_orders['start_time'] + all_orders['duration']

            all_orders.fillna(0, inplace=True)
            building_orders.append(all_orders)

            all_orders['time_created'] = pd.to_datetime(all_orders['time_created'], unit='ms')
            all_orders['start_time'] = pd.to_datetime(all_orders['start_time'], unit='ms')
            all_orders['completion_time'] = pd.to_datetime(all_orders['completion_time'], unit='ms')

        self.orders = pd.concat(building_orders)
        self.buildings = pd.DataFrame(planet_buildings)


class Workforce(object):
    def __init__(self, data):
        global destination

        self.data = data
        wf_needs = {wf['WorkforceType'].lower(): {n['MaterialTicker']: n['Amount'] for n in wf['Needs']} for wf in data}
        wf_needs_df = pd.DataFrame([w for w in wf_needs.values()], index=[w for w in wf_needs.keys()])
        self.needs = wf_needs_df / 100

    def get_costs(self):
        current_source = [destination['price_source'],destination['cost_method']]
        try:
            costs = self.costs
            assert(costs['source'] == current_source)
            return costs['value']

        except (AssertionError, AttributeError) as e:
            costs = self.needs.loc[:]
            for col in costs:
                costs[col] = costs[col] * destination['materials'][col.lower()].getInfo()
            costs = costs.sum(axis=1)
            self.costs = {
                'value':costs,
                'source':current_source
            }
            return costs


class Recipe(object):
    def __init__(self, datum):
        name = datum['RecipeName']
        self.building = datum['BuildingTicker']
        self.key = f'{name.split("=>")[0]}@{self.building}=>{name.split("=>")[1]}'
        self.inputs = datum['Inputs']
        self.outputs = datum['Outputs']
        self.time = datum['TimeMs']

        self.type = 'recipe'
        if len(self.inputs) + len(self.outputs) == 0:
            self.type = 'extraction'

    def mat_cost(self, target: str):
        """Finds the total cost or revenue of inputs or outputs for the recipe object
            target: str: "inputs" or "outputs"
        """
        global destination
        price_source = destination['price_source']
        method = destination['cost_method']

        target = self.inputs if target == 'inputs' else self.outputs

        total_prices = []
        costs = {}
        for i in target:
            ticker = i['Ticker'].lower()
            amount = i['Amount']
            price = destination['materials'][ticker].getInfo()
            total_price = price * amount
            total_prices.append(total_price)
            costs[ticker] = total_price

        val = round(sum(costs.values()), 2)

        if target == 'inputs':
            self.input_values = total_prices
            self.cogs = val
        elif target == 'outputs':
            self.output_values = total_prices
            self.revenue = val

        return val

    def get_gross_profit(self):
        self.revenue = self.mat_cost('outputs')
        self.cogs = self.mat_cost('inputs')
        self.gross_profit = round(self.revenue - self.cogs, 2)
        self.profit_margin = self.gross_profit / self.revenue

        return self.gross_profit

    def cpu(self):
        global destination
        price_source = destination['price_source']
        method = destination['cost_method']

        try:
            profit_margin = self.profit_margin
        except AttributeError:
            revenue = self.mat_cost('outputs')
            cogs = self.mat_cost('inputs')
            gross_profit = round(revenue - cogs, 2)
            profit_margin = gross_profit / revenue

        cost_margin = 1 - profit_margin
        cpus = {}

        index = 0
        for output in self.outputs:
            try:
                value = self.output_values[index]
            except AttributeError:
                amount = output['Amount']
                price = destination['materials'][output['Ticker'].lower()].getInfo()
                value = price * amount

            share_of_cost = cost_margin * value
            cpus[output['Ticker']] = share_of_cost

            index += 1

        self.cpus = cpus
        return cpus

    def full_info(self):
        x = self.get_gross_profit()
        x = self.cpu()
        self.has_info = True


# ---- PARSING FUNCTIONS ----

def parse_materials(data, name):
    print('Parsing Materials')
    global destination

    parsed = {M.ticker.lower(): M for M in [Material(datum) for datum in data]}
    id_dict = {mat.matId: mat.ticker for mat in parsed.values()}
    destination[name] = parsed
    destination['mat_dict'] = id_dict
    print('Materials successfully parsed.')


def set_prices(data, name):
    """
    Parses market/all data and posts material market info as attributes to each material in the destination

    fio_object: pre-created fio-endpoint object, where market data can be accessed as an attribute
    material_dict: dictionary of materials, already parsed into objects with key as the ticker.
        e.g. st.session_state['materials'], or local mat dictionary
    """

    print('Parsing market data...')
    global destination
    material_dict = destination['materials']

    for datum in data:
        ticker, exchange_code = datum['MaterialTicker'].lower(), datum['ExchangeCode'].lower()
        destination['exchange_codes'].add(exchange_code)
        setattr(material_dict[ticker], f'{exchange_code}_avg', datum['PriceAverage'])
        setattr(material_dict[ticker], f'{exchange_code}_bid', datum['Bid'])
        setattr(material_dict[ticker], f'{exchange_code}_ask', datum['Ask'])
        setattr(material_dict[ticker], f'{exchange_code}_supply', datum['Supply'])
        setattr(material_dict[ticker], f'{exchange_code}_demand', datum['Demand'])
        setattr(material_dict[ticker], f'{exchange_code}_mm_buy', datum['MMBuy'])
        setattr(material_dict[ticker], f'{exchange_code}_mm_sell', datum['MMSell'])

    destination[name] = True

    print('Market data successfully parsed.')


def parse_buildings(data, name):
    print('Parsing buildings')
    global destination
    parsed = {b.ticker: b for b in [Building(datum) for datum in data]}

    destination[name] = parsed
    print('Buildings successfully parsed.')


def parse_planets(data, name):
    print('Parsing Planets')
    global destination
    parsed = {p.nat_id: p for p in [Planet(datum) for datum in data]}

    destination[name] = parsed
    print('Planets successfully parsed')


def parse_user_data(data, name):
    global destination
    print('Parsing user data...')
    data['Balances'] = pd.DataFrame(data['Balances'])[['Currency', 'Amount']].set_index('Currency')
    data['Planets'] = [datum['PlanetNaturalId'] for datum in data['Planets']]
    destination[name] = data
    print('User data successfully parsed.')


def parse_wf_needs(data, name):
    print('Parsing workforce needs...')
    global destination

    parsed = Workforce(data)
    destination[name] = parsed

    print('Workforce Needs parsed.')


def parse_planet_production(data, name):
    print('Parsing planet production data...')
    global destination

    parsed = PlanetProduction(data)
    destination[name] = parsed

    print('Planet Production parsed.')


def parse_recipes(data, name):
    print('Parsing recipes')
    global destination
    recipes = {r.key: r for r in [Recipe(r) for r in data] if r.building not in ['COL', 'RIG', 'EXT']}

    destination[name] = recipes
    print('Recipes successfully parsed')


def add_user(user_info):
    print('Adding user...')
    global destination
    fio_user = user_info[0]
    fio_pass = user_info[1]
    ign = user_info[2]

    if (fio_user != '') and (fio_pass != ''):
        json_data = {
            "UserName": fio_user,
            "Password": fio_pass
        }

        obj = destination['FIO Endpoints']['authentication']
        headers = {'Accept': 'application/json'}
        data = requests.post(obj.url, headers=headers, json=json_data)
        if data.status_code == 200:
            print('User added!')
            response = data.content.decode('UTF-8')
            data = json.loads(response)
            destination['FIO Authorization'] = data
            st.success('Authenticated!')
            destination['fio_status'] = 'Active'
            destination['FIO Authorization']['ign'] = ign
            destination['FIO Authorization']['fio_user'] = fio_user
            destination['FIO Authorization']['fio_pass'] = fio_pass
            force_fio_get([['user_data']])

        else:
            st.error('Invalid Username and/or Password')
            destination['fio_status'] = 'Not authenticated'

    else:
        st.error("Please Enter All Fields (Otherwise things won't work correctly.")


# ---- UTILITIES ----
def get_build_ticker(name):
    for building in destination['buildings'].values():
        if building.name == name:
            return building.ticker


def get_building_wf_cost(building_ticker: str):
    global destination
    building=destination['buildings'][building_ticker]
    return building.get_wf_cost()


def profit_df(recipe_list: list, daily: bool = True) -> pd.DataFrame:
    buildings = destination['buildings']
    ms_day = 1000 * 60 * 60 * 24
    recipes = [destination['recipes'][r] for r in recipe_list]

    [r.full_info() for r in recipes]
    building = [r.building for r in recipes]
    expertise = [buildings[b].expertise for b in building]
    raw_duration = np.array([r.time for r in recipes])
    level_dict = {
        0:'Pioneer',
        1:'Settler',
        2:'Technician',
        3:'Engineer',
        4:'Scientist'
    }
    tier = pd.Series([buildings[b].level for b in building]).replace(level_dict)

    profit_df = pd.DataFrame(
        dict(
            recipe=[r.key for r in recipes],
            building=building,
            expertise=expertise,
            tier=tier,
            raw_duration=raw_duration
        )
    )

    material_costs = [r.cogs for r in recipes]
    revenue = [r.revenue for r in recipes]
    gross_profit = [r.gross_profit for r in recipes]
    cycles_per_day = np.array([ms_day / duration for duration in raw_duration])
    building_daily_labor_cost = np.array(buildings[b].get_wf_cost() for b in building)

    if daily:
        profit_df['material_costs'] = np.array(material_costs) * cycles_per_day
        profit_df['revenue'] = np.array(revenue) * cycles_per_day
        profit_df['gross_profit'] = np.array(gross_profit) * cycles_per_day
        profit_df['labor'] = building_daily_labor_cost
        profit_df['cogs'] = profit_df['material_costs'] + profit_df['labor']
        profit_df['net'] = profit_df['revenue'] - profit_df['cogs']
        profit_df['Profit Margin'] = (profit_df['net']/profit_df['revenue'])*100
    else:
        profit_df['material_costs'] = material_costs
        profit_df['revenue'] = revenue
        profit_df['gross_profit'] = gross_profit
        profit_df['labor'] = building_daily_labor_cost
        profit_df['cogs'] = profit_df['material_costs'] + profit_df['labor']
        profit_df['net'] = profit_df['revenue'] - profit_df['cogs']
        profit_df['Profit Margin'] = (profit_df['net']/profit_df['revenue'])*100
        profit_df['labor'] = profit_df['labor'].astype(float)
        profit_df['labor'] = profit_df['labor'] * (raw_duration / ms_day)


    profit_df = profit_df \
        .set_index('recipe') \
        .sort_values(['tier', 'building', 'gross_profit'], ascending=[True, True, False])

    return profit_df


# ----


@st.cache()
def fio_get(keywords):
    """
    Takes a list of keywords (names of previously set FIO Endpoints), and fetches and parses the data into session.
    :param keyword: FIO Endpoint object name, stored in destination
    :return: Appends updated and parsed data to destination
    """
    print('Running fio_get()...')
    global destination
    for keyword in keywords:
        destination['FIO Endpoints'][keyword].fetch_and_parse()


def force_fio_get(args_list):
    print('Running force_fio_get()...')
    global destination
    for args in args_list:
        keyword = args[0]
        query = None if len(args) == 0 else args[-1]
        print(keyword, query)
        destination['FIO Endpoints'][keyword].fetch(query)
        destination['FIO Endpoints'][keyword].parse()


def fio_init():
    global destination

    print('Initiating FIO connection...')

    destination['FIO Endpoints'] = {}
    destination['fio_status'] = 'Not authenticated'
    destination['exchange_codes'] = set()

    endpoints = [
        {
            'name': 'materials',
            'endpoint': '/material/allmaterials',
            'access': 'public',
            'func': parse_materials,
            'type': 'json'
        },
        {
            'name': 'prices',
            'endpoint': '/exchange/all',
            'access': 'public',
            'func': set_prices,
            'type': 'json'
        },
        {
            'name': 'buildings',
            'endpoint': '/building/allbuildings',
            'access': 'public',
            'func': parse_buildings,
            'type': 'json'
        },
        {
            'name': 'planets',
            'endpoint': '/planet/allplanets/full',
            'access': 'public',
            'func': parse_planets,
            'type': 'json'
        },
        {
            'name': 'authentication',
            'endpoint': '/auth/login',
            'access': 'private',
            'func': None,
            'type': 'json'
        },
        {
            'name': 'user_data',
            'endpoint': f'/user/username_placeholder',
            'access': 'private',
            'func': parse_user_data,
            'type': 'json'
        },
        {
            'name': 'planet_production',
            'endpoint': '/production/username_placeholder/query_placeholder',
            'access': 'private',
            'func': parse_planet_production,
            'type': 'json'
        },
        {
            'name': 'workforce_needs',
            'endpoint': '/global/workforceneeds',
            'access': 'public',
            'func': parse_wf_needs,
            'type': 'json'
        },
        {
            'name': 'planet_workforce',
            'endpoint': '/workforce/username_placeholder/query_placeholder',
            'access': 'private',
            'func': None,
            'type': 'json'
        },
        {
            'name': 'recipes',
            'endpoint': '/recipes/allrecipes',
            'access': 'public',
            'func': parse_recipes,
            'type': 'json'
        }
    ]

    for endpoint in endpoints:
        obj = FioEndpoint(**endpoint)
        destination['FIO Endpoints'][obj.name] = obj

    destination['init'] = True

    if 'FIO Authorization' not in destination:
        auth_dict = {}
        auth_dict['ign'] = ''
        auth_dict['fio_pass'] = ''
        auth_dict['fio_user'] = ''
        destination['FIO Authorization'] = auth_dict


if __name__ == '__main__':
    destination = {}
    fio_init()

    page_data = [
        ['materials', None],
        ['prices', None],
        ['buildings', None],
        ['workforce_needs', None],
        ['recipes']
    ]

    force_fio_get(page_data)

    destination['price_source'] = 'nc1'
    destination['cost_method'] = 'ask'

    x = 1
else:
    destination = st.session_state
