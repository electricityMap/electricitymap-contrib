from typing import Dict, List

ENTSOE_ENDPOINT = "https://transparency.entsoe.eu/api"
ENTSOE_PARAMETER_DESC = {
    "B01": "Biomass",
    "B02": "Fossil Brown coal/Lignite",
    "B03": "Fossil Coal-derived gas",
    "B04": "Fossil Gas",
    "B05": "Fossil Hard coal",
    "B06": "Fossil Oil",
    "B07": "Fossil Oil shale",
    "B08": "Fossil Peat",
    "B09": "Geothermal",
    "B10": "Hydro Pumped Storage",
    "B11": "Hydro Run-of-river and poundage",
    "B12": "Hydro Water Reservoir",
    "B13": "Marine",
    "B14": "Nuclear",
    "B15": "Other renewable",
    "B16": "Solar",
    "B17": "Waste",
    "B18": "Wind Offshore",
    "B19": "Wind Onshore",
    "B20": "Other",
}
ENTSOE_PARAMETER_BY_DESC = {v: k for k, v in ENTSOE_PARAMETER_DESC.items()}
ENTSOE_PARAMETER_GROUPS = {
    "production": {
        "biomass": ["B01", "B17"],
        "coal": ["B02", "B05", "B07", "B08"],
        "gas": ["B03", "B04"],
        "geothermal": ["B09"],
        "hydro": ["B11", "B12"],
        "nuclear": ["B14"],
        "oil": ["B06"],
        "solar": ["B16"],
        "wind": ["B18", "B19"],
        "unknown": ["B20", "B13", "B15"],
    },
    "storage": {"hydro storage": ["B10"]},
}
ENTSOE_PARAMETER_BY_GROUP = {
    v: k for k, g in ENTSOE_PARAMETER_GROUPS.items() for v in g
}
# Define all ENTSOE zone_key <-> domain mapping
# see https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html
ENTSOE_DOMAIN_MAPPINGS: Dict[str, str] = {
    "AL": "10YAL-KESH-----5",
    "AT": "10YAT-APG------L",
    "AZ": "10Y1001A1001B05V",
    "BA": "10YBA-JPCC-----D",
    "BE": "10YBE----------2",
    "BG": "10YCA-BULGARIA-R",
    "BY": "10Y1001A1001A51S",
    "CH": "10YCH-SWISSGRIDZ",
    "CZ": "10YCZ-CEPS-----N",
    "DE": "10Y1001A1001A83F",
    "DE-LU": "10Y1001A1001A82H",
    "DK-DK1": "10YDK-1--------W",
    "DK-DK2": "10YDK-2--------M",
    "EE": "10Y1001A1001A39I",
    "ES": "10YES-REE------0",
    "FI": "10YFI-1--------U",
    "FR": "10YFR-RTE------C",
    "GB": "10YGB----------A",
    "GB-NIR": "10Y1001A1001A016",
    "GE": "10Y1001A1001B012",
    "GR": "10YGR-HTSO-----Y",
    "HR": "10YHR-HEP------M",
    "HU": "10YHU-MAVIR----U",
    "IE": "10YIE-1001A00010",
    "IE(SEM)": "10Y1001A1001A59C",
    "IT": "10YIT-GRTN-----B",
    "IT-BR": "10Y1001A1001A699",
    "IT-CA": "10Y1001C--00096J",
    "IT-CNO": "10Y1001A1001A70O",
    "IT-CSO": "10Y1001A1001A71M",
    "IT-FO": "10Y1001A1001A72K",
    "IT-NO": "10Y1001A1001A73I",
    "IT-PR": "10Y1001A1001A76C",
    "IT-SAR": "10Y1001A1001A74G",
    "IT-SIC": "10Y1001A1001A75E",
    "IT-SO": "10Y1001A1001A788",
    "LT": "10YLT-1001A0008Q",
    "LU": "10YLU-CEGEDEL-NQ",
    "LV": "10YLV-1001A00074",
    # 'MD': 'MD',
    "ME": "10YCS-CG-TSO---S",
    "MK": "10YMK-MEPSO----8",
    "MT": "10Y1001A1001A93C",
    "NL": "10YNL----------L",
    "NO": "10YNO-0--------C",
    "NO-NO1": "10YNO-1--------2",
    "NO-NO2": "10YNO-2--------T",
    "NO-NO3": "10YNO-3--------J",
    "NO-NO4": "10YNO-4--------9",
    "NO-NO5": "10Y1001A1001A48H",
    "PL": "10YPL-AREA-----S",
    "PT": "10YPT-REN------W",
    "RO": "10YRO-TEL------P",
    "RS": "10YCS-SERBIATSOV",
    "RU": "10Y1001A1001A49F",
    "RU-KGD": "10Y1001A1001A50U",
    "SE": "10YSE-1--------K",
    "SE-SE1": "10Y1001A1001A44P",
    "SE-SE2": "10Y1001A1001A45N",
    "SE-SE3": "10Y1001A1001A46L",
    "SE-SE4": "10Y1001A1001A47J",
    "SI": "10YSI-ELES-----O",
    "SK": "10YSK-SEPS-----K",
    "TR": "10YTR-TEIAS----W",
    "UA": "10YUA-WEPS-----0",
    "XK": "10Y1001C--00100H",
    "DE-ENBW": "10YDE-ENBW-----N",
    "DE-EON": "10YDE-EON------1",
    "DE-RWE": "10YDE-RWENET---I",
    "DE-50HZ": "10YDE-VE-------2",
    "DK": "10Y1001A1001A796",
}

