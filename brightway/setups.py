import bw2data as bd
import bw2calc as bc

option = "Chaerhan"
li_name = f"{option}_38"

project = f"Uncertainties {option}"
bd.projects.set_current(project)

# 1. Let's choose product for LCA
lithium = bd.Database(li_name)
demand_act = [act for act in lithium if "Rotary dryer" in act['name']][0]
functional_unit = {demand_act: 1}  # functional unit

# 2. And impact assessment method
method = ('IPCC 2013', 'climate change', 'GWP 100a')

# 3. Create `lca` object that contains necessary methods for LCI and LCIA
lca = bc.LCA(functional_unit, method)

# 4. Solve life cycle inventory problem
lca.lci()

# 5. Compute LCIA score
lca.lcia()

# 6. Returns the score, i.e. the sum of the characterized inventory
deterministic_score = lca.score

print(deterministic_score)
