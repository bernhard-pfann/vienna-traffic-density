from typing import Tuple
import os

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from sklearn.model_selection import train_test_split

import params.config as conf


def train_test() -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Load and split data into train and test sets.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]: A tuple containing four objects:
            1. A DataFrame containing the feature matrix for the training set.
            2. A DataFrame containing the feature matrix for the test set.
            3. A Series containing the target variable for the training set.
            4. A Series containing the target variable for the test set.
    """
    X = pd.read_csv(os.path.join(conf.root_output, "csv", "X.csv"))
    y = pd.read_csv(os.path.join(conf.root_output, "csv", "y.csv")).squeeze()

    # Drop areas that are outside of borders of Vienna
    X.drop(columns=conf.outer_areas, errors="ignore", inplace=True)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=5)
    return X_train, X_test, y_train, y_test

def optimizer() -> pd.DataFrame:
    """Optimize the model's coefficients using the training set and return the results.

    Returns:
        pd.DataFrame: A DataFrame containing the optimal coefficients for each feature.
    """
    global iteration, coefs_all

    X_train, X_test, y_train, y_test = train_test()

    # Number of observations in train & test set
    n_train = len(X_train)
    n_test  = len(X_test)
    n_coefs = X_train.shape[1]

    # Initialize coefficients
    coefs_init = np.random.normal(
        loc=conf.coef_mu, 
        scale=conf.coef_sigma, 
        size=n_coefs
    )
    coefs_all = coefs_init.copy()

    # Coefficients shall be bounded
    bounds = [conf.coef_bounds] * n_coefs
    iteration = 0

    # Run optimization
    result = minimize( 
        fun=lambda x: loss_func(x, X_train, y_train, n_train),
        callback=lambda x: callback_func(x, X_train, y_train, n_train),
        x0=coefs_init,
        bounds=bounds
    )
    # Collect optimal coefficients
    coefs = pd.Series(data=result.x, index=X_train.columns, name="coefs")
    coefs_df = pd.DataFrame(data=coefs_all, columns=X_train.columns).T
    coefs_df.index.name = "area"

    rmse_train = result.fun
    rmse_test = loss_func(
        coefs=coefs, 
        X=X_test, 
        y=y_test, 
        n=n_test, 
    )
    print("\n")
    print (f"Train RMSE: {rmse_train:.4f}")
    print (f"Test RMSE: {rmse_test:.4f}")

    return coefs_df

def loss_func(coefs: np.ndarray, X: pd.DataFrame, y: pd.Series, n: int) -> float:
    """Calculate the residual squared error based on a set of coefficients.

    Args:
        coefs (np.ndarray): A numpy array of coefficients.
        X (pd.DataFrame): A pandas DataFrame containing the feature matrix.
        y (pd.Series): A pandas Series
    """
    est  = np.dot(X, coefs)
    err  = np.sum(np.power(est - y, 2))
    rmse = np.sqrt(err/n)
    return rmse

def callback_func(coefs_i: np.ndarray, X: pd.DataFrame, y: pd.Series, n: int) -> None:
    """A function that prints the residual squared error at each iteration.

    Args:
        coefs_i (np.ndarray): A numpy array of coefficients.
        X (pd.DataFrame): A pandas DataFrame containing the feature matrix.
        y (pd.Series): A pandas Series containing the target variable.
        n (int): The number of observations in the dataset.
    """
    global iteration, coefs_all
    
    iteration += 1
    rmse = loss_func(coefs_i, X, y, n)
    coefs_all = np.vstack((coefs_all, coefs_i))
    
    print ("RMSE (iter {}): {:.4f}".format(str(iteration), rmse))
