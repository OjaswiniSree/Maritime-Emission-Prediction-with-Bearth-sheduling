import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import SMOTE
import joblib

# Load data
data = pd.read_csv("emissions_dataset2.csv")
data = data.dropna(subset=['emissions'])

# Separate features and target
X = data.drop(columns=['emissions'])
y = data['emissions']
# Split data into train and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Apply SMOTE to balance classes
smote = SMOTE(random_state=42)
X_resampled, y_resampled = smote.fit_resample(X_train, y_train)

# Train the RandomForestClassifier with balanced class weights
rf_classifier = RandomForestClassifier(
    max_depth=10, 
    min_samples_leaf=1, 
    min_samples_split=7, 
    n_estimators=50,               # Increased estimators for better learning
    class_weight='balanced',       # Adjust class importance
    random_state=42
)
rf_classifier.fit(X_resampled, y_resampled)

# Save the trained model
joblib.dump(rf_classifier, 'trained_model.pkl')

# Output feature names and counts
if hasattr(rf_classifier, "feature_names_in_"):
    print("Feature names:", rf_classifier.feature_names_in_)
else:
    print("The model does NOT support feature_names_in_.")
print("Features used during training:", rf_classifier.feature_names_in_)
print("Number of features expected:", len(rf_classifier.feature_names_in_))
