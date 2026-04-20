import streamlit as st
import sqlite3
import pandas as pd
import os
import plotly.express as px

# Configuração da Página
st.set_page_config(page_title="Avatar Lana Overlord", page_icon="🧠", layout="wide")

# Estilo Moderno (Vibrant)
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMetric { background-color: #161b22; border-radius: 10px; padding: 15px; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# No Cloud Run, o banco será copiado para a raiz da app
DB_PATH = os.environ.get("DB_PATH", "registry.db")
if not os.path.exists(DB_PATH):
    # Fallback para desenvolvimento local
    DB_PATH = os.path.join(os.path.dirname(__file__), "..", "infrastructure", "registry.db")

def load_data():
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT * FROM production_logs ORDER BY timestamp DESC", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Erro ao carregar banco de dados: {e}")
        return pd.DataFrame()

# Header
st.title("🧠 Avatar Lana Overlord")
st.subheader("Controle Financeiro e Gestão de Ecossistema")

df = load_data()

if df.empty:
    st.info("Aguardando os primeiros registros de renderização para popular o dashboard...")
else:
    # --- METRICAS ---
    col1, col2, col3, col4 = st.columns(4)
    total_cost = df['estimated_cost_usd'].sum()
    total_jobs = len(df)
    avg_cost = df['estimated_cost_usd'].mean()
    uptime_total = df['uptime_minutes'].sum()

    with col1:
        st.metric("Investimento Total (USD)", f"${total_cost:.2f}")
    with col2:
        st.metric("Total de Avatares", total_jobs)
    with col3:
        st.metric("Custo Médio/Vídeo", f"${avg_cost:.2f}")
    with col4:
        st.metric("Tempo Total GPU (min)", f"{uptime_total:.1f}")

    st.divider()

    # --- GRAFICOS ---
    g_col1, g_col2 = st.columns(2)

    with g_col1:
        st.write("### 📈 Investimento Diário")
        df['date'] = pd.to_datetime(df['timestamp']).dt.date
        daily_spend = df.groupby('date')['estimated_cost_usd'].sum().reset_index()
        fig_daily = px.bar(daily_spend, x='date', y='estimated_cost_usd', 
                           labels={'estimated_cost_usd': 'USD', 'date': 'Data'},
                           color_discrete_sequence=['#ff4b4b'])
        st.plotly_chart(fig_daily, use_container_width=True)

    with g_col2:
        st.write("### 🛸 Distribuição de Hardware")
        gpu_counts = df['gpu_type'].value_counts().reset_index()
        fig_pie = px.pie(gpu_counts, values='count', names='gpu_type', hole=.4,
                         color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_pie, use_container_width=True)

    # --- TABELA DETALHADA ---
    st.write("### 📜 Histórico de Produção Industrial")
    st.dataframe(df[['job_id', 'timestamp', 'region', 'gpu_type', 'estimated_cost_usd', 'status']], 
                 use_container_width=True, hide_index=True)

# Rodapé
st.caption("Ecossistema Industrial Brasil AI - Gerenciado por Lana Overlord v10.1")
