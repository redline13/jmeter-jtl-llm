import pandas as pd
import plotly.express as px

# Load the data
file1_path = "/Users/mikebugden/Desktop/jmeter-jtl-llm/uploads/results1.csv"
df1 = pd.read_csv(file1_path)

# Convert timestamp to datetime
df1['timeStamp'] = pd.to_datetime(df1['timeStamp'], unit='ms')

# Set timestamp as index
df1.set_index('timeStamp', inplace=True)

# Resample to get the number of threads per second
threads_per_second = df1['elapsed'].resample('S').count()

# Create the plot
fig = px.line(threads_per_second, title='JMeter Threads per Second', labels={'value': 'Threads', 'timeStamp': 'Time'})

# Generate HTML
plot_html = fig.to_html(full_html=False)
print(plot_html)
