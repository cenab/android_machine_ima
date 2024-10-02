#!/usr/bin/env python3

"""

Usage:
    python analyze.py <experiment_name> <function>

Functions:
    - process: Processes data and trains models with feature selection and cross-validation.
    - count: Builds a count table of flows per application.

Example:
    python analyze.py experiment1 process
"""

import sys
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.model_selection import train_test_split, cross_validate, StratifiedKFold
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import SVC
from sklearn.feature_selection import mutual_info_classif
from sklearn.utils import shuffle

# -------------------------------
# Configuration and Global Variables
# -------------------------------

# Define applications and their full names
apps = ["discord", "messenger", "rocketchat", "signal", "skype", "slack", "telegram", "teams"]
apps_fullname = ["Discord", "Messenger", "RocketChat", "Signal", "Skype", "Slack", "Telegram", "Teams"]

# Mapping for label encoding based on type
app_to_num = {app.lower(): idx for idx, app in enumerate(apps_fullname)}
# Removed outbound mappings since outbound data is not available

# Define classifiers dictionary
cdic = {
    "DecisionTree": DecisionTreeClassifier(random_state=42),
    "RandomForest": RandomForestClassifier(random_state=42),
    "GradientBoosting": GradientBoostingClassifier(random_state=42),
    "LogisticRegression": LogisticRegression(max_iter=1000, random_state=42),
    "NaiveBayes": GaussianNB(),
    "SVM": SVC(random_state=42),
}

cdic_names = list(cdic.keys())

# Define paths relative to the current script location
base_dir = Path(__file__).parent  # Directory containing analyze.py
flow_dirs = [base_dir / f"flow{i}" for i in range(1, 4)]  # flow1, flow2, flow3
plots_root = base_dir / "plots"      # Directory to save plots
csvs = base_dir / "csvs"             # Directory to save CSVs

# Ensure directories exist
plots_root.mkdir(parents=True, exist_ok=True)
csvs.mkdir(parents=True, exist_ok=True)

# -------------------------------
# Utility Functions
# -------------------------------

def export_df(df: pd.DataFrame, filepath: Path):
    """
    Exports a DataFrame to a CSV file.

    Parameters:
    - df (pd.DataFrame): The DataFrame to export.
    - filepath (Path): The file path where the CSV will be saved.
    """
    try:
        df.to_csv(filepath, index=False)
        print(f"DataFrame exported to {filepath}")
    except Exception as e:
        print(f"Error exporting DataFrame to {filepath}: {e}")
        raise

def export_cm(cm: np.ndarray, labels: list, filepath: Path):
    """
    Exports a confusion matrix as a heatmap image.

    Parameters:
    - cm (np.ndarray): The confusion matrix.
    - labels (list): The labels for the axes.
    - filepath (Path): The file path where the heatmap image will be saved.
    """
    try:
        df_cm = pd.DataFrame(cm, index=labels, columns=labels)
        plt.figure(figsize=(12, 10))
        sns.heatmap(df_cm, annot=True, fmt='d', cmap='Blues')
        plt.ylabel('Actual')
        plt.xlabel('Predicted')
        plt.title('Confusion Matrix')
        plt.tight_layout()
        plt.savefig(filepath)
        plt.close()
        print(f"Confusion matrix heatmap saved to {filepath}")
    except Exception as e:
        print(f"Error exporting confusion matrix to {filepath}: {e}")
        raise

# -------------------------------
# Feature Manipulation Functions
# -------------------------------

def all_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Selects all features by dropping non-feature columns.

    Parameters:
    - df (pd.DataFrame): The input DataFrame.

    Returns:
    - pd.DataFrame: The DataFrame with selected features.
    """
    return df.drop(["lengths", "timestamps", "directions", "label"], axis=1, errors='ignore')

def only_stat_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Selects only statistical features by dropping non-statistical columns.

    Parameters:
    - df (pd.DataFrame): The input DataFrame.

    Returns:
    - pd.DataFrame: The DataFrame with statistical features.
    """
    return df.drop(["lengths", "timestamps", "directions", "label", "flow"], axis=1, errors='ignore')

