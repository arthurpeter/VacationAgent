import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# 1. Citirea fisierului CSV
if not os.path.exists("results.csv"):
    print("results.csv nu a fost gasit. Folosind datele de test hardcodate pentru generarea ploturilor.")
    import io
    csv_data = """Endpoint,Cache,Concurrency,Pipelining,Duration,Requests,Requests_Per_Second,Avg_Latency_ms,P97.5_Latency_ms,Errors
mockup/refresh,no,10,1,20,4000,189,52ms,59ms,0
mockup/refresh,no,50,1,20,6000,315,156ms,323ms,0
mockup/refresh,no,100,2,20,7000,354,553ms,1257ms,0
mockup/refresh,no,250,2,20,7246,366,1297ms,3687ms,0
mock/offers/{id},no,10,1,10,1000,112,88ms,51ms,0
mock/offers/{id},yes,50,1,20,20000,1016,48ms,56ms,0
mock/offers/{id},yes,100,2,20,22000,1093,182ms,335ms,0
mock/offers/{id},yes,250,2,20,22000,1085,455ms,574ms,0
mock/discovery/stream/{id},no,10,1,60,120,1.84,5109ms,5120ms,0
mock/discovery/stream/{id},no,50,1,60,600,9.17,5121ms,5169ms,0
mock/discovery/stream/{id},no,100,1,60,1000,18.34,5125ms,5207ms,0
mock/discovery/stream/{id},no,250,1,60,3000,45.84,5173ms,5478ms,0
itinerary/schedule/action,no,5,1,60,22,0.29,16s,21s,0
itinerary/schedule/action,no,20,1,60,60,0.67,30s,33s,0
itinerary/schedule/action,no,50,1,120,100,0.42,62s,63s,0"""
    df = pd.read_csv(io.StringIO(csv_data))
else:
    df = pd.read_csv("results.csv")

# 2. Conversia latentelor in secunde
def to_seconds(val):
    val = str(val).lower().strip()
    if 'ms' in val:
        return float(val.replace('ms', '')) / 1000.0
    if 's' in val:
        return float(val.replace('s', ''))
    return float(val)

df['Avg_Latency_s'] = df['Avg_Latency_ms'].apply(to_seconds)
df['P97.5_Latency_s'] = df['P97.5_Latency_ms'].apply(to_seconds)

# Crearea unei etichete care sa contina si factorul de pipelining pentru transparenta totala
df['Concurrency_Label'] = df.apply(lambda r: f"{r['Concurrency']} (P={r['Pipelining']})", axis=1)

# Configurare stil global academic (fara diacritice, titluri in engleza)
sns.set_theme(style="whitegrid")
plt.rcParams.update({
    'font.size': 11, 
    'axes.labelsize': 12, 
    'axes.titlesize': 12,
    'legend.fontsize': 10
})

# =========================================================================
# GRAPH 1: Token Refresh (PostgreSQL Blacklist)
# =========================================================================
df_auth = df[df['Endpoint'].str.contains('refresh')].copy()
fig, ax1 = plt.subplots(figsize=(8, 5))

color = '#1f77b4'
ax1.set_xlabel('Concurrency & Pipelining Factor: X (P=Pipeline)')
ax1.set_ylabel('Throughput (RPS)', color=color)
line1 = ax1.plot(df_auth['Concurrency_Label'], df_auth['Requests_Per_Second'], marker='o', color=color, linewidth=2.5, label='Throughput (RPS)')
ax1.tick_params(axis='y', labelcolor=color)

ax2 = ax1.twinx()  
color = '#d62728'
ax2.set_ylabel('Average Latency (Seconds)', color=color)
line2 = ax2.plot(df_auth['Concurrency_Label'], df_auth['Avg_Latency_s'], marker='s', linestyle='--', color=color, linewidth=2.5, label='Average Latency (s)')
ax2.tick_params(axis='y', labelcolor=color)

lines = line1 + line2
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='upper left')

