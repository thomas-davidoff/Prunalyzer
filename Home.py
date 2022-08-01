import pandas as pd
import streamlit as st
import parser
import streamlit_funx as sf
import styles_import


# ---- PAGE SETUP ----

# ---- SIDEBAR ----

# ---- BODY ----



def main():
    print('---- HOME MAIN ----')
    styles_import.local_css('local.css')


    # specify which data is relevant to the current page
    page_data = []

    # Check if FIO connection has been initialized
    if 'init' not in st.session_state:
        parser.fio_init()

    for dataset in page_data:
        if dataset[0] not in st.session_state:
            parser.force_fio_get(args_list=page_data)

    fio_username = st.text_input(
        label='FIO Username:',
        value='Username'
        # value=st.session_state['FIO Authorization']['fio_user']
    )
    fio_pass = st.text_input(
        label='FIO Password (stored locally)',
        value='Password'
        # value=st.session_state['FIO Authorization']['fio_pass']
    )
    username = st.text_input(
        label='In-game Username',
        value='PRUN Username'
        # value=st.session_state['FIO Authorization']['ign']
    )

    sf.CustomButton(
        text='Verify Token',
        session_key='authenticate_token',
        hint=None,
        func=parser.add_user,
        args=[fio_username, fio_pass, username]
    )


if __name__ == '__main__':
    main()