def filter_by_direction(df: pd.DataFrame, direction: str) -> pd.DataFrame:
    """
    Filters the DataFrame based on the direction.

    Parameters:
    - df (pd.DataFrame): The input DataFrame.
    - direction (str): 'A' for out, 'B' for in.

    Returns:
    - pd.DataFrame: The filtered DataFrame.
    """
    if direction not in ["A", "B"]:
        raise ValueError("Direction must be 'A' or 'B'")
    return df[df["directions"] == direction]

def input_label(df: pd.DataFrame) -> tuple:
    """
    Separates the DataFrame into labels and inputs.

    Parameters:
    - df (pd.DataFrame): The input DataFrame.

    Returns:
    - tuple: A tuple containing (labels, inputs).
    """
    labels = df["label"]
    inputs = df.drop("label", axis=1, errors='ignore')
    return labels, inputs

def feature_selection(comb: pd.DataFrame, name: str, threshold: float = 0.05) -> pd.DataFrame:
    """
    Performs mutual information-based feature selection.

    Parameters:
    - comb (pd.DataFrame): Combined DataFrame with features and labels.
    - name (str): Experiment name used for exporting results.
    - threshold (float): Mutual information threshold for feature selection.

    Returns:
    - pd.DataFrame: DataFrame containing selected features based on mutual information.
    """
    y, X = input_label(comb)
    if X.empty:
        print("Error: No features available for mutual information calculation.")
        sys.exit(1)
    np.set_printoptions(suppress=True)
    cols = X.columns
    # Calculate mutual information
    infos = mutual_info_classif(X, y, discrete_features='auto', random_state=42)
    dic = dict(zip(cols, infos))
    
    # Debug: Print mutual information scores
    print("\nMutual Information Scores:")
    for feature, mi in dic.items():
        print(f"{feature}: {mi:.4f}")
    
    # Select features with MI > threshold
    new_dic = {col: mi for col, mi in dic.items() if mi > threshold}
    selected_features = list(new_dic.keys())
    
    if not selected_features:
        print(f"No features selected with mutual information threshold > {threshold}. Consider lowering the threshold.")
        sys.exit(1)
    
    print(f"\nSelected Features (MI > {threshold}): {selected_features}\n")
    
    df = pd.DataFrame({
        "Feature": selected_features,
        "Mutual Information": [new_dic[col] for col in selected_features]
    })
    export_df(df, csvs / f"{name}_mutual_info_features.csv")
    return comb[selected_features + ["label"]]

def choose_features(comb: pd.DataFrame, features: str, name: str, typee: str = "intra") -> pd.DataFrame:
    """
    Chooses features based on the specified feature type.

    Parameters:
    - comb (pd.DataFrame): Combined DataFrame with features and labels.
    - features (str): Feature selection type ('all', 'categorical', 'statistical', 'custom_categorical', 'custom_statistical', 'mutual_info').
    - name (str): Experiment name used for exporting results.
    - typee (str): Type of label encoding ('intra' or 'inter').

    Returns:
    - pd.DataFrame: DataFrame with selected features and encoded labels.
    """
    # Encode labels
    if typee == "inter":
        comb["label"] = comb["label"].map({"in": 0, "out": 1})
    else:
        comb["label"] = comb["label"].map(app_to_num)
    
    # Check for unmapped labels
    if comb["label"].isnull().any():
        unmapped = comb[comb["label"].isnull()]["label"].unique()
        print(f"Error: Found unmapped labels: {unmapped}")
        sys.exit(1)
    
    # Fill missing values
    comb = comb.fillna(0)
    
    # Drop unnecessary columns
    comb = comb.drop(["timeFirst", "timeLast", "flowInd"], axis=1, errors='ignore')
    to_drop = ["macStat", "macPairs", "srcMac_dstMac_numP", "srcMacLbl_dstMacLbl", "srcMac", "dstMac", "srcPort", "hdrDesc", "duration"]
    comb = comb.drop(columns=[col for col in to_drop if col in comb.columns], errors='ignore')
    
    # Convert categorical columns to numerical codes
    nonnumeric_cols = []
    for col in comb.select_dtypes(include=["object", "category"]).columns:
        nonnumeric_cols.append(col)
        comb[col] = comb[col].astype("category").cat.codes
    
    # Select features based on the 'features' parameter
    if features == "all":
        pass  # All features are already included
    elif features == "categorical":
        comb = comb[["label"] + nonnumeric_cols]
    elif features == "statistical":
        comb = comb.drop(columns=nonnumeric_cols, errors='ignore')
    elif features == "custom_categorical":
        custom_cat_cols = ["dstIPOrg", "srcIPOrg", "%dir", "dstPortClass"]
        available_cols = [col for col in custom_cat_cols if col in comb.columns]
        comb = comb[["label"] + available_cols]
    elif features == "custom_statistical":
        custom_stat_cols = [
            "numPktsSnt", "numPktsRcvd", "numBytesSnt", "numBytesRcvd",
            "minPktSz", "maxPktSz", "avePktSize", "stdPktSize",
            "minIAT", "maxIAT", "aveIAT", "stdIAT", "bytps"
        ]
        available_cols = [col for col in custom_stat_cols if col in comb.columns]
        comb = comb[["label"] + available_cols]
    elif features == "mutual_info":
        comb = feature_selection(comb, name)
    else:
        raise ValueError(f"Unknown feature type: {features}")
    
    return comb

