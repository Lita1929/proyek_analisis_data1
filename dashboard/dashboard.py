import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency
sns.set_theme(style='white')

#create_daily_orders_df() digunakan untuk menyiapkan daily_orders_df.

def create_daily_orders_df(df):
    daily_orders_df = df.resample(rule='D', on='order_purchase_timestamp').agg({
        "order_id": "nunique",
        "payment_value": "sum"
    })

    daily_orders_df = daily_orders_df.reset_index()
    daily_orders_df.rename(columns={
        "order_id": "order_count",
        "payment_value": "revenue"
    }, inplace=True)

    return daily_orders_df

#create_sum_order_products_df() bertanggung jawab untuk menyiapkan sum_orders_products_df.
def create_sum_order_products_df(df):
    sum_order_products_df = df.groupby("product_category_name_english").order_id.nunique().sort_values(ascending=False).reset_index()
    
    return sum_order_products_df

#create_cust_bystate_df() digunakan untuk menyiapkan cust_bystate_df.
def create_cust_bystate_df(df):
    cust_bystate_df = df.groupby(by="customer_state").customer_id.nunique().reset_index()
    cust_bystate_df.rename(columns={
        "customer_id": "customer_count"
    }, inplace=True)

    return cust_bystate_df

#create_seller_bystate_df() digunakan untuk menyiapkan seller_bystate_df.
def create_seller_bystate_df(df):
    seller_bystate_df = df.groupby(by="seller_state").seller_id.nunique().reset_index()
    seller_bystate_df.rename(columns={
        "seller_id": "seller_count"
    }, inplace=True)

    return seller_bystate_df

#create_rfm_df() bertanggung jawab untuk menghasilkan rfm_df.
def create_rfm_df(df):
    rfm_df = df.groupby(by=["customer_id","customer_num"], as_index=False).agg({
        "order_purchase_timestamp": "max", # mengambil tanggal order terakhir
        "order_id": "nunique", # menghitung jumlah order
        "payment_value": "sum" # menghitung jumlah revenue yang dihasilkan
    })
    rfm_df.columns = ["customer_id", "customer_num", "max_order_timestamp", "frequency","monetary"]

    rfm_df["max_order_timestamp"] = rfm_df["max_order_timestamp"].dt.date
    recent_date = df["order_purchase_timestamp"].dt.date.max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days)
    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)

    return rfm_df

#tahap berikutnya ialah load berkas all_data.csv sebagai sebuah DataFrame
all_df = pd.read_csv("all_data.csv")

# Mengurutkan DataFrame berdasarkan order_date serta memastikan kedua kolom tersebut bertipe datetime.

datetime_columns = ["order_purchase_timestamp", "order_delivered_customer_date"]
all_df.sort_values(by="order_purchase_timestamp", inplace=True)
all_df.reset_index(inplace=True)

for column in datetime_columns:
    all_df[column] = pd.to_datetime(all_df[column])


# Membuat Komponen Filter
# tahap berikutnya ialah menambahkan filter pada dashboard yang akan dibuat.

min_date = all_df["order_purchase_timestamp"].min()
max_date = all_df["order_purchase_timestamp"].max()

with st.sidebar:
    # Menambahkan logo perusahaan
    st.image("https://cdn.icon-icons.com/icons2/1949/PNG/512/free-30-instagram-stories-icons37_122583.png")

    # Mengambil start_date & end_date dari date_input
    start_date, end_date = st.date_input(
        label='Time Range', min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

#Kode di atas akan menghasilkan start_date dan end_date yang selanjutnya akan digunakan untuk memfilter DataFrame.

main_df = all_df[(all_df["order_purchase_timestamp"] >= str(start_date)) &
                (all_df["order_purchase_timestamp"] <= str(end_date))]

# Proses ini dilakukan dengan memanggil helper function yang telah kita buat sebelumnya.

daily_orders_df = create_daily_orders_df(main_df)
sum_order_products_df = create_sum_order_products_df(main_df)
cust_bystate_df = create_cust_bystate_df(main_df)
seller_bystate_df = create_seller_bystate_df(main_df)
rfm_df = create_rfm_df(main_df)

# Melengkapi Dashboard dengan Berbagai Visualisasi Data

#menambahkan header pada dashboard
st.header('Glicínia ComprasFáceis Dashboard 🛍️')

#menampilkan informasi total order dan revenue dalam bentuk metric()
st.subheader('Daily Orders')

col1, col2 = st.columns(2)

with col1:
    total_orders = daily_orders_df.order_count.sum()
    st.metric("Total orders", value=total_orders)

with col2:
    total_revenue = format_currency(daily_orders_df.revenue.sum(), "BRL", locale='pt_BR')
    st.metric("Total Revenue", value=total_revenue)

fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(
    daily_orders_df["order_purchase_timestamp"],
    daily_orders_df["order_count"],
    linewidth=2,
    color="#2C7DA0"
)
# Menggambar area di bawah garis
ax.fill_between(
    daily_orders_df["order_purchase_timestamp"],
    daily_orders_df["order_count"],
    color="#ADE8F4",
    alpha=0.3  # Transparansi untuk area
)

ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15)

st.pyplot(fig)

# menampilkan 8 produk paling laris dan paling sedikit terjual

st.subheader("Best & Worst Performing Product")

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(35, 15))

