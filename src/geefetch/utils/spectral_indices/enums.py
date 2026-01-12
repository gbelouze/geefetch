from enum import Enum

L = 1.0
GAIN = 2.5
C1 = (6.0,)
C2 = (7.5,)
CEXP = (1.16,)
NEXP = (2.0,)
ALPHA = (0.1,)
BETA = (0.05,)
GAMMA = (1.0,)
OMEGA = (2.0,)
K = 0.0
PAR = (None,)
LAMBDAG = (None,)
LAMBDAR = (None,)
LAMBDAN = (None,)
LAMBDAN2 = (None,)
LAMBDAS1 = (None,)
LAMBDAS2 = (None,)
SLA = (1.0,)
SLB = (0.0,)
SIGMA = (0.5,)
P = (2.0,)
C = (1.0,)
FDELTA = (0.581,)
EPSILON = 1


class IndeciesExpressions(Enum):
    BNDVI = {
        "long_name": "Blue Normalized Difference Vegetation Index",
        "formula": "(N - B)/(N + B)",
        "denominator": "(N + B)",
        "reference": "https://doi.org/10.1016/S1672-6308(07)60027-4",
        "application_domain": "vegetation",
        "contributor": "https://github.com/MATRIX4284",
    }
    CIG = {
        "long_name": "Chlorophyll Index Green",
        "formula": "(N / G) - 1.0",
        "denominator": "G",
        "reference": "https://doi.org/10.1078/0176-1617-00887",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    CVI = {
        "long_name": "Chlorophyll Vegetation Index",
        "formula": "(N * R) / (pow(G , 2.0))",
        "denominator": "(pow(G , 2.0))",
        "reference": "https://doi.org/10.1007/s11119-010-9204-3",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    EVI = {
        "long_name": "Enhanced Vegetation Index",
        "formula": f"{GAIN} * (N - R) / (N + {C1} * R - {C2} * B + {L})",
        "denominator": f"(N + {C1} * R - {C2} * B + {L})",
        "reference": "https://doi.org/10.1016/S0034-4257(96)00112-5",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    EVI2 = {
        "long_name": "Two-Band Enhanced Vegetation Index",
        "formula": f"{GAIN} * (N - R) / (N + 2.4 * R + {L})",
        "denominator": f"(N + 2.4 * R + {L})",
        "reference": "https://doi.org/10.1016/j.rse.2008.06.006",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    GARI = {
        "long_name": "Green Atmospherically Resistant Vegetation Index",
        "formula": "(N - (G - (B - R))) / (N - (G + (B - R)))",
        "denominator": "(N - (G + (B - R))",
        "reference": "https://doi.org/10.1016/S0034-4257(96)00072-7",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    GBNDVI = {
        "long_name": "Green-Blue Normalized Difference Vegetation Index",
        "formula": "(N - (G + B))/(N + (G + B))",
        "denominator": "(N + (G + B))",
        "reference": "https://doi.org/10.1016/S1672-6308(07)60027-4",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    GEMI = {
        "long_name": "Global Environment Monitoring Index",
        "formula": """
            ((2.0*((pow(N , 2.0))-(pow(R , 2.0))) + 1.5*N + 0.5*R)/(N + R + 0.5)) *
            (1.0 - 0.25*((2.0 * ((pow(N , 2.0)) -
            (pow(R , 2))) + 1.5 * N + 0.5 * R)/(N + R + 0.5)))-((R - 0.125)/(1 - R))
        """,
        "denominator": "(N + R + 0.5)*(1 - R)",
        "reference": "http://dx.doi.org/10.1007/bf00031911",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    GLI = {
        "long_name": "Green Leaf Index",
        "formula": "(2.0 * G - R - B) / (2.0 * G + R + B)",
        "denominator": "(2.0 * G + R + B)",
        "reference": "http://dx.doi.org/10.1080/10106040108542184",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    GNDVI = {
        "long_name": "Green Normalized Difference Vegetation Index",
        "formula": "(N - G)/(N + G)",
        "denominator": "(N + G)",
        "reference": "https://doi.org/10.1016/S0034-4257(96)00072-7",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    GRNDVI = {
        "long_name": "Green-Red Normalized Difference Vegetation Index",
        "formula": "(N - (G + R))/(N + (G + R))",
        "denominator": "(N + (G + R))",
        "reference": "https://doi.org/10.1016/S1672-6308(07)60027-4",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    GVMI = {
        "long_name": "Global Vegetation Moisture Index",
        "formula": "((N + 0.1) - (S2 + 0.02)) / ((N + 0.1) + (S2 + 0.02))",
        "denominator": "((N + 0.1) + (S2 + 0.02))",
        "reference": "https://doi.org/10.1016/S0034-4257(02)00037-8",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    MNDVI = {
        "long_name": "Modified Normalized Difference Vegetation Index",
        "formula": "(N - S2)/(N + S2)",
        "denominator": "(N + S2)",
        "reference": "https://doi.org/10.1080/014311697216810",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    NDVI = {
        "long_name": "Normalized Difference Vegetation Index",
        "formula": "(N - R)/(N + R)",
        "denominator": "(N + R)",
        "reference": "https://ntrs.nasa.gov/citations/19740022614",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    NGRDI = {
        "long_name": "Normalized Green Red Difference Index",
        "formula": "(G - R) / (G + R)",
        "denominator": "(G + R)",
        "reference": "https://doi.org/10.1016/0034-4257(79)90013-0",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    RVI = {
        "long_name": "Ratio Vegetation Index",
        "formula": "RE2 / R",
        "denominator": "R",
        "reference": "https://doi.org/10.2134/agronj1968.00021962006000060016x",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    SAVI = {
        "long_name": "Soil-Adjusted Vegetation Index",
        "formula": f"(1.0 + {L}) * (N - R) / (N + R + {L})",
        "denominator": f"(N + R + {L})",
        "reference": "https://doi.org/10.1016/0034-4257(88)90106-X",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    VARI = {
        "long_name": "Visible Atmospherically Resistant Index",
        "formula": "(G - R) / (G + R - B)",
        "denominator": "(G + R - B)",
        "reference": "https://doi.org/10.1016/S0034-4257(01)00289-9",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    BAI = {
        "long_name": "Burned Area Index",
        "formula": "1.0 / (pow((0.1 - R) , 2.0) + pow((0.06 - N) , 2.0))",
        "denominator": "(pow((0.1 - R), 2.0) + pow((0.06 - N), 2.0))",
        "reference": """
            https://digital.csic.es/bitstream/10261/6426/1/Martin_Isabel_Serie_Geografica.pdf
        """,
        "application_domain": "burn",
        "contributor": "https://github.com/davemlz",
    }
    BAIS2 = {
        "long_name": "Burned Area Index for Sentinel 2",
        "formula": """
            (1.0 - (pow((RE2 * RE3 * N2) / R) , 0.5)) * (((S2 - N2)/pow((S2 + N2) , 0.5)) + 1.0)
        """,
        "denominator": "R * pow((S2 + N2), 0.5)",
        "reference": "https://doi.org/10.3390/ecrs-2-05177",
        "application_domain": "burn",
        "contributor": "https://github.com/davemlz",
    }
    NBR = {
        "long_name": "Normalized Burn Ratio",
        "formula": "(N - S2) / (N + S2)",
        "denominator": "(N + S2)",
        "reference": "https://doi.org/10.3133/ofr0211",
        "application_domain": "burn",
        "contributor": "https://github.com/davemlz",
    }
    MNDWI = {
        "long_name": "Modified Normalized Difference Water Index",
        "formula": "(G - S1) / (G + S1)",
        "denominator": "(G + S1)",
        "reference": "https://doi.org/10.1080/01431160600589179",
        "application_domain": "water",
        "contributor": "https://github.com/davemlz",
    }
    NDWI = {
        "long_name": "Normalized Difference Water Index",
        "formula": "(G - N) / (G + N)",
        "denominator": "(G + N)",
        "reference": "https://doi.org/10.1080/01431169608948714",
        "application_domain": "water",
        "contributor": "https://github.com/davemlz",
    }
    NDSI = {
        "long_name": "Normalized Difference Snow Index",
        "formula": "(G - S1) / (G + S1)",
        "denominator": "(G + S1)",
        "reference": "https://doi.org/10.1109/IGARSS.1994.399618",
        "application_domain": "snow",
        "contributor": "https://github.com/davemlz",
    }
    NDDI = {
        "long_name": "Normalized Difference Drought Index",
        "formula": """
            (((N - R)/(N + R)) - ((G - N)/(G + N)))/(((N - R)/(N + R)) + ((G - N)/(G + N)))
        """,
        "denominator": "((N + R) * (G + N) * (((N - R)/(N + R)) + ((G - N)/(G + N))))",
        "reference": "https://doi.org/10.1029/2006GL029127",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    SeLI = {
        "long_name": "Sentinel-2 LAI Green Index",
        "formula": "(N2 - RE1) / (N2 + RE1)",
        "denominator": "(N2 + RE1)",
        "reference": "https://doi.org/10.3390/s19040904",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    OSAVI = {
        "long_name": "Optimized Soil-Adjusted Vegetation Index",
        "formula": "(N - R) / (N + R + 0.16)",
        "denominator": "(N + R + 0.16)",
        "reference": "https://doi.org/10.1016/0034-4257(95)00186-7",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    ARVI = {
        "long_name": "Atmospherically Resistant Vegetation Index",
        "formula": f"(N - (R - {GAMMA} * (R - B))) / (N + (R - {GAMMA} * (R - B)))",
        "denominator": f"(N + (R - {GAMMA} * (R - B)))",
        "reference": "https://doi.org/10.1109/36.134076",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    SARVI = {
        "long_name": "Soil Adjusted and Atmospherically Resistant Vegetation Index",
        "formula": f"(1 + {L})*(N - (R - (R - B))) / (N + (R - (R - B)) + {L})",
        "denominator": f"(N + (R - (R - B)) + {L})",
        "reference": "https://doi.org/10.1109/36.134076",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    NLI = {
        "long_name": "Non-Linear Vegetation Index",
        "formula": "((pow(N , 2)) - R)/((pow(N , 2)) + R)",
        "denominator": "((pow(N, 2)) + R)",
        "reference": "https://doi.org/10.1080/02757259409532252",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    MNLI = {
        "long_name": "Modified Non-Linear Vegetation Index",
        "formula": f"(1 + {L})*((pow(N , 2)) - R)/((pow(N , 2)) + R + {L})",
        "denominator": f"((pow(N, 2)) + R + {L})",
        "reference": "https://doi.org/10.1109/TGRS.2003.812910",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    NMDI = {
        "long_name": "Normalized Multi-band Drought Index",
        "formula": "(N - (S1 - S2))/(N + (S1 - S2))",
        "denominator": "(N + (S1 - S2))",
        "reference": "https://doi.org/10.1029/2007GL031021",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    MSAVI = {
        "long_name": "Modified Soil-Adjusted Vegetation Index",
        "formula": "0.5 * (2.0 * N + 1 - (pow((pow((2 * N + 1) , 2)) - 8 * (N - R)) , 0.5))",
        "denominator": None,
        "reference": "https://doi.org/10.1016/0034-4257(94)90134-1",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    MCARI = {
        "long_name": "Modified Chlorophyll Absorption in Reflectance Index",
        "formula": "((RE1 - R) - 0.2 * (RE1 - G)) * (RE1 / R)",
        "denominator": "R",
        "reference": "http://dx.doi.org/10.1016/S0034-4257(00)00113-9",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    OCVI = {
        "long_name": "Optimized Chlorophyll Vegetation Index",
        "formula": f"(N / G) * pow((R / G) , {CEXP})",
        "denominator": "(G * G)",
        "reference": "http://dx.doi.org/10.1007/s11119-008-9075-z",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    NDREI = {
        "long_name": "Normalized Difference Red Edge Index",
        "formula": "(N - RE1) / (N + RE1)",
        "denominator": "(N + RE1)",
        "reference": "https://doi.org/10.1016/1011-1344(93)06963-4",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    CIRE = {
        "long_name": "Chlorophyll Index Red Edge",
        "formula": "(N / RE1) - 1",
        "denominator": "RE1",
        "reference": "https://doi.org/10.1078/0176-1617-00887",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    MTCI = {
        "long_name": "MERIS Terrestrial Chlorophyll Index",
        "formula": "(RE2 - RE1) / (RE1 - R)",
        "denominator": "(RE1 - R)",
        "reference": "https://doi.org/10.1080/0143116042000274015",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    TCARI = {
        "long_name": "Transformed Chlorophyll Absorption in Reflectance Index",
        "formula": "3 * ((RE1 - R) - 0.2 * (RE1 - G) * (RE1 / R))",
        "denominator": "R",
        "reference": "https://doi.org/10.1016/S0034-4257(02)00018-4",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    GDVI = {
        "long_name": "Generalized Difference Vegetation Index",
        "formula": f"""
            ((pow(N , {NEXP})) - (pow(R , {NEXP}))) / ((pow(N , {NEXP})) + (pow(R , {NEXP})))
        """,
        "denominator": f"((pow(N , {NEXP})) + (pow(R , {NEXP})))",
        "reference": "https://doi.org/10.3390/rs6021211",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    WDRVI = {
        "long_name": "Wide Dynamic Range Vegetation Index",
        "formula": f"({ALPHA} * N - R) / ({ALPHA} * N + R)",
        "denominator": f"({ALPHA} * N + R)",
        "reference": "https://doi.org/10.1078/0176-1617-01176",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    MCARI1 = {
        "long_name": "Modified Chlorophyll Absorption in Reflectance Index 1",
        "formula": "1.2 * (2.5 * (N - R) - 1.3 * (N - G))",
        "denominator": None,
        "reference": "https://doi.org/10.1016/j.rse.2003.12.013",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    MTVI1 = {
        "long_name": "Modified Triangular Vegetation Index 1",
        "formula": "1.2 * (1.2 * (N - G) - 2.5 * (R - G))",
        "denominator": None,
        "reference": "https://doi.org/10.1016/j.rse.2003.12.013",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    MCARI2 = {
        "long_name": "Modified Chlorophyll Absorption in Reflectance Index 2",
        "formula": """
            (1.5 * (2.5 * (N - R) - 1.3 * (N - G))) /
            (((pow((2.0 * N + 1) , 2)) - pow((6.0 * N - 5 * (pow(R , 0.5))) - 0.5) , 0.5))
        """,
        "denominator": """
            ((pow((2.0 * N + 1) , 2)) - pow((6.0 * N - 5 * (pow(R , 0.5))) - 0.5) , 0.5)
        """,
        "reference": "https://doi.org/10.1016/j.rse.2003.12.013",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    MTVI2 = {
        "long_name": "Modified Triangular Vegetation Index 2",
        "formula": """
            (1.5 * (1.2 * (N - G) - 2.5 * (R - G))) /
            (((pow((2.0 * N + 1) , 2)) - pow((6.0 * N - 5 * (pow(R , 0.5))) - 0.5) , 0.5))
        """,
        "denominator": """
            ((pow((2.0 * N + 1) , 2)) - pow((6.0 * N - 5 * (pow(R , 0.5))) - 0.5) , 0.5)
        """,
        "reference": "https://doi.org/10.1016/j.rse.2003.12.013",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    TriVI = {
        "long_name": "Triangular Vegetation Index",
        "formula": "0.5 * (120 * (N - G) - 200 * (R - G))",
        "denominator": None,
        "reference": "http://dx.doi.org/10.1016/S0034-4257(00)00197-8",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    MSR = {
        "long_name": "Modified Simple Ratio",
        "formula": "(N / R - 1) / (pow((N / R + 1) , 0.5))",
        "denominator": "R * pow((N / R + 1) , 0.5)",
        "reference": "https://doi.org/10.1080/07038992.1996.10855178",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    RDVI = {
        "long_name": "Renormalized Difference Vegetation Index",
        "formula": "(N - R) / (pow((N + R) , 0.5))",
        "denominator": "pow((N + R) , 0.5)",
        "reference": "https://doi.org/10.1016/0034-4257(94)00114-3",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    NDBI = {
        "long_name": "Normalized Difference Built-Up Index",
        "formula": "(S1 - N) / (S1 + N)",
        "denominator": "(S1 + N)",
        "reference": "http://dx.doi.org/10.1080/01431160304987",
        "application_domain": "urban",
        "contributor": "https://github.com/davemlz",
    }
    MGRVI = {
        "long_name": "Modified Green Red Vegetation Index",
        "formula": "(pow(G , 2.0) - pow(R , 2.0)) / (pow(G , 2.0) + pow(R , 2.0))",
        "denominator": "(pow(G , 2.0) + pow(R , 2.0))",
        "reference": "https://doi.org/10.1016/j.jag.2015.02.012",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    ExG = {
        "long_name": "Excess Green Index",
        "formula": "2 * G - R - B",
        "denominator": None,
        "reference": "https://doi.org/10.13031/2013.27838",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    DVI = {
        "long_name": "Difference Vegetation Index",
        "formula": "N - R",
        "denominator": None,
        "reference": "https://doi.org/10.1016/0034-4257(94)00114-3",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    WDVI = {
        "long_name": "Weighted Difference Vegetation Index",
        "formula": f"N - {SLA} * R",
        "denominator": None,
        "reference": "https://doi.org/10.1016/0034-4257(89)90076-X",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    TSAVI = {
        "long_name": "Transformed Soil-Adjusted Vegetation Index",
        "formula": f"{SLA} * (N - {SLA} * R - {SLB}) / ({SLA} * N + R - {SLA} * {SLB})",
        "denominator": f"({SLA} * N + R - {SLA} * {SLB})",
        "reference": "https://doi.org/10.1109/IGARSS.1989.576128",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    ATSAVI = {
        "long_name": "Adjusted Transformed Soil-Adjusted Vegetation Index",
        "formula": f"""
            {SLA} * (N - {SLA} * R - {SLB}) /
            ({SLA} * N + R - {SLA} * {SLB} + 0.08 * (1 + pow({SLA} , 2.0)))
        """,
        "denominator": f"({SLA} * N + R - {SLA} * {SLB} + 0.08 * (1 + pow({SLA} , 2.0)))",
        "reference": "https://doi.org/10.1016/0034-4257(91)90009-U",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    SAVI2 = {
        "long_name": "Soil-Adjusted Vegetation Index 2",
        "formula": f"N / (R + ({SLB} / {SLA}))",
        "denominator": f"(R + ({SLB} / {SLA}))",
        "reference": "https://doi.org/10.1080/01431169008955053",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    TCI = {
        "long_name": "Triangular Chlorophyll Index",
        "formula": "1.2 * (RE1 - G) - 1.5 * (R - G) * pow((RE1 / R) , 0.5)",
        "denominator": "R",
        "reference": "http://dx.doi.org/10.1109/TGRS.2007.904836",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    TGI = {
        "long_name": "Triangular Greenness Index",
        "formula": "- 0.5 * (190 * (R - G) - 120 * (R - B))",
        "denominator": None,
        "reference": "http://dx.doi.org/10.1016/j.jag.2012.07.020",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    IRECI = {
        "long_name": "Inverted Red-Edge Chlorophyll Index",
        "formula": "(RE3 - R) / (RE1 / RE2)",
        "denominator": "RE1",
        "reference": "https://doi.org/10.1016/j.isprsjprs.2013.04.007",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    S2REP = {
        "long_name": "Sentinel-2 Red-Edge Position",
        "formula": "705.0 + 35.0 * ((((RE3 + R) / 2.0) - RE1) / (RE2 - RE1))",
        "denominator": "(RE2 - RE1)",
        "reference": "https://doi.org/10.1016/j.isprsjprs.2013.04.007",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    SIPI = {
        "long_name": "Structure Insensitive Pigment Index",
        "formula": "(N - A) / (N - R)",
        "denominator": "(N - R)",
        "reference": "https://eurekamag.com/research/009/395/009395053.php",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    NHFD = {
        "long_name": "Non-Homogeneous Feature Difference",
        "formula": "(RE1 - A) / (RE1 + A)",
        "denominator": "(RE1 + A)",
        "reference": "https://www.semanticscholar.org/paper/Using-WorldView-2-Vis-NIR-MSI-Imagery-to-Support-Wolf/5e5063ccc4ee76b56b721c866e871d47a77f9fb4",  # noqa: E501
        "application_domain": "urban",
        "contributor": "https://github.com/davemlz",
    }
    NDYI = {
        "long_name": "Normalized Difference Yellowness Index",
        "formula": "(G - B) / (G + B)",
        "denominator": "(G + B)",
        "reference": "https://doi.org/10.1016/j.rse.2016.06.016",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    NRFIr = {
        "long_name": "Normalized Rapeseed Flowering Index Red",
        "formula": "(R - S2) / (R + S2)",
        "denominator": "(R + S2)",
        "reference": "https://doi.org/10.3390/rs13010105",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    NRFIg = {
        "long_name": "Normalized Rapeseed Flowering Index Green",
        "formula": "(G - S2) / (G + S2)",
        "denominator": "(G + S2)",
        "reference": "https://doi.org/10.3390/rs13010105",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    TRRVI = {
        "long_name": "Transformed Red Range Vegetation Index",
        "formula": "((RE2 - R) / (RE2 + R)) / (((N - R) / (N + R)) + 1.0)",
        "denominator": "((RE2 + R) * (N + R) * (((N - R) / (N + R)) + 1.0))",
        "reference": "https://doi.org/10.3390/rs12152359",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    TTVI = {
        "long_name": "Transformed Triangular Vegetation Index",
        "formula": "0.5 * ((865.0 - 740.0) * (RE3 - RE2) - (N2 - RE2) * (783.0 - 740))",
        "denominator": None,
        "reference": "https://doi.org/10.3390/rs12010016",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    NDSaII = {
        "long_name": "Normalized Difference Snow and Ice Index",
        "formula": "(R - S1) / (R + S1)",
        "denominator": "(R + S1)",
        "reference": "https://doi.org/10.1080/01431160119766",
        "application_domain": "snow",
        "contributor": "https://github.com/davemlz",
    }
    SWI = {
        "long_name": "Snow Water Index",
        "formula": "(G * (N - S1)) / ((G + N) * (N + S1))",
        "denominator": "((G + N) * (N + S1))",
        "reference": "https://doi.org/10.3390/rs11232774",
        "application_domain": "snow",
        "contributor": "https://github.com/davemlz",
    }
    S3 = {
        "long_name": "S3 Snow Index",
        "formula": "(N * (R - S1)) / ((N + R) * (N + S1))",
        "denominator": "((N + R) * (N + S1))",
        "reference": "https://doi.org/10.3178/jjshwr.12.28",
        "application_domain": "snow",
        "contributor": "https://github.com/davemlz",
    }
    WI1 = {
        "long_name": "Water Index 1",
        "formula": "(G - S2) / (G + S2)",
        "denominator": "(G + S2)",
        "reference": "https://doi.org/10.3390/rs11182186",
        "application_domain": "water",
        "contributor": "https://github.com/davemlz",
    }
    WI2 = {
        "long_name": "Water Index 2",
        "formula": "(B - S2) / (B + S2)",
        "denominator": "(B + S2)",
        "reference": "https://doi.org/10.3390/rs11182186",
        "application_domain": "water",
        "contributor": "https://github.com/davemlz",
    }
    AWEInsh = {
        "long_name": "Automated Water Extraction Index",
        "formula": "4.0 * (G - S1) - 0.25 * N + 2.75 * S2",
        "denominator": None,
        "reference": "https://doi.org/10.1016/j.rse.2013.08.029",
        "application_domain": "water",
        "contributor": "https://github.com/davemlz",
    }
    AWEIsh = {
        "long_name": "Automated Water Extraction Index with Shadows Elimination",
        "formula": "B + 2.5 * G - 1.5 * (N + S1) - 0.25 * S2",
        "denominator": None,
        "reference": "https://doi.org/10.1016/j.rse.2013.08.029",
        "application_domain": "water",
        "contributor": "https://github.com/davemlz",
    }
    NBR2 = {
        "long_name": "Normalized Burn Ratio 2",
        "formula": "(S1 - S2) / (S1 + S2)",
        "denominator": "(S1 + S2)",
        "reference": "https://www.usgs.gov/core-science-systems/nli/landsat/landsat-normalized-burn-ratio-2",  # noqa: E501
        "application_domain": "burn",
        "contributor": "https://github.com/davemlz",
    }
    BWDRVI = {
        "long_name": "Blue Wide Dynamic Range Vegetation Index",
        "formula": f"({ALPHA} * N - B) / ({ALPHA} * N + B)",
        "denominator": f"({ALPHA} * N + B)",
        "reference": "https://doi.org/10.2135/cropsci2007.01.0031",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    ARI = {
        "long_name": "Anthocyanin Reflectance Index",
        "formula": "(1 / G) - (1 / RE1)",
        "denominator": "(G * RE1)",
        "reference": "https://doi.org/10.1562/0031-8655(2001)074%3C0038:OPANEO%3E2.0.CO;2",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    VIG = {
        "long_name": "Vegetation Index Green",
        "formula": "(G - R) / (G + R)",
        "denominator": "(G + R)",
        "reference": "https://doi.org/10.1016/S0034-4257(01)00289-9",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    VI700 = {
        "long_name": "Vegetation Index (700 nm)",
        "formula": "(RE1 - R) / (RE1 + R)",
        "denominator": "(RE1 + R)",
        "reference": "https://doi.org/10.1016/S0034-4257(01)00289-9",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    VARI700 = {
        "long_name": "Visible Atmospherically Resistant Index (700 nm)",
        "formula": "(RE1 - 1.7 * R + 0.7 * B) / (RE1 + 1.3 * R - 1.3 * B)",
        "denominator": "(RE1 + 1.3 * R - 1.3 * B)",
        "reference": "https://doi.org/10.1016/S0034-4257(01)00289-9",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    TCARIOSAVI = {
        "long_name": "TCARI/OSAVI Ratio",
        "formula": """
            (3 * ((RE1 - R) - 0.2 * (RE1 - G) * (RE1 / R))) / (1.16 * (N - R) / (N + R + 0.16))
        """,
        "denominator": "(1.16 * (N - R) / (N + R + 0.16))",
        "reference": "https://doi.org/10.1016/S0034-4257(02)00018-4",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    MCARIOSAVI = {
        "long_name": "MCARI/OSAVI Ratio",
        "formula": """
            (((RE1 - R) - 0.2 * (RE1 - G)) * (RE1 / R)) / (1.16 * (N - R) / (N + R + 0.16))
        """,
        "denominator": "(1.16 * (N - R) / (N + R + 0.16))",
        "reference": "https://doi.org/10.1016/S0034-4257(00)00113-9",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    TCARIOSAVI705 = {
        "long_name": "TCARI/OSAVI Ratio (705 and 750 nm)",
        "formula": """
            (3 * ((RE2 - RE1) - 0.2 * (RE2 - G) * (RE2 / RE1))) /
            (1.16 * (RE2 - RE1) / (RE2 + RE1 + 0.16))
        """,
        "denominator": "(1.16 * (RE2 - RE1) / (RE2 + RE1 + 0.16))",
        "reference": "https://doi.org/10.1016/j.agrformet.2008.03.005",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    MCARIOSAVI705 = {
        "long_name": "MCARI/OSAVI Ratio (705 and 750 nm)",
        "formula": """
            (((RE2 - RE1) - 0.2 * (RE2 - G)) * (RE2 / RE1)) /
            (1.16 * (RE2 - RE1) / (RE2 + RE1 + 0.16))
        """,
        "denominator": "(1.16 * (RE2 - RE1) / (RE2 + RE1 + 0.16))",
        "reference": "https://doi.org/10.1016/j.agrformet.2008.03.005",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    MCARI705 = {
        "long_name": "Modified Chlorophyll Absorption in Reflectance Index (705 and 750 nm)",
        "formula": "((RE2 - RE1) - 0.2 * (RE2 - G)) * (RE2 / RE1)",
        "denominator": "RE1",
        "reference": "https://doi.org/10.1016/j.agrformet.2008.03.005",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    MSR705 = {
        "long_name": "Modified Simple Ratio (705 and 750 nm)",
        "formula": "(RE2 / RE1 - 1) / (pow((RE2 / RE1 + 1) , 0.5))",
        "denominator": "pow((RE2 / RE1 + 1), 0.5)",
        "reference": "https://doi.org/10.1016/j.agrformet.2008.03.005",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    NDVI705 = {
        "long_name": "Normalized Difference Vegetation Index (705 and 750 nm)",
        "formula": "(RE2 - RE1) / (RE2 + RE1)",
        "denominator": "(RE2 + RE1)",
        "reference": "https://doi.org/10.1016/S0176-1617(11)81633-0",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    SR705 = {
        "long_name": "Simple Ratio (705 and 750 nm)",
        "formula": "RE2 / RE1",
        "denominator": "RE1",
        "reference": "https://doi.org/10.1016/S0176-1617(11)81633-0",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    SR555 = {
        "long_name": "Simple Ratio (555 and 750 nm)",
        "formula": "RE2 / G",
        "denominator": "G",
        "reference": "https://doi.org/10.1016/S0176-1617(11)81633-0",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    REDSI = {
        "long_name": "Red-Edge Disease Stress Index",
        "formula": "((705.0 - 665.0) * (RE3 - R) - (783.0 - 665.0) * (RE1 - R)) / (2.0 * R)",
        "denominator": "(2.0 * R)",
        "reference": "https://doi.org/10.3390/s18030868",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    NIRv = {
        "long_name": "Near-Infrared Reflectance of Vegetation",
        "formula": "((N - R) / (N + R)) * N",
        "denominator": "(N + R)",
        "reference": "https://doi.org/10.1126/sciadv.1602244",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    AFRI2100 = {
        "long_name": "Aerosol Free Vegetation Index (2100 nm)",
        "formula": "(N - 0.5 * S2) / (N + 0.5 * S2)",
        "denominator": "(N + 0.5 * S2)",
        "reference": "https://doi.org/10.1016/S0034-4257(01)00190-0",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    AFRI1600 = {
        "long_name": "Aerosol Free Vegetation Index (1600 nm)",
        "formula": "(N - 0.66 * S1) / (N + 0.66 * S1)",
        "denominator": "(N + 0.66 * S1)",
        "reference": "https://doi.org/10.1016/S0034-4257(01)00190-0",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    NIRvP = {
        "long_name": "Near-Infrared Reflectance of Vegetation and Incoming PAR",
        "formula": f"((N - R) / (N + R)) * N * {PAR}",
        "denominator": f"((N + R) * {PAR})",
        "reference": "https://doi.org/10.1016/j.rse.2021.112763",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    NDMI = {
        "long_name": "Normalized Difference Moisture Index",
        "formula": "(N - S1)/(N + S1)",
        "denominator": "(N + S1)",
        "reference": "https://doi.org/10.1016/S0034-4257(01)00318-2",
        "application_domain": "vegetation",
        "contributor": "https://github.com/bpurinton",
    }
    QpRVI = {
        "long_name": "Quad-Polarized Radar Vegetation Index",
        "formula": "(8.0 * HV)/(HH + VV + 2.0 * HV)",
        "denominator": "(HH + VV + 2.0 * HV)",
        "reference": "https://doi.org/10.1109/IGARSS.2001.976856",
        "application_domain": "radar",
        "contributor": "https://github.com/davemlz",
    }
    RFDI = {
        "long_name": "Radar Forest Degradation Index",
        "formula": "(HH - HV)/(HH + HV)",
        "denominator": "(HH + HV)",
        "reference": "https://doi.org/10.5194/bg-9-179-2012",
        "application_domain": "radar",
        "contributor": "https://github.com/davemlz",
    }
    DpRVIHH = {
        "long_name": "Dual-Polarized Radar Vegetation Index HH",
        "formula": "(4.0 * HV)/(HH + HV)",
        "denominator": "(HH + HV)",
        "reference": "https://www.tandfonline.com/doi/abs/10.5589/m12-043",
        "application_domain": "radar",
        "contributor": "https://github.com/davemlz",
    }
    DpRVIVV = {
        "long_name": "Dual-Polarized Radar Vegetation Index VV",
        "formula": "(4.0 * VH)/(VV + VH)",
        "denominator": "(VV + VH)",
        "reference": "https://doi.org/10.3390/app9040655",
        "application_domain": "radar",
        "contributor": "https://github.com/davemlz",
    }
    NWI = {
        "long_name": "New Water Index",
        "formula": "(B - (N + S1 + S2))/(B + (N + S1 + S2))",
        "denominator": "(B + (N + S1 + S2))",
        "reference": "https://doi.org/10.11873/j.issn.1004-0323.2009.2.167",
        "application_domain": "water",
        "contributor": "https://github.com/davemlz",
    }
    WRI = {
        "long_name": "Water Ratio Index",
        "formula": "(G + R)/(N + S1)",
        "denominator": "(N + S1)",
        "reference": "https://doi.org/10.1109/GEOINFORMATICS.2010.5567762",
        "application_domain": "water",
        "contributor": "https://github.com/davemlz",
    }
    NDVIMNDWI = {
        "long_name": "NDVI-MNDWI Model",
        "formula": "((N - R)/(N + R)) - ((G - S1)/(G + S1))",
        "denominator": "((N + R) * (G + S1))",
        "reference": "https://doi.org/10.1007/978-3-662-45737-5_51",
        "application_domain": "water",
        "contributor": "https://github.com/davemlz",
    }
    MBWI = {
        "long_name": "Multi-Band Water Index",
        "formula": f"({OMEGA} * G) - R - N - S1 - S2",
        "denominator": None,
        "reference": "https://doi.org/10.1016/j.jag.2018.01.018",
        "application_domain": "water",
        "contributor": "https://github.com/davemlz",
    }
    GCC = {
        "long_name": "Green Chromatic Coordinate",
        "formula": "G / (R + G + B)",
        "denominator": "(R + G + B)",
        "reference": "https://doi.org/10.1016/0034-4257(87)90088-5",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    RCC = {
        "long_name": "Red Chromatic Coordinate",
        "formula": "R / (R + G + B)",
        "denominator": "(R + G + B)",
        "reference": "https://doi.org/10.1016/0034-4257(87)90088-5",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    BCC = {
        "long_name": "Blue Chromatic Coordinate",
        "formula": "B / (R + G + B)",
        "denominator": "(R + G + B)",
        "reference": "https://doi.org/10.1016/0034-4257(87)90088-5",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    NIRvH2 = {
        "long_name": "Hyperspectral Near-Infrared Reflectance of Vegetation",
        "formula": f"N - R - {K} * ({LAMBDAN} - {LAMBDAR})",
        "denominator": f"({K} * ({LAMBDAN} - {LAMBDAR}) + R)",
        "reference": "https://doi.org/10.1016/j.rse.2021.112723",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    NDPI = {
        "long_name": "Normalized Difference Phenology Index",
        "formula": f"""
            (N - ({ALPHA} * R + (1.0 - {ALPHA}) * S1))/(N + ({ALPHA} * R + (1.0 - {ALPHA}) * S1))
        """,
        "denominator": f"(N + ({ALPHA} * R + (1.0 - {ALPHA}) * S1))",
        "reference": "https://doi.org/10.1016/j.rse.2017.04.031",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    NDII = {
        "long_name": "Normalized Difference Infrared Index",
        "formula": "(N - S1)/(N + S1)",
        "denominator": "(N + S1)",
        "reference": "https://www.asprs.org/wp-content/uploads/pers/1983journal/jan/1983_jan_77-83.pdf",  # noqa: E501
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    DVIplus = {
        "long_name": "Difference Vegetation Index Plus",
        "formula": f"""
            (({LAMBDAN} - {LAMBDAR})/({LAMBDAN} - {LAMBDAG})) *
            G + (1.0 - (({LAMBDAN} - {LAMBDAR})/({LAMBDAN} - {LAMBDAG}))) * N - R
        """,
        "denominator": None,
        "reference": "https://doi.org/10.1016/j.rse.2019.03.028",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    NDGI = {
        "long_name": "Normalized Difference Greenness Index",
        "formula": f"""
            ((({LAMBDAN} - {LAMBDAR})/({LAMBDAN} - {LAMBDAG})) * G +
            (1.0 - (({LAMBDAN} - {LAMBDAR})/({LAMBDAN} - {LAMBDAG}))) * N - R) /
            ((({LAMBDAN} - {LAMBDAR})/({LAMBDAN} - {LAMBDAG})) * G +
            (1.0 - (({LAMBDAN} - {LAMBDAR})/({LAMBDAN} - {LAMBDAG}))) * N + R)
        """,
        "denominator": None,
        "reference": "https://doi.org/10.1016/j.rse.2019.03.028",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    FCVI = {
        "long_name": "Fluorescence Correction Vegetation Index",
        "formula": "N - ((R + G + B)/3.0)",
        "denominator": None,
        "reference": "https://doi.org/10.1016/j.rse.2020.111676",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    UI = {
        "long_name": "Urban Index",
        "formula": "(S2 - N)/(S2 + N)",
        "denominator": "(S2 + N)",
        "reference": "https://www.isprs.org/proceedings/XXXI/congress/part7/321_XXXI-part7.pdf",
        "application_domain": "urban",
        "contributor": "https://github.com/davemlz",
    }
    VrNIRBI = {
        "long_name": "Visible Red-Based Built-Up Index",
        "formula": "(R - N)/(R + N)",
        "denominator": "(R + N)",
        "reference": "https://doi.org/10.1016/j.ecolind.2015.03.037",
        "application_domain": "urban",
        "contributor": "https://github.com/davemlz",
    }
    VgNIRBI = {
        "long_name": "Visible Green-Based Built-Up Index",
        "formula": "(G - N)/(G + N)",
        "denominator": "(G + N)",
        "reference": "https://doi.org/10.1016/j.ecolind.2015.03.037",
        "application_domain": "urban",
        "contributor": "https://github.com/davemlz",
    }
    IBI = {
        "long_name": "Index-Based Built-Up Index",
        "formula": f"""
            (((S1-N)/(S1+N))-(((N-R)*(1.0+{L})/(N+R+{L})) +
            ((G-S1)/(G+S1)))/2.0)/(((S1-N)/(S1+N)) +
            (((N-R)*(1.0+{L})/(N+R+{L}))+((G-S1)/(G+S1)))/2.0)
        """,
        "denominator": f"(((S1-N)/(S1+N)) + (((N-R)*(1.0+{L})/(N+R+{L})) + ((G-S1)/(G+S1)))/2.0)",
        "reference": "https://doi.org/10.1080/01431160802039957",
        "application_domain": "urban",
        "contributor": "https://github.com/davemlz",
    }
    BLFEI = {
        "long_name": "Built-Up Land Features Extraction Index",
        "formula": "(((G+R+S2)/3.0)-S1)/(((G+R+S2)/3.0)+S1)",
        "denominator": "(((G+R+S2)/3.0)+S1)",
        "reference": "https://doi.org/10.1080/10106049.2018.1497094",
        "application_domain": "urban",
        "contributor": "https://github.com/davemlz",
    }
    S2WI = {
        "long_name": "Sentinel-2 Water Index",
        "formula": "(RE1 - S2)/(RE1 + S2)",
        "denominator": "(RE1 + S2)",
        "reference": "https://doi.org/10.3390/w13121647",
        "application_domain": "water",
        "contributor": "https://github.com/MATRIX4284",
    }
    NDWIns = {
        "long_name": "Normalized Difference Water Index with no Snow Cover and Glaciers",
        "formula": f"(G - {ALPHA} * N)/(G + N)",
        "denominator": "(G + N)",
        "reference": "https://doi.org/10.3390/w12051339",
        "application_domain": "water",
        "contributor": "https://github.com/davemlz",
    }
    NDSInw = {
        "long_name": "Normalized Difference Snow Index with no Water",
        "formula": f"(N - S1 - {BETA})/(N + S1)",
        "denominator": "(N + S1)",
        "reference": "https://doi.org/10.3390/w12051339",
        "application_domain": "snow",
        "contributor": "https://github.com/davemlz",
    }
    ExGR = {
        "long_name": "ExG - ExR Vegetation Index",
        "formula": "(2.0 * G - R - B) - (1.3 * R - G)",
        "denominator": None,
        "reference": "https://doi.org/10.1016/j.compag.2008.03.009",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    ExR = {
        "long_name": "Excess Red Index",
        "formula": "1.3 * R - G",
        "denominator": None,
        "reference": "https://doi.org/10.1117/12.336896",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    MRBVI = {
        "long_name": "Modified Red Blue Vegetation Index",
        "formula": "(pow(R , 2.0) - pow(B , 2.0))/(pow(R , 2.0) + pow(B , 2.0))",
        "denominator": "(pow(R , 2.0) + pow(B , 2.0))",
        "reference": "https://doi.org/10.3390/s20185055",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    AVI = {
        "long_name": "Advanced Vegetation Index",
        "formula": "pow((N * (1.0 - R) * (N - R)) , (1/3))",
        "denominator": None,
        "reference": "http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.465.8749&rep=rep1&type=pdf",  # noqa: E501
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    BI = {
        "long_name": "Bare Soil Index",
        "formula": "((S1 + R) - (N + B))/((S1 + R) + (N + B))",
        "denominator": "((S1 + R) + (N + B))",
        "reference": "http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.465.8749&rep=rep1&type=pdf",  # noqa: E501
        "application_domain": "soil",
        "contributor": "https://github.com/davemlz",
    }
    SI = {
        "long_name": "Shadow Index",
        "formula": "pow(((1.0 - B) * (1.0 - G) * (1.0 - R)) , (1/3))",
        "denominator": None,
        "reference": "http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.465.8749&rep=rep1&type=pdf",  # noqa: E501
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    MSI = {
        "long_name": "Moisture Stress Index",
        "formula": "S1/N",
        "denominator": "N",
        "reference": "https://doi.org/10.1016/0034-4257(89)90046-1",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    NDGlaI = {
        "long_name": "Normalized Difference Glacier Index",
        "formula": "(G - R)/(G + R)",
        "denominator": "(G + R)",
        "reference": "https://doi.org/10.1080/01431160802385459",
        "application_domain": "snow",
        "contributor": "https://github.com/davemlz",
    }
    NDSII = {
        "long_name": "Normalized Difference Snow Ice Index",
        "formula": "(G - N)/(G + N)",
        "denominator": "(G + N)",
        "reference": "https://doi.org/10.1080/01431160802385459",
        "application_domain": "snow",
        "contributor": "https://github.com/davemlz",
    }
    IKAW = {
        "long_name": "Kawashima Index",
        "formula": "(R - B)/(R + B)",
        "denominator": "(R + B)",
        "reference": "https://doi.org/10.1006/anbo.1997.0544",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    RGRI = {
        "long_name": "Red-Green Ratio Index",
        "formula": "R/G",
        "denominator": "G",
        "reference": "https://doi.org/10.1016/j.jag.2014.03.018",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    RGBVI = {
        "long_name": "Red Green Blue Vegetation Index",
        "formula": "(pow(G , 2.0) - B * R)/(pow(G , 2.0) + B * R)",
        "denominator": "(pow(G , 2.0) + B * R)",
        "reference": "https://doi.org/10.1016/j.jag.2015.02.012",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    ARI2 = {
        "long_name": "Anthocyanin Reflectance Index 2",
        "formula": "N * ((1 / G) - (1 / RE1))",
        "denominator": "1/G",
        "reference": "https://doi.org/10.1562/0031-8655(2001)074%3C0038:OPANEO%3E2.0.CO;2",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    NormNIR = {
        "long_name": "Normalized NIR",
        "formula": "N/(N + G + R)",
        "denominator": "(N + G + R)",
        "reference": "https://doi.org/10.2134/agronj2004.0314",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    NormR = {
        "long_name": "Normalized Red",
        "formula": "R/(N + G + R)",
        "denominator": "(N + G + R)",
        "reference": "https://doi.org/10.2134/agronj2004.0314",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    NormG = {
        "long_name": "Normalized Green",
        "formula": "G/(N + G + R)",
        "denominator": "(N + G + R)",
        "reference": "https://doi.org/10.2134/agronj2004.0314",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    GRVI = {
        "long_name": "Green Ratio Vegetation Index",
        "formula": "N/G",
        "denominator": "G",
        "reference": "https://doi.org/10.2134/agronj2004.0314",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    GSAVI = {
        "long_name": "Green Soil Adjusted Vegetation Index",
        "formula": f"(1.0 + {L}) * (N - G) / (N + G + {L})",
        "denominator": "(N + G + L)",
        "reference": "https://doi.org/10.2134/agronj2004.0314",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    GOSAVI = {
        "long_name": "Green Optimized Soil Adjusted Vegetation Index",
        "formula": "(N - G) / (N + G + 0.16)",
        "denominator": "(N + G + 0.16)",
        "reference": "https://doi.org/10.2134/agronj2004.0314",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    SR = {
        "long_name": "Simple Ratio",
        "formula": "N/R",
        "denominator": "R",
        "reference": "https://doi.org/10.2307/1936256",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    TVI = {
        "long_name": "Transformed Vegetation Index",
        "formula": "pow((((N - R)/(N + R)) + 0.5) , 0.5)",
        "denominator": "N + R",
        "reference": "https://ntrs.nasa.gov/citations/19740022614",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    GM1 = {
        "long_name": "Gitelson and Merzlyak Index 1",
        "formula": "RE2/G",
        "denominator": "G",
        "reference": "https://doi.org/10.1016/S0176-1617(96)80284-7",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    GM2 = {
        "long_name": "Gitelson and Merzlyak Index 2",
        "formula": "RE2/RE1",
        "denominator": "RE1",
        "reference": "https://doi.org/10.1016/S0176-1617(96)80284-7",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    IAVI = {
        "long_name": "New Atmospherically Resistant Vegetation Index",
        "formula": f"(N - (R - {GAMMA} * (B - R)))/(N + (R - {GAMMA} * (B - R)))",
        "denominator": "(N + (R - GAMMA * (B - R)))",
        "reference": "https://www.jipb.net/EN/abstract/abstract23925.shtml",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    IPVI = {
        "long_name": "Infrared Percentage Vegetation Index",
        "formula": "N/(N + R)",
        "denominator": "(N + R)",
        "reference": "https://doi.org/10.1016/0034-4257(90)90085-Z",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    kIPVI = {
        "long_name": "Kernel Infrared Percentage Vegetation Index",
        "formula": "kNN/(kNN + kNR)",
        "denominator": "(kNN + kNR)",
        "reference": "https://doi.org/10.1126/sciadv.abc7447",
        "application_domain": "kernel",
        "contributor": "https://github.com/davemlz",
    }
    ND705 = {
        "long_name": "Normalized Difference (705 and 750 nm)",
        "formula": "(RE2 - RE1)/(RE2 + RE1)",
        "denominator": "(RE2 + RE1)",
        "reference": "https://doi.org/10.1016/S0034-4257(02)00010-X",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    mSR705 = {
        "long_name": "Modified Simple Ratio (705 and 445 nm)",
        "formula": "(RE2 - A)/(RE2 + A)",
        "denominator": "(RE2 + A)",
        "reference": "https://doi.org/10.1016/S0034-4257(02)00010-X",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    mND705 = {
        "long_name": "Modified Normalized Difference (705, 750 and 445 nm)",
        "formula": "(RE2 - RE1)/(RE2 + RE1 - A)",
        "denominator": "(RE2 + RE1 - A)",
        "reference": "https://doi.org/10.1016/S0034-4257(02)00010-X",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    PSRI = {
        "long_name": "Plant Senescing Reflectance Index",
        "formula": "(R - B)/RE2",
        "denominator": "RE2",
        "reference": "https://doi.org/10.1034/j.1399-3054.1999.106119.x",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    NBSIMS = {
        "long_name": "Non-Binary Snow Index for Multi-Component Surfaces",
        "formula": "0.36 * (G + R + N) - (((B + S2)/G) + S1)",
        "denominator": None,
        "reference": "https://doi.org/10.3390/rs13142777",
        "application_domain": "snow",
        "contributor": "https://github.com/davemlz",
    }
    MuWIR = {
        "long_name": "Revised Multi-Spectral Water Index",
        "formula": """
            -4.0 * ((B - G)/(B + G)) + 2.0 * ((G - N)/(G + N)) +
            2.0 * ((G - S2)/(G + S2)) - ((G - S1)/(G + S1))
        """,
        "denominator": "(B + G) * (G + N) * (G + S2) *(G + S1)",
        "reference": "https://doi.org/10.3390/rs10101643",
        "application_domain": "water",
        "contributor": "https://github.com/davemlz",
    }
    RENDVI = {
        "long_name": "Red Edge Normalized Difference Vegetation Index",
        "formula": "(RE2 - RE1)/(RE2 + RE1)",
        "denominator": "(RE2 + RE1)",
        "reference": "https://doi.org/10.1016/S0176-1617(11)81633-0",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    RI = {
        "long_name": "Redness Index",
        "formula": "(R - G)/(R + G)",
        "denominator": "(R + G)",
        "reference": "https://www.documentation.ird.fr/hor/fdi:34390",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    SR2 = {
        "long_name": "Simple Ratio (800 and 550 nm)",
        "formula": "N/G",
        "denominator": "G",
        "reference": "https://doi.org/10.1080/01431169308904370",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    SR3 = {
        "long_name": "Simple Ratio (860, 550 and 708 nm)",
        "formula": "N2/(G * RE1)",
        "denominator": "(G * RE1)",
        "reference": "https://doi.org/10.1016/S0034-4257(98)00046-7",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    TDVI = {
        "long_name": "Transformed Difference Vegetation Index",
        "formula": "1.5 * ((N - R)/pow(((pow(N , 2.0) + R + 0.5) , 0.5)))",
        "denominator": "pow((pow(N , 2.0) + R + 0.5) , 0.5)",
        "reference": "https://doi.org/10.1109/IGARSS.2002.1026867",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    PISI = {
        "long_name": "Perpendicular Impervious Surface Index",
        "formula": "0.8192 * B - 0.5735 * N + 0.0750",
        "denominator": None,
        "reference": "https://doi.org/10.3390/rs10101521",
        "application_domain": "urban",
        "contributor": "https://github.com/davemlz",
    }
    NSDS = {
        "long_name": "Normalized Shortwave Infrared Difference Soil-Moisture",
        "formula": "(S1 - S2)/(S1 + S2)",
        "denominator": "(S1 + S2)",
        "reference": "https://doi.org/10.3390/land10030231",
        "application_domain": "soil",
        "contributor": "https://github.com/davemlz",
    }
    MBI = {
        "long_name": "Modified Bare Soil Index",
        "formula": "((S1 - S2 - N)/(S1 + S2 + N)) + 0.5",
        "denominator": "(S1 + S2 + N)",
        "reference": "https://doi.org/10.3390/land10030231",
        "application_domain": "soil",
        "contributor": "https://github.com/davemlz",
    }
    EMBI = {
        "long_name": "Enhanced Modified Bare Soil Index",
        "formula": """
            ((((S1 - S2 - N)/(S1 + S2 + N)) + 0.5) -
            ((G - S1)/(G + S1)) - 0.5) /
            ((((S1 - S2 - N)/(S1 + S2 + N)) + 0.5) + ((G - S1)/(G + S1)) + 1.5)
        """,
        "denominator": "(S1 + S2 + N) * (G + S1)",
        "reference": "https://doi.org/10.1016/j.jag.2022.102703",
        "application_domain": "soil",
        "contributor": "https://github.com/davemlz",
    }
    NDSoI = {
        "long_name": "Normalized Difference Soil Index",
        "formula": "(S2 - G)/(S2 + G)",
        "denominator": "(S2 + G)",
        "reference": "https://doi.org/10.1016/j.jag.2015.02.010",
        "application_domain": "soil",
        "contributor": "https://github.com/davemlz",
    }
    BaI = {
        "long_name": "Bareness Index",
        "formula": "R + S1 - N",
        "denominator": None,
        "reference": "https://doi.org/10.1109/IGARSS.2005.1525743",
        "application_domain": "soil",
        "contributor": "https://github.com/davemlz",
    }
    DBSI = {
        "long_name": "Dry Bareness Index",
        "formula": "((S1 - G)/(S1 + G)) - ((N - R)/(N + R))",
        "denominator": "(S1 + G) * (N + R)",
        "reference": "https://doi.org/10.3390/land7030081",
        "application_domain": "soil",
        "contributor": "https://github.com/davemlz",
    }
    CSI = {
        "long_name": "Char Soil Index",
        "formula": "N/S2",
        "denominator": "S2",
        "reference": "https://doi.org/10.1016/j.rse.2005.04.014",
        "application_domain": "burn",
        "contributor": "https://github.com/davemlz",
    }
    MIRBI = {
        "long_name": "Mid-Infrared Burn Index",
        "formula": "10.0 * S2 - 9.8 * S1 + 2.0",
        "denominator": None,
        "reference": "https://doi.org/10.1080/01431160110053185",
        "application_domain": "burn",
        "contributor": "https://github.com/davemlz",
    }
    DPDD = {
        "long_name": "Dual-Pol Diagonal Distance",
        "formula": "(VV + VH)/pow(2.0 , 0.5)",
        "denominator": "pow(2.0 , 0.5)",
        "reference": "https://doi.org/10.1016/j.rse.2018.09.003",
        "application_domain": "radar",
        "contributor": "https://github.com/davemlz",
    }
    VDDPI = {
        "long_name": "Vertical Dual De-Polarization Index",
        "formula": "(VV + VH)/VV",
        "denominator": "VV",
        "reference": "https://doi.org/10.1016/j.rse.2018.09.003",
        "application_domain": "radar",
        "contributor": "https://github.com/davemlz",
    }
    NDPolI = {
        "long_name": "Normalized Difference Polarization Index",
        "formula": "(VV - VH)/(VV + VH)",
        "denominator": "(VV + VH)",
        "reference": "https://www.isprs.org/proceedings/XXXVII/congress/4_pdf/267.pdf",
        "application_domain": "radar",
        "contributor": "https://github.com/davemlz",
    }
    VHVVR = {
        "long_name": "VH-VV Ratio",
        "formula": "VH/VV",
        "denominator": "VV",
        "reference": "https://doi.org/10.1109/IGARSS47720.2021.9554099",
        "application_domain": "radar",
        "contributor": "https://github.com/davemlz",
    }
    VHVVP = {
        "long_name": "VH-VV Product",
        "formula": "VH * VV",
        "denominator": None,
        "reference": "https://doi.org/10.1109/IGARSS47720.2021.9554099",
        "application_domain": "radar",
        "contributor": "https://github.com/davemlz",
    }
    VVVHD = {
        "long_name": "VV-VH Difference",
        "formula": "VV - VH",
        "denominator": None,
        "reference": "https://doi.org/10.1109/IGARSS47720.2021.9554099",
        "application_domain": "radar",
        "contributor": "https://github.com/davemlz",
    }
    VVVHS = {
        "long_name": "VV-VH Sum",
        "formula": "VV + VH",
        "denominator": None,
        "reference": "https://doi.org/10.1109/IGARSS47720.2021.9554099",
        "application_domain": "radar",
        "contributor": "https://github.com/davemlz",
    }
    VVVHR = {
        "long_name": "VV-VH Ratio",
        "formula": "VV/VH",
        "denominator": "VH",
        "reference": "https://doi.org/10.3390/app9040655",
        "application_domain": "radar",
        "contributor": "https://github.com/davemlz",
    }
    VHVVD = {
        "long_name": "VH-VV Difference",
        "formula": "VH - VV",
        "denominator": None,
        "reference": "https://doi.org/10.3390/app9040655",
        "application_domain": "radar",
        "contributor": "https://github.com/davemlz",
    }
    BAIM = {
        "long_name": "Burned Area Index adapted to MODIS",
        "formula": "1.0/(pow((0.05 - N) , 2.0)) + (pow((0.2 - S2) , 2.0))",
        "denominator": "pow((0.05 - N) , 2.0)",
        "reference": "https://doi.org/10.1016/j.foreco.2006.08.248",
        "application_domain": "burn",
        "contributor": "https://github.com/davemlz",
    }
    SWM = {
        "long_name": "Sentinel Water Mask",
        "formula": "(B + G)/(N + S1)",
        "denominator": "(N + S1)",
        "reference": "https://eoscience.esa.int/landtraining2017/files/posters/MILCZAREK.pdf",
        "application_domain": "water",
        "contributor": "https://github.com/davemlz",
    }
    LSWI = {
        "long_name": "Land Surface Water Index",
        "formula": "(N - S1)/(N + S1)",
        "denominator": "(N + S1)",
        "reference": "https://doi.org/10.1016/j.rse.2003.11.008",
        "application_domain": "water",
        "contributor": "https://github.com/davemlz",
    }
    MLSWI26 = {
        "long_name": "Modified Land Surface Water Index (MODIS Bands 2 and 6)",
        "formula": "(1.0 - N - S1)/(1.0 - N + S1)",
        "denominator": "(1.0 - N + S1)",
        "reference": "https://doi.org/10.3390/rs71215805",
        "application_domain": "water",
        "contributor": "https://github.com/davemlz",
    }
    MLSWI27 = {
        "long_name": "Modified Land Surface Water Index (MODIS Bands 2 and 7)",
        "formula": "(1.0 - N - S2)/(1.0 - N + S2)",
        "denominator": "(1.0 - N + S2)",
        "reference": "https://doi.org/10.3390/rs71215805",
        "application_domain": "water",
        "contributor": "https://github.com/davemlz",
    }
    NBRplus = {
        "long_name": "Normalized Burn Ratio Plus",
        "formula": "(S2 - N2 - G - B)/(S2 + N2 + G + B)",
        "denominator": "(S2 + N2 + G + B)",
        "reference": "https://doi.org/10.3390/rs14071727",
        "application_domain": "burn",
        "contributor": "https://github.com/davemlz",
    }
    NBRSWIR = {
        "long_name": "Normalized Burn Ratio SWIR",
        "formula": "(S2 - S1 - 0.02)/(S2 + S1 + 0.1)",
        "denominator": "(S2 + S1 + 0.1)",
        "reference": "https://doi.org/10.1080/22797254.2020.1738900",
        "application_domain": "burn",
        "contributor": "https://github.com/davemlz",
    }
    NDSWIR = {
        "long_name": "Normalized Difference SWIR",
        "formula": "(N - S1)/(N + S1)",
        "denominator": "(N + S1)",
        "reference": "https://doi.org/10.1109/TGRS.2003.819190",
        "application_domain": "burn",
        "contributor": "https://github.com/davemlz",
    }
    SEVI = {
        "long_name": "Shadow-Eliminated Vegetation Index",
        "formula": f"(N/R) + {FDELTA} * (1.0/R)",
        "denominator": "R",
        "reference": "https://doi.org/10.1080/17538947.2018.1495770",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    ANDWI = {
        "long_name": "Augmented Normalized Difference Water Index",
        "formula": "(B + G + R - N - S1 - S2)/(B + G + R + N + S1 + S2)",
        "denominator": "(B + G + R + N + S1 + S2)",
        "reference": "https://doi.org/10.1016/j.envsoft.2021.105030",
        "application_domain": "water",
        "contributor": "https://github.com/davemlz",
    }
    NBAI = {
        "long_name": "Normalized Built-up Area Index",
        "formula": "(S2 - S1/G)/(S2 + S1/G)",
        "denominator": "(S2 + S1/G)",
        "reference": "https://www.omicsonline.org/scientific-reports/JGRS-SR136.pdf",
        "application_domain": "urban",
        "contributor": "https://github.com/davemlz",
    }
    BRBA = {
        "long_name": "Band Ratio for Built-up Area",
        "formula": "R/S1",
        "denominator": "S1",
        "reference": "https://www.omicsonline.org/scientific-reports/JGRS-SR136.pdf",
        "application_domain": "urban",
        "contributor": "https://github.com/davemlz",
    }
    VIBI = {
        "long_name": "Vegetation Index Built-up Index",
        "formula": "((N-R)/(N+R))/(((N-R)/(N+R)) + ((S1-N)/(S1+N)))",
        "denominator": "(((N-R)/(N+R)) + ((S1-N)/(S1+N)))",
        "reference": "http://dx.doi.org/10.1080/01431161.2012.687842",
        "application_domain": "urban",
        "contributor": "https://github.com/davemlz",
    }
    NSDSI1 = {
        "long_name": "Normalized Shortwave-Infrared Difference Bare Soil Moisture Index 1",
        "formula": "(S1-S2)/S1",
        "denominator": "S1",
        "reference": "https://doi.org/10.1016/j.isprsjprs.2019.06.012",
        "application_domain": "soil",
        "contributor": "https://github.com/CvenGeo",
    }
    NSDSI2 = {
        "long_name": "Normalized Shortwave-Infrared Difference Bare Soil Moisture Index 2",
        "formula": "(S1-S2)/S2",
        "denominator": "S2",
        "reference": "https://doi.org/10.1016/j.isprsjprs.2019.06.012",
        "application_domain": "soil",
        "contributor": "https://github.com/CvenGeo",
    }
    NSDSI3 = {
        "long_name": "Normalized Shortwave-Infrared Difference Bare Soil Moisture Index 3",
        "formula": "(S1-S2)/(S1+S2)",
        "denominator": "(S1 + S2)",
        "reference": "https://doi.org/10.1016/j.isprsjprs.2019.06.012",
        "application_domain": "soil",
        "contributor": "https://github.com/CvenGeo",
    }
    NDTI = {
        "long_name": "Normalized Difference Turbidity Index",
        "formula": "(R-G)/(R+G)",
        "denominator": "(R + G)",
        "reference": "https://doi.org/10.1016/j.rse.2006.07.012",
        "application_domain": "water",
        "contributor": "https://github.com/CvenGeo",
    }
    NDPonI = {
        "long_name": "Normalized Difference Pond Index",
        "formula": "(S1-G)/(S1+G)",
        "denominator": "(S1 + G)",
        "reference": "https://doi.org/10.1016/j.rse.2006.07.012",
        "application_domain": "water",
        "contributor": "https://github.com/CvenGeo",
    }
    NDCI = {
        "long_name": "Normalized Difference Chlorophyll Index",
        "formula": "(RE1 - R)/(RE1 + R)",
        "denominator": "(RE1 + R)",
        "reference": "https://doi.org/10.1016/j.rse.2011.10.016",
        "application_domain": "water",
        "contributor": "https://github.com/kalab-oto",
    }
    WI2015 = {
        "long_name": "Water Index 2015",
        "formula": "1.7204 + 171 * G + 3 * R - 70 * N - 45 * S1 - 71 * S2",
        "denominator": None,
        "reference": "https://doi.org/10.1016/j.rse.2015.12.055",
        "application_domain": "water",
        "contributor": "https://github.com/remi-braun",
    }
    DSWI5 = {
        "long_name": "Disease-Water Stress Index 5",
        "formula": "(N + G)/(S1 + R)",
        "denominator": "(S1 + R)",
        "reference": "https://doi.org/10.1080/01431160310001618031",
        "application_domain": "vegetation",
        "contributor": "https://github.com/remi-braun",
    }
    DSWI1 = {
        "long_name": "Disease-Water Stress Index 1",
        "formula": "N/S1",
        "denominator": "S1",
        "reference": "https://doi.org/10.1080/01431160310001618031",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    DSWI2 = {
        "long_name": "Disease-Water Stress Index 2",
        "formula": "S1/G",
        "denominator": "G",
        "reference": "https://doi.org/10.1080/01431160310001618031",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    DSWI3 = {
        "long_name": "Disease-Water Stress Index 3",
        "formula": "S1/R",
        "denominator": "R",
        "reference": "https://doi.org/10.1080/01431160310001618031",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    DSWI4 = {
        "long_name": "Disease-Water Stress Index 4",
        "formula": "G/R",
        "denominator": "R",
        "reference": "https://doi.org/10.1080/01431160310001618031",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    DSI = {
        "long_name": "Drought Stress Index",
        "formula": "S1/N",
        "denominator": "N",
        "reference": "https://www.asprs.org/wp-content/uploads/pers/1999journal/apr/1999_apr_495-501.pdf",  # noqa: E501
        "application_domain": "vegetation",
        "contributor": "https://github.com/remi-braun",
    }
    BITM = {
        "long_name": "Landsat TM-based Brightness Index",
        "formula": """
            pow((
                (
                    (pow(B , 2.0))+(pow(G , 2.0))+(pow(R , 2.0))
                )/3.0
            ) fr, 0.5)
        """,
        "denominator": None,
        "reference": "https://doi.org/10.1016/S0034-4257(98)00030-3",
        "application_domain": "soil",
        "contributor": "https://github.com/davemlz",
    }
    BIXS = {
        "long_name": "SPOT HRV XS-based Brightness Index",
        "formula": "pow((((pow(G , 2.0))+(pow(R , 2.0)))/2.0) , 0.5)",
        "denominator": None,
        "reference": "https://doi.org/10.1016/S0034-4257(98)00030-3",
        "application_domain": "soil",
        "contributor": "https://github.com/remi-braun",
    }
    RI4XS = {
        "long_name": "SPOT HRV XS-based Redness Index 4",
        "formula": "(pow(R , 2.0))/(pow(G , 4.0))",
        "denominator": "pow(G , 4.0)",
        "reference": "https://doi.org/10.1016/S0034-4257(98)00030-3",
        "application_domain": "soil",
        "contributor": "https://github.com/davemlz",
    }
    TWI = {
        "long_name": "Triangle Water Index",
        "formula": """
            (2.84 * (RE1 - RE2) / (G + S2)) +
            ((1.25 * (G - B) - (N - B)) / (N + 1.25 * G - 0.25 * B))
        """,
        "denominator": "(G + S2)*(N + 1.25 * G - 0.25 * B)",
        "reference": "https://doi.org/10.3390/rs14215289",
        "application_domain": "water",
        "contributor": "https://github.com/remi-braun",
    }
    CCI = {
        "long_name": "Chlorophyll Carotenoid Index",
        "formula": "(G1 - R)/(G1 + R)",
        "denominator": "(G1 + R)",
        "reference": "https://doi.org/10.1073/pnas.1606162113",
        "application_domain": "vegetation",
        "contributor": "https://github.com/joanvlasschaert",
    }
    SLAVI = {
        "long_name": "Specific Leaf Area Vegetation Index",
        "formula": "N/(R + S2)",
        "denominator": "(R + S2)",
        "reference": "https://www.asprs.org/wp-content/uploads/pers/2000journal/february/2000_feb_183-191.pdf",  # noqa: E501
        "application_domain": "vegetation",
        "contributor": "https://github.com/geoSanjeeb",
    }
    EBI = {
        "long_name": "Enhanced Bloom Index",
        "formula": f"(R + G + B)/((G/B) * (R - B + {EPSILON}))",
        "denominator": "((G/B) * (R - B + EPSILON))",
        "reference": "https://doi.org/10.1016/j.isprsjprs.2019.08.006",
        "application_domain": "vegetation",
        "contributor": "https://github.com/geoSanjeeb",
    }
    ENDVI = {
        "long_name": "Enhanced Normalized Difference Vegetation Index",
        "formula": "((N + G) - (2 * B)) / ((N + G) + (2 * B))",
        "denominator": "((N + G) + (2 * B))",
        "reference": "https://doi.org/10.1371/journal.pone.0186193",
        "application_domain": "vegetation",
        "contributor": "https://github.com/gagev",
    }
    bNIRv = {
        "long_name": "Blue Near-Infrared Reflectance of Vegetation",
        "formula": "((N - B)/(N + B)) * N",
        "denominator": "(N + B)",
        "reference": "https://doi.org/10.1029/2024JG008240",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    EVIv = {
        "long_name": "Enhanced Vegetation Index of Vegetation",
        "formula": "2.5 * ((N - R)/(N + 6 * R - 7.5 * B + 1.0)) * N",
        "denominator": "(N + 6 * R - 7.5 * B + 1.0)",
        "reference": "https://doi.org/10.1029/2024JG008240",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    sNIRvLSWI = {
        "long_name": "SWIR-enhanced Near-Infrared Reflectance of Vegetation for LSWI",
        "formula": "((N - S2)/(N + S2)) * N",
        "denominator": "(N + S2)",
        "reference": "https://doi.org/10.1029/2024JG008240",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    sNIRvNDPI = {
        "long_name": "SWIR-enhanced Near-Infrared Reflectance of Vegetation for NDPI",
        "formula": f"""
            (N - ({ALPHA} * R + (1.0 - {ALPHA}) * S2)) /
            (N + ({ALPHA} * R + (1.0 - {ALPHA}) * S2)) * N
        """,
        "denominator": "(N + (ALPHA * R + (1.0 - ALPHA) * S2))",
        "reference": "https://doi.org/10.1029/2024JG008240",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    sNIRvSWIR = {
        "long_name": "SWIR-enhanced Near-Infrared Reflectance of Vegetation",
        "formula": "((N - R - pow(S2 , 2.0))/(N + R + pow(S2 , 2.0))) * N",
        "denominator": "(N + R + pow(S2 , 2.0))",
        "reference": "https://doi.org/10.1029/2024JG008240",
        "application_domain": "vegetation",
        "contributor": "https://github.com/MartinuzziFrancesco",
    }
    sNIRvNDVILSWIP = {
        "long_name": """
            SWIR-enhanced Near-Infrared Reflectance of Vegetation for the NDVI-LSWI Product
        """,
        "formula": "((N - R)/(N + R)) * ((N - S2)/(N + S2)) * N",
        "denominator": "(N + R)*(N + S2)",
        "reference": "https://doi.org/10.1029/2024JG008240",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    sNIRvNDVILSWIS = {
        "long_name": "SWIR-enhanced Near-Infrared Reflectance of Vegetation for the NDVI-LSWI Sum",
        "formula": "(((N - R)/(N + R)) + ((N - S2)/(N + S2))) * N",
        "denominator": None,
        "reference": "https://doi.org/10.1029/2024JG008240",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    OSI = {
        "long_name": "Oil Spill Index",
        "formula": "(G + R)/B",
        "denominator": "B",
        "reference": "https://doi.org/10.1016/j.mex.2021.101327",
        "application_domain": "water",
        "contributor": "https://github.com/emanuelcastanho",
    }
    PI = {
        "long_name": "Plastic Index",
        "formula": "N/(N + R)",
        "denominator": None,
        "reference": "https://doi.org/10.3390/rs12162648",
        "application_domain": "water",
        "contributor": "https://github.com/emanuelcastanho",
    }
    FAI = {
        "long_name": "Floating Algae Index",
        "formula": f"N - (R + (S1 - R)*(({LAMBDAN} - {LAMBDAR})/({LAMBDAS1} - {LAMBDAR})))",
        "denominator": "({LAMBDAS1} - {LAMBDAR})",
        "reference": "https://doi.org/10.1016/j.rse.2009.05.012",
        "application_domain": "water",
        "contributor": "https://github.com/emanuelcastanho",
    }
    RNDVI = {
        "long_name": "Reversed Normalized Difference Vegetation Index",
        "formula": "(R - N)/(R + N)",
        "denominator": "R + N",
        "reference": "https://doi.org/10.3390/rs12162648",
        "application_domain": "water",
        "contributor": "https://github.com/davemlz",
    }
    CRI550 = {
        "long_name": "Carotenoid Reflectance Index using 550 nm",
        "formula": "(1.0 / B) - (1.0 / G)",
        "denominator": "B * G",
        "reference": "https://doi.org/10.1562/0031-8655(2002)0750272ACCIPL2.0.CO2",
        "application_domain": "vegetation",
        "contributor": "https://github.com/eomasters-repos",
    }
    CRI700 = {
        "long_name": "Carotenoid Reflectance Index using 700 nm",
        "formula": "(1.0 / B) - (1.0 / RE1)",
        "denominator": "B*RE1",
        "reference": "https://doi.org/10.1562/0031-8655(2002)0750272ACCIPL2.0.CO2",
        "application_domain": "vegetation",
        "contributor": "https://github.com/eomasters-repos",
    }
    NPCI = {
        "long_name": "Normalized Pigments Chlorophyll Ratio Index",
        "formula": "(R - A) / (R + A)",
        "denominator": "(R + A)",
        "reference": "https://doi.org/10.1016/0034-4257(94)90136-8",
        "application_domain": "vegetation",
        "contributor": "https://github.com/MartinuzziFrancesco",
    }
    FWEI = {
        "long_name": "Flood/Water Extraction Index",
        "formula": "(((B + G + R) / 3.0) - N)/(((B + G + R) / 3.0) + N)",
        "denominator": "(((B + G + R) / 3.0) + N)",
        "reference": "https://doi.org/10.1007/s00477-024-02660-z",
        "application_domain": "water",
        "contributor": "https://github.com/kalab-oto",
    }
    CRSWIR = {
        "long_name": "Continuum Removal SWIR",
        "formula": f"""
            S1 / (N2 + ((S2 - N2) / ({LAMBDAS2} - {LAMBDAN2})) * ({LAMBDAS1} - {LAMBDAN2}))
        """,
        "denominator": "(N2 + ((S2 - N2)",
        "reference": "https://www.onf.fr/onf/+/cec::les-rendez-vous-techniques-de-lonf-no69-70.html",  # noqa: E501
        "application_domain": "vegetation",
        "contributor": "https://github.com/kenoz",
    }
    MVI = {
        "long_name": "Mangrove Vegetation Index",
        "formula": "(N - G) / (S1 - G)",
        "denominator": "(S1 - G)",
        "reference": "https://doi.org/10.1016/j.isprsjprs.2020.06.001",
        "application_domain": "vegetation",
        "contributor": "https://github.com/delatorredm",
    }
    MI = {
        "long_name": "Mangrove Index",
        "formula": "(N - S1) / (N * S1)",
        "denominator": "(N * S1)",
        "reference": "https://www.researchgate.net/profile/Gathot-Winarso/publication/277137915_NEW_MANGROVE_INDEX_AS_DEGRADATIONHEALTH_INDICATOR_USING_REMOTE_SENSING_DATA_SEGARA_ANAKAN_AND_ALAS_PURWO_CASE_STUDY/links/5562d90c08ae8c0cab333ab4/NEW-MANGROVE-INDEX-AS-DEGRADATION-HEALTH-INDICATOR-USING-REMOTE-SENSING-DATA-SEGARA-ANAKAN-AND-ALAS-PURWO-CASE-STUDY.pdf",  # noqa: E501
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    IRGBVI = {
        "long_name": "Improved-Red-Green-Blue Vegetation Index",
        "formula": """
            (5.0 * (pow(G , 2.0)) - 2.0 * (pow(R , 2.0)) - 5.0 * (pow(B , 2.0))) /
            (5.0 * (pow(G , 2.0)) + 2.0 * (pow(R , 2.0)) + 5.0 * (pow(B , 2.0)))
        """,
        "denominator": "(5.0 * (pow(G , 2.0)) + 2.0 * (pow(R , 2.0)) + 5.0 * (pow(B , 2.0)))",
        "reference": "https://doi.org/10.1016/j.jag.2024.103668",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    FDI = {
        "long_name": "Floating Debris Index",
        "formula": f"""
            N - (RE2 + 10 * (S1 - RE2) * ({LAMBDAN} - {LAMBDAR})/({LAMBDAS1} - {LAMBDAR}))
        """,
        "denominator": "({LAMBDAS1} - {LAMBDAR})",
        "reference": "https://doi.org/10.1038/s41598-020-62298-z",
        "application_domain": "water",
        "contributor": "https://github.com/guillemc23",
    }
    NDVI4RE = {
        "long_name": "4-band Red Edge Normalized Difference Vegetation Index",
        "formula": f"""
            (({ALPHA} * RE3 + (1 - {ALPHA}) * RE2) - ({BETA} * R + (1 - {BETA}) * RE1)) /
            (({ALPHA} * RE3 + (1 - {ALPHA}) * RE2) + ({BETA} * R + (1 - {BETA}) * RE1))
        """,
        "denominator": f"""
            (({ALPHA} * RE3 + (1 - {ALPHA}) * RE2) + ({BETA} * R + (1 - {BETA}) * RE1))
        """,
        "reference": "https://doi.org/10.1016/j.jag.2022.102793",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    SAVI4RE = {
        "long_name": "4-band Red Edge Soil Adjusted Vegetation Index",
        "formula": f"""
            2.0 * (({ALPHA} * RE3 + (1 - {ALPHA}) * RE2) - ({BETA} * R + (1 - {BETA}) * RE1)) /
            (({ALPHA} * RE3 + (1 - {ALPHA}) * RE2) + ({BETA} * R + (1 - {BETA}) * RE1 + 1))
        """,
        "denominator": f"""
            (({ALPHA} * RE3 + (1 - {ALPHA}) * RE2) + ({BETA} * R + (1 - {BETA}) * RE1 + 1))
        """,
        "reference": "https://doi.org/10.1016/j.jag.2022.102793",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    RVI4RE = {
        "long_name": "4-band Red Edge Ratio Vegetation Index",
        "formula": f"""
            ({ALPHA} * RE3 + (1 - {ALPHA}) * RE2)/({BETA} * R + (1 - {BETA}) * RE1)
        """,
        "denominator": f"({BETA} * R + (1 - {BETA}) * RE1)",
        "reference": "https://doi.org/10.1016/j.jag.2022.102793",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    NDTI4RE = {
        "long_name": "4-band Red Edge Normalized Difference Tillage Index",
        "formula": f"{GAMMA} * (S1 - S2)/(S1 + S2) + (1 - {GAMMA}) * (N - RE3)/(N + RE3)",
        "denominator": "(S1 + S2)*(N + RE3)",
        "reference": "https://doi.org/10.1016/j.jag.2022.102793",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    SNDTI4RE = {
        "long_name": "4-band Red Edge Soil-Adjusted Normalized Difference Tillage Index",
        "formula": f"""
            {GAMMA} * ((S1 - S2) * 2.0)/(S1 + S2 + 1.0) +
            (1 - {GAMMA}) * ((N - RE3) * 2.0)/(N + RE3 + 1.0)
        """,
        "denominator": "(S1 + S2 + 1.0)*(N + RE3 + 1.0)",
        "reference": "https://doi.org/10.1016/j.jag.2022.102793",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    STI4RE = {
        "long_name": "4-band Red Edge Soil Tillage Index",
        "formula": f"{GAMMA} * S1/S2 + (1 - {GAMMA}) * N/RE3",
        "denominator": "RE3*S2",
        "reference": "https://doi.org/10.1016/j.jag.2022.102793",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    STI = {
        "long_name": "Simple Tillage Index",
        "formula": "S1 / S2",
        "denominator": "S2",
        "reference": "https://www.asprs.org/wp-content/uploads/pers/1997journal/jan/1997_jan_87-93.pdf",  # noqa: E501
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    NDTillI = {
        "long_name": "Normalized Difference Tillage Index",
        "formula": "(S1 - S2)/(S1 + S2)",
        "denominator": "(S1 + S2)",
        "reference": "https://www.asprs.org/wp-content/uploads/pers/1997journal/jan/1997_jan_87-93.pdf",  # noqa: E501
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
    SNDTI = {
        "long_name": "Soil-Adjusted Normalized Difference Tillage Index",
        "formula": f"(1.0 + {L}) * (S1 - S2) / (S1 + S2 + {L})",
        "denominator": f"(S1 + S2 + {L})",
        "reference": "https://doi.org/10.1080/22797254.2017.1418186",
        "application_domain": "vegetation",
        "contributor": "https://github.com/davemlz",
    }