# -------------------------------
# Data Import Functions
# -------------------------------

def tran_name(app: str, flow_dir: Path) -> Path:
    """
    Constructs the file path for the tranalyzer output based on the app and flow directory.

    Parameters:
    - app (str): Application identifier (e.g., 'discord').
    - flow_dir (Path): Path to the flow directory (flow1, flow2, flow3).

    Returns:
    - Path: The file path to the tranalyzer output.
    """
    # Capitalize the first letter to match the filenames (e.g., 'Discord_filtered_flows.txt')
    app_capitalized = app.capitalize()
    filename = f"{app_capitalized}_filtered_flows.txt"
    return flow_dir / filename

def build_count_table(comb: pd.DataFrame, name: str):
    """
    Builds and exports a count table of flows per application.

    Parameters:
    - comb (pd.DataFrame): Combined DataFrame with all flows.
    - name (str): Experiment name used for exporting results.
    """
    # Define labels and their full names for the count table
    all_labels = apps  # ["discord", "messenger", "rocketchat", "signal", "skype", "slack", "telegram", "teams"]
    fullnames = apps_fullname
    
    app_counts = []
    for label in all_labels:
        count = len(comb[comb["label"] == app_to_num[label]].index)
        app_counts.append(count)
    
    count_df = pd.DataFrame({
        "Setting": fullnames,
        "Number of Total Flows": app_counts
    })
    
    export_df(count_df, csvs / f"{name}_num_flows.csv")

# -------------------------------
# Model Training and Evaluation Functions
# -------------------------------

