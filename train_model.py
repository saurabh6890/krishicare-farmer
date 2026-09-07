# Simple educational ML prototype.
# It is deliberately small and should be replaced with real, validated agricultural data.
import pickle, os
import numpy as np
from sklearn.tree import DecisionTreeClassifier

X=np.array([
    [15,32,10],[22,30,20],[28,31,15],[35,29,20],
    [45,27,40],[55,25,60],[65,24,70],[75,23,80],
    [18,35,5],[40,33,30],[60,28,65],[80,26,75]
])
y=np.array(["Irrigation check","Irrigation check","Irrigation check","Monitor",
            "Monitor","Monitor","Monitor","Rain-aware",
            "Irrigation check","Monitor","Rain-aware","Rain-aware"])
model=DecisionTreeClassifier(max_depth=3, random_state=42)
model.fit(X,y)
path=os.path.join(os.path.dirname(__file__),"crop_model.pkl")
with open(path,"wb") as f: pickle.dump(model,f)
print("Saved",path)
