import parser
import streamlit as st
import streamlit_funx as sf
import pandas as pd
import numpy as np
import styles_import


def main():
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
    try:
        user_planets = destination['user_data']['Planets']

        st.title('Base Overview')



        planet_selection = st.selectbox(
            label='Select Base',
            options=user_planets
        )

        selected_planet = planets[planet_selection]

        df = pd.DataFrame(selected_planet.resources)

        planet_info_tab,user_data_tab,test_tab = st.tabs(['Planet Info','Raw User Data','testing'])

        with planet_info_tab:
            st.subheader(selected_planet.name)
            st.write(f'Current COGC Program: {selected_planet.last_cogc}')
            if np.isnan(selected_planet.fertility):
                st.write('Fertility bonus: None (infertile)')
            else:
                st.write(f'Fertility bonus: {str(selected_planet.fertility)}%')


            if df.empty:
                st.write('Planet has no resources...')
            else:
                st.markdown(sf.class_table(df),unsafe_allow_html=True)

        with user_data_tab:

            if destination['fio_status'] == 'Active':
                user_data = destination['user_data']
                parser.force_fio_get([['planet_production', planet_selection]])
                planet_production = destination['planet_production']

                with st.expander('Balances', expanded=False):
                    st.table(user_data['Balances'])

                with st.expander(label='Orders',expanded=False):
                    st.write(
                        'If there is a recipe missing, or one that shows "=>", open up the details tab of that buildings \
                        production in APEX to refresh the data, and click any button on this screen.'
                    )
                    df = planet_production.orders
                    st.table(df)

                with st.expander(label='Buildings',expanded=True):
                    df = planet_production.buildings
                    df['daily workforce cost'] = df['ticker'].map(parser.get_building_wf_cost)
                    st.table(planet_production.buildings)

            else:
                st.write('Fetch user data first.')




        with test_tab:
            st.write(parser.get_building_wf_cost('RIG'))
            st.write(destination['price_source'])
            st.write(destination['cost_method'])
            st.write('check selection price:')
            st.write(destination['materials']['bse'].getInfo())

            st.write('bse nc1 ask')
            st.write(destination['materials']['bse'].nc1_ask)
            st.write('bse ci1 ask')
            st.write(destination['materials']['bse'].ci1_ask)
            st.write('bse nc1 bid')
            st.write(destination['materials']['bse'].nc1_bid)

            st.write(parser.profit_df(destination['recipes'].keys()))

    except KeyError:
        st.subheader('User must enter info on Home page.')



if __name__ == '__main__':
    main()
