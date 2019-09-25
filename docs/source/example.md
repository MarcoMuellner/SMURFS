#1) Smurfs embedded in code

The core of SMURFS consists of three classes: 
* ```smurfs.Smurfs```
    * Point of entry for SMURFS
* ```smurfs.FFinder```
    * Performs the frequency extraction
* ```smurfs.Frequency```
    * Represents a single extracted frequency
    
## 1.1 ```smurfs.Smurfs```
The ```Smurfs``` class is the entry point and you need to instantiate an object to start the analysis. You have three
different input options for ```Smurfs```:
* ```target_name```: The name or identifier of a star that has been observed by either of the TESS/Kepler/K2 missions.
It is also possible to choose PDCSAP/SAP flux through the ```flux_type``` parameter.
If no pre-processed light curves for this target are available on MAST, it will try to extract a light curve from the 
TESS FFIs. If this is the case, the code will also generate a validation page in the results, containing the cutout 
from the ccd, the original as well as the reduced light curve. The code also automatically subtracts the mean of the 
flux and converts the electron counts to magnitude.
* ```file```: The path to a file containing the light curve. The data is read from this file and then reduced by 
subtracting the mean and converting to magnitude.
* ```time``` and ```flux```: You can also directly pass time and flux columns. No further reduction of the data is 
done when using this mode.

In general, SMURFS expects a light curve as an input, measured in electron counts. For files and downloads, this 
conversion is done automatically.

You can also pass a name to the ```label``` parameter. If you set this, the label is used throughout the code and will
save the data under this label.

After creating an instance of the class, you can start the frequency extraction using the ```run``` method.
```python
from smurfs import Smurfs
s = Smurfs(target_name='Gamma Doradus')
s.run(4,2)
``` 
The first parameter in the call is the signal to noise ratio (SNR), the second the window size. 
This will start ```FFinder.run```, which extracts frequencies in order of power until one is below the SNR. You can 
extend this behaviour by settings the ```extend_frequencies``` parameter. So by setting ```extend_frequencies=5``` 
, the extraction will only stop after 5 consecutive frequencies below the SNR have been found. 

You can also restrict the extraction to a certain frequency range, by setting ```f_min``` and/or ```f_max```. The 
extraction will also stop after 10 frequencies with a standard deviation below 0.05 have been found. This behaviour can 
be overwritten by either setting ```similar_chancel=False``` or ```skip_similar=True``` (setting this, will make 
Smurfs ignore these regions.).

Below you can find a set of examples, that show
the usage of Smurfs within a Python script. We use notebooks as examples,
but they can just be as easily included in Python scripts.

## Example 1: Analysing a TESS SC light curve

```eval_rst
.. raw:: html
   :file: Example_1_TESS.html
```