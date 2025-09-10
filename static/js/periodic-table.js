// Periodic Table Integration with CSV Data
class PeriodicTable {
    constructor() {
        this.elements = [];
        this.container = document.getElementById('periodic-table-container');
        this.legend = document.getElementById('legend');
        this.loadElements();
    }

    async loadElements() {
        try {
            // Load CSV data from the server
            const response = await fetch('/api/periodic-table-data');
            if (response.ok) {
                this.elements = await response.json();
                this.renderPeriodicTable();
            } else {
                // Fallback: create a simple periodic table structure
                this.createFallbackTable();
            }
        } catch (error) {
            console.error('Error loading periodic table data:', error);
            this.createFallbackTable();
        }
    }

    renderPeriodicTable() {
        if (!this.container) return;

        // Create the periodic table structure
        const table = document.createElement('div');
        table.className = 'periodic-table';
        table.style.cssText = `
            display: grid;
            grid-template-columns: repeat(18, 1fr);
            gap: 2px;
            max-width: 100%;
            margin: 0 auto;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        `;

        // Create element cells
        this.elements.forEach(element => {
            const cell = this.createElementCell(element);
            table.appendChild(cell);
        });

        this.container.innerHTML = '';
        this.container.appendChild(table);
        this.createLegend();
    }

    createElementCell(element) {
        const cell = document.createElement('div');
        cell.className = 'element-cell';
        cell.dataset.atomicNumber = element.atomic_number;
        cell.dataset.symbol = element.symbol;
        cell.dataset.name = element.name;

        // Set position based on atomic number
        const position = this.getElementPosition(element.atomic_number);
        cell.style.gridColumn = position.column;
        cell.style.gridRow = position.row;

        // Set color based on group
        const color = this.getGroupColor(element.group_block);
        cell.style.backgroundColor = color;
        cell.style.color = this.getTextColor(color);

        // Create cell content
        cell.innerHTML = `
            <div class="atomic-number">${element.atomic_number}</div>
            <div class="symbol">${element.symbol}</div>
            <div class="name">${element.name}</div>
            <div class="mass">${element.atomic_mass ? element.atomic_mass.toFixed(2) : ''}</div>
        `;

        // Add hover effect
        cell.addEventListener('mouseenter', () => this.showElementInfo(element));
        cell.addEventListener('mouseleave', () => this.hideElementInfo());

        // Add click event
        cell.addEventListener('click', () => this.selectElement(element));

        return cell;
    }

    getElementPosition(atomicNumber) {
        // Simplified periodic table positioning
        const positions = {
            1: { row: 1, column: 1 },   // H
            2: { row: 1, column: 18 },  // He
            3: { row: 2, column: 1 },   // Li
            4: { row: 2, column: 2 },   // Be
            5: { row: 2, column: 13 },  // B
            6: { row: 2, column: 14 },  // C
            7: { row: 2, column: 15 },  // N
            8: { row: 2, column: 16 },  // O
            9: { row: 2, column: 17 },  // F
            10: { row: 2, column: 18 }, // Ne
            11: { row: 3, column: 1 },  // Na
            12: { row: 3, column: 2 },  // Mg
            13: { row: 3, column: 13 }, // Al
            14: { row: 3, column: 14 }, // Si
            15: { row: 3, column: 15 }, // P
            16: { row: 3, column: 16 }, // S
            17: { row: 3, column: 17 }, // Cl
            18: { row: 3, column: 18 }, // Ar
            19: { row: 4, column: 1 },  // K
            20: { row: 4, column: 2 },  // Ca
            21: { row: 4, column: 3 },  // Sc
            22: { row: 4, column: 4 },  // Ti
            23: { row: 4, column: 5 },  // V
            24: { row: 4, column: 6 },  // Cr
            25: { row: 4, column: 7 },  // Mn
            26: { row: 4, column: 8 },  // Fe
            27: { row: 4, column: 9 },  // Co
            28: { row: 4, column: 10 }, // Ni
            29: { row: 4, column: 11 }, // Cu
            30: { row: 4, column: 12 }, // Zn
            31: { row: 4, column: 13 }, // Ga
            32: { row: 4, column: 14 }, // Ge
            33: { row: 4, column: 15 }, // As
            34: { row: 4, column: 16 }, // Se
            35: { row: 4, column: 17 }, // Br
            36: { row: 4, column: 18 }, // Kr
        };

        return positions[atomicNumber] || { row: 1, column: 1 };
    }