# Generation per unit can only be obtained at EIC (Control Area) level
ENTSOE_EIC_MAPPING: Dict[str, str] = {
    "DK-DK1": "10Y1001A1001A796",
    "DK-DK2": "10Y1001A1001A796",
    "FI": "10YFI-1--------U",
    "PL": "10YPL-AREA-----S",
    "SE": "10YSE-1--------K",
    # TODO: ADD DE
}

# Define zone_keys to an array of zone_keys for aggregated production data
ZONE_KEY_AGGREGATES: Dict[str, List[str]] = {
    "IT-SO": ["IT-CA", "IT-SO"],
    "SE": ["SE-SE1", "SE-SE2", "SE-SE3", "SE-SE4"],
}

# Some exchanges require specific domains
ENTSOE_EXCHANGE_DOMAIN_OVERRIDE: Dict[str, List[str]] = {
    "AT->IT-NO": [ENTSOE_DOMAIN_MAPPINGS["AT"], ENTSOE_DOMAIN_MAPPINGS["IT"]],
    "BY->UA": [ENTSOE_DOMAIN_MAPPINGS["BY"], "10Y1001C--00003F"],
    "DE->DK-DK1": [ENTSOE_DOMAIN_MAPPINGS["DE-LU"], ENTSOE_DOMAIN_MAPPINGS["DK-DK1"]],
    "DE->DK-DK2": [ENTSOE_DOMAIN_MAPPINGS["DE-LU"], ENTSOE_DOMAIN_MAPPINGS["DK-DK2"]],
    "DE->SE-SE4": [ENTSOE_DOMAIN_MAPPINGS["DE-LU"], ENTSOE_DOMAIN_MAPPINGS["SE-SE4"]],
    "DK-DK2->SE": [ENTSOE_DOMAIN_MAPPINGS["DK-DK2"], ENTSOE_DOMAIN_MAPPINGS["SE-SE4"]],
    "DE->NO-NO2": [ENTSOE_DOMAIN_MAPPINGS["DE-LU"], ENTSOE_DOMAIN_MAPPINGS["NO-NO2"]],
    "FR-COR->IT-CNO": ["10Y1001A1001A893", ENTSOE_DOMAIN_MAPPINGS["IT-CNO"]],
    "GE->RU-1": [ENTSOE_DOMAIN_MAPPINGS["GE"], ENTSOE_DOMAIN_MAPPINGS["RU"]],
    "GR->IT-SO": [ENTSOE_DOMAIN_MAPPINGS["GR"], ENTSOE_DOMAIN_MAPPINGS["IT-SO"]],
    "IT-CSO->ME": [ENTSOE_DOMAIN_MAPPINGS["IT"], ENTSOE_DOMAIN_MAPPINGS["ME"]],
    "NO-NO3->SE": [ENTSOE_DOMAIN_MAPPINGS["NO-NO3"], ENTSOE_DOMAIN_MAPPINGS["SE-SE2"]],
    "NO-NO4->SE": [ENTSOE_DOMAIN_MAPPINGS["NO-NO4"], ENTSOE_DOMAIN_MAPPINGS["SE-SE2"]],
    "NO-NO1->SE": [ENTSOE_DOMAIN_MAPPINGS["NO-NO1"], ENTSOE_DOMAIN_MAPPINGS["SE-SE3"]],
    "PL->UA": [ENTSOE_DOMAIN_MAPPINGS["PL"], "10Y1001A1001A869"],
    "IT-SIC->IT-SO": [
        ENTSOE_DOMAIN_MAPPINGS["IT-SIC"],
        ENTSOE_DOMAIN_MAPPINGS["IT-CA"],
    ],
}
# Some zone_keys are part of bidding zone domains for price data
ENTSOE_PRICE_DOMAIN_OVERRIDE: Dict[str, str] = {
    "AX": ENTSOE_DOMAIN_MAPPINGS["SE-SE3"],
    "DK-BHM": ENTSOE_DOMAIN_MAPPINGS["DK-DK2"],
    "DE": ENTSOE_DOMAIN_MAPPINGS["DE-LU"],
    "IE": ENTSOE_DOMAIN_MAPPINGS["IE(SEM)"],
    "LU": ENTSOE_DOMAIN_MAPPINGS["DE-LU"],
}

