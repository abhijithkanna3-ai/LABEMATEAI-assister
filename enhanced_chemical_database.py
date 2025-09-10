#!/usr/bin/env python3
"""
Enhanced Chemical Database with PubChem Integration
Combines the existing chemical database with PubChem integration
"""

from chemical_database import CHEMICAL_DATABASE, calculate_reagent
from pubchem_fetcher import fetch_chemical_data
import json
from typing import Dict, List, Optional, Any

class EnhancedChemicalDatabase:
    """Enhanced chemical database with PubChem integration"""
    
    def __init__(self):
        self.local_database = CHEMICAL_DATABASE
    
    def get_chemical_data(self, chemical_name: str, use_pubchem: bool = True) -> Dict[str, Any]:
        """
        Get comprehensive chemical data from multiple sources
        
        Args:
            chemical_name (str): Name of the chemical
            use_pubchem (bool): Whether to fetch from PubChem if not found locally
            
        Returns:
            dict: Comprehensive chemical data
        """
        result = {
            'chemical_name': chemical_name,
            'source': 'unknown',
            'data': {},
            'status': 'error',
            'error_message': None
        }
        
        # First, try local database
        if chemical_name in self.local_database:
            local_data = self.local_database[chemical_name]
            result.update({
                'source': 'local_database',
                'data': {
                    'formula': local_data.get('formula'),
                    'molar_mass': local_data.get('molar_mass'),
                    'hazards': local_data.get('hazards', []),
                    'description': local_data.get('description')
                },
                'status': 'success'
            })
            return result
        
        # Try PubChem if enabled and not found locally
        if use_pubchem:
            try:
                pubchem_data = fetch_chemical_data(chemical_name)
                if pubchem_data['status'] == 'success':
                    result.update({
                        'source': 'pubchem',
                        'data': {
                            'molecular_weight': pubchem_data.get('molecular_weight'),
                            'density': pubchem_data.get('density'),
                            'boiling_point': pubchem_data.get('boiling_point'),
                            'heat_capacity': pubchem_data.get('heat_capacity'),
                            'safety_classification': pubchem_data.get('safety_classification'),
                            'ghs_data': pubchem_data.get('ghs_data'),
                            'pubchem_cid': pubchem_data.get('pubchem_cid'),
                            'molecular_formula': pubchem_data.get('molecular_formula'),
                            'smiles': pubchem_data.get('smiles')
                        },
                        'status': 'success'
                    })
                    return result
                else:
                    result['error_message'] = pubchem_data.get('error_message', 'PubChem lookup failed')
            except Exception as e:
                result['error_message'] = f'PubChem error: {str(e)}'
        
        result['error_message'] = f'Chemical "{chemical_name}" not found in any database'
        return result
    
    def search_chemicals(self, query: str) -> List[Dict[str, Any]]:
        """Search for chemicals across all databases"""
        results = []
        
        # Search local database
        query_lower = query.lower()
        for name, data in self.local_database.items():
            if (query_lower in name.lower() or 
                query_lower in data.get('formula', '').lower() or
                query_lower in data.get('description', '').lower()):
                results.append({
                    'name': name,
                    'source': 'local_database',
                    'formula': data.get('formula'),
                    'molar_mass': data.get('molar_mass'),
                    'hazards': data.get('hazards', []),
                    'description': data.get('description')
                })
        
        return results
    
    def calculate_reagent_enhanced(self, reagent_name: str, molarity: float, volume_ml: float) -> Dict[str, Any]:
        """
        Enhanced reagent calculation with additional data sources
        """
        # Get basic calculation
        basic_result = calculate_reagent(reagent_name, molarity, volume_ml)
        
        if 'error' in basic_result:
            return basic_result
        
        # Get additional chemical data
        chemical_data = self.get_chemical_data(reagent_name, use_pubchem=False)
        
        # Enhance the result
        enhanced_result = basic_result.copy()
        enhanced_result['additional_data'] = chemical_data.get('data', {})
        enhanced_result['data_source'] = chemical_data.get('source', 'unknown')
        
        return enhanced_result
    
    def get_chemical_properties_summary(self, chemical_name: str) -> Dict[str, Any]:
        """Get a comprehensive summary of chemical properties"""
        data = self.get_chemical_data(chemical_name)
        
        if data['status'] != 'success':
            return data
        
        summary = {
            'chemical_name': chemical_name,
            'data_source': data['source'],
            'properties': {}
        }
        
        chemical_data = data['data']
        
        # Organize properties by category
        summary['properties']['basic'] = {
            'formula': chemical_data.get('formula') or chemical_data.get('molecular_formula'),
            'molar_mass': chemical_data.get('molar_mass') or chemical_data.get('molecular_weight'),
            'pubchem_cid': chemical_data.get('pubchem_cid')
        }
        
        summary['properties']['physical'] = {
            'density': chemical_data.get('density'),
            'boiling_point': chemical_data.get('boiling_point'),
            'heat_capacity': chemical_data.get('heat_capacity')
        }
        
        summary['properties']['safety'] = {
            'hazards': chemical_data.get('hazards', []),
            'ghs_data': chemical_data.get('ghs_data'),
            'safety_classification': chemical_data.get('safety_classification')
        }
        
        summary['properties']['other'] = {
            'description': chemical_data.get('description'),
            'smiles': chemical_data.get('smiles')
        }
        
        return summary

