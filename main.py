# https://www.cuemath.com/algebra/linear-programming/
# https://mlabonne.github.io/blog/linearoptimization/
import math

from ortools.linear_solver import pywraplp

# Create a solver using the GLOP backend
solver = pywraplp.Solver('Optimise Feed Digestible Protein', pywraplp.Solver.GLOP_LINEAR_PROGRAMMING)


class Ingredient:
    name: str
    shona_name: str
    calcium: float
    salt: float
    methionine: float
    digestible_crude_protein: float
    solver_num_var: pywraplp.Solver.NumVar

    def __init__(self, name, shona_name, calcium, salt, methionine, digestible_crude_protein, min_weight, max_weight):
        self.name = name
        self.shona_name = shona_name
        self.calcium = calcium
        self.salt = salt
        self.methionine = methionine
        self.digestible_crude_protein = digestible_crude_protein

        self.solver_num_var = solver.NumVar(min_weight, max_weight, f"{name} - {shona_name}")

    @property
    def weight(self):
        # Solver must be solved before this is called
        if self.name == 'Salt':
            return self.solver_num_var.solution_value()
        return round(self.solver_num_var.solution_value())

    # create properties for weights of calcium methionine and digestible crude protein
    @property
    def calcium_weight(self):
        return self.calcium * self.weight

    @property
    def methionine_weight(self):
        return self.methionine * self.weight

    @property
    def salt_weight(self):
        return self.salt * self.weight

    @property
    def digestible_crude_protein_weight(self):
        return self.digestible_crude_protein * self.weight

    @property
    def result(self):
        if self.name == 'Salt':
            return f"{i} : {i.solver_num_var.solution_value():.2f} kg"
        return f"{i} : {round(i.solver_num_var.solution_value()):.2f} kg"

    def __str__(self):
        return f"{self.name} ({self.shona_name}): [DCP={self.digestible_crude_protein}]"


if __name__ == '__main__':
    feed_required_per_chicken_per_day = 0.150  # kg (150g)
    target_percentage_calcium_required_per_chicken_per_day = 0.04  # 5g a day (5g/150g) 4 % in feed weight

    # Read your feedbag label. Most chickens need between 0.12% to 0.2% sodium in the diet.
    # If measured as NaCl or “salt,” it should be 0.4-0.6%.
    # https://extension.umaine.edu/livestock/poultry/nutrition-for-chickens/
    # 0.4 % in feed weight is the recommended allowance, however we are using 0.3% to er on the side of caution
    target_percentage_salt_required_per_chicken_per_day = 0.003  

    target_percentage_methionine_required_per_chicken_per_day = 0.6  # 0.0009kg per 150g ->  0.60 %. in feed weight
    target_percentage_digestible_crude_protein = 0.20  # 20%
    total_feed_weight = 20  # kg

    other_count = 4
    available_weight = 0.5*total_feed_weight
    average_weight = available_weight / other_count
    upper_limit = 1.5 * average_weight
    lower_limit = 0.5 * average_weight

    base_ingredient = Ingredient(
        name="Pearl Millet", shona_name="Mapfunde", calcium=0.05 / 100, methionine=0.28 / 100,
        digestible_crude_protein=12 / 100, min_weight=0.4 * total_feed_weight, max_weight=0.5 * total_feed_weight,
        salt=0
    )

    calcium_grit = Ingredient(
        name="Limestone Grit (Calcium)", shona_name="", calcium=1, methionine=0, digestible_crude_protein=0,
        min_weight=0, max_weight=solver.infinity(), salt=0
    )
    salt = Ingredient(
        name="Salt", shona_name="Munyu", calcium=0, methionine=0, digestible_crude_protein=0, salt=1,
        min_weight=0, max_weight=solver.infinity()
    )

    ingredients = [
        calcium_grit,
        salt,
        base_ingredient,

        Ingredient(
            name="Maize", shona_name="Chibage", calcium=0.04/100, methionine=0.0, digestible_crude_protein=7.5/100,
            salt=0, min_weight=lower_limit, max_weight=upper_limit
        ),
        Ingredient(
            name="Soybean", shona_name="Soya", calcium=0.25/100, methionine=0.6/100, digestible_crude_protein=44/100,
            salt=0, min_weight = lower_limit, max_weight=upper_limit
    ),
        Ingredient(
            name="Sorghum", shona_name="Mhunga", calcium=0.04/100, methionine=0.09/100, digestible_crude_protein=11/100,
            salt=0, min_weight=lower_limit, max_weight=upper_limit
        ),
        Ingredient(
            name="Sunflower Seeds", shona_name="Ruva re Zuva", calcium=0.3/100, methionine=0.6/100,
            salt=0, digestible_crude_protein=34/100, min_weight=lower_limit, max_weight=upper_limit
        )
    ]

    #  add a constraint to the solver that the sum of the ingredients must be equal to the total weight
    solver.Add(sum(i.solver_num_var for i in ingredients) >= total_feed_weight)

    # The target weight of calcium must be greater than our target
    solver.Add(sum(i.calcium * i.solver_num_var for i in ingredients)
               == target_percentage_calcium_required_per_chicken_per_day * total_feed_weight)

    # the target weight of salt must be greater than our target
    solver.Add(sum(i.salt * i.solver_num_var for i in ingredients)
               == target_percentage_salt_required_per_chicken_per_day * total_feed_weight)

    # The target weight of protein must be greater than our target
    solver.Add(sum(i.digestible_crude_protein * i.solver_num_var for i in ingredients)
               >= target_percentage_digestible_crude_protein * total_feed_weight)
    """
    Set the objective function to minimize the weight of protein
    (with a constraint that our total protein weight must be greater than our target)
    """

    objective = solver.Minimize(sum(i.digestible_crude_protein * i.solver_num_var for i in ingredients))

    status = solver.Solve()
    print(f"Status: {status}")
    # If an optimal solution has been found, print results
    if status == pywraplp.Solver.OPTIMAL:
        print('================= Solution =================')
        print(f'Solved in {solver.wall_time():.2f} milliseconds in {solver.iterations()} iterations')
        print()
        print(f'Optimal Protein % = {solver.Objective().Value()/total_feed_weight} 💪')

        print('Feed Weights:')
        for i in ingredients:
            print(i.result)

        print()
        print("Total Feed Weight", sum(i.weight for i in ingredients))
        # total calcium weight
        print("Total Calcium Weight", sum(i.calcium * i.solver_num_var.solution_value() for i in ingredients))

        # total methionine converted to a percentage
        print("Total Methionine Percentage",
              f"{sum(i.methionine * i.solver_num_var.solution_value() for i in ingredients)/total_feed_weight * 100:.2f}"
              , "target", target_percentage_methionine_required_per_chicken_per_day)

    else:
        print('The solver could not find an optimal solution.')
