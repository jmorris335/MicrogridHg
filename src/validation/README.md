The microgrid is a general purpose model, it was validated by incorporating 
information from an experimental microgrid setup and run in Monterey, California
at the Naval Postgraduate School by [Richard Alves](https://orcid.org/0009-0003-4150-5961)
and [Douglas Van Bossuyt](https://orcid.org/0000-0001-9910-371X). This setup is 
known as the Spanagel Rooftop Microgrid.

The data from this testrun was collected in 2025 and is available both in the 
CSV file in the repository as well as via DOI: [10.5281/zenodo.15675037](https://doi.org/10.5281/zenodo.15675037).

The specific configuration of the microgrid model to match the experimental setup
constitutes a digital twin, and is given in `spanagel_hg.py`, which differs mildly
from the more general constraint hypergraph given in `microgrid.py`.

Running the `validation_caller.py` script from the `src` directory allows you to 
query the Spanagel digital twin. The main plot should look something like this:

<h2 align="center">
<img src="https://github.com/jmorris335/MicrogridHg/blob/421d0f69edf06eab1c873b4258261d1613d04c0f/media/validation_study.png" width="800">
</h2>