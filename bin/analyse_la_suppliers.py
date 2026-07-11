import csv
from collections import defaultdict

##
# Writes a CSV file to tmp/la_supplier_counts.csv with the number of GP practices
# using each GPIT supplier in each upper-tier Local Authority
##


def analyse_la_suppliers():
    la_to_supplier_counts = defaultdict(lambda: defaultdict(int))
    suppliers = []

    with open("data/gp_suppliers.csv", "r") as file:
        reader = csv.reader(file)
        for index, row in enumerate(reader):
            if index == 0:
                continue

            district = row[5]
            county = row[6]

            la_code = district if county == "E99999999" else county
            if la_code.strip() == "":
                continue

            supplier = row[8]
            if supplier not in suppliers:
                suppliers.append(supplier)

            la_to_supplier_counts[la_code][supplier] += 1

    return la_to_supplier_counts, suppliers


def write_la_supplier_counts(la_to_supplier_counts: dict, suppliers: list[str]):
    with open("tmp/la_supplier_counts.csv", "w") as file:
        writer = csv.writer(file)
        writer.writerow(["LA", *suppliers])
        for la, supplier_counts in la_to_supplier_counts.items():
            row = [la]
            for supplier in suppliers:
                row.append(supplier_counts.get(supplier, 0))
            writer.writerow(row)


if __name__ == "__main__":
    la_to_supplier_counts, suppliers = analyse_la_suppliers()
    write_la_supplier_counts(la_to_supplier_counts, suppliers)
