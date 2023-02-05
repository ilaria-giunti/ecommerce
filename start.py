import streamlit as st
import pandas as pd
import sys
import os
import numpy as np
import locale
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
import pandas_profiling


# setup page
st.set_page_config(page_title='eCommerce Data', page_icon='🚀', layout='wide')

# validate file
def validate_file(file):
    filename = file.name
    name, ext = os.path.splitext(filename)
    if ext in ('.csv', '.xlsx'):
        return ext
    else:
        return False

# sidebar
with st.sidebar:
    uploader_file = st.file_uploader("Upload .csv or .xlsx files not exceeding 10MB")
    budget = st.number_input("Qual è il tuo budget")
    button = st.button("Submit")

if button:
    if uploader_file:
        file = uploader_file.getvalue()
        # process the uploaded file and budget value here
        st.write("File and Budget submitted successfully.")
    else:
        st.write("Please upload a file and set the budget.")


if uploader_file is not None:
    ext = validate_file(uploader_file)
    if ext:
        if ext == '.csv':
            df = pd.read_csv(uploader_file)

            df['order_date'] = pd.to_datetime(df['order_date'])
            df['order_date'] = df['order_date'].dt.strftime('%Y-%m-%d')
            df['order_date'] = pd.to_datetime(df['order_date'])
            df['order_total'] = round(df['order_total'], 2)

            def get_customer_metrics():
                client = df['customer_id'].nunique()
                client2orders = df[df.groupby('customer_id').order_id.transform('count') > 1].customer_id.nunique()
                repurchaserate = round(client2orders/client*100, 2)
                orders = df['order_id'].count()
                COC = round(orders/client, 3)
                return client, client2orders, repurchaserate, orders, COC

            client, client2orders, repurchaserate, orders, COC = get_customer_metrics()

            def add_month_column(df):
                df['mese'] = df['order_date'].dt.strftime('%Y-%m')
                return df

            df = add_month_column(df)

            def add_first_order_info(df):
                first_order_date = df.groupby("customer_id")["order_date"].min()
                df["primo_ordine"] = df["customer_id"].map(first_order_date)
                df['primo_ordine'] = df['primo_ordine'].dt.strftime('%Y-%m-%d')
                df['primo_ordine'] = pd.to_datetime(df['primo_ordine'])
                df["primo_ordine"] = pd.to_datetime(df['primo_ordine'])
                df['order_type'] = np.where(df['order_date'] == df['primo_ordine'], 'New', 'Recurring')
                df['30_days'] = (df['primo_ordine'] + pd.Timedelta(days=30)).dt.date
                df['60_days'] = df['30_days'] + pd.Timedelta(days=30)
                df['90_days'] = df['60_days'] + pd.Timedelta(days=30)
                df['120_days'] = df['90_days'] + pd.Timedelta(days=30)
                return df

            df = add_first_order_info(df)

            def get_new_clients_per_month():
                new_clients_per_month = df.loc[df['order_type'] == 'New'].groupby('mese').size().mean()
                return new_clients_per_month

            new_clients_per_month = get_new_clients_per_month()

            def get_cost_of_acquisition():
                cost_of_acquisition = budget / new_clients_per_month
                return cost_of_acquisition
            
            cost_of_acquisition=round(get_cost_of_acquisition(),2)

            def add_ltv_columns(df):
                    periods = [30, 60, 90, 120]
                    for period in periods:
                        ltv_col = f"{period}_days_ltv"
                        df[ltv_col] = df[(df["order_date"] - df["primo_ordine"]).dt.days <= period].groupby("customer_id")["order_total"].sum().reset_index()["order_total"].round(2)
                    return df


            df= add_ltv_columns(df)

            def get_repurchase_date(customer_id, order_date, df, n):
                customer_orders = df[df["customer_id"] == customer_id].sort_values("order_date")
                if len(customer_orders) >= n:
                    repurchase_order = customer_orders.iloc[n - 1]["order_date"]
                    return repurchase_order
                else:
                    return pd.NaT
            
            def second_order_date(customer_id, order_date, df):
                customer_orders = df[df["customer_id"] == customer_id].sort_values("order_date")
                if len(customer_orders) >= 2:
                    second_order = customer_orders.iloc[1]["order_date"]
                    return second_order
                else:
                    return pd.NaT

            df["second_order_date"] = df.apply(lambda x: second_order_date(x["customer_id"], x["order_date"], df), axis=1)
            df["second_order_date"].fillna(pd.NaT, inplace=True)
            df["time_to_repurchase 1-2"] = round((df["second_order_date"] - df["primo_ordine"]).dt.days,2)

            def third_order_date(customer_id, order_date, df):
                customer_orders = df[df["customer_id"] == customer_id].sort_values("order_date")
                if len(customer_orders) >= 3:
                    third_order = customer_orders.iloc[1]["order_date"]
                    return third_order
                else:
                    return pd.NaT

            df["third_order_date"] = df.apply(lambda x: third_order_date(x["customer_id"], x["order_date"], df), axis=1)
            df["third_order_date"].fillna(pd.NaT, inplace=True)
            df["time_to_repurchase 2-3"] = (df["third_order_date"] - df["second_order_date"]).dt.days
            average_timetorepurchase=round(df['time_to_repurchase 1-2'].mean(),2)
            average_ltv3mesi=round(df['90_days_ltv'].mean(),2)

            #pivot
            pivot = df.pivot_table(index='mese', columns='order_type', values='order_id', aggfunc='count', fill_value=0)
            pivot = pivot.sort_index(ascending=True)
            pivot['Totale DB'] = pivot['New'].cumsum()
            pivot['Totale Rep_Recurring'] = round(pivot['Recurring'] / pivot['Totale DB']*100,2)

            if len(pivot) <= 8:
                repmonth=0
            else:
                repmonth=round(pivot['Totale Rep_Recurring'].tail(4).mean(),2)

            with st.expander('Clicca qui per vedere il Dataframe'):
                st.dataframe(df, width=None, height=None)
            with st.expander('Clicca qui per vedere il Report per Mese'):
                st.dataframe(pivot, width=None, height=None)
            
            with st.container():
                if repmonth==0:
                    st.write(f"""il tuo CAC Overall è {cost_of_acquisition}€""")
                    st.write(f"\nHai {client} clienti e solo il {repurchaserate}% fa più di un ordine")
                    st.write(f"\nInfatti in media i tuoi clienti fanno {COC} ordini")
                    st.write(f"\nIl tuo LTV a 90 giorni è {average_ltv3mesi}€")
                    st.write(f"\nTra il 1 e il 2 ordine passano {average_timetorepurchase} giorni")
                    st.write(f"\nnNon abbiamo abbastanza dati per dirti qual è la percentuale di acquisto ogni mese. Dobbiamo avere almeno 8 mesi di storico")
                else:
                    st.write(f"""il tuo CAC Overall è {cost_of_acquisition}€""")
                    st.write(f"\nHai {client} clienti e solo il {repurchaserate}% fa più di un ordine")
                    st.write(f"\nInfatti in media i tuoi clienti fanno {COC} ordini")
                    st.write(f"\nIl tuo LTV a 90 giorni è {average_ltv3mesi}€")
                    st.write(f"\nTra il 1 e il 2 ordine passano {average_timetorepurchase} giorni")
                    st.write(f"\nSolo {repmonth}% dei tuoi clienti riacquista ogni mese")
        else:
            st.error("Kindly upload only .csv or .xlsx files")
else:
    st.title("eCommerce Data")
    st.info("Upload your data in the left sidebar to generate a profiling report")
