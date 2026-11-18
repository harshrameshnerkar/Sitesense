"""
Generates 20 Company Safety Policies and 10 Safety Handbooks in both Markdown and PDF format.
These documents represent realistic industrial warehouse compliance standards that will be ingested
and retrieved by the SiteSense RAG engine and evaluated against real-world warehouse imagery.
"""

import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

POLICIES = [
    {
        "id": "POL-001",
        "title": "Pedestrian Walkway and Egress Route Clearances",
        "clause": "Clause 1.2: Egress Route Clearances",
        "category": "Egress & Facility Traffic",
        "content": (
            "1. Objective & Scope: To ensure all pedestrian thoroughfares and emergency exit pathways remain 100% unobstructed.\n"
            "2. Standards: All designated pedestrian walkways marked with yellow or reflective epoxy floor striping must maintain a minimum clear width of 1.2 meters (48 inches) at all times.\n"
            "3. Strict Prohibitions: No temporary or permanent staging of wooden pallets, corrugated carton boxes, plastic totes, or material handling equipment is permitted inside walkway boundaries under any circumstances.\n"
            "4. Immediate Corrective Action: Any item detected inside a designated walkway must be tagged and relocated to an approved staging bay within 15 minutes of discovery."
        )
    },
    {
        "id": "POL-002",
        "title": "Fire Extinguisher and Suppression Equipment Accessibility",
        "clause": "Clause 2.1: Fire Safety Equipment Access",
        "category": "Fire & Life Safety",
        "content": (
            "1. Objective & Scope: Guarantee immediate access to portable fire extinguishers and suppression control valves.\n"
            "2. Physical Clearance: A minimum clearance radius of 1.0 meter (36 inches) must be maintained around every wall-mounted fire extinguisher, hose station, and fire sprinkler riser valve.\n"
            "3. Floor Demarcation: The floor area below each fire extinguisher must be painted with alternating red and white diagonal safety stripes.\n"
            "4. Prohibited Acts: Storing inventory, leaning ladders, or stacking pallets in front of extinguishers is a Class-A critical safety violation requiring immediate supervisor intervention."
        )
    },
    {
        "id": "POL-003",
        "title": "Mandatory Personal Protective Equipment Protocols",
        "clause": "Clause 3.4: Mandatory Personal Protective Equipment",
        "category": "Personnel Safety",
        "content": (
            "1. Scope: Applies to all employees, contractors, and visitors entering active warehouse operational zones.\n"
            "2. Core Requirements: High-visibility fluorescent vests (ANSI Class 2 minimum) and steel-toe composite safety footwear (ASTM F2413 compliant) are mandatory facility-wide.\n"
            "3. Loading Bay & High-Bay Specifics: Inbound dock areas, high-rack storage aisles, and active forklift corridors require certified industrial safety helmets (hard hats compliant with ANSI Z89.1).\n"
            "4. Enforcement: Personnel observed without required hard hats in loading docks must be halted immediately and escorted to the safety locker station."
        )
    },
    {
        "id": "POL-004",
        "title": "Material Stacking Standards and Pallet Height Limits",
        "clause": "Clause 4.1: Material Stacking Standards",
        "category": "Material Handling",
        "content": (
            "1. Scope: Dictates allowable vertical height and stability criteria for floor-staged unit loads.\n"
            "2. Open Floor Stacking Limit: Palletized goods staged directly on the warehouse floor must not exceed 3 tiers (maximum 2.4 meters / 8 feet in total height).\n"
            "3. Stability Controls: Any pallet stack exceeding tier 1 must be securely shrink-wrapped with corner boards where required. Leaning stacks exceeding 5 degrees vertical tilt are strictly forbidden.\n"
            "4. Heavy Goods: Pallets containing liquids, chemical drums, or loose heavy machinery parts must remain single-tier unless racked in rated steel uprights."
        )
    },
    {
        "id": "POL-005",
        "title": "Forklift and Material Handling Equipment Traffic Segregation",
        "clause": "Clause 5.1: MHE Traffic Segregation",
        "category": "Equipment Operations",
        "content": (
            "1. Segregation Rules: Forklifts, order pickers, and reach trucks must operate strictly in designated vehicle travel lanes marked with blue safety lines.\n"
            "2. Pedestrian Buffer: Operators must maintain a minimum 3.0-meter (10 feet) safe operating buffer from any pedestrian walking in shared staging zones.\n"
            "3. Speed Limits: Maximum speed within enclosed warehouse aisles is 8 km/h (5 mph); loading dock threshold speed is 3 km/h (2 mph).\n"
            "4. Blind Corner Protocol: Operators must sound their horn and come to a complete rolling stop at all blind T-junctions and corridor entrances."
        )
    },
    {
        "id": "POL-006",
        "title": "Hazardous Chemical Spill Containment and Emergency Response",
        "clause": "Clause 6.2: Hazardous Fluid Spill Response",
        "category": "Environmental & Chemical",
        "content": (
            "1. Immediate Notification: Any liquid spill exceeding 1 liter of chemical, solvent, hydraulic fluid, or fuel requires immediate evacuation of the affected aisle.\n"
            "2. Spill Kit Deployment: Universal absorbent socks, pads, and non-sparking scoops must be deployed within 5 minutes of identification.\n"
            "3. PPE for Cleanup: Spill response personnel must wear nitrile chemical-resistant gauntlets, splash goggles, and half-face respirators with organic vapor cartridges.\n"
            "4. Disposal: Spent absorbent materials must be sealed in yellow hazardous waste recovery drums with completed manifests."
        )
    },
    {
        "id": "POL-007",
        "title": "Emergency Exit Door Operations and Illuminated Signage",
        "clause": "Clause 7.1: Emergency Exit Integrity",
        "category": "Life Safety & Egress",
        "content": (
            "1. Exit Door Standards: All designated emergency fire exits must feature panic hardware (crash bars) that open outward with less than 15 pounds of pushing force.\n"
            "2. Zero Obstruction: A clear, unencumbered space of 2.0 meters on both sides of every exit door is legally mandated. No wedging or propping doors open.\n"
            "3. Illumination: Overhead EXIT signs must remain continuously illuminated with 90-minute battery backup power in event of main electrical failure.\n"
            "4. Auditing: Daily visual verification of exit door swing paths is conducted by the morning shift supervisor."
        )
    },
    {
        "id": "POL-008",
        "title": "Loading Dock Safety, Levelers and Wheel Chocking Mandates",
        "clause": "Clause 8.3: Dock Safety & Chocking",
        "category": "Dock Logistics",
        "content": (
            "1. Vehicle Restraint: Semi-trailers backed into loading bays 1 through 8 must have automated dock lock restraints engaged or dual rubber wheel chocks positioned.\n"
            "2. Dock Leveler Operation: Hydraulic dock levelers must be inspected for lip engagement before any forklift or hand truck traverses the trailer threshold plate.\n"
            "3. Fall Protection: Dock bay doors that remain open without a trailer docked must have the yellow high-visibility safety barrier chain securely latched across the opening.\n"
            "4. Driver Staging: Truck drivers must wait in the designated driver safety lounge and surrender trailer keys during all unloading cycles."
        )
    },
    {
        "id": "POL-009",
        "title": "Structural Racking Integrity and Load Limit Placards",
        "clause": "Clause 9.1: Pallet Racking Integrity",
        "category": "Structural Engineering",
        "content": (
            "1. Load Capacities: Every selective pallet racking bay must feature visible yellow load capacity placards specifying maximum allowable weight per beam pair (e.g. 2,500 kg).\n"
            "2. Damage Criteria: Any rack upright exhibiting deflection greater than 3 mm across a 1-meter span from forklift impact must be tagged with a RED out-of-service placard.\n"
            "3. Unloading Mandate: Damaged racking bays must be completely depalletized within 2 hours of structural damage discovery.\n"
            "4. Beam Safety Pins: Every beam connection must have safety locking pins engaged to prevent accidental dislodgement during pallet lifting."
        )
    },
    {
        "id": "POL-010",
        "title": "Electrical Service Panel and Switchgear Clearance Standards",
        "clause": "Clause 10.2: Electrical Equipment Clearances",
        "category": "Electrical Safety",
        "content": (
            "1. OSHA 1910.303 Compliance: All electrical breaker panels, transformers, and motor disconnect switches require a minimum 36-inch (91 cm) deep, unobstructed frontal clearance zone.\n"
            "2. Floor Striping: Electrical clearance zones must be bounded by yellow safety paint on the warehouse floor with the warning 'ELECTRICAL PANEL - KEEP CLEAR AT ALL TIMES'.\n"
            "3. Staging Ban: No pallets, rolling carts, waste bins, or cleaning equipment may rest inside this envelope, even momentarily.\n"
            "4. Qualified Personnel: Only licensed electrician contractors or certified maintenance engineers may open energized switchgear enclosures."
        )
    },
    {
        "id": "POL-011",
        "title": "Overhead Conveyor Systems and Nip-Point Safety Guarding",
        "clause": "Clause 11.1: Mechanical Conveyor Safety",
        "category": "Machinery Guarding",
        "content": (
            "1. Guarding: All chain drives, rollers, and belt pinch points along automated package sorting lines must be fitted with fixed metal mesh safety guards.\n"
            "2. Emergency Stops: Continuous emergency pull cords (e-stop cables) must run the entire length of overhead conveyor lines within reach of floor personnel.\n"
            "3. De-jamming Protocol: Under no circumstances may an employee reach into a running conveyor to dislodge cartons. Lockout/Tagout (LOTO) is mandatory before jam clearing.\n"
            "4. Overhead Nets: Conveyors traversing pedestrian walkways must have side containment netting to catch falling packages."
        )
    },
    {
        "id": "POL-012",
        "title": "Inbound Trailer Security Seals and Freight Discrepancy Audits",
        "clause": "Clause 12.4: Inbound Freight Seal Verification",
        "category": "Logistics & Compliance",
        "content": (
            "1. Seal Inspection: Before cutting any inbound trailer bolt seal, the receiving clerk must photograph the seal and verify the numeric identifier against the bill of lading.\n"
            "2. Broken or Missing Seals: Any trailer arriving with a broken, missing, or mismatched seal must not be unloaded until an EHS supervisor and security lead conduct an audit.\n"
            "3. Manifest Comparison: Declared pallet count and hazardous cargo designations must be validated against the physical load before issuing receipt signatures.\n"
            "4. Retention: Seal audit photos and paperwork manifests are archived in the digital document repository for 12 months."
        )
    },
    {
        "id": "POL-013",
        "title": "Industrial Battery Charging Station Ventilation and Safety",
        "clause": "Clause 13.1: Battery Charging Safety",
        "category": "Battery Operations",
        "content": (
            "1. Ventilation: Lead-acid and lithium forklift battery charging zones must feature continuous active exhaust fans to prevent hydrogen gas accumulation (>1% lower explosive limit).\n"
            "2. Eyewash Proximity: An OSHA-approved emergency eyewash station capable of 15-minute continuous flushing must be located within 25 feet (7.6 meters) of all charging bays.\n"
            "3. PPE Requirements: Personnel handling battery electrolyte must wear a rubber apron, face shield, and chemical-resistant neoprene gauntlets.\n"
            "4. No Open Flames: Smoking, welding, and non-intrinsically safe electrical devices are strictly prohibited within a 10-meter radius of the charging room."
        )
    },
    {
        "id": "POL-014",
        "title": "Defective Pallet Quarantine and Disposal Standards",
        "clause": "Clause 14.2: Defective Pallet Quarantine",
        "category": "Asset Management",
        "content": (
            "1. Inspection Criteria: Pallets exhibiting cracked deck boards, broken stringers, protruding nails, or severe oil contamination must be taken out of service immediately.\n"
            "2. Designated Quarantine: Defective units must be moved to the designated 'Pallet Quarantine Corral' located near Bay 12 and tagged with a fluorescent orange notice.\n"
            "3. Stacking for Disposal: Quarantine pallets may be stacked up to a maximum of 15 units high in a stable interlocking pattern awaiting timber recycler pickup.\n"
            "4. Reuse Prohibition: Re-introducing quarantined pallets into high-bay automated racking is grounds for disciplinary review."
        )
    },
    {
        "id": "POL-015",
        "title": "Combustible Waste and Packaging Rubbish Accumulation Control",
        "clause": "Clause 15.3: Combustible Material Housekeeping",
        "category": "Housekeeping & Fire",
        "content": (
            "1. Daily Housekeeping: Discarded shrink wrap, corrugated cardboard scrap, wooden dunnage, and broken strapping bands must not accumulate in operating aisles.\n"
            "2. Baler Operations: Cardboard and clean plastic film must be transferred to the pneumatic balers at least twice per 8-hour shift.\n"
            "3. Fire Risk Mitigation: Accumulation of combustible packaging within 5 meters of electrical panels or charging stations is classified as a severe fire hazard.\n"
            "4. End-of-Shift Signoff: Shift supervisors must walk all picking aisles and certify 100% floor clearance before handing over facility custody."
        )
    },
    {
        "id": "POL-016",
        "title": "Emergency Eyewash and Safety Shower Maintenance Protocols",
        "clause": "Clause 16.1: Eyewash & Safety Showers",
        "category": "Occupational Health",
        "content": (
            "1. Travel Time: Emergency eyewash stations must be accessible within 10 seconds of uninhibited walking from any chemical or battery handling workstation.\n"
            "2. Weekly Inspection: Stations must be activated and flushed weekly for 3 minutes to verify water pressure, clear bacterial growth, and check temperature (16°C to 38°C).\n"
            "3. Unobstructed Path: The pathway to eyewash fixtures must remain completely flat, unencumbered by hoses, cords, or freight.\n"
            "4. Inspection Tagging: A physical laminated inspection tag must be signed and dated by the facility safety technician upon weekly verification."
        )
    },
    {
        "id": "POL-017",
        "title": "Pedestrian Crosswalks and Convex Blind Intersection Mirrors",
        "clause": "Clause 17.2: Crosswalk Right-of-Way",
        "category": "Traffic Management",
        "content": (
            "1. Pedestrian Right of Way: Pedestrians utilizing painted yellow safety crosswalks have absolute right of way over all forklifts, tuggers, and pallet jacks.\n"
            "2. Convex Mirrors: Industrial 36-inch convex mirrors must be installed at all four-way warehouse intersections and maintained free of dust and visual obstruction.\n"
            "3. Stop & Sound: Forklift operators approaching marked crosswalks must decelerate to 3 km/h, tap horn twice, and visually confirm the mirror is clear before proceeding.\n"
            "4. Floor Stenciling: Crosswalk approaches must feature bold white lettering: 'LOOK BOTH WAYS - FORKLIFT TRAFFIC'."
        )
    },
    {
        "id": "POL-018",
        "title": "Cold Storage and Freezer Facility Thermal Safety and Slip Hazards",
        "clause": "Clause 18.4: Cold Storage Safety",
        "category": "Specialized Environments",
        "content": (
            "1. Thermal Gear: Employees entering deep-freeze areas (-20°C to -25°C) must wear certified insulated sub-zero coveralls, thermal boots, and fleece-lined gloves.\n"
            "2. Exposure Limits: No worker may remain continuously inside freezer chambers for more than 90 minutes without a 15-minute warming break in the ambient vestibule.\n"
            "3. Ice & Frost Abatement: Ice buildup on freezer thresholds or walkway ramps must be mechanically scraped and treated with approved calcium chloride pellets daily.\n"
            "4. Emergency Release: All freezer doors must feature luminous internal mechanical emergency push-to-exit plunger latches that cannot be locked from the outside."
        )
    },
    {
        "id": "POL-019",
        "title": "Chemical Drum Secondary Containment Sump Standards",
        "clause": "Clause 19.1: Chemical Drum Storage",
        "category": "Hazardous Materials",
        "content": (
            "1. Secondary Containment: All 55-gallon (208L) drums containing hazardous chemicals, lubricants, or paints must rest on certified polyethylene secondary spill pallets.\n"
            "2. Sump Capacity: The secondary containment sump must have a minimum holding capacity equal to 110% of the single largest drum or 25% of total volume stored.\n"
            "3. Incompatible Materials: Acids and bases, or flammables and oxidizers, must be segregated into distinct containment bays separated by a minimum of 6 meters.\n"
            "4. Inspection Frequency: Sumps must be visually checked daily for fluid collection. Any accumulated rainwater or chemical must be pumped out and disposed of."
        )
    },
    {
        "id": "POL-020",
        "title": "Contractor, Vendor and Visitor Safety Badging and Escort Rules",
        "clause": "Clause 20.3: Visitor & Contractor Badging",
        "category": "Site Security & Governance",
        "content": (
            "1. Check-In & Safety Briefing: All non-badged visitors and third-party maintenance contractors must register at the security desk and complete the 5-minute safety orientation.\n"
            "2. Badging: High-visibility RED contractor visitor badges must be worn conspicuously on outer garments above the waist.\n"
            "3. Mandatory Escorts: Visitors are strictly prohibited from walking onto active logistics warehouse floors without an authorized SiteSense employee escort.\n"
            "4. PPE Provision: The receiving team is responsible for providing compliant hard hats, high-vis vests, and safety glasses to visitors before floor entry."
        )
    }
]