    getGroupColor(group) {
        const colors = {
            'Alkali metal': '#ff9999',
            'Alkaline earth metal': '#ffcc99',
            'Transition metal': '#99ccff',
            'Post-transition metal': '#cccccc',
            'Metalloid': '#ffccff',
            'Nonmetal': '#ccffcc',
            'Halogen': '#ffff99',
            'Noble gas': '#ffccff',
            'Lanthanide': '#ff99cc',
            'Actinide': '#cc99ff'
        };
        return colors[group] || '#f0f0f0';
    }

    getTextColor(backgroundColor) {
        // Simple contrast calculation
        const hex = backgroundColor.replace('#', '');
        const r = parseInt(hex.substr(0, 2), 16);
        const g = parseInt(hex.substr(2, 2), 16);
        const b = parseInt(hex.substr(4, 2), 16);
        const brightness = (r * 299 + g * 587 + b * 114) / 1000;
        return brightness > 128 ? '#000000' : '#ffffff';
    }

    createLegend() {
        if (!this.legend) return;

        const groups = [...new Set(this.elements.map(e => e.group_block))];
        const legendHTML = groups.map(group => {
            const color = this.getGroupColor(group);
            return `
                <div class="legend-item d-flex align-items-center">
                    <div class="legend-color" style="background-color: ${color}; width: 20px; height: 20px; margin-right: 8px; border: 1px solid #ccc;"></div>
                    <span class="legend-label">${group}</span>
                </div>
            `;
        }).join('');

        this.legend.innerHTML = legendHTML;
    }

    showElementInfo(element) {
        // Create or update element info tooltip
        let tooltip = document.getElementById('element-tooltip');
        if (!tooltip) {
            tooltip = document.createElement('div');
            tooltip.id = 'element-tooltip';
            tooltip.className = 'element-tooltip';
            tooltip.style.cssText = `
                position: absolute;
                background: rgba(0, 0, 0, 0.9);
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-size: 12px;
                z-index: 1000;
                pointer-events: none;
                max-width: 200px;
            `;
            document.body.appendChild(tooltip);
        }

        tooltip.innerHTML = `
            <strong>${element.name} (${element.symbol})</strong><br>
            Atomic Number: ${element.atomic_number}<br>
            Atomic Mass: ${element.atomic_mass ? element.atomic_mass.toFixed(2) + ' u' : 'N/A'}<br>
            Group: ${element.group_block}<br>
            State: ${element.standard_state}<br>
            Electronegativity: ${element.electronegativity || 'N/A'}<br>
            Density: ${element.density_g_cm3 ? element.density_g_cm3.toFixed(3) + ' g/cm³' : 'N/A'}
        `;

        // Position tooltip
        const rect = event.target.getBoundingClientRect();
        tooltip.style.left = (rect.left + rect.width / 2) + 'px';
        tooltip.style.top = (rect.top - tooltip.offsetHeight - 10) + 'px';
        tooltip.style.display = 'block';
    }

    hideElementInfo() {
        const tooltip = document.getElementById('element-tooltip');
        if (tooltip) {
            tooltip.style.display = 'none';
        }
    }

    selectElement(element) {
        // Highlight selected element
        document.querySelectorAll('.element-cell').forEach(cell => {
            cell.classList.remove('selected');
        });
        event.target.closest('.element-cell').classList.add('selected');

        // You can add more functionality here, like showing detailed info in a modal
        console.log('Selected element:', element);
    }

    createFallbackTable() {
        // Create a simple fallback table if CSV data is not available
        this.container.innerHTML = `
            <div class="alert alert-info">
                <h5>Periodic Table</h5>
                <p>Periodic table data is being loaded. Please ensure the CSV file is available.</p>
                <p>This will display all 118 elements with their properties from your CSV data.</p>
            </div>
        `;
    }
}

// Initialize periodic table when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('periodic-table-container')) {
        new PeriodicTable();
    }
});
