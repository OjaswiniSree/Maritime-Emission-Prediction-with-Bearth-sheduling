import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

print("hi")

# Load data
data = pd.read_csv("emissions_dataset2.csv")
data = data.dropna(subset=['emissions'])
X = data.drop(columns=['emissions'])
y = data['emissions']


# Split data into train and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
rf_classifier = RandomForestClassifier(max_depth=10, min_samples_leaf=1, min_samples_split=7, n_estimators=7, random_state=42)
rf_classifier.fit(X_train, y_train)

if hasattr(rf_classifier, "feature_names_in_"):
    print("Feature names:", rf_classifier.feature_names_in_)
else:
    print("The model does NOT support feature_names_in_.")

# Save the trained model
import joblib
joblib.dump(rf_classifier, 'trained_model.pkl')

print("Features used during training:", rf_classifier.feature_names_in_)
print("Number of features expected:", len(rf_classifier.feature_names_in_))
