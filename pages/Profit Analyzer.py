import parser
import streamlit as st
import streamlit_funx as sf
import pandas as pd
import numpy as np
import styles_import
from importlib import reload


def main():
    reload(parser)
    destination = st.session_state

    styles_import.local_css('local.css')
    print('--------')

    # specify which data is relevant to the current page
    page_data = [
        ['materials'],
        ['prices'],
        ['planets'],
        ['buildings'],
        ['workforce_needs'],
        ['recipes']
    ]

    # Check if FIO connection has been initialized
    if 'init' not in destination:
        parser.fio_init()

    for dataset in page_data:
        if dataset[0] not in destination:
            parser.force_fio_get(args_list=page_data)

    planets = destination['planets']


# ---- SIDEBAR ----

    with st.sidebar:
        sf.CustomButton(
            text='Refresh Data',
            session_key='refresh_data',
            hint=None,
            func=parser.force_fio_get,
            args=page_data
        )


        st.write(
            f'Currently logged in as {destination["FIO Authorization"]["ign"]}'
        )
        st.write(
            f'Authenticated against FIO: {destination["fio_status"]}'
        )

        st.selectbox(
            label = 'Price Source (exchange)',
            key='price_source',
            options= [c.upper() for c in destination['exchange_codes']]
        )

        st.selectbox(
            label='Price Method',
            key='cost_method',
            options=['Ask','Bid','Avg']
        )

# ----  BODY ----

    st.title('Profit Analyzer')



    col1, col2 = st.columns([2,5],gap='large')

    with col1:

        daily = st.checkbox(
            label='Calculate per day?',
            value=True
        )

        df = parser.profit_df(destination['recipes'].keys(), daily=daily)

        expertise = st.multiselect(
            label='Select Expertise',
            options=set(df['expertise']),
            default=set(df['expertise'])
        )

        tier = st.multiselect(
            label='Select Workforce Required',
            options=set(df['tier']),
            default=set(df['tier'])
        )

        min_profit = st.slider(
            label='Minimum Profit',
            min_value=0,
            max_value=10000,
            value=0,
            step=100
        )
    with col2:
        df = df[df['expertise'].isin(expertise)]
        df = df[df['tier'].isin(tier)]
        df = df[df['net'] > min_profit]
        df = df[
            ['building','expertise','tier','material_costs','labor','cogs','revenue','net']
        ].sort_values(['net'],ascending=False)
        st.dataframe(df,2000,600)





if __name__ == '__main__':
    main()
