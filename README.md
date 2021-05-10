# MODELING TRAFFIC-DENSTIY OF THE CITY OF VIENNA

In this project I attempt to model the traffic-density for the City of Vienna solely based on publicly available data.<br><br>

### Data Sources
- <b>Road network:</b> The official road network from (https://www.data.gv.at/) consists of information on ~30000 street segments and its respective geolocation and street-type.
- <b>Uber rides:</b> Information on Uber rides per City can be accessed at (https://movement.uber.com/). Uber is splitting the City of Vienna into 1370 subdistricts where travel-time between these starting & ending-areas is reported. Additional categorical information about weekdays or time of the day are available.

### Approach
<b>Part 1: Simulating Paths</b>
<ul>
    <li>Initialize a network graph consisting of all recorded streets of the City of Vienna</li>
    <li>Map maximum speed-limit to each network edge dependent on its street-type</li>
    <li>Calculate the shortest path of streets between pairs of start/end-nodes in the network</li>
    <li>Collect shortest path information for every start/end combination observed in the set of Uber rides</li>
</ul>

<b>Part 2: Constrained Optimization</b>
<ul>
    <li>Frame a constrained optimiziation problem to derive a "traffic-coefficient" per each area, representing its traffic-density</li>
    <li>Analyze traffic-density per area during different times of the day</li>
    
### A2. Project Structure
The script can be executed via "main.ipynb" and thereby calls custom modules:
- yieldcurves.py --> Cleaning of raw input put from source
- principalcomponents.py --> Object class that conducts all transformations of PCs
- autoregressive.py --> Object class fits a time series model and returns predictions, based on a simple autoregressive-process
   
### Road-Network

<p align="center"> <img src="https://github.com/bernhard-pfann/vienna-traffic-density/blob/main/img/network-by-type.png"></p>

### Areas
The Uber defined areas

### Shortest-Path

### Constrained Optimization

### Scenario Analysis
