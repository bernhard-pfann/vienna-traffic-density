# MODELING TRAFFIC-DENSTIY OF THE CITY OF VIENNA

In this project I attempt to model the traffic-density for the City of Vienna solely based on publicly available data.<br><br>

#### Data Sources
- <b>Road network:</b> The official road network from (https://www.data.gv.at/) consists of information on ~30000 street segments and its respective geolocation and street-type.
- <b>Uber rides:</b> Information on Uber rides per City can be accessed at (https://movement.uber.com/). Uber is splitting the City of Vienna into 1370 subdistricts where travel-time between these starting & ending-areas is reported. Additional categorical information about weekdays or time of the day are available.

#### Approach
<b>Part 1: Simulating Paths</b>
<ul>
    <li>Initialize a network graph consisting of all recorded streets of the City of Vienna</li>
    <li>Map maximum speed-limit to each network edge dependent on its street-type</li>
    <li>Calculate the shortest path of streets between pairs of start/end-nodes in the network</li>
    <li>Collect shortest path information for every start/end combination observed in the set of Uber rides</li>
</ul>

<b>Part 2: Constrained Optimization</b>
<ul>
    <li>Frame a constrained optimiziation problem to estimate a "traffic-coefficient" per each area, representing its traffic-density</li>
    <li>Analyze traffic-density per area during different times of the day</li>
</ul>
    
#### Project Structure
Recalculation of all results can be executed by running "calc-paths.ipynb" to simluate all path information. After that, "optimize.ipynb" can be executed to fit optimal coefficients for each area. Following custom modules are called in the background:
- data_streets.py --> 
- data_areas.py -->
- data_uber.py
- street_network.py -->

<br>
## PART 1: Simulating Paths
### Road-Network
The official road network consists of ~30000 street segments. Each respective geolocation, node-connectivity, as well as street-type are provided.
<p align="center"> <img src="https://github.com/bernhard-pfann/vienna-traffic-density/blob/main/img/network-by-type.png" width="800"></p>

### Areas
Uber is splitting the City of Vienna into 1370 geospacial polygons where travel-time between these starting & ending-areas is reported. Therefore it is necessary to map each network node to its respective area. 
<p align="center"> <img src="https://github.com/bernhard-pfann/vienna-traffic-density/blob/main/img/shapes.png" width="800"></p>

### Shortest-Path
After successfully mapping area information, the shortest path between any pair of nodes/areas can be obtained. The networkx library provides the algorithm the calcuate this optimal path based on meter-distance or max. speed limits per street.
<p align="center"> <img src="https://github.com/bernhard-pfann/vienna-traffic-density/blob/main/img/path-areas.png" width="800"></p>

## PART 2: Constrained Optimization
### Estimating Coefficients
By multiplying traveled-distance per area with a area-specific parameter, the actual Uber-travel-time can be fitted by a function. The parameters are thereby constrained to sensbile values that translate to range between 5 - 120 km/h.
<p align="center"> <img src="https://github.com/bernhard-pfann/vienna-traffic-density/blob/main/img/coefs-distribution-allday.gif" width="800"></p>
<p align="center"> <img src="https://github.com/bernhard-pfann/vienna-traffic-density/blob/main/img/coefs-map-allday.png" width="800"></p>

### Scenario Analysis

<p align="center"> <img src="https://github.com/bernhard-pfann/vienna-traffic-density/blob/main/img/coefs-distribution-scenarios.png" width="800"></p>
