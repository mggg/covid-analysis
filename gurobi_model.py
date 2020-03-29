"""Gurobi version of the university-hospital assignment model.

This model differs from the simpler CVXPY-based model in the following ways:
    * All flows are integer-valued.
    * We introduce a decision matrix with sparsity constraints to ensure
      that each hospital can only send to a specified number of universities,
      and each university can only send to a specified number of hospitals.

This model requires a Gurobi license. Academic licenses are available for
free.
"""
from typing import Dict
import numpy as np
import gurobipy as gp
from gurobipy import GRB

def run_gurobi_model(distances: np.ndarray,
                     dorm_bed_capacity: np.ndarray,
                     staff_bed_demand: np.ndarray,
                     patient_bed_demand: np.ndarray,
                     relative_transport_cost: float,
                     min_ed_inst_beds: int = 0,
                     max_ed_inst_per_hosp: int = 1,
                     max_hosp_per_ed_inst: int = 2,
                     hosp_systems: np.ndarray = None,
                     verbose: bool = True,
                     *args, **kwargs) -> Dict:
    """Runs the Gurobi-based model for university-hospital assignment.

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
        Capacities will be rounded and converted to integers.
    :param staff_bed_demand: The staff bed demand from each hospital.
        Demands will be rounded and converted to integers.
    :param patient_bed_demand: The patient bed demand from each hospital.
        Demands will be rounded and converted to integers.
    :param relative_transport_cost: The relative cost per distance unit
        of moving a patient compared to moving a staff member.
    :param min_ed_inst_beds: The minimum number of beds assigned to a
         university **if it is used**.
    :param max_ed_inst_per_hosp: The maximum number of universities assigned
        to each hospital.
    :param max_ed_inst_per_hosp: The maximum number of hospitals assigned
        to each universtity.
    :param hosp_systems: Coded hospital systems.
    :param verbose: Determines whether to print solver output.
    :return: A dictionary of assignment matrices.
    """
    n_hosp, n_ed = distances.shape
    assert dorm_bed_capacity.size == n_ed
    assert staff_bed_demand.size == n_hosp
    assert patient_bed_demand.size == n_hosp

    dorm_bed_capacity = np.round(dorm_bed_capacity).astype(int)
    staff_bed_demand = np.round(staff_bed_demand).astype(int)
    patient_bed_demand = np.round(patient_bed_demand).astype(int)

    m = gp.Model('beds')
    m.modelSense = GRB.MINIMIZE
    m.setParam('OutputFlag', verbose)

    # Variables
    # Difference from CVXPY: Gurobi variables are implicitly non-negative.
    staff_assignment = m.addVars(n_hosp,
                                 n_ed,
                                 name='staff_assignment',
                                 vtype=GRB.INTEGER,
                                 obj=distances)
    patient_assignment = m.addVars(n_hosp,
                                   n_ed,
                                   name='patient_assignment',
                                   vtype=GRB.INTEGER,
                                   obj=relative_transport_cost * distances)
    open_beds = m.addVars(n_hosp,
                          n_ed,
                          vtype=GRB.BINARY,
                          name='open_beds')

    # Constraints: flow.
    for i in range(n_hosp):
        # Constraints: hospital bed demand must be satisfied.
        m.addConstr(sum(open_beds[i, j] * staff_assignment[i, j] for j in range(n_ed)) == staff_bed_demand[i])
        m.addConstr(sum(open_beds[i, j] * patient_assignment[i, j] for j in range(n_ed)) == patient_bed_demand[i])
    for j in range(n_ed):
            # Constraints: dorm beds cannot be overutilized.
            m.addConstr(sum(open_beds[i, j] * (staff_assignment[i, j] + patient_assignment[i, j])
                            for i in range(n_hosp)) <= dorm_bed_capacity[j])
            # Constraints: dorm beds cannot be underutilized.
            m.addConstr(sum(staff_assignment[i, j] + patient_assignment[i, j]
                            for i in range(n_hosp)) >= min_ed_inst_beds)

    # Constraints: sparsity.
    for i in range(n_hosp):
        m.addConstr(sum(open_beds[i, j] for j in range(n_ed)) == max_ed_inst_per_hosp)
    for j in range(n_ed):
        m.addConstr(sum(open_beds[i, j] for i in range(n_hosp)) <= max_hosp_per_ed_inst)
        
    if hosp_systems is not None:
        for outer in range(n_hosp):
            for inner in range(outer + 1, n_hosp):
                if hosp_systems[inner] != hosp_systems[outer]:
                    for i in range(n_ed):
                        m.addConstr(open_beds[outer, i] + open_beds[inner, i] <= 1)

    m.optimize()

    # Load matrix of results
    staff_results = np.zeros((n_hosp, n_ed), dtype=int)
    patient_results = np.zeros((n_hosp, n_ed), dtype=int)
    open_results = np.zeros((n_hosp, n_ed), dtype=int)
    for i in range(n_hosp):
        for j in range(n_ed):
            staff_results[i, j] = staff_assignment[i, j].X
            patient_results[i, j] = patient_assignment[i, j].X
            open_results[i, j] = open_beds[i, j].X

    return {
        'staff': np.multiply(open_results, staff_results),
        'patient': np.multiply(open_results, patient_results)
    }

