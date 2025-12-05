import os


def month_to_name(month: str):
    """
    Translate a zero-padded month string to a name
    """
    month = int(month)

    return {
        1: "january",
        2: "february",
        3: "march",
        4: "april",
        5: "may",
        6: "june",
        7: "july",
        8: "august",
        9: "september",
        10: "october",
        11: "november",
        12: "december",
    }[month]


def get_month_and_year_from_iso_month(iso_month: str):
    """
    Get the month and year from an ISO month string

    Args:
        iso_month: The ISO month string (e.g. "2025-01")

    Returns:
        The month and year as a tuple (e.g. ("january", "2025"))
    """
    [year, month] = iso_month.split("-")
    month = month_to_name(month)
    return month, year


def get_data_file_paths(unzip_dir: str, iso_month: str):
    """
    Get the paths to the Practice Level Crosstab files in an extracted zip file for an ISO month

    Args:
        unzip_dir: The directory to search for the files in (e.g. "tmp/2025-01")
        iso_month: The ISO month string (e.g. "2025-01")

    Returns:
        The paths to the Practice Level Crosstab files in an extracted zip file
        (e.g. ["tmp/2025-01/Practice_Level_Crosstab_Midlands_Feb_25.csv", "tmp/2025-01/Practice_Level_Crosstab_North_East_Feb_25.csv"])
    """
    month, year = get_month_and_year_from_iso_month(iso_month)
    abbreviated_month = month[:3].capitalize()  # e.g. 10 becomes Oct
    abbreviated_year = year[2:4]  # e.g. 2025 becomes 25
    search_string = f"{abbreviated_month}_{abbreviated_year}.csv"

    return [
        os.path.join(unzip_dir, f)
        for f in os.listdir(unzip_dir)
        if f.endswith(search_string)
    ]


def get_main_system_from_value(value):
    """
    Get the main GP IT system from a the appointments systems value

    Args:
        value: The value to get the main system from (e.g. "EVERGREENLIFE/TPP")

    Returns:
        The main system (e.g. "MEDICUS")
    """
    systems = value.split("/")
    if len(systems) == 1:
        return systems[0]
    elif systems[0] == "EVERGREENLIFE":
        return systems[1]
    elif systems[1] == "EVERGREENLIFE":
        return systems[0]
    else:
        return systems[0]
