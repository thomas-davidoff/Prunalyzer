import streamlit as st
import pandas as pd


def class_table(df):
    materials = st.session_state['materials']
    cols = list(df.columns)
    cols.insert(0, cols.pop(cols.index('Ticker')))
    df = df[cols]
    categories = [materials[ticker].category.replace(' ', '_') for ticker in df['Ticker']]
    categories = [category + ' material' for category in categories]
    classes = pd.DataFrame(categories, columns=['Ticker'])
    df.Ticker = df.Ticker.str.upper()
    df.ResourceType = df.ResourceType.str[0:1] + df.ResourceType.str[1:].str.lower()
    df = df.style.set_td_classes(classes)
    df = df.set_table_attributes('class="material-table"')
    return df.to_html()


html_f = 'layout.html'
category_colors = {
        'minerals': ['rgb(153, 113, 73)','rgb(178, 138, 98)'],
        'gases': ['rgb(0, 105, 107)', 'rgb(25, 130, 132)'],
        'liquids': ['rgb(114, 164, 202)', 'rgb(139, 189, 227)'],
        'ores': ['rgb(82, 87, 97)', 'rgb(107, 112, 122)'],
        'alloys': ['rgb(123, 76, 30)', 'rgb(148, 101, 55)'],
        'ship engines': ['rgb(123, 76, 30)', 'rgb(148, 101, 55)'],
        'plastics': ['rgb(123, 76, 30)', 'rgb(148, 101, 55)'],
        'chemicals': ['rgb(183, 46, 91)', 'rgb(208, 71, 116)'],
        'elements': ['rgb(123, 76, 30)', 'rgb(148, 101, 55)'],
        'metals': ['rgb(123, 76, 30)', 'rgb(148, 101, 55)'],
        'electronic pieces': ['rgb(123, 76, 30)', 'rgb(148, 101, 55)'],
        'ship parts': ['rgb(123, 76, 30)', 'rgb(148, 101, 55)'],
        'ship kits': ['rgb(123, 76, 30)', 'rgb(148, 101, 55)'],
        'software systems': ['rgb(123, 76, 30)', 'rgb(148, 101, 55)'], # HERE IS WHERE I STOPPED COPYING
        'electronic parts': ['rgb(123, 76, 30)', 'rgb(148, 101, 55)'],
        'utility': ['rgb(123, 76, 30)', 'rgb(148, 101, 55)'],
        'agricultural products': ['rgb(123, 76, 30)', 'rgb(148, 101, 55)'],
        'software components': ['rgb(123, 76, 30)', 'rgb(148, 101, 55)'],
        'energy systems': ['rgb(123, 76, 30)', 'rgb(148, 101, 55)'],
        'fuels': ['rgb(123, 76, 30)', 'rgb(148, 101, 55)'],
        'software tools': ['rgb(123, 76, 30)', 'rgb(148, 101, 55)'],
        'construction prefabs': ['rgb(15, 30, 98)', 'rgb(40, 55, 123)'],
        'medical equipment': ['rgb(123, 76, 30)', 'rgb(148, 101, 55)'],
        'drones': ['rgb(123, 76, 30)', 'rgb(148, 101, 55)'],
        'construction parts': ['rgb(41, 77, 107)', 'rgb(66, 102, 132)'],
        'electronic devices': ['rgb(123, 76, 30)', 'rgb(148, 101, 55)'],
        'consumables (basic)': ['rgb(149, 46, 46)', 'rgb(174, 71, 71)'],
        'consumables (luxury)': ['rgb(136, 24, 39)', 'rgb(161, 49, 64)'],
        'unit prefabs': ['rgb(123, 76, 30)', 'rgb(148, 101, 55)'],
        'construction materials': ['rgb(24, 91, 211)', 'rgb(49, 116, 236)'],
        'ship shields': ['rgb(123, 76, 30)', 'rgb(148, 101, 55)'],
        'textiles': ['rgb(123, 76, 30)', 'rgb(148, 101, 55)'],
        'electronic systems': ['rgb(123, 76, 30)', 'rgb(148, 101, 55)']
}



# ---- BUTTON CLASSES ----
class CustomButton(object):
    def execute(self):
        self.func(self.args)
    def __init__(self, text, session_key, hint=None, func=None, args=None):
        self.func = func
        self.args = args
        st.button(
            text,
            key=session_key,
            on_click=self.execute,
            help=hint
        )

if __name__ == '__main__':
    pass
else:
    print('Streamlit_funx imported.')
    destination = st.session_state
