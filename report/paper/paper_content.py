"""Content for the IEEE conference paper (two-column).

Each block is a tuple consumed by build_paper.py:
    ("title", text)            paper title, 24 pt, spans both columns
    ("authors", [[...], [...]]) author grid, 3 columns
    ("abstract", text)
    ("keywords", text)
    ("h1", "I. INTRODUCTION")
    ("h2", "A. Something")
    ("h3", "1) Run-in head:", "rest of the paragraph")
    ("p", text)
    ("fig", filename, "Fig. 1.  Caption text.", width_inches)
    ("tbl", label, title, header_row, rows, col_widths_inches, footnote)
    ("eq", "equation text", "(1)")
"""
from __future__ import annotations

TITLE = ("HYDRO RAIN GUARD: An Auditable Decision-Support System for Rooftop "
         "Rainwater Harvesting and Artificial Groundwater Recharge")

AUTHORS = [
    [
        ("Shubham Desai", "Department of Information Technology",
         "JSPM's Rajarshi Shahu College of Engineering", "Pune, India",
         "desaishubham696@gmail.com"),
        ("Dr. Dipali H. Patil", "Department of Information Technology",
         "JSPM's Rajarshi Shahu College of Engineering", "Pune, India",
         "patildipali07@gmail.com"),
        ("Siddhesh Mahadik", "Department of Information Technology",
         "JSPM's Rajarshi Shahu College of Engineering", "Pune, India",
         "siddheshamahadik@gmail.com"),
    ],
    [
        ("Omkar Kshirsagar", "Department of Information Technology",
         "JSPM's Rajarshi Shahu College of Engineering", "Pune, India",
         "omkarkshirsagar2005@gmail.com"),
        ("Kaushal Agale", "Department of Information Technology",
         "JSPM's Rajarshi Shahu College of Engineering", "Pune, India",
         "kaushalagale907@gmail.com"),
    ],
]

ABSTRACT = (
    "Most rooftop rainwater harvesting calculators answer one question: how much water falls on this roof. "
    "The decision a household or a municipal engineer actually faces is wider. How much of that water can be "
    "captured, how much can be returned to the ground, which structure should be built first, what it will cost, "
    "and how much of the answer can be defended when someone asks where a number came from. This paper describes "
    "HYDRO RAIN GUARD, a web application that answers those questions in a single pass and keeps every intermediate "
    "quantity visible. Rainfall is taken from a 2.5-degree monthly climatology (NOAA CMAP, 1991-2020), interpolated "
    "at the site and rescaled to a measured annual total where one is available. Runoff is computed twice, once by "
    "the Rational method and once by the SCS curve number method, and the gap between them is reported instead of "
    "hidden. Harvestable volume is discounted for first flush, recharge is bounded by both soil infiltration and "
    "the rain that actually falls, and five candidate structures are ranked by an analytic hierarchy process whose "
    "pairwise matrix, weights, principal eigenvalue and consistency ratio are all displayed to the user. A reference "
    "case in Pune (100 square metre RCC roof, 700 mm of rain) gives 63.0 kL of runoff, 43.0 kL harvestable, 24.5 kL "
    "of recharge potential and a storage tank scored 93 out of 100, with a simple payback of 60.6 years at the local "
    "tariff of INR 35 per kilolitre. We report that payback rather than adjusting the assumptions until it looks "
    "better. Five scenarios, 38 automated tests and a clean production build support the results."
)

KEYWORDS = ("index terms - rooftop rainwater harvesting, artificial recharge, SCS curve number, analytic hierarchy "
            "process, decision support system, WebXR, multilingual report generation")

