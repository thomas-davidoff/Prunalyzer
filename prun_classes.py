import numpy as np


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
        self.mm_buy = np.nan
        self.mm_sell = np.nan
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


class Price(object):
    def __init__(self, data):
        self.ticker = '.'.join([data['MaterialTicker'], data['ExchangeCode']])
        self.mm_buy = data['MMBuy']
        self.mm_sell = data['MMSell']
        self.price = data['PriceAverage']
        self.ask_count = data['AskCount']
        self.ask = data['Ask']
        self.supply = data['Supply']
        self.bid_count = data['BidCount']
        self.bid = data['Bid']
        self.demand = data['Demand']


class WorkforceRequirement(object):
    def __init__(self, data):
        self.workforce_type = data['WorkforceType']
        self.needs = {n['MaterialTicker']: n['Amount'] for n in data['Needs']}


class Planet(object):
    def __init__(self, datapoint):
        self.planet = datapoint['Planet']
        self.name = None
        self.resources = [datapoint['Ticker']]
        self.resource_types = [datapoint['Type']]
        self.resource_factors = [datapoint['Factor']]
