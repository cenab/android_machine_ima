#!/usr/bin/env python3

"""
Usage:
    python analyze.py <experiment_name> <function>

Functions:
    - process: Processes data and trains models with feature selection, cross-validation, and hyperparameter tuning.
    - count: Builds a count table of flows per application and per device.
    - eda: Performs Exploratory Data Analysis on the dataset.
    - train_model: Trains a selected model and saves it for future use.

Examples:
    python analyze.py experiment1 process
    python analyze.py experiment1 count
    python analyze.py experiment1 eda
    python analyze.py experiment1 train_model
"""

import sys
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.model_selection import train_test_split, cross_validate, StratifiedKFold, GridSearchCV
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
    make_scorer,
)
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import SVC
from sklearn.feature_selection import mutual_info_classif, VarianceThreshold, SelectKBest, f_classif
from sklearn.utils import shuffle, resample
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.multioutput import MultiOutputClassifier
from sklearn.inspection import permutation_importance
from imblearn.over_sampling import SMOTE
import joblib
import logging
import multiprocessing
import os

# -------------------------------
# Logging Configuration
# -------------------------------

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("analyze.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger()

# -------------------------------
# Configuration and Global Variables
# -------------------------------

# Define applications and their full names
apps = ["discord", "messenger", "rocketchat", "signal", "skype", "slack", "telegram", "teams"]
apps_fullname = ["Discord", "Messenger", "RocketChat", "Signal", "Skype", "Slack", "Telegram", "Teams"]

# Define devices
devices = ["flow1", "flow2", "flow3"]
devices_fullname = ["Device1", "Device2", "Device3"]

# Mapping for label encoding based on type
app_to_num = {app.lower(): idx for idx, app in enumerate(apps_fullname)}
device_to_num = {device: idx for idx, device in enumerate(devices_fullname)}

# Define classifiers dictionary with initial classifiers
cdic = {
    # "DecisionTree": DecisionTreeClassifier(random_state=42, class_weight='balanced'),
    # "RandomForest": RandomForestClassifier(random_state=42, class_weight='balanced'),
    "GradientBoosting": GradientBoostingClassifier(random_state=42),  # Does not support class_weight
    # "LogisticRegression": LogisticRegression(max_iter=1000, random_state=42, class_weight='balanced'),
    # "NaiveBayes": GaussianNB()  # Does not support class_weight
}

cdic_names = list(cdic.keys())

# Define paths relative to the current script location
base_dir = Path(__file__).parent  # Directory containing analyze.py
flow_dirs = [base_dir / f"flow{i}" for i in range(1, 4)]  # flow1, flow2, flow3 representing different devices
plots_root = base_dir / "plots"      # Directory to save plots
csvs = base_dir / "csvs"             # Directory to save CSVs
models_dir = base_dir / "models"     # Directory to save trained models

# Ensure directories exist
plots_root.mkdir(parents=True, exist_ok=True)
csvs.mkdir(parents=True, exist_ok=True)
models_dir.mkdir(parents=True, exist_ok=True)

# -------------------------------
# Custom Scoring Function
# -------------------------------

def multioutput_f1_macro(y_true, y_pred):
    """
    Calculates the mean F1 macro score for multi-output classification.

    Parameters:
    - y_true (np.ndarray): True labels.
    - y_pred (np.ndarray): Predicted labels.

    Returns:
    - float: Mean F1 macro score across all outputs.
    """
    f1_scores = []
    for i in range(y_true.shape[1]):
        f1 = f1_score(y_true[:, i], y_pred[:, i], average='macro', zero_division=0)
        f1_scores.append(f1)
    return np.mean(f1_scores)

multioutput_scorer = make_scorer(multioutput_f1_macro)

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
        logger.info(f"DataFrame exported to {filepath}")
    except Exception as e:
        logger.error(f"Error exporting DataFrame to {filepath}: {e}")
        raise

def export_cm(cm: np.ndarray, labels: list, filepath: Path, title: str):
    """
    Exports a confusion matrix as a heatmap image.

    Parameters:
    - cm (np.ndarray): The confusion matrix.
    - labels (list): The labels for the axes.
    - filepath (Path): The file path where the heatmap image will be saved.
    - title (str): Title for the confusion matrix plot.
    """
    try:
        df_cm = pd.DataFrame(cm, index=labels, columns=labels)
        plt.figure(figsize=(8, 6))  # Smaller figure size

        # Create the heatmap and capture the Axes object
        ax = sns.heatmap(
            df_cm, annot=True, fmt='d', cmap='Blues',
            annot_kws={"size": 14},       # Increase font size for annotations
            cbar_kws={'label': 'Color bar label'}  # Removed 'fontsize' here
        )

        # Set the colorbar label and tick label font sizes
        cbar = ax.collections[0].colorbar
        cbar.ax.yaxis.label.set_size(14)   # Set colorbar label font size
        cbar.ax.tick_params(labelsize=14)  # Set colorbar tick labels font size

        plt.ylabel('Actual', fontsize=16)    # Larger y-axis label
        plt.xlabel('Predicted', fontsize=16)  # Larger x-axis label
        plt.title(title, fontsize=18)        # Larger title
        plt.xticks(fontsize=14)              # Larger x-axis tick labels
        plt.yticks(fontsize=14)              # Larger y-axis tick labels
        plt.tight_layout()
        plt.savefig(filepath)
        plt.close()
        logger.info(f"Confusion matrix heatmap saved to {filepath}")

    except Exception as e:
        logger.error(f"Error exporting confusion matrix to {filepath}: {e}")
        raise

def export_feature_importance(importances: pd.DataFrame, filepath: Path, title: str):
    """
    Exports feature importances as a bar plot.

    Parameters:
    - importances (pd.DataFrame): DataFrame containing feature importances.
    - filepath (Path): The file path where the plot will be saved.
    - title (str): Title for the feature importance plot.
    """
    try:
        plt.figure(figsize=(12, 8))
        sns.barplot(x='Importance', y='Feature', data=importances.sort_values(by='Importance', ascending=False))
        plt.title(title)
        plt.tight_layout()
        plt.savefig(filepath)
        plt.close()
        logger.info(f"Feature importance plot saved to {filepath}")
    except Exception as e:
        logger.error(f"Error exporting feature importance to {filepath}: {e}")
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
    labels = df[["application", "device"]]
    inputs = df.drop(["application", "device"], axis=1, errors='ignore')
    return labels, inputs

def feature_selection(comb: pd.DataFrame, name: str, threshold: float = 0.05, sample_size: int = 10000) -> pd.DataFrame:
    """
    Performs mutual information-based feature selection with optimizations.

    Parameters:
    - comb (pd.DataFrame): Combined DataFrame with features and labels.
    - name (str): Experiment name used for exporting results.
    - threshold (float): Mutual information threshold for feature selection.
    - sample_size (int): Number of samples to use for mutual information computation.

    Returns:
    - pd.DataFrame: DataFrame containing selected features based on mutual information.
    """
    y, X = input_label(comb)

    # Debugging: Print unique labels and their counts
    unique_apps, app_counts = np.unique(y["application"], return_counts=True)
    unique_devices, device_counts = np.unique(y["device"], return_counts=True)
    app_label_counts = dict(zip(unique_apps, app_counts))
    device_label_counts = dict(zip(unique_devices, device_counts))
    logger.info(f"Application Labels for Feature Selection: {unique_apps}")
    logger.info(f"Application Label Counts: {app_label_counts}")
    logger.info(f"Device Labels for Feature Selection: {unique_devices}")
    logger.info(f"Device Label Counts: {device_label_counts}\n")

    # Encode multi-labels for mutual_info_classif
    # For simplicity, we'll perform feature selection based on application labels
    y_app = y["application"]

    if X.empty:
        logger.error("No features available for mutual information calculation.")
        sys.exit(1)
    
    # Remove low-variance features
    selector = VarianceThreshold(threshold=0.0)  # Adjust threshold as needed
    X_var = selector.fit_transform(X)
    selected_features = X.columns[selector.get_support()]
    comb = comb[selected_features.tolist() + ["application", "device"]]
    logger.info(f"Dataset shape after variance threshold: {comb.shape}")

    # Sampling if dataset is large
    if comb.shape[0] > sample_size:
        comb_sampled = resample(comb, n_samples=sample_size, random_state=42, stratify=y_app)
        logger.info(f"Sampled {sample_size} samples for mutual information computation.")
    else:
        comb_sampled = comb.copy()
        logger.info(f"Using the entire dataset for mutual information computation.")

    y_app_sampled = comb_sampled["application"]
    X_sampled = comb_sampled.drop(["application", "device"], axis=1)

    # Calculate mutual information
    logger.info("Starting mutual information computation...")
    try:
        infos = mutual_info_classif(
            X_sampled,
            y_app_sampled,
            discrete_features='auto',
            random_state=42,
            n_neighbors=3,  # Reduced number of neighbors for speed
            n_jobs=2         # Limit the number of parallel jobs
        )
    except Exception as e:
        logger.error(f"Error during mutual information computation: {e}")
        sys.exit(1)
    
    dic = dict(zip(X_sampled.columns, infos))

    # Debug: Print mutual information scores
    logger.info("\nMutual Information Scores:")
    for feature, mi in dic.items():
        logger.info(f"{feature}: {mi:.4f}")

    # Select features with MI > threshold
    new_dic = {col: mi for col, mi in dic.items() if mi > threshold}
    selected_features_mi = list(new_dic.keys())

    if not selected_features_mi:
        logger.error(f"No features selected with mutual information threshold > {threshold}. Consider lowering the threshold.")
        sys.exit(1)

    logger.info(f"\nSelected Features (MI > {threshold}): {selected_features_mi}\n")

    df = pd.DataFrame({
        "Feature": selected_features_mi,
        "Mutual Information": [new_dic[col] for col in selected_features_mi]
    })
    export_df(df, csvs / f"{name}_mutual_info_features.csv")
    return comb[selected_features_mi + ["application", "device"]]

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
    # if typee == "inter":
    #     comb["application"] = comb["application"].map(app_to_num)
    # else:
    #     comb["application"] = comb["application"].map(app_to_num)

    # comb["device"] = comb["device"].map(device_to_num)

    # Check for unmapped labels
    if comb["application"].isnull().any() or comb["device"].isnull().any():
        unmapped_apps = comb[comb["application"].isnull()]["application"].unique()
        unmapped_devices = comb[comb["device"].isnull()]["device"].unique()
        logger.error(f"Found unmapped labels: Applications - {unmapped_apps}, Devices - {unmapped_devices}")
        sys.exit(1)

    # Fill missing values
    comb = comb.fillna(0)

    # Drop unnecessary columns
    comb = comb.drop(["timeFirst", "timeLast", "flowInd"], axis=1, errors='ignore')
    to_drop = [] #["macStat", "macPairs", "srcMac_dstMac_numP", "srcMacLbl_dstMacLbl", "srcMac", "dstMac", "srcPort", "hdrDesc", "duration"]
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
        comb = comb[["application", "device"] + nonnumeric_cols]
    elif features == "statistical":
        comb = comb.drop(columns=nonnumeric_cols, errors='ignore')
    elif features == "custom_categorical":
        custom_cat_cols = ["dstIPOrg", "srcIPOrg", "%dir", "dstPortClass"]
        available_cols = [col for col in custom_cat_cols if col in comb.columns]
        comb = comb[["application", "device"] + available_cols]
    elif features == "custom_statistical":
        custom_stat_cols = [
            "numPktsSnt", "numPktsRcvd", "numBytesSnt", "numBytesRcvd",
            "minPktSz", "maxPktSz", "avePktSize", "stdPktSize",
            "minIAT", "maxIAT", "aveIAT", "stdIAT", "bytps"
        ]
        available_cols = [col for col in custom_stat_cols if col in comb.columns]
        comb = comb[["application", "device"] + available_cols]
    elif features == "mutual_info":
        comb = feature_selection(comb, name)
    elif features == "anova_f_test":
        comb = anova_feature_selection(comb, name)
    else:
        raise ValueError(f"Unknown feature type: {features}")

    return comb

def anova_feature_selection(comb: pd.DataFrame, name: str, k: int = 100) -> pd.DataFrame:
    """
    Performs ANOVA F-test-based feature selection.

    Parameters:
    - comb (pd.DataFrame): Combined DataFrame with features and labels.
    - name (str): Experiment name used for exporting results.
    - k (int): Number of top features to select.

    Returns:
    - pd.DataFrame: DataFrame with selected features based on ANOVA F-test.
    """
    y, X = input_label(comb)
    y_app = y["application"]

    logger.info("Starting ANOVA F-test feature selection...")
    selector = SelectKBest(score_func=f_classif, k=k)
    selector.fit(X, y_app)
    selected_features = X.columns[selector.get_support()]
    logger.info(f"Selected top {k} features based on ANOVA F-test.")

    # Save feature scores
    scores = selector.scores_
    fi_df = pd.DataFrame({
        "Feature": X.columns,
        "F-Score": scores
    }).sort_values(by="F-Score", ascending=False)
    export_df(fi_df, csvs / f"{name}_anova_f_test_features.csv")

    return comb[selected_features.tolist() + ["application", "device"]]

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
    Builds and exports a count table of flows per application and per device.

    Parameters:
    - comb (pd.DataFrame): Combined DataFrame with all flows.
    - name (str): Experiment name used for exporting results.
    """
    # Define labels and their full names for the count table
    full_app_names = apps_fullname
    full_device_names = devices_fullname

    # Count per application
    app_counts = comb['application'].value_counts().sort_index()
    app_counts_df = pd.DataFrame({
        "Application": full_app_names,
        "Number of Total Flows": app_counts.values
    })

    # Count per device
    device_counts = comb['device'].value_counts().sort_index()
    device_counts_df = pd.DataFrame({
        "Device": full_device_names,
        "Number of Total Flows": device_counts.values
    })

    # Export both tables
    export_df(app_counts_df, csvs / f"{name}_num_flows_per_application.csv")
    export_df(device_counts_df, csvs / f"{name}_num_flows_per_device.csv")

# -------------------------------
# Exploratory Data Analysis (EDA)
# -------------------------------

def perform_eda(comb: pd.DataFrame, name: str):
    """
    Performs Exploratory Data Analysis on the combined DataFrame.

    Parameters:
    - comb (pd.DataFrame): Combined DataFrame with all flows.
    - name (str): Experiment name used for exporting EDA results.
    """
    logger.info("Starting Exploratory Data Analysis (EDA)...")

    # Summary statistics
    summary = comb.describe(include='all')
    export_df(summary, csvs / f"{name}_eda_summary.csv")
    # logger.info(f"EDA summary statistics exported to {csvs / f'{name}_eda_summary.csv'}")

    # Distribution of applications
    plt.figure(figsize=(10, 6))
    sns.countplot(y='application', data=comb, order=comb['application'].value_counts().index)
    plt.title('Distribution of Applications')
    plt.xlabel('Count')
    plt.ylabel('Application')
    plt.tight_layout()
    plt.savefig(plots_root / f"{name}_eda_application_distribution.png")
    plt.close()
    # logger.info(f"Application distribution plot saved to {plots_root / f'{name}_eda_application_distribution.png'}")

    # Distribution of devices
    plt.figure(figsize=(8, 6))
    sns.countplot(x='device', data=comb, order=comb['device'].value_counts().index)
    plt.title('Distribution of Devices')
    plt.xlabel('Device')
    plt.ylabel('Count')
    plt.tight_layout()
    plt.savefig(plots_root / f"{name}_eda_device_distribution.png")
    plt.close()
    # logger.info(f"Device distribution plot saved to {plots_root / f'{name}_eda_device_distribution.png'}")

    # Correlation heatmap
    numerical_features = comb.select_dtypes(include=[np.number]).columns.tolist()
    plt.figure(figsize=(16, 14))
    corr = comb[numerical_features].corr()
    sns.heatmap(corr, annot=False, cmap='coolwarm')
    plt.title('Correlation Heatmap of Numerical Features')
    plt.tight_layout()
    plt.savefig(plots_root / f"{name}_eda_correlation_heatmap.png")
    plt.close()
    # logger.info(f"Correlation heatmap saved to {plots_root / f'{name}_eda_correlation_heatmap.png'}")

    # Box plots for numerical features
    for feature in numerical_features:
        plt.figure(figsize=(8, 6))
        sns.boxplot(x='application', y=feature, data=comb)
        plt.title(f'Box Plot of {feature} by Application')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(plots_root / f"{name}_eda_boxplot_{feature}.png")
        plt.close()
        # logger.info(f"Box plot for {feature} saved to {plots_root / f'{name}_eda_boxplot_{feature}.png'}")

    # Violin plots for numerical features
    for feature in numerical_features:
        plt.figure(figsize=(8, 6))
        sns.violinplot(x='application', y=feature, data=comb)
        plt.title(f'Violin Plot of {feature} by Application')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(plots_root / f"{name}_eda_violinplot_{feature}.png")
        plt.close()
        # logger.info(f"Violin plot for {feature} saved to {plots_root / f'{name}_eda_violinplot_{feature}.png'}")

    # Feature clustering using hierarchical clustering
    try:
        from scipy.cluster.hierarchy import linkage, dendrogram
        from scipy.cluster.hierarchy import fcluster
        from sklearn.preprocessing import StandardScaler

        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(comb.select_dtypes(include=[np.number]))

        linked = linkage(scaled_features, 'ward')

        plt.figure(figsize=(25, 10))
        dendrogram(linked, orientation='top', distance_sort='descending', show_leaf_counts=False)
        plt.title('Hierarchical Clustering Dendrogram')
        plt.xlabel('Sample Index')
        plt.ylabel('Distance')
        plt.tight_layout()
        plt.savefig(plots_root / f"{name}_eda_feature_clustering.png")
        plt.close()
        # logger.info(f"Feature clustering dendrogram saved to {plots_root / f'{name}_eda_feature_clustering.png'}")
    except ImportError:
        logger.warning("Scipy is not installed. Skipping feature clustering.")
    except Exception as e:
        logger.error(f"Error during feature clustering: {e}")

    logger.info("EDA completed.\n")

# -------------------------------
# Handling Imbalanced Data
# -------------------------------

def handle_imbalance(X: np.ndarray, y: np.ndarray, strategy: str = "class_weight") -> tuple:
    """
    Handles imbalanced data using the specified strategy.

    Parameters:
    - X (np.ndarray): Feature matrix.
    - y (np.ndarray): Label matrix.
    - strategy (str): Balancing strategy ('smote', 'undersample', 'class_weight').

    Returns:
    - tuple: Balanced (X, y) or original (X, y) if strategy is 'class_weight'.
    """
    if strategy == "smote":
        logger.info("Applying SMOTE for oversampling minority classes.")
        smote = SMOTE(random_state=42, sampling_strategy='auto', n_jobs=-1)
        X_res, y_res = smote.fit_resample(X, y)
        logger.info("SMOTE applied successfully.")
        return X_res, y_res
    elif strategy == "undersample":
        logger.info("Applying undersampling to balance classes.")
        from imblearn.under_sampling import RandomUnderSampler
        rus = RandomUnderSampler(random_state=42)
        X_res, y_res = rus.fit_resample(X, y)
        logger.info("Undersampling applied successfully.")
        return X_res, y_res
    elif strategy == "class_weight":
        logger.info("Using class weighting instead of resampling to handle imbalanced classes.")
        # No resampling needed; class weighting is handled within classifiers
        return X, y
    else:
        logger.error(f"Unknown balancing strategy: {strategy}")
        raise ValueError(f"Unknown balancing strategy: {strategy}")

# -------------------------------
# Model Training and Evaluation Functions
# -------------------------------

def train_plotrange(
    comb: pd.DataFrame,
    name: str,
    cross_validateq: bool,
    direction: str,
    features: str,
    typee: str = "intra",
    imbalance_strategy: str = "class_weight",
    hyperparameter_tuning: bool = True
):
    """
    Trains classifiers and evaluates their performance using multi-output classification.

    Parameters:
    - comb (pd.DataFrame): Combined DataFrame with features and labels.
    - name (str): Experiment name used for exporting results.
    - cross_validateq (bool): Whether to perform cross-validation.
    - direction (str): Direction of flows ('A', 'B', or 'both').
    - features (str): Feature selection type.
    - typee (str): Type of label encoding ('intra' or 'inter').
    - imbalance_strategy (str): Strategy for handling imbalanced data ('smote', 'undersample', 'class_weight').
    - hyperparameter_tuning (bool): Whether to perform hyperparameter tuning.
    """
    y, X = input_label(comb)

    # Debugging: Print unique labels and their counts
    unique_apps, app_counts = np.unique(y["application"], return_counts=True)
    unique_devices, device_counts = np.unique(y["device"], return_counts=True)
    app_label_counts = dict(zip(unique_apps, app_counts))
    device_label_counts = dict(zip(unique_devices, device_counts))
    logger.info(f"Application Labels: {unique_apps}")
    logger.info(f"Application Label Counts: {app_label_counts}")
    logger.info(f"Device Labels: {unique_devices}")
    logger.info(f"Device Label Counts: {device_label_counts}\n")

    # Check if multiple classes are present
    if len(unique_apps) < 2 or len(unique_devices) < 2:
        logger.error("Less than two classes present in the label vectors. Classification requires at least two classes for each label.")
        sys.exit(1)

    # Debugging: Print shapes of X and y
    logger.info(f"Shape of X: {X.shape}")
    logger.info(f"Shape of y: {y.shape}\n")

    if X.empty or y.empty:
        logger.error("Feature matrix X or label vector y is empty.")
        sys.exit(1)

    # Feature Scaling
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    logger.info("Feature scaling applied.\n")

    # Encode multi-output labels
    encoder_app = LabelEncoder()
    encoder_dev = LabelEncoder()
    y_app = encoder_app.fit_transform(y["application"])
    y_dev = encoder_dev.fit_transform(y["device"])
    y_encoded = np.vstack((y_app, y_dev)).T  # Shape: (n_samples, 2)

    # Save the scaler
    joblib.dump(scaler, models_dir / f"{name}_scaler.joblib")
    logger.info(f"Scaler saved to {models_dir / f'{name}_scaler.joblib'}")

    # Save the encoders
    np.save(models_dir / f"{name}_encoder_app_classes.npy", encoder_app.classes_)
    np.save(models_dir / f"{name}_encoder_dev_classes.npy", encoder_dev.classes_)
    logger.info(f"Label encoders' classes saved to {models_dir}")

    # Handle imbalanced data
    X_res, y_res = handle_imbalance(X_scaled, y_encoded, strategy=imbalance_strategy)

    logger.info(f"After imbalance handling, X_res shape: {X_res.shape}, y_res shape: {y_res.shape}")

    # Initialize MultiOutputClassifier
    classifiers = {clf_name: MultiOutputClassifier(clf) for clf_name, clf in cdic.items()}

    # Initialize containers for results
    results = {}

    # Iterate over classifiers
    for clf_name, clf in classifiers.items():
        logger.info(f"Processing classifier: {clf_name}")

        # Define the model filename
        model_filename = models_dir / f"{name}_{clf_name}.joblib"

        # Check if the model already exists
        if model_filename.exists():
            # Load the existing model
            clf_best = joblib.load(model_filename)
            logger.info(f"Loaded existing model for {clf_name} from {model_filename}")
        else:
            # Model does not exist; proceed to train
            logger.info(f"No existing model found for {clf_name}. Training a new model.")

            if imbalance_strategy == "class_weight":
                # Apply class weighting if the base estimator supports it
                base_estimator = clf.estimator
                if hasattr(base_estimator, 'class_weight'):
                    base_estimator.class_weight = 'balanced'
                    logger.info(f"Applied class_weight='balanced' to {clf_name}")

            if hyperparameter_tuning:
                logger.info(f"Starting hyperparameter tuning for {clf_name}")
                # Define parameter grid for hyperparameter tuning
                param_grid = {}
                if clf_name == "DecisionTree":
                    param_grid = {
                        'estimator__max_depth': [None, 10, 20, 30],
                        'estimator__min_samples_split': [2, 5, 10]
                    }
                elif clf_name == "RandomForest":
                    param_grid = {
                        'estimator__n_estimators': [100, 200],
                        'estimator__max_depth': [None, 10, 20],
                        'estimator__min_samples_split': [2, 5]
                    }
                elif clf_name == "GradientBoosting":
                    param_grid = {
                        'estimator__n_estimators': [100, 200],
                        'estimator__learning_rate': [0.01, 0.1],
                        'estimator__max_depth': [3, 5]
                    }
                elif clf_name == "LogisticRegression":
                    param_grid = {
                        'estimator__C': [0.1, 1, 10],
                        'estimator__penalty': ['l2']
                    }
                elif clf_name == "NaiveBayes":
                    # GaussianNB has limited hyperparameters
                    param_grid = {}
                elif clf_name == "SVM":
                    param_grid = {
                        'estimator__C': [0.1, 1, 10],
                        'estimator__gamma': ['scale', 'auto'],
                        'estimator__kernel': ['rbf', 'linear']
                    }

                if param_grid:
                    grid_search = GridSearchCV(
                        estimator=clf,
                        param_grid=param_grid,
                        cv=5,  # Changed from StratifiedKFold to KFold by setting cv to integer
                        scoring=multioutput_scorer,  # Use custom scorer
                        n_jobs=-1,
                        verbose=1
                    )
                    grid_search.fit(X_res, y_res)
                    clf_best = grid_search.best_estimator_
                    logger.info(f"Best parameters for {clf_name}: {grid_search.best_params_}")
                else:
                    clf_best = clf
                    clf_best.fit(X_res, y_res)
                    logger.info(f"No hyperparameters to tune for {clf_name}. Model trained with default parameters.")

            else:
                clf_best = clf
                clf_best.fit(X_res, y_res)
                logger.info(f"Model trained without hyperparameter tuning for {clf_name}.")

            # Save the trained model
            joblib.dump(clf_best, model_filename)
            logger.info(f"Trained model saved to {model_filename}")

        # Proceed with evaluation whether the model was loaded or newly trained
        if not cross_validateq:
            # Single train-test split with stratification on combined labels
            X_train, X_test, y_train, y_test = train_test_split(
                X_res, y_res, test_size=0.4, random_state=42, stratify=y_res
            )
            clf_best.fit(X_train, y_train)
            y_predic = clf_best.predict(X_test)

            # Metrics for Application
            acc_app = accuracy_score(y_test[:, 0], y_predic[:, 0])
            prec_app = precision_score(y_test[:, 0], y_predic[:, 0], average='macro', zero_division=0)
            recall_app = recall_score(y_test[:, 0], y_predic[:, 0], average='macro', zero_division=0)
            f1_app = f1_score(y_test[:, 0], y_predic[:, 0], average='macro', zero_division=0)

            # Metrics for Device
            acc_dev = accuracy_score(y_test[:, 1], y_predic[:, 1])
            prec_dev = precision_score(y_test[:, 1], y_predic[:, 1], average='macro', zero_division=0)
            recall_dev = recall_score(y_test[:, 1], y_predic[:, 1], average='macro', zero_division=0)
            f1_dev = f1_score(y_test[:, 1], y_predic[:, 1], average='macro', zero_division=0)

            # Store metrics
            results[clf_name] = {
                "Application": {
                    "Accuracy": acc_app,
                    "Precision": prec_app,
                    "Recall": recall_app,
                    "F1 Score": f1_app
                },
                "Device": {
                    "Accuracy": acc_dev,
                    "Precision": prec_dev,
                    "Recall": recall_dev,
                    "F1 Score": f1_dev
                }
            }

            # Generate classification reports
            report_app = classification_report(y_test[:, 0], y_predic[:, 0], target_names=apps_fullname)
            report_dev = classification_report(y_test[:, 1], y_predic[:, 1], target_names=devices_fullname)

            # Save classification reports
            with open(csvs / f"{name}_report_{clf_name}_application.txt", "w") as f:
                f.write(f"Classification Report for Application - {clf_name}\n")
                f.write(report_app)
            with open(csvs / f"{name}_report_{clf_name}_device.txt", "w") as f:
                f.write(f"Classification Report for Device - {clf_name}\n")
                f.write(report_dev)

            logger.info(f"Classification reports for {clf_name} saved.\n")

            # Generate confusion matrices
            cm_app = confusion_matrix(y_test[:, 0], y_predic[:, 0], labels=range(len(apps_fullname)))
            cm_dev = confusion_matrix(y_test[:, 1], y_predic[:, 1], labels=range(len(devices_fullname)))

            export_cm(cm_app, apps_fullname, plots_root / f"{name}_cm_{clf_name}_application.png", "Confusion Matrix - Application")
            export_cm(cm_dev, devices_fullname, plots_root / f"{name}_cm_{clf_name}_device.png", "Confusion Matrix - Device")

            # Feature Importance Analysis
            analyze_feature_importance(clf_best, X.columns, name, clf_name)

        else:
            # 10-fold cross-validation using StratifiedKFold on combined labels
            combined_label = y_res[:, 0] * len(devices_fullname) + y_res[:, 1]
            cv = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)
            scoring = ['accuracy', 'precision_macro', 'recall_macro', 'f1_macro']

            scores_app = {'accuracy': [], 'precision': [], 'recall': [], 'f1': []}
            scores_dev = {'accuracy': [], 'precision': [], 'recall': [], 'f1': []}

            logger.info(f"Starting cross-validation for {clf_name}...")
            for fold, (train_idx, test_idx) in enumerate(cv.split(X_res, combined_label), 1):
                logger.info(f"Fold {fold}/10")
                X_train, X_test = X_res[train_idx], X_res[test_idx]
                y_train, y_test = y_res[train_idx], y_res[test_idx]
                clf_best.fit(X_train, y_train)
                y_pred = clf_best.predict(X_test)

                # Metrics for Application
                scores_app['accuracy'].append(accuracy_score(y_test[:, 0], y_pred[:, 0]))
                scores_app['precision'].append(precision_score(y_test[:, 0], y_pred[:, 0], average='macro', zero_division=0))
                scores_app['recall'].append(recall_score(y_test[:, 0], y_pred[:, 0], average='macro', zero_division=0))
                scores_app['f1'].append(f1_score(y_test[:, 0], y_pred[:, 0], average='macro', zero_division=0))

                # Metrics for Device
                scores_dev['accuracy'].append(accuracy_score(y_test[:, 1], y_pred[:, 1]))
                scores_dev['precision'].append(precision_score(y_test[:, 1], y_pred[:, 1], average='macro', zero_division=0))
                scores_dev['recall'].append(recall_score(y_test[:, 1], y_pred[:, 1], average='macro', zero_division=0))
                scores_dev['f1'].append(f1_score(y_test[:, 1], y_pred[:, 1], average='macro', zero_division=0))

            # Store average and range of metrics
            results[clf_name] = {
                "Application": {
                    "Accuracy": f"{np.min(scores_app['accuracy']):.3f}-{np.max(scores_app['accuracy']):.3f}",
                    "Precision": f"{np.min(scores_app['precision']):.3f}-{np.max(scores_app['precision']):.3f}",
                    "Recall": f"{np.min(scores_app['recall']):.3f}-{np.max(scores_app['recall']):.3f}",
                    "F1 Score": f"{np.min(scores_app['f1']):.3f}-{np.max(scores_app['f1']):.3f}"
                },
                "Device": {
                    "Accuracy": f"{np.min(scores_dev['accuracy']):.3f}-{np.max(scores_dev['accuracy']):.3f}",
                    "Precision": f"{np.min(scores_dev['precision']):.3f}-{np.max(scores_dev['precision']):.3f}",
                    "Recall": f"{np.min(scores_dev['recall']):.3f}-{np.max(scores_dev['recall']):.3f}",
                    "F1 Score": f"{np.min(scores_dev['f1']):.3f}-{np.max(scores_dev['f1']):.3f}"
                }
            }

            # Export fold scores
            df_scores_app = pd.DataFrame(scores_app)
            df_scores_dev = pd.DataFrame(scores_dev)
            export_df(df_scores_app, csvs / f"{name}_fold_{clf_name}_application.csv")
            export_df(df_scores_dev, csvs / f"{name}_fold_{clf_name}_device.csv")
            logger.info(f"Cross-validation scores for {clf_name} exported.\n")

            # Fit on the entire dataset for confusion matrix and feature importance
            clf_best.fit(X_res, y_res)
            y_predic = clf_best.predict(X_res)

            # Generate confusion matrices
            cm_app = confusion_matrix(y_res[:, 0], y_predic[:, 0], labels=range(len(apps_fullname)))
            cm_dev = confusion_matrix(y_res[:, 1], y_predic[:, 1], labels=range(len(devices_fullname)))

            export_cm(cm_app, apps_fullname, plots_root / f"{name}_cm_{clf_name}_application.png", "Confusion Matrix - Application")
            export_cm(cm_dev, devices_fullname, plots_root / f"{name}_cm_{clf_name}_device.png", "Confusion Matrix - Device")

            # Feature Importance Analysis
            analyze_feature_importance(clf_best, X.columns, name, clf_name)

def analyze_feature_importance(clf, feature_names, name, clf_name):
    """
    Analyzes and exports feature importances for the given classifier.

    Parameters:
    - clf: Trained classifier.
    - feature_names (list): List of feature names.
    - name (str): Experiment name.
    - clf_name (str): Classifier name.
    """
    try:
        base_estimator = clf.estimator  # Correctly access the base estimator
        if hasattr(base_estimator, 'feature_importances_'):
            # For tree-based classifiers
            importances = base_estimator.feature_importances_
            fi_df = pd.DataFrame({
                "Feature": feature_names,
                "Importance": importances
            })
            fi_df = fi_df.sort_values(by="Importance", ascending=False)
            export_feature_importance(fi_df, plots_root / f"{name}_feature_importance_{clf_name}.png", f"Feature Importance - {clf_name}")
        elif hasattr(base_estimator, 'coef_'):
            # For linear models
            importances = np.abs(base_estimator.coef_).mean(axis=0)
            fi_df = pd.DataFrame({
                "Feature": feature_names,
                "Importance": importances
            })
            fi_df = fi_df.sort_values(by="Importance", ascending=False)
            export_feature_importance(fi_df, plots_root / f"{name}_feature_importance_{clf_name}.png", f"Feature Importance - {clf_name}")
        else:
            # For models without feature_importances_ or coef_
            logger.warning(f"Feature importance not available for classifier: {clf_name}")
    except Exception as e:
        logger.error(f"Error during feature importance analysis for {clf_name}: {e}")

# -------------------------------
# Process and EDA Functions
# -------------------------------

def process(
    name: str,
    direction: str,
    features: str,
    cdic_dict: dict = cdic,
    cross_validateq: bool = False,
    imbalance_strategy: str = "class_weight",
    hyperparameter_tuning: bool = True
):
    """
    Processes data, performs feature selection, conducts EDA, and trains/evaluates classifiers.

    Parameters:
    - name (str): Experiment name.
    - direction (str): Direction of flows ('A', 'B', or 'both').
    - features (str): Feature selection type.
    - cdic_dict (dict): Dictionary of classifiers.
    - cross_validateq (bool): Whether to perform cross-validation.
    - imbalance_strategy (str): Strategy for handling imbalanced data ('smote', 'undersample', 'class_weight').
    - hyperparameter_tuning (bool): Whether to perform hyperparameter tuning.
    """
    arr = []
    for flow_dir in flow_dirs:
        device_id = flow_dirs.index(flow_dir) + 1  # Assign numerical device IDs (1, 2, 3)
        for app, fullname in zip(apps, apps_fullname):
            try:
                filepath = tran_name(app, flow_dir)
                df = pd.read_csv(filepath, delimiter=r'\s+', index_col=False)
                # Automatically read the number of flows (lines) from the txt file
                num_flows = len(df)
                sampled_df = df  # Use all flows; no sampling
                sampled_df["application"] = app.lower()

                # -------------------------------
                # Add Device Information
                # -------------------------------
                sampled_df["device"] = devices_fullname[device_id - 1]  # Add 'device' column indicating the device

                arr.append(sampled_df)
                logger.info(f"Processed {num_flows} flows for app: {fullname} from {flow_dir.name}")
            except FileNotFoundError:
                logger.warning(f"File not found for app: {fullname} in {flow_dir.name}, skipping.")
            except Exception as e:
                logger.error(f"Error processing file for app: {fullname} in {flow_dir.name}: {e}")

    if not arr:
        logger.error("No data to process. Exiting.")
        sys.exit(1)

    comb = pd.concat(arr, ignore_index=True)
    comb = choose_features(comb, features, name, typee="intra")
    comb = shuffle(comb, random_state=42)

    # Debugging: Print class distribution
    unique_apps, app_counts = np.unique(comb["application"], return_counts=True)
    unique_devices, device_counts = np.unique(comb["device"], return_counts=True)
    app_label_counts = dict(zip(unique_apps, app_counts))
    device_label_counts = dict(zip(unique_devices, device_counts))
    logger.info(f"Application Class Distribution:\n{app_label_counts}\n")
    logger.info(f"Device Class Distribution:\n{device_label_counts}\n")

    export_df(comb, csvs / f"{name}_{features}_out.csv")
    logger.info(f"Combined DataFrame exported to {csvs / f'{name}_{features}_out.csv'}\n")

    # Perform EDA
    perform_eda(comb, name)

    # Train and evaluate models
    train_plotrange(
        comb=comb,
        name=name,
        cross_validateq=cross_validateq,
        direction=direction,
        features=features,
        typee="intra",
        imbalance_strategy=imbalance_strategy,
        hyperparameter_tuning=hyperparameter_tuning
    )

# -------------------------------
# Main Execution Block
# -------------------------------

def main():
    """
    Main function to execute the script based on command-line arguments.
    """
    if len(sys.argv) != 3:
        logger.error("Incorrect usage. Please follow the usage instructions below.")
        print(__doc__)
        sys.exit(1)

    name = sys.argv[1]
    function = sys.argv[2].lower()
    feature_options = ["mutual_info", "all", "categorical", "statistical", "custom_statistical", "anova_f_test"]

    if function == "process":
        for feature in feature_options:
            logger.info(f"\nProcessing with feature type: {feature}")
            process(
                name=name,
                direction="both",
                features=feature,
                cross_validateq=True,
                imbalance_strategy="class_weight",
                hyperparameter_tuning=True
            )
    elif function == "count":
        try:
            # Assuming 'count' function requires combined data
            # Update the filename based on the feature selection used during 'process'
            combined_csv = csvs / f"{name}_mutual_info_features_out.csv"
            if not combined_csv.exists():
                logger.error("Combined CSV not found. Please run the 'process' function first.")
                sys.exit(1)
            comb = pd.read_csv(combined_csv)
            build_count_table(comb, name)
        except FileNotFoundError:
            logger.error("Combined CSV not found. Please run the 'process' function first.")
    elif function == "eda":
        try:
            # Assuming 'eda' function requires combined data
            combined_csv = csvs / f"{name}_mutual_info_out.csv"
            if not combined_csv.exists():
                logger.error("Combined CSV not found. Please run the 'process' function first.")
                sys.exit(1)
            comb = pd.read_csv(combined_csv)
            perform_eda(comb, name)
        except FileNotFoundError:
            logger.error("Combined CSV not found. Please run the 'process' function first.")
    elif function == "train_model":
        logger.info("Function 'train_model' is reserved for future implementations.")
        # Placeholder for model training and saving functionalities
    else:
        logger.error(f"Unknown function: {function}. Available functions: process, count, eda, train_model")
        sys.exit(1)

if __name__ == "__main__":
    main()