# plt.title('Token Refresh Service Scalability Profile (AuthX + DB Blacklist)')
plt.tight_layout()
plt.savefig('plot_auth.png', dpi=300)
plt.close()


# =========================================================================
# GRAPH 2: Offers Service (Redis Cache Evaluation)
# =========================================================================
df_offers = df[df['Endpoint'].str.contains('offers')].copy()
df_offers['Cache_Status'] = df_offers['Cache'].apply(lambda x: "With Cache" if str(x).lower() == 'yes' else "WithoutCache")

plt.figure(figsize=(8, 5))
sns.barplot(data=df_offers, x='Concurrency_Label', y='Requests_Per_Second', hue='Cache_Status', palette='Set1')
plt.yscale('log')
plt.xlabel('Concurrency & Pipelining Factor: X (P=Pipeline)')
plt.ylabel('Throughput (Requests Per Second - RPS)')
plt.legend(title='Data Management State')
plt.tight_layout()
plt.savefig('plot_cache.png', dpi=300)
plt.close()


# =========================================================================
# GRAPH 3: Discovery Stream (SSE - Highlight Constant Latency)
# =========================================================================
df_sse = df[df['Endpoint'].str.contains('discovery')].copy()
fig, ax1 = plt.subplots(figsize=(8, 5))

color = '#2ca02c'
ax1.set_xlabel('Concurrency (Concurrent Clients | P=1)')
ax1.set_ylabel('Throughput (RPS)', color=color)
line1 = ax1.plot(df_sse['Concurrency'].astype(str), df_sse['Requests_Per_Second'], marker='^', color=color, linewidth=2.5, label='Throughput (RPS)')
ax1.tick_params(axis='y', labelcolor=color)

ax2 = ax1.twinx()
color = '#9467bd'
ax2.set_ylabel('Average Latency (Seconds)', color=color)
line2 = ax2.plot(df_sse['Concurrency'].astype(str), df_sse['Avg_Latency_s'], marker='o', linestyle=':', color=color, linewidth=2.5, label='Average Latency (s)')
ax2.set_ylim(0, 7) 
ax2.tick_params(axis='y', labelcolor=color)

lines = line1 + line2
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='center left')

# Titlu corectat: contine explicatia tehnica legata de non-blocking calls in paranteza
# plt.title('Discovery Graph Scalability (Non-Blocking Async Nodes)')
plt.tight_layout()
plt.savefig('plot_sse.png', dpi=300)
plt.close()


# =========================================================================
# GRAPH 4: Schedule Engine (OR-Tools Optimization)
# =========================================================================
df_or = df[df['Endpoint'].str.contains('schedule')].copy()
fig, ax1 = plt.subplots(figsize=(8, 5))

color = '#ff7f0e'
ax1.set_xlabel('Concurrency (Concurrent Clients | P=1)')
ax1.set_ylabel('Throughput (RPS)', color=color)
line1 = ax1.plot(df_or['Concurrency'].astype(str), df_or['Requests_Per_Second'], marker='o', color=color, linewidth=2.5, label='Throughput (RPS)')
ax1.tick_params(axis='y', labelcolor=color)

ax2 = ax1.twinx()
color = '#7f7f7f'
ax2.set_ylabel('Average Latency (Seconds)', color=color)
line2 = ax2.plot(df_or['Concurrency'].astype(str), df_or['Avg_Latency_s'], marker='x', linestyle='-.', color=color, linewidth=2.5, label='Average Latency (s)')
ax2.tick_params(axis='y', labelcolor=color)

lines = line1 + line2
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='upper left')

# Titlu corectat: descrie exact performanta si scalabilitatea la procesare computationale
# plt.title('Schedule Engine Performance and Compute Scalability Profile')
plt.tight_layout()
plt.savefig('plot_ortools.png', dpi=300)
plt.close()

print("Succes! Toate cele 4 ploturi au fost actualizate conform cerintelor tale.")