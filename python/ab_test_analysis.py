# A/B TEST ANALYSIS SCRIPT

# Import libraries
import pandas as pd                                         
import matplotlib.pyplot as plt                             
from statsmodels.stats.proportion import proportions_ztest  
from statsmodels.stats.power import NormalIndPower          
import numpy as np

print("=" * 55)
print("  A/B TEST ANALYSIS: Product Page Redesign")
print("=" * 55)

# Load the data
users        = pd.read_csv("users.csv")
sessions     = pd.read_csv("sessions.csv")
events       = pd.read_csv("events.csv")
assignments  = pd.read_csv("experiment_assignments.csv")

print(f"\n Data loaded successfully!")
print(f"   Users: {len(users):,}")
print(f"   Sessions: {len(sessions):,}")
print(f"   Events: {len(events):,}")

# Join the tables together
df = sessions.merge(assignments[['user_id', 'variant']], on='user_id')

df = df.merge(users[['user_id', 'country']], on='user_id')

print("Columns in df:", df.columns.tolist())
print("Sample rows:")
print(df.head(3))

# Flag which sessions resulted in a purchase
purchases = (events[events['event_type'] == 'purchase']
             [['session_id']]
             .drop_duplicates())
purchases['purchased'] = 1

add_to_cart = (events[events['event_type'] == 'add_to_cart']
               [['session_id']]
               .drop_duplicates())
add_to_cart['add_to_cart'] = 1

# Left join: every session kept, 'purchased' = 0 if no purchase
df = df.merge(purchases, on='session_id', how='left')
df = df.merge(add_to_cart, on='session_id', how='left')
df[['purchased', 'add_to_cart']] = df[['purchased', 'add_to_cart']].fillna(0)

# Calculate conversion rates by variant
conversion = df.groupby('variant')['purchased'].agg(
    sessions='count',
    conversions='sum',
    conversion_rate='mean'
)

print("\n CONVERSION RATES BY VARIANT")
print("-" * 40)
for variant, row in conversion.iterrows():
    label = "Control (old page)" if variant == 'A' else "Treatment (new page)"
    print(f"  Variant {variant} [{label}]")
    print(f"    Sessions:        {int(row['sessions']):,}")
    print(f"    Conversions:     {int(row['conversions']):,}")
    print(f"    Conversion Rate: {row['conversion_rate']:.2%}")
    print()

# Run the statistical test (Z-test for proportions)
conversions_arr = conversion['conversions'].values.astype(int)
sessions_arr    = conversion['sessions'].values.astype(int)

z_stat, p_value = proportions_ztest(conversions_arr, sessions_arr)
lift = ((conversion.loc['B', 'conversion_rate'] -
         conversion.loc['A', 'conversion_rate']) /
         conversion.loc['A', 'conversion_rate'])

print(" STATISTICAL TEST RESULTS")
print("-" * 40)
print(f"  Z-statistic: {z_stat:.3f}")
print(f"  P-value:     {p_value:.4f}")
print(f"  Lift:        {lift:.2%}")
print()
if p_value < 0.05:
    print("  RESULT: Statistically significant (p < 0.05)")
    print("  We can reject the null hypothesis.")
    print("  The new page (B) genuinely outperforms the old page (A).")
else:
    print("  RESULT: Not statistically significant (p >= 0.05)")
    print("  We cannot conclude the new page is better.")

# Segment analysis - who benefits most?
print("\n CONVERSION RATE BY DEVICE")
print("-" * 40)
device_seg = (df.groupby(['variant', 'device'])['purchased']
              .mean()
              .unstack()
              .round(4))
print(device_seg.to_string())

# Add-to-cart funnel analysis
print("\n FUNNEL ANALYSIS")
print("-" * 40)
for variant in ['A', 'B']:
    sub = df[df['variant'] == variant]
    label = "Control" if variant == 'A' else "Treatment"
    atc_rate = sub['add_to_cart'].mean()
    conv_rate = sub['purchased'].mean()
    print(f"  Variant {variant} [{label}]:")
    print(f"    Add-to-cart rate: {atc_rate:.2%}")
    print(f"    Purchase rate:    {conv_rate:.2%}")
    print()

# Sample size check (power analysis)
analysis = NormalIndPower()
required_n = analysis.solve_power(
    effect_size=0.05,
    power=0.80,
    alpha=0.05
)
print(f" POWER ANALYSIS")
print("-" * 40)
print(f"  Minimum sample size per group: {required_n:.0f}")
print(f"  Our actual size per group:     ~{sessions_arr.mean():.0f}")
adequate = sessions_arr.mean() >= required_n
print(f"  Sample adequate? {'YES' if adequate else 'NO'}")

# Create charts
fig, axes = plt.subplots(1, 3, figsize=(14, 5))
fig.suptitle('A/B Test Results: Product Page Redesign', fontsize=14, fontweight='bold')

# Chart 1: Conversion rate bar chart
rates = conversion['conversion_rate'] * 100
colors = ['#5b8dee', '#f77f00']
axes[0].bar(['A (Control)', 'B (Treatment)'], rates, color=colors, width=0.5)
axes[0].set_ylabel('Conversion Rate (%)')
axes[0].set_title('Overall Conversion Rate')
axes[0].set_ylim(0, rates.max() * 1.3)
for i, v in enumerate(rates):
    axes[0].text(i, v + 0.2, f'{v:.1f}%', ha='center', fontweight='bold')

# Chart 2: Device segment breakdown
dev = df.groupby(['variant', 'device'])['purchased'].mean().unstack() * 100
dev.T.plot(kind='bar', ax=axes[1], color=colors, width=0.6)
axes[1].set_title('Conversion by Device')
axes[1].set_ylabel('Conversion Rate (%)')
axes[1].set_xlabel('')
axes[1].tick_params(axis='x', rotation=0)
axes[1].legend(title='Variant')

# Chart 3: Funnel comparison
funnel_metrics = ['page_view', 'click', 'add_to_cart', 'purchase']
funnel_data = {}
for v in ['A', 'B']:
    sub_sessions = df[df['variant'] == v]['session_id'].unique()
    ev_v = events[events['session_id'].isin(sub_sessions)]
    total = len(sub_sessions)
    counts = []
    for m in funnel_metrics:
        c = ev_v[ev_v['event_type'] == m]['session_id'].nunique()
        counts.append(c / total * 100)
    funnel_data[v] = counts

x = np.arange(len(funnel_metrics))
w = 0.3
axes[2].bar(x - w/2, funnel_data['A'], w, label='A Control', color=colors[0])
axes[2].bar(x + w/2, funnel_data['B'], w, label='B Treatment', color=colors[1])
axes[2].set_xticks(x)
axes[2].set_xticklabels(['Page View', 'Click', 'Add to Cart', 'Purchase'], fontsize=9)
axes[2].set_ylabel('% of Sessions')
axes[2].set_title('Funnel Comparison')
axes[2].legend()

plt.tight_layout()
plt.savefig('ab_test_results.png', dpi=150, bbox_inches='tight')
print("\n Chart saved as 'ab_test_results.png'")
print("\n Analysis complete!")
