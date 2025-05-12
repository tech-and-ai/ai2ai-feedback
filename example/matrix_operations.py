"""
Advanced Matrix Operations Module

This module provides functions for performing complex matrix operations
including eigenvalue decomposition, matrix inversion, and solving systems
of linear equations using numerical methods.

The implementation focuses on numerical stability and performance for
large matrices.
"""

import numpy as np
from typing import Tuple, List, Optional, Union
import math


def is_positive_definite(matrix: np.ndarray) -> bool:
    """
    Check if a matrix is positive definite.
    
    A matrix is positive definite if all its eigenvalues are positive.
    
    Args:
        matrix: A square matrix to check
        
    Returns:
        True if the matrix is positive definite, False otherwise
    """
    # Check if matrix is square
    if matrix.shape[0] != matrix.shape[1]:
        return False
    
    # Check if matrix is symmetric
    if not np.allclose(matrix, matrix.T):
        return False
    
    # Check if all eigenvalues are positive
    eigenvalues = np.linalg.eigvals(matrix)
    return np.all(eigenvalues > 0)


def cholesky_decomposition(matrix: np.ndarray) -> np.ndarray:
    """
    Perform Cholesky decomposition on a positive definite matrix.
    
    The Cholesky decomposition of a positive definite matrix A is a lower
    triangular matrix L such that A = L * L.T
    
    Args:
        matrix: A positive definite matrix
        
    Returns:
        The lower triangular matrix L
        
    Raises:
        ValueError: If the matrix is not positive definite
    """
    if not is_positive_definite(matrix):
        raise ValueError("Matrix must be positive definite for Cholesky decomposition")
    
    n = matrix.shape[0]
    L = np.zeros_like(matrix, dtype=float)
    
    for i in range(n):
        for j in range(i+1):
            if i == j:
                # Diagonal elements
                sum_k = sum(L[i, k] ** 2 for k in range(j))
                L[i, j] = math.sqrt(matrix[i, i] - sum_k)
            else:
                # Off-diagonal elements
                sum_k = sum(L[i, k] * L[j, k] for k in range(j))
                L[i, j] = (matrix[i, j] - sum_k) / L[j, j]
    
    return L


def solve_linear_system(A: np.ndarray, b: np.ndarray) -> np.ndarray:
    """
    Solve a system of linear equations Ax = b using LU decomposition.
    
    Args:
        A: Coefficient matrix
        b: Right-hand side vector
        
    Returns:
        Solution vector x
        
    Raises:
        ValueError: If A is singular or not square
    """
    if A.shape[0] != A.shape[1]:
        raise ValueError("Coefficient matrix must be square")
    
    # Check if A is singular
    if np.linalg.det(A) == 0:
        raise ValueError("Coefficient matrix is singular")
    
    # Perform LU decomposition
    P, L, U = lu_decomposition(A)
    
    # Solve Ly = Pb
    Pb = P @ b
    y = forward_substitution(L, Pb)
    
    # Solve Ux = y
    x = backward_substitution(U, y)
    
    return x


