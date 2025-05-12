"""
Test cases for the matrix_operations module.

This file contains test cases to verify the correctness of the
matrix operations implemented in the matrix_operations module.
"""

import numpy as np
import unittest
from matrix_operations import (
    is_positive_definite,
    cholesky_decomposition,
    solve_linear_system,
    lu_decomposition,
    forward_substitution,
    backward_substitution,
    matrix_inverse,
    power_iteration,
    qr_algorithm,
    condition_number,
    is_diagonally_dominant,
    jacobi_iteration,
    gauss_seidel
)


class TestMatrixOperations(unittest.TestCase):
    
    def setUp(self):
        # Create a positive definite matrix
        self.A_pd = np.array([
            [4, 1, 1],
            [1, 3, 2],
            [1, 2, 6]
        ])
        
        # Create a diagonally dominant matrix
        self.A_dd = np.array([
            [5, 2, 1],
            [1, 6, 2],
            [2, 1, 7]
        ])
        
        # Create a matrix that is exactly on the boundary of diagonal dominance
        # This matrix has diagonal entries equal to the sum of off-diagonal entries
        self.A_boundary = np.array([
            [3, 1, 2],
            [2, 4, 2],
            [1, 2, 3]
        ])
        
        # Create a non-diagonally dominant matrix
        self.A_not_dd = np.array([
            [3, 2, 2],
            [1, 4, 4],
            [2, 3, 4]
        ])
        
        # Create a right-hand side vector
        self.b = np.array([6, 9, 10])
        
    def test_is_positive_definite(self):
        self.assertTrue(is_positive_definite(self.A_pd))
        self.assertFalse(is_positive_definite(self.A_not_dd))
        
    def test_cholesky_decomposition(self):
        L = cholesky_decomposition(self.A_pd)
        # Verify A = L * L.T
        reconstructed = L @ L.T
        self.assertTrue(np.allclose(self.A_pd, reconstructed))
        
    def test_lu_decomposition(self):
        P, L, U = lu_decomposition(self.A_pd)
        # Verify A = P.T * L * U
        reconstructed = P.T @ L @ U
        self.assertTrue(np.allclose(self.A_pd, reconstructed))
        
    def test_solve_linear_system(self):
        x = solve_linear_system(self.A_pd, self.b)
        # Verify Ax = b
        b_computed = self.A_pd @ x
        self.assertTrue(np.allclose(self.b, b_computed))
        
    def test_matrix_inverse(self):
        A_inv = matrix_inverse(self.A_pd)
        # Verify A * A_inv = I
        I = self.A_pd @ A_inv
        self.assertTrue(np.allclose(I, np.eye(3)))
        
    def test_power_iteration(self):
        eigenvalue, eigenvector = power_iteration(self.A_pd)
        # Verify Ax = λx
        Ax = self.A_pd @ eigenvector
        lambda_x = eigenvalue * eigenvector
        self.assertTrue(np.allclose(Ax, lambda_x, rtol=1e-5))
        
    def test_qr_algorithm(self):
        eigenvalues, eigenvectors = qr_algorithm(self.A_pd)
        # Verify eigenvectors are orthogonal
        for i in range(3):
            for j in range(i+1, 3):
                dot_product = np.abs(np.dot(eigenvectors[:, i], eigenvectors[:, j]))
                self.assertLess(dot_product, 1e-10)
        
    def test_condition_number(self):
        cond = condition_number(self.A_pd)
        # Verify condition number is positive
        self.assertGreater(cond, 0)
        
    def test_is_diagonally_dominant(self):
        self.assertTrue(is_diagonally_dominant(self.A_dd))
        self.assertFalse(is_diagonally_dominant(self.A_not_dd))
        
        # This test should pass but will fail due to the bug
        # The bug is in the is_diagonally_dominant function where it uses <= instead of <
        # A matrix is diagonally dominant if diagonal > sum of off-diagonals
        # But the code checks diagonal <= sum of off-diagonals, which is incorrect
        self.assertTrue(is_diagonally_dominant(self.A_boundary))
        
    def test_jacobi_iteration(self):
        try:
            x = jacobi_iteration(self.A_dd, self.b)
            # Verify Ax = b
            b_computed = self.A_dd @ x
            self.assertTrue(np.allclose(self.b, b_computed, rtol=1e-5))
        except ValueError as e:
            self.fail(f"Jacobi iteration failed: {e}")
            
    def test_gauss_seidel(self):
        try:
            x = gauss_seidel(self.A_dd, self.b)
            # Verify Ax = b
            b_computed = self.A_dd @ x
            self.assertTrue(np.allclose(self.b, b_computed, rtol=1e-5))
        except ValueError as e:
            self.fail(f"Gauss-Seidel failed: {e}")
            
    def test_boundary_case(self):
        # This test will fail due to the bug in is_diagonally_dominant
        # The boundary case matrix should be considered diagonally dominant
        # according to some definitions, but the current implementation rejects it
        try:
            x = jacobi_iteration(self.A_boundary, self.b)
            b_computed = self.A_boundary @ x
            self.assertTrue(np.allclose(self.b, b_computed, rtol=1e-5))
        except ValueError as e:
            self.fail(f"Jacobi iteration failed on boundary case: {e}")


if __name__ == "__main__":
    unittest.main()
