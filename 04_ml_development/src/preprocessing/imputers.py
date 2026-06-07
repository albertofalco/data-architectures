"""Imputer factories."""

from __future__ import annotations


def numeric_imputer():
    """Return the standard numeric imputer."""
    from sklearn.impute import SimpleImputer

    return SimpleImputer(strategy="median")


def categorical_imputer():
    """Return the standard categorical imputer."""
    from sklearn.impute import SimpleImputer

    return SimpleImputer(strategy="most_frequent")