HANDBOOKS = [
    {
        "id": "HBK-001",
        "title": "OSHA General Industry Warehouse Safety Compliance Handbook",
        "code": "OSHA 29 CFR 1910 Standard Operating Procedures",
        "content": (
            "# OSHA General Industry Warehouse Safety Compliance Handbook\n"
            "Standard: 29 CFR 1910 Subpart D (Walking-Working Surfaces) & Subpart N (Materials Handling)\n\n"
            "## Chapter 1: Walking-Working Surfaces (1910.22)\n"
            "All places of employment, passageways, storerooms, and service rooms shall be kept clean, orderly, and in a sanitary condition. Floor surfaces must be kept free from hazards such as sharp objects, loose boards, spills, and protruding obstacles. Permanent aisles and passageways must be clearly demarcated with painted striping.\n\n"
            "## Chapter 2: Means of Egress (1910.36)\n"
            "Exit routes must remain unobstructed at all times. Exit paths must not lead through rooms or areas that can be locked or through spaces that contain hazardous storage. Maintenance of fire resistance ratings and visibility of exit signs is mandatory.\n\n"
            "## Chapter 3: Materials Handling and Storage (1910.176)\n"
            "Storage of material shall not create a hazard. Bags, containers, bundles, etc., stored in tiers shall be stacked, blocked, interlocked, and limited in height so that they are stable and secure against sliding or collapse. Aisles and passageways shall be kept clear with no obstructions across doorways."
        )
    },
    {
        "id": "HBK-002",
        "title": "ISO 45001 Occupational Health and Safety Management System Manual",
        "code": "ISO 45001:2018 Management Code",
        "content": (
            "# ISO 45001 Occupational Health & Safety Management Manual\n"
            "Clause 8: Operational Planning and Control\n\n"
            "## 8.1.2 Eliminating Hazards and Reducing OH&S Risks\n"
            "The organization must establish, implement, and maintain a process for the elimination of hazards and reduction of OH&S risks using the hierarchy of controls: Elimination, Substitution, Engineering Controls, Administrative Controls, and Personal Protective Equipment.\n\n"
            "## 8.2 Emergency Preparedness and Response\n"
            "The organization must maintain structured readiness for potential emergency scenarios, including structural collapse, chemical spills, and fire incidents. Periodic evacuation drills and audit checklists ensure continuous operational compliance."
        )
    },
    {
        "id": "HBK-003",
        "title": "Powered Industrial Trucks Operator Certification & Operational Guide",
        "code": "OSHA 1910.178 & ANSI B56.1",
        "content": (
            "# Powered Industrial Trucks Operator Certification & Operational Guide\n\n"
            "## Section 1: Pre-Shift Inspection Mandate\n"
            "Operators must perform and log a documented pre-shift physical inspection covering hydraulic systems, brakes, steering, horn, backup alarm, and fork condition. Any vehicle with safety deficiencies must be immediately locked out.\n\n"
            "## Section 2: Traveling and Speed Management\n"
            "Loads must be tilted backward and carried as low to the ground as safely possible (4 to 6 inches off floor). When ascending or descending grades in excess of 10 percent, loaded trucks shall be driven with the load upgrade.\n\n"
            "## Section 3: Dockboard and Trailer Safety\n"
            "Prior to driving onto any truck or trailer, operators must visually confirm that the trailer wheels are securely chocked or the automated vehicle restraint system is locked."
        )
    },
    {
        "id": "HBK-004",
        "title": "Comprehensive Facility Emergency Action and Evacuation Plan (EAP)",
        "code": "EAP-2026 Emergency Manual",
        "content": (
            "# Comprehensive Facility Emergency Action and Evacuation Plan (EAP)\n\n"
            "## Part I: Emergency Reporting and Alarm Activation\n"
            "In the event of active fire, structural compromise, or toxic atmospheric release, the discovering employee must pull the nearest manual fire alarm station and dial emergency extension 5555.\n\n"
            "## Part II: Evacuation Protocols\n"
            "All personnel must immediately drop non-essential tasks and exit via the nearest illuminated emergency egress door. Do not use elevators or material lifts. Floor wardens conduct sweep audits of breakrooms and restrooms.\n\n"
            "## Part III: Muster Point Assembly\n"
            "All building occupants assemble at designated Muster Station Alpha (North Gate Parking) or Muster Station Bravo (South Lawn). Roll-call must be finalized within 8 minutes of alarm initiation."
        )
    },
    {
        "id": "HBK-005",
        "title": "Hazard Communication, GHS Labeling, and Safety Data Sheets Standard",
        "code": "29 CFR 1910.1200 HazCom",
        "content": (
            "# Hazard Communication & Chemical Safety Guide\n\n"
            "## 1. Globally Harmonized System (GHS) Labeling\n"
            "All chemical containers, including secondary squeeze bottles and sprayers, must display standardized GHS pictograms, signal words (DANGER or WARNING), hazard statements, and manufacturer contact details.\n\n"
            "## 2. Safety Data Sheet (SDS) Access\n"
            "Digital and physical SDS binders must be accessible 24/7 without password restriction to all warehouse personnel in the EHS kiosk near the shipping office.\n\n"
            "## 3. Chemical Spill Kit Placement\n"
            "Spill response stations equipped with chemical-neutralizing absorbents and PPE must be positioned every 30 meters along chemical staging corridors."
        )
    },
    {
        "id": "HBK-006",
        "title": "Heavy-Duty Pallet Racking Inspection, Maintenance and Load Limits Manual",
        "code": "RMI ANSI MH16.1 Design Code",
        "content": (
            "# Heavy-Duty Pallet Racking Inspection and Maintenance Code\n\n"
            "## Article 1: Structural Inspection Standards\n"
            "Quarterly engineering audits evaluate upright column verticality, diagonal brace damage, and baseplate anchor bolt torque (minimum 65 ft-lbs). Any sheared or loosened anchor requires immediate structural repair.\n\n"
            "## Article 2: Beam Deflection Limits\n"
            "Maximum vertical deflection of horizontal beam pairs under full load must not exceed L/180 of the beam span. Beams exceeding this threshold indicate severe overload and must be depalletized.\n\n"
            "## Article 3: Pallet Overhang Guidelines\n"
            "Standard pallets must have a minimum front-to-back beam overlap of 50 mm (2 inches) on both front and rear beams. Side overhang exceeding 75 mm is strictly prohibited."
        )
    },
    {
        "id": "HBK-007",
        "title": "Freight Receiving, Loading Dock Operations and Yard Safety Handbook",
        "code": "Logistics Yard Operating Manual",
        "content": (
            "# Freight Receiving, Loading Dock Operations & Yard Safety Handbook\n\n"
            "## Section 1: Inbound Yard Traffic Patterns\n"
            "External tractor-trailers must follow the clockwise yard loop at speeds not exceeding 15 km/h. Backing into dock bays must be guided by dock spotters when visibility is limited.\n\n"
            "## Section 2: Dock Door Drop Hazards\n"
            "Unprotected edges of loading docks exceeding 48 inches in height represent significant fall hazards. Warning gates or safety nets must be deployed across any bay opening whenever a trailer is not positioned.\n\n"
            "## Section 3: Material Lift Gate Safety\n"
            "Hydraulic lift gates on delivery box trucks must be fully lowered and flat on concrete before loading personnel or hand trucks roll onto the platform."
        )
    },
    {
        "id": "HBK-008",
        "title": "Industrial Fire Prevention, Hot Work, and Life Safety Code",
        "code": "NFPA 1 & NFPA 13 Compliance Manual",
        "content": (
            "# Industrial Fire Prevention, Hot Work & Life Safety Code\n\n"
            "## Chapter 1: Sprinkler Head Clearance (NFPA 13)\n"
            "A minimum vertical clearance of 18 inches (45 cm) must be maintained below all sprinkler deflectors throughout standard pallet storage. In high-density ESFR storage areas, clearance must be 36 inches.\n\n"
            "## Chapter 2: Hot Work Permitting\n"
            "Any welding, torch cutting, or grinding requires an issued Hot Work Permit signed by the safety supervisor. A dedicated fire watch personnel with a 10-lb ABC extinguisher must monitor the site for 60 minutes post-work.\n\n"
            "## Chapter 3: Flammable Liquid Storage Cabinets\n"
            "Flammable liquids in quantities greater than 5 gallons must be stored in double-walled self-closing yellow FM-approved safety cabinets with three-point door latches."
        )
    },
    {
        "id": "HBK-009",
        "title": "Warehouse Ergonomics, Lifting Protocols and Musculoskeletal Safety",
        "code": "NIOSH Lifting Equation Guidelines",
        "content": (
            "# Warehouse Ergonomics, Lifting Protocols & Musculoskeletal Safety\n\n"
            "## Rule 1: The 23 kg (50 lb) Maximum Single-Person Lift\n"
            "No single warehouse associate is permitted to lift any object exceeding 23 kg (50 lbs) unassisted. Loads exceeding this limit require mandatory dual-person team lifting or mechanical hoist equipment.\n\n"
            "## Rule 2: Biomechanical Lifting Technique\n"
            "Lift with the legs and core, keeping the load within the 'power zone' (mid-thigh to mid-chest). Avoid twisting the torso while carrying unit loads; reposition feet to turn.\n\n"
            "## Rule 3: High-Frequency Picking Rotation\n"
            "Order pickers performing continuous manual carton selection must rotate workstations every 2 hours to avoid repetitive strain on shoulder and lumbar muscle groups."
        )
    },
    {
        "id": "HBK-010",
        "title": "Environmental Compliance, Hazardous Waste and Spill Response Guide",
        "code": "EPA RCRA & Spill Prevention Plan",
        "content": (
            "# Environmental Compliance, Hazardous Waste & Spill Response Guide\n\n"
            "## Section 1: EPA Resource Conservation and Recovery (RCRA)\n"
            "Hazardous wastes generated from cleaning solvents, expired paint, and battery acids must be labeled 'HAZARDOUS WASTE' with accumulation start dates clearly inscribed on exterior drum faces.\n\n"
            "## Section 2: Stormwater Discharge Protection\n"
            "Outdoor dock drains and retention pond spillways must be protected with storm drain filter inserts. Chemical washing of trucks or pallets in exterior yards is strictly banned.\n\n"
            "## Section 3: Waste Manifest Documentation\n"
            "All hazardous waste hauling requires signed EPA Uniform Hazardous Waste Manifests. Copies must be countersigned by certified waste transporters and retained for 3 years."
        )
    }
]