colors = ["#2C7DA0", "#ADE8F4", "#ADE8F4", "#ADE8F4", "#ADE8F4", "#ADE8F4", "#ADE8F4", "#ADE8F4"]

sns.barplot(x="order_id", y="product_category_name_english", data=sum_order_products_df.head(8), palette=colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel("Number of Sales", fontsize=30)
ax[0].set_title("Best Performing Product", loc="center", fontsize=50)
ax[0].tick_params(axis='y', labelsize=35)
ax[0].tick_params(axis='x', labelsize=30)

sns.barplot(x="order_id", y="product_category_name_english", data=sum_order_products_df.sort_values(by="order_id", ascending=True).head(8), palette=colors, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel("Number of Sales", fontsize=30)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Worst Performing Product", loc="center", fontsize=50)
ax[1].tick_params(axis='y', labelsize=35)
ax[1].tick_params(axis='x', labelsize=30)

st.pyplot(fig)

#Informasi berikutnya yang ingin ditampilkan pada dashboard ialah terkait demografi pelanggan yang kita miliki.
st.subheader("Customer Demographics")

colors = ["#2C7DA0"]
fig, ax = plt.subplots(figsize=(20, 10))
sns.barplot(
    x="customer_count",
    y="customer_state",
    data=cust_bystate_df.sort_values(by="customer_count", ascending=False),
    palette=colors,
    ax=ax
)
ax.set_title("Number of Customer by States", loc="center", fontsize=40)
ax.set_ylabel(None)
ax.set_xlabel(None)
ax.set_xscale('log')
ax.tick_params(axis='x', labelsize=25)
ax.tick_params(axis='y', labelsize=20)
st.pyplot(fig)

#Informasi berikutnya yang ingin ditampilkan pada dashboard ialah demografi penjual yang kita miliki.
st.subheader("Seller Demographics")

colors = ["#ADE8F4"]
fig, ax = plt.subplots(figsize=(20, 10))
sns.barplot(
    x="seller_count",
    y="seller_state",
    data=seller_bystate_df.sort_values(by="seller_count", ascending=False),
    palette=colors,
    ax=ax
)
ax.set_title("Number of Seller by States", loc="center", fontsize=40)
ax.set_ylabel(None)
ax.set_xlabel(None)
ax.set_xscale('log')
ax.tick_params(axis='x', labelsize=25)
ax.tick_params(axis='y', labelsize=20)
st.pyplot(fig)

# Informasi terakhir yang harus kita tampilkan ialah terkait parameter RFM (Recency, Frequency, & Monetary).
# menampilkan nilai average atau rata-rata dari ketiga parameter tersebut menggunakan widget metric().
st.subheader("Best Customer Based on RFM Parameters")

col1, col2, col3 = st.columns(3)

with col1:
    avg_recency = round(rfm_df.recency.mean(), 1)
    st.metric("Average Recency (days)", value=avg_recency)

with col2:
    avg_frequency = round(rfm_df.frequency.mean(), 2)
    st.metric("Average Frequency", value=avg_frequency)

with col3:
    avg_frequency = format_currency(rfm_df.monetary.mean(), "BRL", locale='pt_BR')
    st.metric("Average Monetary", value=avg_frequency)

fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(35, 15))
colors = ["#2C7DA0", "#2C7DA0", "#2C7DA0", "#2C7DA0", "#2C7DA0"]

sns.barplot(y="recency", x="customer_id", hue="recency",data=rfm_df.sort_values(by="recency", ascending=True).head(5), palette=colors, ax=ax[0], legend=False)
ax[0].set_ylabel(None)
ax[0].set_xlabel("customer_id", fontsize=30)
ax[0].set_title("By Recency (days)", loc="center", fontsize=50)
ax[0].tick_params(axis='y', labelsize=30)
ax[0].tick_params(axis='x', labelsize=35)
# Mengatur ticks untuk sumbu x
ax[0].set_xticks(range(len(rfm_df.head(5))))
# Mengambil nilai customer_num
ax[0].set_xticklabels(rfm_df['customer_num'].head(5).values)

sns.barplot(y="frequency", x="customer_id", hue="frequency", data=rfm_df.sort_values(by="frequency", ascending=False).head(5), palette=colors, ax=ax[1], legend=False)
ax[1].set_ylabel(None)
ax[1].set_xlabel("customer_id", fontsize=30)
ax[1].set_title("By Frequency", loc="center", fontsize=50)
ax[1].tick_params(axis='y', labelsize=30)
ax[1].tick_params(axis='x', labelsize=35)
ax[1].set_xticks(range(len(rfm_df.head(5))))
ax[1].set_xticklabels(rfm_df['customer_num'].head(5).values)

sns.barplot(y="monetary", x="customer_id", hue="monetary", data=rfm_df.sort_values(by="monetary", ascending=False).head(5), palette=colors, ax=ax[2], legend=False)
ax[2].set_ylabel(None)
ax[2].set_xlabel("customer_id", fontsize=30)
ax[2].set_title("By Monetary", loc="center", fontsize=50)
ax[2].tick_params(axis='y', labelsize=30)
ax[2].tick_params(axis='x', labelsize=35)
ax[2].set_xticks(range(len(rfm_df.head(5))))
ax[2].set_xticklabels(rfm_df['customer_num'].head(5).values)

st.pyplot(fig)

st.caption('Copyright (c) Glicínia ComprasFáceis 2024')

