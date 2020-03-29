"""CVXPY version of the university-hospital assignment model.

This model differs from the simpler Gurobi-based model in the following ways:
    * Output flows are rounded to integers, but the optimization problem is
      posed as a pure linear program, not a mixed integer program.
    * We omit the sparsity decision matrix and constraints that ensure
      each hospital can only send to a specified number of universities
      and each university can only send to a specified number of hospitals.
    * Dorm bed underutilization is repaired with a greedy algorithm.

However, this model can be run for free without any licensing restrictions,
whereas the Gurobi-based model requires a Gurobi license. Note that academic
Gurobi licenses are free.
"""
from typing import Dict
import numpy as np
import cvxpy as cp

def run_cvxpy_model(distances: np.ndarray,
                    dorm_bed_capacity: np.ndarray,
                    staff_bed_demand: np.ndarray,
                    patient_bed_demand: np.ndarray,
                    relative_transport_cost: float,
                    min_ed_inst_beds: int = 0,
                    verbose: bool = True,
                    *args, **kwargs) -> Dict:
    """Runs the CVXPY-based model for university-hospital assignment.

    The average travel cost between hospitals and universities is minimized,
    subject to the following constraints:
        * All bed demand must be sastisfied.
        * University dorm capacity cannot be overloaded.
        * If a university is used, a minimum threshold of its beds
          must be used.
        * Sparsity must be satisfied--hospitals can only send to a
          specified number of universities, and universities can only
          send to a specified number of hospitals.

    :param distances: The matrix of pairwise distances between hospitals
       and universities. Rows are hospitals; columns are universities.
    :param dorm_bed_capacity: The dorm capacity at each university.
    :param staff_bed_demand: The staff bed demand from each hospital.
    :param patient_bed_demand: The patient bed demand from each hospital.
    :param relative_transport_cost: The relative cost per distance unit
        of moving a patient compared to moving a staff member.
    :param min_ed_inst_beds: The minimum number of beds assigned to a
         university **if it is used**.
    :param verbose: Determines whether to print solver output.
    :return: A dictionary of assignment matrices.
    """
    n_hosp, n_ed = distances.shape
    assert dorm_bed_capacity.size == n_ed
    assert staff_bed_demand.size == n_hosp
    assert patient_bed_demand.size == n_hosp

    # Variables
    staff_assignment = cp.Variable((n_hosp, n_ed))
    patient_assignment = cp.Variable((n_hosp, n_ed))

    constraints = [
        # Constraints: non-negativity.
        staff_assignment >= 0,
        patient_assignment >= 0,

        # Constraints: dorm beds cannot be overutilized.
        cp.sum(staff_assignment, axis=0) + cp.sum(patient_assignment, axis=0) <= dorm_bed_capacity,

        # Constraints: hospital bed demand must be satisfied.
        cp.sum(staff_assignment, axis=1) == staff_bed_demand,
        cp.sum(patient_assignment, axis=1) == patient_bed_demand
    ]

    # Objective: minimize average travel cost.
    objective = cp.Minimize(cp.sum(
        cp.multiply(distances,
                    staff_assignment + (relative_transport_cost * patient_assignment)
    )))

    # Greedily eliminate schools that are underutilized.
    worst_utilization = 0
    worst_utilization_idx = None
    while worst_utilization < min_ed_inst_beds:
        if worst_utilization_idx is not None:
            dorm_bed_capacity[worst_utilization_idx] = 0
            print()

        # TODO: warm start?
        prob = cp.Problem(objective, constraints=constraints)
        try:
            # The ECOS solver is generally faster and better but may fail
            # for large problems.
            prob.solve(solver='ECOS', verbose=verbose)
        except cp.SolverError:
            print('Warning: solving with ECOS failed. Trying OSQP...')
            prob.solve(solver='OSQP', verbose=verbose)

        staff_results = np.round(staff_assignment.value)
        patient_results = np.round(patient_assignment.value)
        staff_by_inst = np.sum(staff_results, axis=0)
        patients_by_inst = np.sum(patient_results, axis=0)
        utilization = staff_by_inst + patients_by_inst
        utilization[utilization == 0] = dorm_bed_capacity.max()
        worst_utilization = np.min(utilization)
        worst_utilization_idx = np.argmin(utilization)

    return {
        'staff': staff_results.astype(int),
        'patient': patient_results.astype(int)
    }