ENTSOE_UNITS_TO_ZONE: Dict[str, str] = {
    # DK-DK1
    "Anholt": "DK-DK1",
    "Esbjergvaerket 3": "DK-DK1",
    "Fynsvaerket 7": "DK-DK1",
    "Horns Rev A": "DK-DK1",
    "Horns Rev B": "DK-DK1",
    "Nordjyllandsvaerket 3": "DK-DK1",
    "Silkeborgvaerket": "DK-DK1",
    "Skaerbaekvaerket 3": "DK-DK1",
    "Studstrupvaerket 3": "DK-DK1",
    "Studstrupvaerket 4": "DK-DK1",
    # DK-DK2
    "Amagervaerket 3": "DK-DK2",
    "Asnaesvaerket 2": "DK-DK2",
    "Asnaesvaerket 5": "DK-DK2",
    "Avedoerevaerket 1": "DK-DK2",
    "Avedoerevaerket 2": "DK-DK2",
    "Kyndbyvaerket 21": "DK-DK2",
    "Kyndbyvaerket 22": "DK-DK2",
    "Roedsand 1": "DK-DK2",
    "Roedsand 2": "DK-DK2",
    # FI
    "Alholmens B2": "FI",
    "Haapavesi B1": "FI",
    "Kaukaan Voima G10": "FI",
    "Keljonlahti B1": "FI",
    "Loviisa 1 G11": "FI",
    "Loviisa 1 G12": "FI",
    "Loviisa 2 G21": "FI",
    "Loviisa 2 G22": "FI",
    "Olkiluoto 1 B1": "FI",
    "Olkiluoto 2 B2": "FI",
    "Toppila B2": "FI",
    # SE
    "Bastusel G1": "SE",
    "Forsmark block 1 G11": "SE",
    "Forsmark block 1 G12": "SE",
    "Forsmark block 2 G21": "SE",
    "Forsmark block 2 G22": "SE",
    "Forsmark block 3 G31": "SE",
    "Gallejaur G1": "SE",
    "Gallejaur G2": "SE",
    "Gasturbiner Halmstad G12": "SE",
    "HarsprÃ¥nget G1": "SE",
    "HarsprÃ¥nget G2": "SE",
    "HarsprÃ¥nget G4": "SE",
    "HarsprÃ¥nget G5": "SE",
    "KVV Västerås G3": "SE",
    "KVV1 VÃ¤rtaverket": "SE",
    "KVV6 VÃ¤rtaverket ": "SE",
    "KVV8 VÃ¤rtaverket": "SE",
    "Karlshamn G1": "SE",
    "Karlshamn G2": "SE",
    "Karlshamn G3": "SE",
    "Letsi G1": "SE",
    "Letsi G2": "SE",
    "Letsi G3": "SE",
    "Ligga G3": "SE",
    "Messaure G1": "SE",
    "Messaure G2": "SE",
    "Messaure G3": "SE",
    "Oskarshamn G1Ö+G1V": "SE",
    "Oskarshamn G3": "SE",
    "Porjus G11": "SE",
    "Porjus G12": "SE",
    "Porsi G3": "SE",
    "Ringhals block 1 G11": "SE",
    "Ringhals block 1 G12": "SE",
    "Ringhals block 2 G21": "SE",
    "Ringhals block 2 G22": "SE",
    "Ringhals block 3 G31": "SE",
    "Ringhals block 3 G32": "SE",
    "Ringhals block 4 G41": "SE",
    "Ringhals block 4 G42": "SE",
    "Ritsem G1": "SE",
    "Rya KVV": "SE",
    "Seitevare G1": "SE",
    "Stalon G1": "SE",
    "Stenungsund B3": "SE",
    "Stenungsund B4": "SE",
    "Stornorrfors G1": "SE",
    "Stornorrfors G2": "SE",
    "Stornorrfors G3": "SE",
    "Stornorrfors G4": "SE",
    "TrÃ¤ngslet G1": "SE",
    "TrÃ¤ngslet G2": "SE",
    "TrÃ¤ngslet G3": "SE",
    "Uppsala KVV": "SE",
    "Vietas G1": "SE",
    "Vietas G2": "SE",
    "Ã…byverket Ã–rebro": "SE",
}
