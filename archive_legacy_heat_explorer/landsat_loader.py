"""Future Landsat Collection 2 Level-2 surface-temperature integration contract.

Expected conversion: kelvin = DN * 0.00341802 + 149.0; celsius = kelvin - 273.15.
Implementation must record provenance/acquisition date and apply fill, QA/cloud,
missing-observation and spatial-resolution handling before exposing measurements.
"""
def load_landsat_surface_temperature(*args, **kwargs):
    raise NotImplementedError("No Landsat data has been downloaded or processed in this prototype.")
