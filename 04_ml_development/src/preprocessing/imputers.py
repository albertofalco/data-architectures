"""Imputer factories."""

# ==================== IMPORTS ====================

from __future__ import annotations


# ==================== HELPER FUNCTIONS ====================

def numeric_imputer():
    """Return a numeric imputer that replaces missing values with the median."""
    from sklearn.impute import SimpleImputer

    return SimpleImputer(strategy="median")


def categorical_imputer():
    """Return a categorical imputer that uses the most frequent value."""
    from sklearn.impute import SimpleImputer

    return SimpleImputer(strategy="most_frequent")