# Global instance
enhanced_db = EnhancedChemicalDatabase()

# Convenience functions
def get_chemical_data(chemical_name: str, use_pubchem: bool = True) -> Dict[str, Any]:
    """Get chemical data from enhanced database"""
    return enhanced_db.get_chemical_data(chemical_name, use_pubchem)

def search_chemicals(query: str) -> List[Dict[str, Any]]:
    """Search chemicals in enhanced database"""
    return enhanced_db.search_chemicals(query)

def calculate_reagent_enhanced(reagent_name: str, molarity: float, volume_ml: float) -> Dict[str, Any]:
    """Enhanced reagent calculation"""
    return enhanced_db.calculate_reagent_enhanced(reagent_name, molarity, volume_ml)

def get_chemical_properties_summary(chemical_name: str) -> Dict[str, Any]:
    """Get comprehensive chemical properties summary"""
    return enhanced_db.get_chemical_properties_summary(chemical_name)

# Example usage
if __name__ == "__main__":
    print("Enhanced Chemical Database Test")
    print("=" * 40)
    
    # Test with various chemicals
    test_chemicals = ['water', 'sodium chloride', 'ethanol', 'aspirin']
    
    for chemical in test_chemicals:
        print(f"\nTesting: {chemical}")
        print("-" * 30)
        
        # Get comprehensive data
        data = get_chemical_data(chemical)
        print(f"Source: {data.get('source', 'unknown')}")
        print(f"Status: {data.get('status', 'unknown')}")
        
        if data['status'] == 'success':
            props = data['data']
            print(f"Formula: {props.get('formula') or props.get('molecular_formula', 'N/A')}")
            print(f"Molar Mass: {props.get('molar_mass') or props.get('molecular_weight', 'N/A')}")
            print(f"Density: {props.get('density', 'N/A')}")
        else:
            print(f"Error: {data.get('error_message', 'Unknown error')}")
    
    # Test search functionality
    print(f"\nSearching for 'acid':")
    results = search_chemicals('acid')
    print(f"Found {len(results)} results")
    
    # Test enhanced calculation
    print(f"\nEnhanced calculation for sodium chloride:")
    calc_result = calculate_reagent_enhanced('Sodium Chloride', 1.0, 1000)
    if 'error' not in calc_result:
        print(f"Mass needed: {calc_result['mass_needed']:.2f} g")
        print(f"Data source: {calc_result.get('data_source', 'unknown')}")
    
    # Test properties summary
    print(f"\nProperties summary for water:")
    summary = get_chemical_properties_summary('water')
    if summary.get('status') != 'error':
        print(f"Data source: {summary.get('data_source')}")
        print(f"Basic properties: {summary['properties']['basic']}")