def create_pdf(filename: str, title: str, category_or_code: str, body_text: str):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=40, leftMargin=40,
        topMargin=40, bottomMargin=40
    )
    styles = getSampleStyleSheet()

    header_style = ParagraphStyle(
        "HeaderTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        "SubTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#2563eb"),
        spaceAfter=12
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=15,
        textColor=colors.HexColor("#334155"),
        spaceAfter=8
    )

    story = [
        Paragraph(title, header_style),
        Paragraph(category_or_code, subtitle_style),
        HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563eb"), spaceAfter=14),
    ]

    for paragraph in body_text.split("\n"):
        clean_p = paragraph.strip()
        if not clean_p:
            continue
        if clean_p.startswith("#"):
            h_text = clean_p.lstrip("# ").strip()
            story.append(Paragraph(f"<b>{h_text}</b>", ParagraphStyle("H", parent=styles["Heading2"], fontSize=12, leading=16, textColor=colors.HexColor("#1e293b"), spaceBefore=8, spaceAfter=4)))
        else:
            story.append(Paragraph(clean_p, body_style))

    doc.build(story)


def main():
    base_policies_dir = Path("data/policies/company_policies")
    base_handbooks_dir = Path("data/policies/safety_handbooks")
    base_policies_dir.mkdir(parents=True, exist_ok=True)
    base_handbooks_dir.mkdir(parents=True, exist_ok=True)

    print("--- Generating 20 Company Policies ---")
    for pol in POLICIES:
        md_path = base_policies_dir / f"{pol['id']}_{pol['title'].replace(' ', '_').replace('/', '_')}.md"
        pdf_path = base_policies_dir / f"{pol['id']}_{pol['title'].replace(' ', '_').replace('/', '_')}.pdf"

        # Write markdown
        md_content = f"# {pol['id']}: {pol['title']}\n"
        md_content += f"**Compliance Reference:** {pol['clause']} | **Category:** {pol['category']}\n\n"
        md_content += pol['content'] + "\n"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        # Write PDF
        create_pdf(str(pdf_path), f"{pol['id']}: {pol['title']}", f"{pol['clause']} | {pol['category']}", pol['content'])
        print(f"Generated Policy: {md_path.name} & {pdf_path.name}")

    print("\n--- Generating 10 Safety Handbooks ---")
    for hbk in HANDBOOKS:
        md_path = base_handbooks_dir / f"{hbk['id']}_{hbk['title'].replace(' ', '_').replace('/', '_')}.md"
        pdf_path = base_handbooks_dir / f"{hbk['id']}_{hbk['title'].replace(' ', '_').replace('/', '_')}.pdf"

        # Write markdown
        md_content = f"# {hbk['id']}: {hbk['title']}\n"
        md_content += f"**Standards Code:** {hbk['code']}\n\n"
        md_content += hbk['content'] + "\n"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        # Write PDF
        create_pdf(str(pdf_path), f"{hbk['id']}: {hbk['title']}", hbk['code'], hbk['content'])
        print(f"Generated Handbook: {md_path.name} & {pdf_path.name}")


if __name__ == "__main__":
    main()
