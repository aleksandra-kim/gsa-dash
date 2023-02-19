import bw2data as bd
import bw2io as bi
from gsa_dash.application import app


project = f"Uncertainties Chaerhan"
bd.projects.set_current(project)

# Import biosphere
bi.bw2setup()

# Import ecoinvent 3.8
ei_path = "TODO give path to /ecoinvent_38_cutoff/datasets"
ei_name = "ecoinvent 3.8 cutoff"
if ei_name in bd.databases:
    print("ecoinvent database already exists")
else:
    ei = bi.SingleOutputEcospold2Importer(ei_path, ei_name)
    ei.apply_strategies()
    assert ei.all_linked
    ei.write_database()

# Import foreground water database
if "Water_38" in bd.databases:
    print("Water_38 database already exists")
else:
    # 1. Specify filepath to your foreground inventories.
    water_path = "data/Water_database_38.xlsx"
    # 2. Create an instance of a class that contains basic methods for importing a database from an excel file.
    water = bi.ExcelImporter(water_path)
    # 3. `apply_strategies` is one of such basic methods, it makes sure units, locations, etc are in correct format.
    water.apply_strategies()
    # 4. Next step is to link your foreground exchanges to existing databases by matching relevant exchanges fields.
    water.match_database("biosphere3", fields=("name", "unit", "categories"))
    water.match_database("ecoinvent 3.8 cutoff", fields=("name", "location", "unit"))
    water.metadata.pop(None)  # Remove metadata None entry.
    # 5. If everything is linked, write database so that it is saved in your project.
    if water.all_linked:
        water.write_database()

# Import foreground lithium database
if "Chaerhan_38" in bd.databases:
    print("Chaerhan_38 database already exists")
else:
    lithium_path = "data/Chaerhan_database_38.xlsx"
    lithium = bi.ExcelImporter(lithium_path)
    lithium.apply_strategies()
    lithium.match_database("biosphere3", fields=("name", "unit", "categories"))
    lithium.match_database("ecoinvent 3.8 cutoff", fields=("name", "location", "unit"))
    # We also need to link Lithium database to the Water database
    lithium.match_database("Water_38", fields=("name", "location", "unit"))
    lithium.metadata.pop(None)
    if lithium.all_linked:
        lithium.write_database()