BLOCKS = [
    ("h1", "I. INTRODUCTION"),

    ("p", "India adds roughly ten million new urban residents every year, and most of them are supplied by "
          "groundwater or by a municipal network that itself runs on groundwater. The result is familiar: falling "
          "water tables in the Deccan basalt, drying borewells in the summer, and tanker water sold at several times "
          "the municipal rate. Rooftops are the one large impervious surface in a city that is easy to intercept. "
          "A single 100 square metre slab in Pune sheds about 63 kilolitres of water a year, which is more than a "
          "family of four uses for flushing and gardening."),

    ("p", "The engineering needed to capture that water is not complicated. A gutter, a first-flush diverter, a "
          "storage tank and a recharge pit will do. What stops people is the arithmetic that comes before the "
          "plumbing. How much water can this specific roof yield? Is the soil below it permeable enough for a pit to "
          "work? Should the money go into storage or into recharge? What does the whole thing cost, and when does it "
          "pay for itself? These questions are answered today either by a consultant quoting a lump sum, or by a "
          "spreadsheet built around a single runoff coefficient."),

    ("p", "The tools that do exist tend to be narrow. Municipal calculators ask for roof area and rainfall and return "
          "one volume. Catchment-scale models such as SWMM or HEC-HMS are far more capable but assume a trained user, "
          "a digital elevation model and a licence. Neither kind tells the user how confident the answer is, and "
          "almost none of them produce a document that a housing society can attach to a building proposal or that a "
          "ward office can file."),

    ("p", "This paper reports what we built to close that gap, and what the numbers looked like when we ran it. The "
          "contributions are as follows."),

    ("bullets", [
        "A single assessment pipeline that moves from a map pin to a costed recommendation, with each stage exposed "
        "as a separate service rather than folded into one opaque formula.",
        "A dual runoff estimate. The Rational method drives the design volume and the SCS curve number method runs "
        "alongside it as an independent check; the divergence is shown to the user instead of being averaged away.",
        "An AHP ranking of five recharge and storage structures in which the pairwise matrix, the derived weights and "
        "the consistency diagnostics are printed in the interface, so a reviewer can recompute them by hand.",
        "A reporting layer that produces a multi-page PDF in English, Hindi and Marathi, using a Devanagari shaping "
        "pipeline, because the households most likely to build a recharge pit are not always comfortable reading an "
        "English engineering report.",
    ]),

    ("p", "Section II places the work against existing literature. Section III sets out the model and its equations, "
          "Section IV covers implementation, Section V reports results from five sites, and Sections VI and VII "
          "discuss limitations and conclude."),

    ("h1", "II. RELATED WORK"),

    ("h2", "A. Runoff Estimation from Roofs"),
    ("p", "The Rational method remains the standard first estimate for small impervious catchments. Its appeal is "
          "that it needs one coefficient and one rainfall depth, and its weakness is that the coefficient absorbs "
          "everything the modeller does not know. Published values for concrete roofs cluster between 0.85 and 0.95, "
          "which means a 100 square metre roof at 700 mm can credibly yield anywhere between 59 and 66 kilolitres. "
          "The SCS curve number approach, developed for agricultural catchments and codified for urban use in TR-55 "
          "[1], handles the non-linearity of runoff generation better because it subtracts an initial abstraction "
          "before any runoff is produced. Applied to a roof, the curve number sits near 98, close to the impervious "
          "limit, and the two methods usually land within a few percent of each other at annual scale. They diverge "
          "sharply at monthly scale, which is exactly where storage sizing matters."),

    ("p", "Recent work has moved towards connecting rooftop harvesting with catchment hydrology rather than treating "
          "it as a household appliance. Lu et al. [2] used a connectivity index to show that roof harvesting in "
          "Hamadan reduced the area of high hydrological connectivity from 20.4 percent to 11.4 percent, which is a "
          "flood argument for the practice rather than a supply argument. Hari and Kasa [3] estimated the rooftop "
          "potential of Greater Hyderabad from building footprints and gridded rainfall and concluded that harvesting "
          "could meet about a third of domestic demand. Both studies work at city scale; neither produces a "
          "site-specific recommendation that a single building owner can act on."),

    ("h2", "B. Rainfall Data and Geospatial Screening"),
    ("p", "Rainfall is the largest single source of uncertainty in a rooftop assessment, and it is usually handled by "
          "picking the nearest gauge. Gridded products offer an alternative. The CPC Merged Analysis of Precipitation "
          "blends gauge observations, satellite estimates and reanalysis output onto a 2.5-degree grid [4], and its "
          "monthly climatology is freely available. A 2.5-degree cell is roughly 278 km across, so it cannot resolve "
          "a rain shadow inside a city. It can, however, describe the seasonal shape of the monsoon, and that shape "
          "is what determines whether a tank sized for July will overflow in September. Combining the grid's monthly "
          "distribution with a locally measured annual total is a pragmatic compromise, and it is the approach we "
          "adopt."),

    ("p", "GIS-based screening studies follow the same logic at larger scale. Preeti and Rahman [5] reviewed the use "
          "of GIS in rainwater harvesting research and found that most studies stop at potential mapping, without "
          "carrying the estimate through to a structure or a cost. Ali et al. [6] surveyed the barriers to urban "
          "implementation and identified cost uncertainty and the absence of decision tools, rather than technical "
          "feasibility, as the binding constraints."),

    ("h2", "C. Multi-Criteria Ranking"),
    ("p", "Where several structures are possible, the choice is multi-criteria by nature. The Analytic Hierarchy "
          "Process [7] remains the most widely used method in water planning because its weights can be inspected "
          "and its consistency can be tested. A consistency ratio below 0.10 is the usual acceptance threshold, and "
          "publishing the ratio alongside the result is what separates a defensible ranking from an arbitrary one. "
          "Alternatives such as TOPSIS or weighted overlay are equally common, but AHP has the advantage that its "
          "input is a small matrix that a reviewer can reconstruct."),

    ("h2", "D. Reporting, Visualisation and Language"),
    ("p", "Decision support in water management has been criticised for producing answers whose assumptions never "
          "reach the person making the decision. Doorn [8] argues that responsible use of computational tools in the "
          "water sector depends on the values embedded in the problem formulation being visible to stakeholders. Our "
          "design response is literal: weights, coefficients, data sources and consistency statistics appear on the "
          "results page and again in the exported PDF. Three-dimensional and augmented-reality previews, built with "
          "WebXR, are used to show a proposed tank or pit at its real dimensions on the ground; similar approaches "
          "have been used for subsurface utility visualisation [9] and are now practical in a browser without a "
          "plugin."),

    ("h2", "E. Gap"),
    ("p", "The literature provides good component methods and good city-scale screening. What is missing is a tool "
          "that joins them at the scale of one building, keeps the intermediate quantities visible, and returns a "
          "document. That is the gap this work addresses. We make no claim to a new hydrological model; the "
          "contribution is in the assembly, the transparency of the assembly, and the evidence that it runs."),

    ("h1", "III. SYSTEM DESIGN AND METHODS"),
    ("p", "The system is a three-tier application. A Next.js client collects site data and renders results, a "
          "FastAPI service orchestrates the calculation, and a set of pure Python functions performs each "
          "hydrological step. Keeping the numerical work in pure functions with no database or HTTP dependency was a "
          "deliberate choice: it makes every formula testable in isolation and lets the same code run inside the "
          "request handler and inside the test suite."),

    ("fig", "fig2_arch.png", "Fig. 1.  Layer structure of the system. The domain services carry no state and are "
                             "exercised directly by the test suite.", 2.95),

    ("h2", "A. Rainfall Sampling and Scaling"),
    ("p", "The climatology grid stores twelve monthly means on a 72 by 144 lattice, together with the number of "
          "years behind each cell. For a site at latitude phi and longitude lambda the sampler locates the four "
          "surrounding cell centres and forms a bilinear weighted mean. Cells flagged as no-data drop out of the "
          "average and their weight is redistributed, which matters near coastlines where the grid is partly water. "
          "Longitude wraps at the antimeridian; latitude is clamped at the poles."),

    ("p", "The interpolated monthly vector is then scaled so that its sum matches a local annual total when the user "
          "supplies one, preserving the monthly shape but correcting the magnitude. Every response records the source, "
          "the climatology period, the nearest cell centre and whether interpolation actually took place. In the Pune "
          "reference case the site falls at 18.75 degrees north, 73.75 degrees east, where the grid gives 700 mm and "
          "the user value agrees, so no rescaling is applied."),

    ("h2", "B. Runoff: Two Models, One Design Volume"),
    ("p", "The Rational method gives the annual volume directly from roof area *A*, coefficient *C* and rainfall depth *R*:"),

    ("eq", "*V* = *C* x *R* x *A*", "(1)"),

    ("p", "with *C* taken as 0.90 for RCC, 0.85 for metal, 0.75 for tile, 0.80 for asphalt and 0.30 for a green roof, "
          "following the ranges in the CGWB manual [10] and IS 15797 [11]. The SCS curve number method is applied "
          "monthly. Potential retention and initial abstraction are"),

    ("eq", "*S* = 25400 / *CN* \u2212 254 ,     *I*~a~ = 0.2 *S*", "(2)"),

    ("p", "and the runoff depth for a month with *P* millimetres of rain is"),

    ("eq", "*Q* = (*P* \u2212 *I*~a~)^2^ / (*P* \u2212 *I*~a~ + *S*)   for *P* > *I*~a~,   *Q* = 0 otherwise", "(3)"),

    ("p", "Because one millimetre over one square metre is exactly one litre, *Q* multiplied by *A* gives litres "
          "directly. Curve numbers are 98, 97, 95, 96 and 75 for RCC, metal, tile, asphalt and green roofs. Applying "
          "a daily-scale method to monthly totals is an approximation, and we say so in the interface: it "
          "under-predicts runoff from a few intense storms and over-predicts it from long drizzle. The two estimates "
          "are reported side by side, and the Rational result drives costing unless the user selects otherwise."),

    ("p", "The peak discharge for gutter and pipe sizing is obtained from the same Rational formula with an intensity "
          "taken as three times the mean hourly intensity of the wettest month, which is crude but conservative for "
          "the small catchments involved."),

    ("h2", "C. First Flush and Harvestable Volume"),
    ("p", "The first two millimetres of each rain event are discarded, a common recommendation for rooftop systems in "
          "Indian practice. Assuming around one hundred events a year, the loss is"),

    ("eq", "*V*~h~ = *V* \u2212 *n* *d*~f~ *A* ,     *n* = 100 ,  *d*~f~ = 2 mm", "(4)"),

    ("p", "For the Pune roof this removes 20 kilolitres from 63, leaving 43 kilolitres harvestable. The assumption of "
          "a hundred events is itself an estimate, and a user who knows the local rain-day count can change the "
          "coefficient in the configuration."),

    ("h2", "D. Recharge Potential"),
    ("p", "Recharge is limited by two things: how fast water can enter the soil, and how much rain actually falls on "
          "the open area set aside for infiltration. We take the smaller of the two, with a 0.70 efficiency factor "
          "for clogging and lateral losses:"),

    ("eq", "*R*~g~ = min( *K*~s~ *A*~o~ *t*~d~ ,  0.70 *P* *A*~o~ )", "(5)"),

    ("p", "where *K*~s~ is the infiltration rate of the soil class (25 mm/h for sandy, 12.5 for loamy, 6.5 for silty, "
          "2.5 for clay), *A*~o~ is the open area and *t*~d~ is an effective infiltration time of 960 hours per year, from "
          "120 rain days at eight hours each. The same routine produces a feasibility score on a 0-100 scale from "
          "water-table depth, soil class, open area and annual rainfall, which is displayed as a single badge. The "
          "score is a screening aid, not a substitute for a percolation test, and the report says so."),

    ("h2", "E. Ranking Structures with AHP"),
    ("p", "Five candidates are scored: a rooftop storage tank, a soak pit or French drain, a recharge pit, a recharge "
          "trench and a recharge well. Five criteria are used: harvestable yield, annual rainfall, soil infiltration, "
          "open space and water-table depth. The pairwise matrix follows a consistent gradient, with yield judged "
          "strongly more important than the rest:"),

    ("tbl", "TABLE I",
     "Pairwise comparison matrix and derived weights",
     ["Criterion", "Yield", "Rain", "Soil", "Space", "Depth", "Weight"],
     [["Harvestable yield", "1.00", "2.00", "3.00", "4.00", "5.00", "0.4174"],
      ["Annual rainfall", "0.50", "1.00", "2.00", "3.00", "4.00", "0.2634"],
      ["Soil infiltration", "0.33", "0.50", "1.00", "2.00", "3.00", "0.1602"],
      ["Open space", "0.25", "0.33", "0.50", "1.00", "2.00", "0.0975"],
      ["Water-table depth", "0.20", "0.25", "0.33", "0.50", "1.00", "0.0615"]],
     [1.05, 0.40, 0.40, 0.40, 0.44, 0.42, 0.44],
     "Principal eigenvalue 5.068, CI 0.017, CR 0.015, well inside the 0.10 threshold."),

    ("p", "Weights are recovered as the normalised geometric mean of each row, which is numerically stabler than "
          "raising the matrix to a high power. Each criterion is mapped to a utility between zero and one by a ramp "
          "or trapezoid, and the composite score for structure *k* is"),

    ("eq", "*S*~k~ = \u03a3~i~ *w*~i~ *u*~ik~", "(6)"),

    ("p", "Structures that cannot function at a site are removed by hard filters before scoring rather than being "
          "penalised. A percolation tank needs at least 100 square metres of open ground; a recharge well needs a "
          "water table shallower than 40 metres. Filtering first, scoring second, keeps a physically impossible "
          "option from appearing in the middle of the ranking."),

    ("h2", "F. Costing and Payback"),
    ("p", "Capital cost is assembled from three components: storage at INR 1,550 per cubic metre of tank volume, "
          "recharge structures at INR 8,000 for a pit of standard size, and plumbing at INR 200 per square metre of "
          "roof. Annual benefit combines the avoided tariff on harvested water with a recharge credit valued at 20 "
          "percent of the tariff, since recharge water is not directly consumed. Maintenance is taken as two percent "
          "of capital. The payback in years is"),

    ("eq", "*T*~p~ = *C*~c~ / ( *B*~a~ \u2212 *M* )", "(7)"),

    ("p", "and the ten-year return on investment compares cumulative net benefit with capital cost. Both are "
          "reported, together with the break-even tariff at which payback would fall to ten years. That last number "
          "turned out to be more useful to users than the payback itself, as Section VI explains."),

    ("h1", "IV. IMPLEMENTATION"),
    ("h2", "A. Back End"),
    ("p", "The API is written in FastAPI with Pydantic v2 models [12] that reject implausible input at the boundary: roof "
          "areas above 100,000 square metres, water tables deeper than 300 metres, or negative open space. "
          "Assessments are persisted through SQLAlchemy into SQLite, which is adequate for single-instance "
          "deployment and keeps the project reproducible on a laptop. The orchestrating endpoint runs the six "
          "services in sequence and returns one response object containing weather provenance, runoff, recharge, "
          "ranking, economics and hydrogeological notes. Because every intermediate value is in that response, the "
          "client can render any of it without recomputation, and the PDF composer receives exactly what the screen "
          "received."),

    ("h2", "B. Client and Three-Dimensional Preview"),
    ("p", "The client is a Next.js 14 application using the App Router [13], with Tailwind for layout, React Hook Form "
          "and Zod for the three-step wizard, Recharts for the monthly charts and Leaflet with Nominatim [14] for the "
          "map pin. The assessment flow is deliberately short: location and roof, then roof and rainfall, then soil and "
          "groundwater. Each step validates before advancing, and the rainfall preview can be refreshed from the grid "
          "without losing the rest of the form."),

    ("fig", "fig3_wizard.png", "Fig. 2.  Roof step of the wizard. The rainfall card shows the grid value, its "
                               "climatology period and cell centre, and accepts a local annual total.", 2.95),

    ("p", "The results page presents four headline figures, then tabs for monthly analysis, structures, cost-benefit "
          "and hydrogeology. A three-dimensional view, built with react-three-fiber, draws the recommended structure "
          "at its computed dimensions on a ground plane and supports WebXR [15] on Android devices, so a tank can "
          "be placed on the actual floor before it is built. The scene is intentionally schematic; it is a "
          "communication device, not a structural drawing."),

    ("fig", "fig4_results.png", "Fig. 3.  Results for the Pune reference case. Every headline figure links to the "
                                "tab that produced it.", 2.95),

    ("fig", "fig7_xr_panel.png", "Fig. 4.  Three-dimensional preview panel: ranked structures with suitability "
                                 "scores, the computed dimensions that drive the scaled model, and the WebXR "
                                 "entry point.", 2.45),

    ("h2", "C. Report Generation"),
    ("p", "The PDF is composed with ReportLab [16] and runs to five pages: summary, monthly water balance, structures "
          "with dimensions and installation notes, economics, and assumptions with data provenance. Hindi and Marathi "
          "text required more than loading a font. ReportLab draws glyphs in logical order, so Devanagari conjuncts "
          "and matras come out reordered and disconnected unless the string is shaped first. We shape with HarfBuzz "
          "through uharfbuzz [17], convert the shaped glyph run into positioned text, and draw with Noto Sans Devanagari; "
          "a glyph-coverage check falls back to English for any character the font cannot supply. The result is that "
          "a Marathi location name entered in the form appears correctly in the heading, the tables and the "
          "recommendation text of the exported report."),

    ("h2", "D. Testing and Deployment"),
    ("p", "The back end carries 38 tests run under pytest with HTTPX, covering each service in isolation and the API "
          "end to end against a temporary database. The suite pins the reference case to its published numbers, so a "
          "change in a coefficient fails a test rather than silently altering every report. PDF output is tested by "
          "extracting text from the generated file and asserting that key labels and the Devanagari name survive the "
          "round trip. The client builds with no TypeScript or lint errors and produces eight static pages. Both "
          "tiers are deployed on managed hosting, with the API on a Python runtime and the client on Vercel."),

    ("h1", "V. RESULTS"),
    ("p", "Results come from two sources: a reference assessment executed through the API and captured for this "
          "paper, and four additional scenarios chosen to exercise different soils, roof types, rainfall regimes and "
          "languages."),

    ("h2", "A. Reference Case"),
    ("p", "The reference building is a four-person household in Pune with a 100 square metre RCC roof, 50 square "
          "metres of open ground, loamy soil and a water table at 15 metres. Rainfall is 700 mm, of which 89 percent "
          "falls between June and September. The Rational estimate is 63.0 kL per year; after first-flush losses "
          "43.0 kL remains available. Recharge potential is 24.5 kL, or about 67 litres a day, with a feasibility "
          "score of 55 out of 100, driven down by the moderate infiltration rate of loam rather than by depth to "
          "water."),

    ("fig", "fig5_monthly.png", "Fig. 5.  Monthly rainfall against the two runoff estimates for the Pune reference "
                                "case. The shaded area is the Rational volume; the dashed line is SCS-CN.", 3.05),

    ("p", "Fig. 5 shows why a monthly view is needed. The two methods agree on the annual total to within 3.7 percent "
          "but differ by up to 11 percent in July and August, where the curve number method responds to the "
          "non-linearity that the Rational coefficient cannot. For storage sizing, the July peak of 18.6 kL is the "
          "number that matters, and it is well above the mean monthly figure of 5.3 kL."),

    ("h2", "B. Structure Ranking"),
    ("p", "The ranked output for the reference case is shown in Table II. The storage tank wins on yield, which "
          "carries 42 percent of the weight, and the soak pit comes second because loam accepts water at a moderate "
          "rate while a recharge well is penalised by the 15-metre water table. The percolation tank is removed by "
          "the area filter, since 50 square metres of open ground is half of what the structure needs."),

    ("tbl", "TABLE II",
     "Ranked structures for the reference case",
     ["Structure", "Score", "Dimensions", "Note"],
     [["Rooftop storage tank", "93.0", "16.2 m\u00b3, 3.21 m \u00d8 \u00d7 2.0 m", "RCC or PVC, ground level"],
      ["Soak pit / French drain", "72.8", "1.0 m \u00d8 \u00d7 1.5 m", "40 mm aggregate fill"],
      ["Recharge pit", "69.0", "1.5 \u00d7 1.5 \u00d7 2.0 m", "Gravel, stone, sand layers"],
      ["Recharge well", "51.8", "250 mm \u00d8 \u00d7 20 m", "MS perforated casing"],
      ["Percolation tank", "n/a", "needs \u2265 100 m\u00b2 open area", "removed by filter"]],
     [1.10, 0.52, 0.98, 1.15],
     "Scores are the weighted sum of five normalised criteria; the percolation tank fails the area filter before "
     "scoring."),

    ("h2", "C. Scenario Sweep"),
    ("p", "Table III reports five sites. The contrast between the Pune and Mumbai rows is the clearest result in the "
          "study. Both buildings intercept rain, but Mumbai receives 2,300 mm, and the same equation that returns a "
          "60-year payback in Pune returns three years there, because the capital cost scales with roof area while "
          "the yield scales with area and rainfall together."),

    ("tbl", "TABLE III",
     "Scenario sweep across five sites",
     ["Site and roof", "Rain", "Runoff", "Harv.", "Rech.", "Cost", "Payback"],
     [["Pune, RCC 100 m\u00b2", "700", "63.0", "43.0", "24.5", "53,000", "60.6"],
      ["Pune, green 100 m\u00b2", "700", "21.0", "1.0", "24.5", "90,000", "not repaid"],
      ["Kolhapur, RCC 150 m\u00b2", "1,530", "206.6", "176.6", "85.7", "94,495", "16.3"],
      ["Mumbai, metal 500 m\u00b2", "2,300", "977.5", "877.5", "483.0", "114,721", "3.1"],
      ["Delhi, RCC 1,000 m\u00b2", "780", "702.0", "502.0", "218.4", "133,246", "4.8"]],
     [1.16, 0.38, 0.42, 0.38, 0.38, 0.50, 0.50],
     "Rainfall in mm, volumes in kL per year, capital in INR, payback in years at a tariff of INR 35/kL (INR 50 "
     "for Delhi)."),

    ("p", "The green-roof row is the most instructive negative result. A green roof cuts the runoff coefficient to "
          "0.30, so the same 700 mm produces 21 kL instead of 63 kL, and after first flush only 1 kL is available for "
          "storage. The recharge estimate is unchanged, because that calculation depends on the open ground rather "
          "than the roof, which is a modelling artefact worth flagging: in practice a green roof would also reduce "
          "the water reaching a downpipe-fed pit. Capital cost rises to INR 90,000 because of the substrate, so the "
          "system never repays. A green roof is a stormwater and thermal-comfort measure, and the tool now says so "
          "instead of quietly recommending a tank."),

    ("fig", "fig9_scenarios.png", "Fig. 6.  Normalised yield per square metre of roof and simple payback across "
                                  "the five scenarios in Table III.", 3.05),

    ("h2", "D. Economics"),
    ("p", "For the reference case the capital cost is INR 53,000, split between storage (25,000), plumbing (20,000) "
          "and the recharge pit (8,000). Annual benefit is INR 1,505 from avoided water purchase plus INR 429 as a "
          "recharge credit; maintenance is INR 1,060, leaving INR 874 net. Payback is 60.6 years and the ten-year ROI "
          "is minus 83.5 percent. At the municipal tariff the system does not pay for itself, and the interface says "
          "this in a warning rather than a footnote."),

    ("fig", "fig8_cost.png", "Fig. 7.  Cost-benefit tab. The warning states the tariff assumption and the "
                             "break-even condition instead of hiding a negative result.", 2.95),

    ("p", "The picture changes with the counterfactual. Where the alternative is tanker water at INR 150 to 200 per "
          "kilolitre, the same system repays in roughly ten years; the API exposes the tariff as an input for "
          "exactly this reason. This is the single most important thing the model communicates. The economics of "
          "rooftop harvesting in Indian cities are decided by what the water would otherwise cost, not by roof area "
          "or by rainfall."),

    ("h2", "E. Software Verification"),
    ("p", "All 38 back-end tests pass, including the API round trip, the PDF text extraction, and the Devanagari "
          "shaping test that checks a Marathi location name survives into the exported document. The front end "
          "builds without errors and emits eight static pages. The reference assessment is reproducible from a "
          "single seeded request, and the values in this paper were read from that response rather than copied from "
          "an earlier draft."),

    ("h1", "VI. DISCUSSION"),
    ("h2", "A. What the Payback Really Says"),
    ("p", "A 60-year payback looks like a failed project, and it would be dishonest to present it any other way. But "
          "the calculation is sensitive to one input and almost nothing else. Doubling the tariff halves the payback; "
          "including a recharge credit priced at the marginal cost of groundwater rather than 20 percent of the "
          "tariff changes it again. The tool therefore reports the break-even tariff next to the payback, which "
          "converts a verdict into a question: at what price of water does this become worth building? For a housing "
          "society buying tankers in May, the answer is usually yes. For a household on a subsidised municipal "
          "connection, it is usually no, and the money is better spent on a smaller pit that addresses recharge and "
          "flooding rather than storage."),

    ("h2", "B. Limits of the Model"),
    ("p", "Four limitations should be read alongside the results. First, applying a daily curve number to monthly "
          "totals is approximate; a proper event-based model would need sub-daily rainfall, which is not available at "
          "the 2.5 degree resolution of the archive [18], since it stores monthly means only [19]. Second, the grid "
          "cannot resolve intra-city variation, so the local annual total matters more "
          "than the interpolated monthly shape. Third, the cost model uses fixed unit rates that will date quickly "
          "and vary by city; they are inputs, not constants, but the defaults are Pune-specific. Fourth, and most "
          "importantly, none of this has been checked against a built system. The model predicts 24.5 kL of recharge "
          "for the reference building; whether a 1.5-metre pit actually delivers that depends on the percolation "
          "test we did not run. A monitored installation is the obvious next step, and we would rather state that "
          "than imply a validation we do not have."),

    ("h2", "C. Where the Tool Fits"),
    ("p", "The system is not a substitute for a hydrogeologist or a structural engineer. It is a way to make the "
          "first conversation concrete. A society can arrive at a consultant with a computed yield, a ranked list of "
          "structures, a capital estimate and a stated payback, and the consultant can challenge specific numbers "
          "instead of starting from a blank sheet. The same argument applies to the reporting layer: a Marathi PDF "
          "with the assumptions printed on page five is more useful to a ward committee than an English spreadsheet. "
          "Groundwater levels in Maharashtra are published every year [20], and a report that cites them is easier to "
          "place in front of a regulator than a number with no provenance."),

    ("h1", "VII. CONCLUSION"),
    ("p", "We built a decision-support pipeline that takes a rooftop and a location and returns a costed, ranked, "
          "explainable recommendation, and we reported what it produced without adjusting the inputs to make the "
          "story neater. The engineering claims are modest: two runoff models that agree to within four percent "
          "annually and disagree where it matters monthly, an AHP ranking with a consistency ratio of 0.015, and a "
          "reporting pipeline that renders Devanagari correctly. The substantive finding is economic. Rooftop "
          "harvesting in Pune does not repay its capital at the municipal tariff, and it does at the tanker price; "
          "the tool makes that difference visible instead of burying it."),

    ("p", "Work in progress follows directly from the limitations. We are adding a percolation-test input so the "
          "recharge estimate can be anchored to a measurement rather than a soil class, a rainfall time series "
          "option for tank-sizing with reliability curves, and a monitored pilot building to compare predicted and "
          "observed recharge over one monsoon. On the software side, the next step is a batch mode for a housing "
          "society or a ward, since the interesting questions at that scale are about aggregate yield and shared "
          "infrastructure rather than one roof."),

    ("h1", "ACKNOWLEDGMENT"),
    ("p", "The authors thank the Department of Information Technology at JSPM's Rajarshi Shahu College of "
          "Engineering for laboratory access and review time, and the open-source communities behind FastAPI, "
          "Next.js, ReportLab, HarfBuzz and the public NOAA PSL gridded precipitation archive, whose documentation "
          "made a reproducible implementation possible."),

    ("h1", "REFERENCES"),
    ("refs", [
        "USDA Natural Resources Conservation Service, Urban Hydrology for Small Watersheds, Technical Release 55, "
        "2nd ed., Washington, DC, USA, 1986.",

        "Q.-O. Lu, R. Bahramloo, J. Rodrigo-Comino, J. Wang, A. Talebi, Q. T. P. Tran, A. Ghahramani, and M. Sepehri, "
        "\u201cEvaluating the impact of roof rainwater harvesting on hydrological connectivity and urban flood "
        "mitigation,\u201d Results Eng., vol. 25, Art. no. 104022, 2025, doi: 10.1016/j.rineng.2025.104022.",

        "D. Hari and R. R. Kasa, \u201cA geospatial approach for rooftop rainwater harvesting potential in Hyderabad "
        "City, Telangana, India,\u201d Grassroots J. Nat. Resour., vol. 8, no. 2, pp. 701\u2013716, 2025, "
        "doi: 10.33002/nr2581.6853.080233.",

        "P. Xie and P. A. Arkin, \u201cGlobal precipitation: A 17-year monthly analysis based on gauge observations, "
        "satellite estimates, and numerical model outputs,\u201d Bull. Amer. Meteor. Soc., vol. 78, no. 11, "
        "pp. 2539\u20132558, 1997.",

        "P. Preeti and A. Rahman, \u201cApplication of GIS in rainwater harvesting research: A scoping review,\u201d "
        "Asian J. Water Environ. Pollut., vol. 18, no. 4, pp. 29\u201335, 2021.",

        "S. Ali, Y.-F. Sang, F. Pilla, V. P. Singh, and A. Dilawar, \u201cImplementing urban rainwater harvesting "
        "systems: Multiple potential performances, barriers, challenges, solutions, and future perspectives,\u201d "
        "Renew. Sustain. Energy Rev., vol. 218, Art. no. 115793, 2025.",

        "T. L. Saaty, The Analytic Hierarchy Process. New York, NY, USA: McGraw-Hill, 1980.",

        "N. Doorn, \u201cArtificial intelligence in the water domain: Opportunities for responsible use,\u201d Sci. "
        "Total Environ., vol. 755, Art. no. 142561, 2021, doi: 10.1016/j.scitotenv.2020.142561.",

        "L. H. Hansen, P. Fleck, M. Stranner, D. Schmalstieg, and C. Arth, \u201cAugmented reality for subsurface "
        "utility engineering, revisited,\u201d IEEE Trans. Vis. Comput. Graph., vol. 27, no. 11, "
        "pp. 4119\u20134128, 2021.",

        "Central Ground Water Board, Manual on Artificial Recharge of Groundwater. New Delhi, India: Ministry of "
        "Water Resources, Government of India, 2007.",

        "Bureau of Indian Standards, Roof Top Rain Water Harvesting, IS 15797:2008, New Delhi, India, 2008.",

        "Pydantic Developers, \u201cPydantic v2 documentation,\u201d 2024. [Online]. Available: "
        "https://docs.pydantic.dev",

        "Vercel Inc., \u201cNext.js 14 App Router documentation,\u201d 2024. [Online]. Available: "
        "https://nextjs.org/docs",

        "OpenStreetMap contributors, \u201cOpenStreetMap and Nominatim geographic data services,\u201d 2026. "
        "[Online]. Available: https://www.openstreetmap.org",

        "W3C Immersive Web Working Group, \u201cWebXR Device API,\u201d 2024. [Online]. Available: "
        "https://immersive-web.github.io/webxr/",

        "ReportLab Inc., \u201cReportLab PDF toolkit user guide, version 4.2,\u201d 2024. [Online]. Available: "
        "https://www.reportlab.com/docs/reportlab-userguide.pdf",

        "HarfBuzz Project, \u201cHarfBuzz text shaping engine documentation,\u201d 2024. [Online]. Available: "
        "https://harfbuzz.github.io",

        "India Meteorological Department, Yearly Gridded Rainfall Data, Climate Research Services, Pune, India, "
        "2024.",

        "NOAA Physical Sciences Laboratory, \u201cCPC Merged Analysis of Precipitation monthly climatology, "
        "1991\u20132020,\u201d public domain dataset. [Online]. Available: https://psl.noaa.gov",

        "Central Ground Water Board, Ground Water Year Book of Maharashtra. New Delhi, India: Ministry of Jal "
        "Shakti, 2023.",
    ]),
]