import matplotlib.pyplot as plt

# Data
english_periods = ['1 Year', '3 Years', '5 Years', '10 Years', '15 Years']
data = {
    '米国': [39.10, 20.20, 13.42, 14.39, 7.81],
    'ヨーロッパ': [17.97, 10.71, 6.65, 7.16, None],
    '日本': [16.56, 18.02, 6.87, 15.54, None],
    'インド': [16.67, 13.79, 7.14, 38.76, None],
    'オーストラリア': [23.51, 42.57, 19.14, 20.86, 19.11],
    'カナダ': [21.79, 35.21, 5.48, 5.43, None],
    '中東・北アフリカ': [81.82, 58.62, 41.38, 15.15, None],
    'ブラジル': [23.95, 23.44, 25.45, 7.69, None],
    '南アフリカ': [52.50, 54.63, 50.24, 30.22, None],
    'メキシコ': [32.56, 29.27, 22.73, 15.00, None],
    'チリ': [75.61, 31.11, 32.65, 6.98, None]
}

# English labels for countries
country_labels = {
    '米国': 'USA',
    'ヨーロッパ': 'Europe',
    '日本': 'Japan',
    'インド': 'India',
    'オーストラリア': 'Australia',
    'カナダ': 'Canada',
    '中東・北アフリカ': 'Middle East & North Africa',
    'ブラジル': 'Brazil',
    '南アフリカ': 'South Africa',
    'メキシコ': 'Mexico',
    'チリ': 'Chile'
}

# Distinct colors for each country
colors = [
    'blue', 'green', 'red', 'purple', 'orange',
    'cyan', 'magenta', 'darkgreen', 'brown', 'pink', 'grey'
]

# Plotting with English labels and distinct colors
plt.figure(figsize=(15, 10))
for i, (country, values) in enumerate(data.items()):
    plt.plot(english_periods, values, label=country_labels[country], color=colors[i], marker='o')

plt.xlabel('Period')
plt.ylabel('Active Fund Winning Rate (%)')
plt.title('Active Fund Winning Rate by Region')
plt.legend(loc='upper right', bbox_to_anchor=(1.15, 1))
plt.grid(True, which='both', linestyle='--', linewidth=0.5)
plt.tight_layout()

plt.show()