def train_plotrange(
    comb: pd.DataFrame,
    labels: list,
    name: str,
    cross_validateq: bool,
    direction: str,
    features: str,
    typee: str = "intra"
):
    """
    Trains classifiers and evaluates their performance, optionally using cross-validation.

    Parameters:
    - comb (pd.DataFrame): Combined DataFrame with features and labels.
    - labels (list): List of label names.
    - name (str): Experiment name used for exporting results.
    - cross_validateq (bool): Whether to perform cross-validation.
    - direction (str): Direction of flows ('A', 'B', or 'both').
    - features (str): Feature selection type.
    - typee (str): Type of label encoding ('intra' or 'inter').
    """
    y, X = input_label(comb)
    
    # Debugging: Print unique labels and their counts
    unique_labels, counts = np.unique(y, return_counts=True)
    label_counts = dict(zip(unique_labels, counts))
    print(f"Unique Labels in y: {unique_labels}")
    print(f"Label Counts: {label_counts}\n")
    
    # Check if multiple classes are present
    if len(unique_labels) < 2:
        print("Error: Less than two classes present in the label vector. Classification requires at least two classes.")
        sys.exit(1)
    
    # Debugging: Print shapes of X and y
    print(f"Shape of X: {X.shape}")
    print(f"Shape of y: {y.shape}\n")
    
    if X.empty or y.empty:
        print("Error: Feature matrix X or label vector y is empty.")
        sys.exit(1)
    
    # Feature Scaling
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    print("Feature scaling applied.\n")
    
    # Optional: Class Balancing (Uncomment if needed)
    # from sklearn.utils import resample
    # majority_class = comb[comb['label'] == app_to_num['slack']]
    # minority_classes = comb[comb['label'] != app_to_num['slack']]
    # minority_upsampled = resample(minority_classes,
    #                               replace=True,
    #                               n_samples=len(majority_class),
    #                               random_state=42)
    # X_scaled = np.vstack((X_scaled[comb['label'] == app_to_num['slack']], scaler.transform(minority_upsampled.drop('label', axis=1))))
    # y = np.concatenate((y[comb['label'] == app_to_num['slack']], minority_upsampled['label'].values))
    # print("Class balancing applied.\n")
    
    arr = []
    f1_ranges = []
    accur_ranges = []
    pred_ranges = []
    recall_ranges = []
    
    for clf_name, clf in cdic.items():
        print(f"Training classifier: {clf_name}")
        if not cross_validateq:
            # Single train-test split
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=0.4, random_state=42, stratify=y
            )
            clf.fit(X_train, y_train)
            y_predic = clf.predict(X_test)
            
            # Debugging: Print unique labels in predictions
            unique_pred = np.unique(y_predic)
            print(f"Unique Labels in y_predic: {unique_pred}\n")
            
            metrics = [
                accuracy_score(y_test, y_predic),
                precision_score(y_test, y_predic, average='macro', zero_division=0),
                recall_score(y_test, y_predic, average='macro', zero_division=0),
                f1_score(y_test, y_predic, average='macro', zero_division=0)
            ]
            arr.append([metrics[0], metrics[1], metrics[2], metrics[3]])
        else:
            # 10-fold cross-validation using StratifiedKFold
            scoring = ['accuracy', 'precision_macro', 'recall_macro', 'f1_macro']
            cv = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)
            try:
                scores = cross_validate(estimator=clf, X=X_scaled, y=y, cv=cv, scoring=scoring, error_score='raise')
            except Exception as e:
                print(f"Error during cross-validation for classifier {clf_name}: {e}\n")
                continue  # Skip to the next classifier
            
            # Collect score ranges
            f1s = scores["test_f1_macro"]
            accurs = scores["test_accuracy"]
            precs = scores["test_precision_macro"]
            recalls = scores["test_recall_macro"]
            
            f1_ranges.append(f"{round(f1s.min(), 3)}-{round(f1s.max(), 3)}")
            accur_ranges.append(f"{round(accurs.min(), 3)}-{round(accurs.max(), 3)}")
            pred_ranges.append(f"{round(precs.min(), 3)}-{round(precs.max(), 3)}")
            recall_ranges.append(f"{round(recalls.min(), 3)}-{round(recalls.max(), 3)}")
            
            # Export individual fold scores
            df_scores = pd.DataFrame({
                "Accuracy": accurs,
                "Precision": precs,
                "Recall": recalls,
                "F1": f1s
            })
            export_df(df_scores, csvs / f"{name}_fold_{clf_name}_{features}.csv")
            
            # Fit on the entire dataset for confusion matrix
            clf.fit(X_scaled, y)
            y_predic = clf.predict(X_scaled)
            
            # Debugging: Print unique labels in predictions
            unique_pred = np.unique(y_predic)
            print(f"Unique Labels in y_predic: {unique_pred}\n")
            
            # Generate confusion matrix with all known labels
            cm = confusion_matrix(y, y_predic, labels=list(app_to_num.values()))
            try:
                export_cm(cm, labels, plots_root / f"{name}_cm_{clf_name}_{features}.png")
            except ValueError as ve:
                print(f"ValueError while exporting confusion matrix for {clf_name}: {ve}")
                print(f"Confusion Matrix Shape: {cm.shape}, Expected Shape: ({len(labels)}, {len(labels)})\n")
    
    # -------------------------------
    # Data Processing Functions
    # -------------------------------

