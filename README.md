# Enabling Material Flow Analysis in Disassembly Systems using Object-Centric Process Mining

## Table of Contents
- [Contact](#contact)
- [Introduction](#introduction)
- [Resources](#resources)
- [Usage Instructions](#usage-instructions)
- [Citation](#citation)
- [License](#license)


## Contact
Patrick Jordan: patrick.jordan@iwb.tum.de  


### Useful Links
- **[Visit our other repositories](https://iwb.github.io)**  
Explore more tools and resources from our research institute.

- **[Visit our institute for more information](https://www.mec.ed.tum.de/en/iwb/homepage/)**  
Learn more about our research and ongoing projects.


## Introduction
This repository provides a comprehensive simulation framework and procedure for enabling the material flow analysis in disassembly systems through object-centric process mining (OCPM). The methodology addresses the challenge of analyzing highly variable and complex material flows in disassembly processes, where traditional process mining approaches fail to capture the relationships between multiple objects.

The repository includes:
1. **Disassembly Simulation Framework**: Python-based implementation for simulating disassembly processes of electric vehicles with different condition scenarios.
2. **OCEL Generation Module**: Automated generation of Object-Centric Event Logs (OCEL 2.0) from disassembly data.
3. **Visualization Tool**: Cytoscape-based visualization of material flows and process graphs.


### Related Research Work
The simulation framework is part of the research published in the following article:

**"Enabling the material flow analysis in disassembly systems using object-centric process mining"**  
*Patrick Jordan, Daniel Piendl, Sebastian Kroeger, Lasse Streibel, Christoph Haider, Michael F. Zaeh*
Proceedings of the 58th CIRP Conference on Manufacturing Systems 2025

[For more details, please refer to the published article (Link)](https://doi.org/10.1016/j.procir.2025.03.019)  

### Abstract
The growing importance of sustainable manufacturing highlights the need for disassembly systems, which enable the reuse of high-quality components from end-of-life (EOL) products. However, the economical viability of disassembly is often constrained by high costs, especially with increased disassembly depth. This repository provides a Python-based simulation framework and toolkit for analyzing material flows in disassembly systems using Object-Centric Process Mining (OCPM). The framework enables users to simulate the disassembly of electric vehicles under various condition scenarios, automatically generate Object-Centric Event Logs (OCEL 2.0), and visualize complex material flows through interactive process graphs. The toolkit addresses the challenge of analyzing highly variable disassembly processes where traditional process mining fails to capture the complex relationships between multiple objects. By providing transparent material flow analysis, the framework supports decision-making on optimal disassembly depths and resource allocation. The repository includes complete source code, example implementations, and documentation for both researchers and practitioners working on circular economy applications in manufacturing.

### Acknowledgements
This research was funded by the Federal Ministry of Economic Affairs and Climate Action (BMWK) as part of the "Car2Car" project (19S22007H).


## Resources
### 1. Disassembly Simulation Framework
The Python framework simulates the disassembly of electric vehicles under different condition scenarios:
- **Car Factory Module** (`car.py`): Creates car components with configurable conditions (Target Disassembly, Motor Damage, Damper Damage)
- **Disassembly Car Module** (`car.py`): Simulates step-by-step disassembly processes with resource allocation
- **Event Generation**: Automatically generates events with timestamps, components, and resource relationships

**Features (of example use case):**
- Three condition scenarios: Target Disassembly (TD), Motor Damage (MD), Damper Damage (DD)
- Configurable disassembly sequences and resource assignments (Resources S1-S5 mapped to workstations ws1-ws5)
- Component hierarchy modeling (products, assemblies, parts)
- Process time simulation based on car model specifications
- Eleven disassembly steps (d1-d11) with specific duration mappings

### 2. OCEL Generation Module
The OCEL module (`ocel.py`) converts disassembly simulation data into OCEL 2.0 compliant logs:
- **Data Transformation**: Converts events and objects tables into OCEL JSON format
- **Relationship Mapping**: Preserves event-to-object and object-to-object relationships
- **Attribute Handling**: Includes component conditions and hierarchical relationships
- **Standards Compliance**: Fully compatible with OCEL 2.0 specification

### 3. Visualization Tool
The visualization module (`visualization.py`) provides interactive process graphs:
- **Cytoscape Integration**: Web-based interactive graph visualization using Dash-Cytoscape
- **Material Flow Display**: Visual representation of component flows through workstations
- **Process Discovery**: Automated discovery of process patterns from OCEL data
- **Export Capabilities**: Save visualizations as JPG, PNG, or SVG formats
- **Position Saving**: Node positions are saved to `node_positions.json` for consistent layouts


## Usage Instructions
### Prerequisites
- Python 3.11 or higher
- Required packages (install via `pip install -r requirements.txt`):
  - pandas
  - numpy
  - dash
  - dash-cytoscape


### Quick Start
**1. Clone the repository**
```bash
git clone https://github.com/iwb/ce-ocel-material-flow-analysis.git
cd ce-ocel-material-flow-analysis
```

**2. Create a virtual environment (optional but recommended)**
```bash
python -m venv .venv
```

**3. Activate the virtual environment**
- On Windows:
```bash
.\.venv\Scripts\activate
```
- On macOS/Linux:
```bash
source .venv/bin/activate
```

**4. Install dependencies**
```bash
pip install -r requirements.txt
```

**5. Install local package**
```bash
pip install -e .
```

**6. Run the simulation**
```bash
cd scripts
python main.py
```

This will:
- Generate simulated disassembly data for 120 car instances (70 TD, 30 MD, 20 DD)
- Create an OCEL file in `scripts/temp/ocel.json`
- Launch the visualization dashboard (opens in browser)


### Detailed Usage / Working with Your Own Data
To use the framework with your own disassembly data:

**1. Define your product conditions** in `car.py`:
```python
class Condition(base.Condition):
    TD = "Target Disassembly"
    DD = "Damper Damage"
    MD = "Motor Damage"
    # Add your custom conditions here
```


**2. Define your resources** in `car.py`: 
```python
class Resource(base.Resource):
    S1 = "ws1"  # Workstation 1
    S2 = "ws2"  # Workstation 2
    # Add your resources here
    S66 = "ws66"  # New workstation 
```


**3. Define your disassembly steps** in `car.py`:
```python
class EventType(base.EventType):
    SPOIL_CAR = "d1"
    BODY_CHASSIS_SEPARATION = "d2"
    # Add your disassembly steps here
    NEW_COMPONENT_REMOVAL = "d99"

# Map durations for each car model
car_model_to_duration_map = {
    CarModel.A: {
        EventType.SPOIL_CAR: 180,  # seconds
        EventType.BODY_CHASSIS_SEPARATION: 120,
        # Add durations for your steps
    }
}


# In car_factory:
# Define new components
new_component = Component("comp123", condition, car_number)
# Attach new component to existing car
front_chassis.install_component(new_component)

# In disassemble_car:
# Add dissambly step, potentially also considering the car condition
output_objects, event = disassembly_step(
    event_number, EventType.NEW_COMPONENT_REMOVAL, event.end_time, front_chassis, ["comp123"], Resource.S66, "aX"
)
```


#### Advanced Features
- Custom Condition Scenarios: Extend the `Condition` enum in `car.py`
- New Car Models: Add entries to `car_model_to_duration_map` and `CarModel`
- Custom Components: Modify `car_factory()` to add new component types
- Alternative Process Mining Analysis: Use generated OCEL with pm4py or OCPM.info for alternative analytics


## Citation
If you use this repository or the tools for your research or industry projects, please cite the following article:

```bibtex
@article{JORDAN2025271,
title = {Enabling the material flow analysis in disassembly systems using object-centric process mining},
journal = {Procedia CIRP},
volume = {134},
pages = {271-276},
year = {2025},
note = {58th CIRP Conference on Manufacturing Systems 2025},
issn = {2212-8271},
doi = {https://doi.org/10.1016/j.procir.2025.03.019},
url = {https://www.sciencedirect.com/science/article/pii/S2212827125004809},
author = {Patrick Jordan and Daniel Piendl and Sebastian Kroeger and Lasse Streibel and Christoph Haider and Michael F. Zaeh}
}
```


## License
This repository and its contents are licensed under the [MIT License](./LICENSE).

---
For questions, suggestions, or collaboration opportunities, please contact the corresponding author or visit our [institute website](https://www.mec.ed.tum.de/en/iwb/homepage/).
