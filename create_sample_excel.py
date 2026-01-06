import pandas as pd

data = [
    ["I have a car", "J'ai une voiture"],
    ["The sky is blue", "Le ciel est bleu"],
    ["Hello world", "Bonjour le monde"]
]

df = pd.DataFrame(data)
df.to_excel("sample.xlsx", index=False, header=False)
print("Created sample.xlsx")
