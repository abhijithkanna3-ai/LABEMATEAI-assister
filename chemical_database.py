# Chemical database with common laboratory reagents
CHEMICAL_DATABASE = {
    'Sodium Chloride': {
        'formula': 'NaCl',
        'molar_mass': 58.44,
        'hazards': ['Irritant'],
        'description': 'Common table salt, used in various laboratory procedures'
    },
    'Sodium Hydroxide': {
        'formula': 'NaOH',
        'molar_mass': 39.997,
        'hazards': ['Corrosive', 'Caustic'],
        'description': 'Strong base, handle with extreme caution'
    },
    'Hydrochloric Acid': {
        'formula': 'HCl',
        'molar_mass': 36.458,
        'hazards': ['Corrosive', 'Toxic'],
        'description': 'Strong acid, use in fume hood'
    },
    'Sulfuric Acid': {
        'formula': 'H2SO4',
        'molar_mass': 98.079,
        'hazards': ['Corrosive', 'Oxidizer'],
        'description': 'Concentrated sulfuric acid, extremely dangerous'
    },
    'Glucose': {
        'formula': 'C6H12O6',
        'molar_mass': 180.156,
        'hazards': ['None'],
        'description': 'Simple sugar, generally safe to handle'
    },
    'Ethanol': {
        'formula': 'C2H5OH',
        'molar_mass': 46.07,
        'hazards': ['Flammable', 'Irritant'],
        'description': 'Common alcohol, keep away from heat sources'
    },
    'Acetic Acid': {
        'formula': 'CH3COOH',
        'molar_mass': 60.052,
        'hazards': ['Corrosive', 'Flammable'],
        'description': 'Weak acid, component of vinegar'
    },
    'Potassium Permanganate': {
        'formula': 'KMnO4',
        'molar_mass': 158.034,
        'hazards': ['Oxidizer', 'Irritant'],
        'description': 'Strong oxidizing agent'
    },
    'Copper Sulfate': {
        'formula': 'CuSO4',
        'molar_mass': 159.609,
        'hazards': ['Harmful', 'Environmental'],
        'description': 'Blue crystalline compound'
    },
    'Silver Nitrate': {
        'formula': 'AgNO3',
        'molar_mass': 169.87,
        'hazards': ['Corrosive', 'Oxidizer'],
        'description': 'Photosensitive compound, store in dark'
    }
}

def calculate_reagent(reagent_name, molarity, volume_ml):
    """
    Calculate the mass of reagent needed for a given molarity and volume.
    
    Args:
        reagent_name (str): Name of the chemical reagent
        molarity (float): Desired molarity in mol/L
        volume_ml (float): Volume in milliliters
    
    Returns:
        dict: Calculation results including mass needed
    """
    if reagent_name not in CHEMICAL_DATABASE:
        return {'error': 'Chemical not found in database'}
    
    chemical = CHEMICAL_DATABASE[reagent_name]
    molar_mass = chemical['molar_mass']
    
    # Convert volume from mL to L
    volume_l = volume_ml / 1000
    
    # Calculate moles needed: moles = molarity × volume
    moles_needed = molarity * volume_l
    
    # Calculate mass needed: mass = moles × molar_mass
    mass_needed = moles_needed * molar_mass
    
    return {
        'reagent': reagent_name,
        'formula': chemical['formula'],
        'molar_mass': molar_mass,
        'molarity': molarity,
        'volume_ml': volume_ml,
        'volume_l': volume_l,
        'moles_needed': moles_needed,
        'mass_needed': mass_needed,
        'instructions': f"Weigh {mass_needed:.3f}g of {reagent_name} and dissolve in distilled water. Transfer to a {volume_ml}mL volumetric flask and dilute to mark."
    }