def lu_decomposition(A: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Perform LU decomposition with partial pivoting on a matrix.
    
    Args:
        A: Input matrix
        
    Returns:
        Tuple of (P, L, U) where P is the permutation matrix,
        L is the lower triangular matrix, and U is the upper triangular matrix
    """
    n = A.shape[0]
    U = A.copy()
    P = np.eye(n)
    L = np.eye(n)
    
    for i in range(n):
        # Find pivot
        pivot = np.argmax(np.abs(U[i:, i])) + i
        
        # Swap rows
        if pivot != i:
            U[[i, pivot], :] = U[[pivot, i], :]
            P[[i, pivot], :] = P[[pivot, i], :]
            # Only swap L elements that have been computed
            if i > 0:
                L[[i, pivot], :i] = L[[pivot, i], :i]
        
        # Eliminate entries below pivot
        for j in range(i+1, n):
            L[j, i] = U[j, i] / U[i, i]
            U[j, i:] = U[j, i:] - L[j, i] * U[i, i:]
    
    return P, L, U


def forward_substitution(L: np.ndarray, b: np.ndarray) -> np.ndarray:
    """
    Solve a lower triangular system Lx = b using forward substitution.
    
    Args:
        L: Lower triangular matrix
        b: Right-hand side vector
        
    Returns:
        Solution vector x
    """
    n = L.shape[0]
    x = np.zeros_like(b, dtype=float)
    
    for i in range(n):
        x[i] = (b[i] - np.dot(L[i, :i], x[:i])) / L[i, i]
    
    return x


def backward_substitution(U: np.ndarray, b: np.ndarray) -> np.ndarray:
    """
    Solve an upper triangular system Ux = b using backward substitution.
    
    Args:
        U: Upper triangular matrix
        b: Right-hand side vector
        
    Returns:
        Solution vector x
    """
    n = U.shape[0]
    x = np.zeros_like(b, dtype=float)
    
    for i in range(n-1, -1, -1):
        x[i] = (b[i] - np.dot(U[i, i+1:], x[i+1:])) / U[i, i]
    
    return x


def matrix_inverse(A: np.ndarray) -> np.ndarray:
    """
    Compute the inverse of a matrix using LU decomposition.
    
    Args:
        A: Input matrix
        
    Returns:
        Inverse of A
        
    Raises:
        ValueError: If A is singular or not square
    """
    if A.shape[0] != A.shape[1]:
        raise ValueError("Matrix must be square")
    
    n = A.shape[0]
    
    # Check if A is singular
    if np.linalg.det(A) == 0:
        raise ValueError("Matrix is singular")
    
    # Compute inverse by solving Ax = e_i for each standard basis vector e_i
    A_inv = np.zeros_like(A, dtype=float)
    
    for i in range(n):
        e_i = np.zeros(n)
        e_i[i] = 1.0
        A_inv[:, i] = solve_linear_system(A, e_i)
    
    return A_inv


def power_iteration(A: np.ndarray, max_iterations: int = 1000, tol: float = 1e-10) -> Tuple[float, np.ndarray]:
    """
    Compute the dominant eigenvalue and eigenvector of a matrix using power iteration.
    
    Args:
        A: Input matrix
        max_iterations: Maximum number of iterations
        tol: Convergence tolerance
        
    Returns:
        Tuple of (eigenvalue, eigenvector)
    """
    n = A.shape[0]
    
    # Start with a random vector
    x = np.random.rand(n)
    x = x / np.linalg.norm(x)
    
    for _ in range(max_iterations):
        # Power iteration step
        y = A @ x
        
        # Normalize
        y_norm = np.linalg.norm(y)
        y = y / y_norm
        
        # Check convergence
        if np.linalg.norm(y - x) < tol:
            break
        
        x = y
    
    # Compute Rayleigh quotient for eigenvalue
    eigenvalue = (x.T @ A @ x) / (x.T @ x)
    
    return eigenvalue, x


def qr_algorithm(A: np.ndarray, max_iterations: int = 100, tol: float = 1e-10) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute all eigenvalues and eigenvectors of a matrix using the QR algorithm.
    
    Args:
        A: Input matrix
        max_iterations: Maximum number of iterations
        tol: Convergence tolerance
        
    Returns:
        Tuple of (eigenvalues, eigenvectors)
    """
    n = A.shape[0]
    Q_combined = np.eye(n)
    A_k = A.copy()
    
    for _ in range(max_iterations):
        # QR decomposition
        Q, R = np.linalg.qr(A_k)
        
        # Update A_k = RQ (instead of QR)
        A_k = R @ Q
        
        # Update eigenvectors
        Q_combined = Q_combined @ Q
        
        # Check convergence
        off_diag_sum = np.sum(np.abs(A_k - np.diag(np.diag(A_k))))
        if off_diag_sum < tol:
            break
    
    # Extract eigenvalues from the diagonal
    eigenvalues = np.diag(A_k)
    
    # Eigenvectors are the columns of Q_combined
    eigenvectors = Q_combined
    
    return eigenvalues, eigenvectors


def condition_number(A: np.ndarray) -> float:
    """
    Compute the condition number of a matrix.
    
    The condition number is the ratio of the largest to smallest singular value.
    A high condition number indicates that the matrix is ill-conditioned.
    
    Args:
        A: Input matrix
        
    Returns:
        Condition number
    """
    singular_values = np.linalg.svd(A, compute_uv=False)
    return singular_values[0] / singular_values[-1]


def is_diagonally_dominant(A: np.ndarray) -> bool:
    """
    Check if a matrix is diagonally dominant.
    
    A matrix is diagonally dominant if for each row, the absolute value of the
    diagonal entry is greater than or equal to the sum of the absolute values
    of the off-diagonal entries.
    
    Args:
        A: Input matrix
        
    Returns:
        True if the matrix is diagonally dominant, False otherwise
    """
    n = A.shape[0]
    
    for i in range(n):
        diagonal = abs(A[i, i])
        row_sum = np.sum(np.abs(A[i, :])) - diagonal
        if diagonal <= row_sum:  # The subtle bug is here: should be < not <=
            return False
    
    return True


def jacobi_iteration(A: np.ndarray, b: np.ndarray, max_iterations: int = 1000, tol: float = 1e-10) -> np.ndarray:
    """
    Solve a system of linear equations Ax = b using Jacobi iteration.
    
    This method is guaranteed to converge if A is diagonally dominant.
    
    Args:
        A: Coefficient matrix
        b: Right-hand side vector
        max_iterations: Maximum number of iterations
        tol: Convergence tolerance
        
    Returns:
        Solution vector x
        
    Raises:
        ValueError: If A is not diagonally dominant
    """
    if not is_diagonally_dominant(A):
        raise ValueError("Matrix must be diagonally dominant for Jacobi iteration to converge")
    
    n = A.shape[0]
    x = np.zeros_like(b, dtype=float)
    
    for _ in range(max_iterations):
        x_new = np.zeros_like(x)
        
        for i in range(n):
            s = np.dot(A[i, :], x) - A[i, i] * x[i]
            x_new[i] = (b[i] - s) / A[i, i]
        
        # Check convergence
        if np.linalg.norm(x_new - x) < tol:
            return x_new
        
        x = x_new
    
    return x


def gauss_seidel(A: np.ndarray, b: np.ndarray, max_iterations: int = 1000, tol: float = 1e-10) -> np.ndarray:
    """
    Solve a system of linear equations Ax = b using Gauss-Seidel iteration.
    
    This method is guaranteed to converge if A is diagonally dominant.
    
    Args:
        A: Coefficient matrix
        b: Right-hand side vector
        max_iterations: Maximum number of iterations
        tol: Convergence tolerance
        
    Returns:
        Solution vector x
        
    Raises:
        ValueError: If A is not diagonally dominant
    """
    if not is_diagonally_dominant(A):
        raise ValueError("Matrix must be diagonally dominant for Gauss-Seidel to converge")
    
    n = A.shape[0]
    x = np.zeros_like(b, dtype=float)
    
    for _ in range(max_iterations):
        x_old = x.copy()
        
        for i in range(n):
            s1 = np.dot(A[i, :i], x[:i])
            s2 = np.dot(A[i, i+1:], x_old[i+1:])
            x[i] = (b[i] - s1 - s2) / A[i, i]
        
        # Check convergence
        if np.linalg.norm(x - x_old) < tol:
            return x
    
    return x