def import_csv(name: str, features: str, direction: str = "both"):
    """
    Imports CSV files for each application, processes them, and exports the combined DataFrame.

    Parameters:
    - name (str): Experiment name used for exporting results.
    - features (str): Feature selection type.
    - direction (str): Direction of flows ('A', 'B', or 'both').
    """
    arr = []
    for flow_dir in flow_dirs:
        for app, fullname in zip(apps, apps_fullname):
            try:
                filepath = tran_name(app, flow_dir)
                df = pd.read_csv(filepath, delimiter=r'\s+', index_col=False)
                df["label"] = app.lower()  # Label as the lowercase app name
                arr.append(df)
                print(f"Imported {len(df)} flows for app: {fullname} from {flow_dir.name}")
            except FileNotFoundError:
                print(f"File not found for app: {fullname} in {flow_dir.name}, skipping.")
            except Exception as e:
                print(f"Error reading file for app: {fullname} in {flow_dir.name}: {e}")
    
    if not arr:
        print("No data imported. Exiting.")
        sys.exit(1)
    
    comb = pd.concat(arr, ignore_index=True)
    comb = choose_features(comb, features, name, typee="intra")
    comb = shuffle(comb, random_state=42)
    comb = comb.reset_index(drop=True)
    print("Combined DataFrame head:")
    print(comb.head())  # Display first few rows for verification
    
    # Debugging: Print class distribution
    unique_labels, counts = np.unique(comb["label"], return_counts=True)
    label_counts = dict(zip(unique_labels, counts))
    print(f"Class Distribution:\n{label_counts}\n")
    
    export_df(comb, csvs / f"{name}_{features}_out.csv")
    print(f"Combined DataFrame exported to {csvs / f'{name}_{features}_out.csv'}\n")

def process(
    name: str,
    direction: str,
    features: str,
    cdic_dict: dict = cdic,
    cross_validateq: bool = False
):
    """
    Processes data, performs feature selection, and trains/evaluates classifiers.

    Parameters:
    - name (str): Experiment name.
    - direction (str): Direction of flows ('A', 'B', or 'both').
    - features (str): Feature selection type.
    - cdic_dict (dict): Dictionary of classifiers.
    - cross_validateq (bool): Whether to perform cross-validation.
    """
    arr = []
    for flow_dir in flow_dirs:
        for app, fullname in zip(apps, apps_fullname):
            try:
                filepath = tran_name(app, flow_dir)
                df = pd.read_csv(filepath, delimiter=r'\s+', index_col=False)
                # Automatically read the number of flows (lines) from the txt file
                num_flows = len(df)
                sampled_df = df  # Use all flows; no sampling
                sampled_df["label"] = app.lower()
                arr.append(sampled_df)
                print(f"Processed {num_flows} flows for app: {fullname} from {flow_dir.name}")
            except FileNotFoundError:
                print(f"File not found for app: {fullname} in {flow_dir.name}, skipping.")
            except Exception as e:
                print(f"Error processing file for app: {fullname} in {flow_dir.name}: {e}")
    
    if not arr:
        print("No data to process. Exiting.")
        sys.exit(1)
    
    comb = pd.concat(arr, ignore_index=True)
    comb = choose_features(comb, features, name, typee="intra")
    comb = shuffle(comb, random_state=42)
    
    # Debugging: Print class distribution
    unique_labels, counts = np.unique(comb["label"], return_counts=True)
    label_counts = dict(zip(unique_labels, counts))
    print(f"Class Distribution:\n{label_counts}\n")
    
    train_plotrange(
        comb=comb,
        labels=apps_fullname,  # Use full names for labels
        name=name,
        cross_validateq=cross_validateq,
        direction=direction,
        features=features,
        typee="intra"
    )

# -------------------------------
# Main Execution Block
# -------------------------------

def main():
    """
    Main function to execute the script based on command-line arguments.
    """
    if len(sys.argv) != 3:
        print("Usage: python analyze.py <experiment_name> <function>")
        print("Functions: process, count")
        sys.exit(1)
    
    name = sys.argv[1]
    function = sys.argv[2].lower()
    feature_options = ["mutual_info", "all", "categorical", "statistical", "custom_statistical"]
    
    if function == "process":
        for feature in feature_options:
            print(f"\nProcessing with feature type: {feature}")
            process(name, direction="both", features=feature, cross_validateq=True)
    elif function == "count":
        try:
            # Assuming 'count' function requires combined data
            import_csv(name, features="all", direction="both")
            comb = pd.read_csv(csvs / f"{name}_all_out.csv")
            build_count_table(comb, name)
        except FileNotFoundError:
            print("Combined CSV not found. Please run the 'process' function first.")
    else:
        print(f"Unknown function: {function}. Available functions: process, count")
        sys.exit(1)

if __name__ == "__main__":
    main()
