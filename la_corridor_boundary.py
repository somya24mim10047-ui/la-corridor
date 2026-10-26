
import pandas as pd
import matplotlib.pyplot as plt

# Example business counts for every 250 metres.
# These are imaginary values, not real LA data.
data = {
    "section": [1, 2, 3, 4, 5, 6, 7, 8],
    "businesses": [3, 5, 14, 18, 20, 17, 5, 2]
}

df = pd.DataFrame(data)

# Smooth the counts using nearby sections
df["average"] = (
    df["businesses"]
    .rolling(window=3, center=True, min_periods=1)
    .mean()
)

# Choose a practice threshold
threshold = 10

# Mark sections with relatively high activity
df["commercial"] = df["average"] >= threshold

# Plot the graph
plt.figure(figsize=(10, 5))

plt.bar(
    df["section"],
    df["businesses"],
    label="Business count"
)

plt.plot(
    df["section"],
    df["average"],
    marker="o",
    label="Rolling average"
)

plt.axhline(
    threshold,
    linestyle="--",
    label="Practice threshold"
)

plt.xlabel("Section along Western Avenue")
plt.ylabel("Number of businesses")
plt.title("Commercial Activity Along Western Avenue")
plt.xticks(df["section"])
plt.legend()
plt.grid(axis="y", alpha=0.3)
plt.show()

print(df)

