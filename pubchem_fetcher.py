import requests
import json
import time
from typing import Dict, Optional, Any

class PubChemFetcher:
    """
    A class to fetch chemical data from PubChem API
    """
    
    def __init__(self):
        self.base_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'LabMateAI/1.0 (Educational Use)'
        })
    
    def get_cid(self, chemical_name: str) -> Optional[int]:
        """
        Get the PubChem CID (Compound Identifier) for a chemical name
        
        Args:
            chemical_name (str): Name of the chemical
            
        Returns:
            int: PubChem CID or None if not found
        """
        try:
            url = f"{self.base_url}/compound/name/{chemical_name}/cids/JSON"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if 'IdentifierList' in data and 'CID' in data['IdentifierList']:
                cids = data['IdentifierList']['CID']
                return cids[0] if cids else None
            return None
            
        except Exception as e:
            print(f"Error getting CID for {chemical_name}: {e}")
            return None
    
    def get_molecular_weight(self, cid: int) -> Optional[float]:
        """Get molecular weight from PubChem"""
        try:
            url = f"{self.base_url}/compound/cid/{cid}/property/MolecularWeight/JSON"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if 'PropertyTable' in data and 'Properties' in data['PropertyTable']:
                properties = data['PropertyTable']['Properties']
                if properties and 'MolecularWeight' in properties[0]:
                    return float(properties[0]['MolecularWeight'])
            return None
            
        except Exception as e:
            print(f"Error getting molecular weight: {e}")
            return None
    
    def get_density(self, cid: int) -> Optional[float]:
        """Get density from PubChem"""
        try:
            # Try multiple property names for density
            density_properties = ['Density', 'ExactMass', 'MolecularWeight']
            
            for prop in density_properties:
                try:
                    url = f"{self.base_url}/compound/cid/{cid}/property/{prop}/JSON"
                    response = self.session.get(url, timeout=10)
                    response.raise_for_status()
                    
                    data = response.json()
                    if 'PropertyTable' in data and 'Properties' in data['PropertyTable']:
                        properties = data['PropertyTable']['Properties']
                        if properties and prop in properties[0]:
                            value = properties[0][prop]
                            if value is not None:
                                return float(value)
                except:
                    continue
            
            return None
            
        except Exception as e:
            print(f"Error getting density: {e}")
            return None
    
    def get_boiling_point(self, cid: int) -> Optional[float]:
        """Get boiling point from PubChem"""
        try:
            # Try different property names for boiling point
            bp_properties = ['BoilingPoint', 'MeltingPoint', 'FlashPoint']
            
            for prop in bp_properties:
                try:
                    url = f"{self.base_url}/compound/cid/{cid}/property/{prop}/JSON"
                    response = self.session.get(url, timeout=10)
                    response.raise_for_status()
                    
                    data = response.json()
                    if 'PropertyTable' in data and 'Properties' in data['PropertyTable']:
                        properties = data['PropertyTable']['Properties']
                        if properties and prop in properties[0]:
                            value = properties[0][prop]
                            if value is not None:
                                return float(value)
                except:
                    continue
            
            return None
            
        except Exception as e:
            print(f"Error getting boiling point: {e}")
            return None
    
    def get_heat_capacity(self, cid: int) -> Optional[float]:
        """Get heat capacity from PubChem"""
        try:
            # Try different property names for heat capacity
            hc_properties = ['HeatCapacity', 'MolarHeatCapacity', 'SpecificHeat']
            
            for prop in hc_properties:
                try:
                    url = f"{self.base_url}/compound/cid/{cid}/property/{prop}/JSON"
                    response = self.session.get(url, timeout=10)
                    response.raise_for_status()
                    
                    data = response.json()
                    if 'PropertyTable' in data and 'Properties' in data['PropertyTable']:
                        properties = data['PropertyTable']['Properties']
                        if properties and prop in properties[0]:
                            value = properties[0][prop]
                            if value is not None:
                                return float(value)
                except:
                    continue
            
            return None
            
        except Exception as e:
            print(f"Error getting heat capacity: {e}")
            return None
    
    def get_ghs_classification(self, cid: int) -> Optional[Dict[str, Any]]:
        """Get GHS hazard classification from PubChem"""
        try:
            # Try different property names for GHS data
            ghs_properties = ['GHSClassification', 'HazardClassification', 'SafetyData']
            
            for prop in ghs_properties:
                try:
                    url = f"{self.base_url}/compound/cid/{cid}/property/{prop}/JSON"
                    response = self.session.get(url, timeout=10)
                    response.raise_for_status()
                    
                    data = response.json()
                    if 'PropertyTable' in data and 'Properties' in data['PropertyTable']:
                        properties = data['PropertyTable']['Properties']
                        if properties and prop in properties[0]:
                            value = properties[0][prop]
                            if value is not None:
                                return value
                except:
                    continue
            
            return None
            
        except Exception as e:
            print(f"Error getting GHS classification: {e}")
            return None
    
    def get_safety_data(self, cid: int) -> Optional[Dict[str, Any]]:
        """Get comprehensive safety data from PubChem"""
        try:
            # Try to get safety-related properties individually
            safety_properties = ['SafetyData', 'Hazardous', 'Toxic', 'Flammable', 'Corrosive', 'Reactive']
            safety_data = {}
            
            for prop in safety_properties:
                try:
                    url = f"{self.base_url}/compound/cid/{cid}/property/{prop}/JSON"
                    response = self.session.get(url, timeout=10)
                    response.raise_for_status()
                    
                    data = response.json()
                    if 'PropertyTable' in data and 'Properties' in data['PropertyTable']:
                        properties_data = data['PropertyTable']['Properties'][0]
                        if prop in properties_data and properties_data[prop] is not None:
                            safety_data[prop.lower()] = properties_data[prop]
                except:
                    continue
            
            return safety_data if safety_data else None
            
        except Exception as e:
            print(f"Error getting safety data: {e}")
            return None
    
    def fetch_chemical_data(self, chemical_name: str) -> Dict[str, Any]:
        """
        Fetch comprehensive chemical data from PubChem
        
        Args:
            chemical_name (str): Name of the chemical
            
        Returns:
            dict: Structured JSON with chemical properties
        """
        result = {
            "chemical_name": chemical_name,
            "molecular_weight": None,
            "density": None,
            "boiling_point": None,
            "heat_capacity": None,
            "safety_classification": None,
            "ghs_data": None,
            "pubchem_cid": None,
            "status": "error",
            "error_message": None
        }
        
        try:
            # Get CID first
            cid = self.get_cid(chemical_name)
            if not cid:
                result["error_message"] = f"Chemical '{chemical_name}' not found in PubChem"
                return result
            
            result["pubchem_cid"] = cid
            
            # Try to get multiple properties in a single request first
            properties_result = self.get_multiple_properties(cid)
            if properties_result:
                result.update(properties_result)
                result["status"] = "success"
                return result
            
            # Fallback to individual property requests
            time.sleep(0.2)  # Increased delay for rate limiting
            
            result["molecular_weight"] = self.get_molecular_weight(cid)
            time.sleep(0.2)
            
            result["density"] = self.get_density(cid)
            time.sleep(0.2)
            
            result["boiling_point"] = self.get_boiling_point(cid)
            time.sleep(0.2)
            
            result["heat_capacity"] = self.get_heat_capacity(cid)
            time.sleep(0.2)
            
            result["ghs_data"] = self.get_ghs_classification(cid)
            time.sleep(0.2)
            
            result["safety_classification"] = self.get_safety_data(cid)
            
            result["status"] = "success"
            
        except Exception as e:
            result["error_message"] = str(e)
            result["status"] = "error"
        
        return result
    
    def get_multiple_properties(self, cid: int) -> Optional[Dict[str, Any]]:
        """Get multiple properties in a single request"""
        try:
            # Use commonly available properties
            properties = ['MolecularWeight', 'MolecularFormula', 'CanonicalSMILES', 'IsomericSMILES']
            url = f"{self.base_url}/compound/cid/{cid}/property/{','.join(properties)}/JSON"
            
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            if 'PropertyTable' in data and 'Properties' in data['PropertyTable']:
                properties_data = data['PropertyTable']['Properties'][0]
                
                result = {}
                if 'MolecularWeight' in properties_data:
                    result['molecular_weight'] = float(properties_data['MolecularWeight'])
                if 'MolecularFormula' in properties_data:
                    result['molecular_formula'] = properties_data['MolecularFormula']
                if 'CanonicalSMILES' in properties_data:
                    result['smiles'] = properties_data['CanonicalSMILES']
                if 'IsomericSMILES' in properties_data:
                    result['isomeric_smiles'] = properties_data['IsomericSMILES']
                
                return result
            
            return None
            
        except Exception as e:
            print(f"Error getting multiple properties: {e}")
            return None

def fetch_chemical_data(chemical_name: str) -> Dict[str, Any]:
    """
    Convenience function to fetch chemical data from PubChem
    
    Args:
        chemical_name (str): Name of the chemical
        
    Returns:
        dict: Structured JSON with chemical properties
    """
    fetcher = PubChemFetcher()
    return fetcher.fetch_chemical_data(chemical_name)

# Example usage and testing
if __name__ == "__main__":
    # Test with a common chemical
    test_chemical = "water"
    print(f"Fetching data for: {test_chemical}")
    
    data = fetch_chemical_data(test_chemical)
    print(json.dumps(data, indent=2))
