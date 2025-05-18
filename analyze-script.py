#!/usr/bin/env python3

"""
analyze_results.py - Analyzes the plugin test results and generates visualization
"""

import os
import re
import sys
import argparse
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import pandas as pd
import numpy as np

def parse_results_directory(results_dir):
    """Parse all result files in the given directory and extract plugin status"""
    results = {}
    
    # Get all result files
    result_files = [f for f in os.listdir(results_dir) if f.endswith('_results.txt')]
    
    for result_file in result_files:
        plugin_name = result_file.replace('_results.txt', '')
        file_path = os.path.join(results_dir, result_file)
        
        with open(file_path, 'r') as f:
            content = f.read()
            
            # Determine status based on content
            if 'STATUS: COMPLETED' in content:
                # Check if output is meaningful by counting non-header lines
                output_lines = len([line for line in content.split('\n') 
                                    if not line.startswith('Progress:') 
                                    and not line.startswith('Test started') 
                                    and not line.startswith('Plugin:') 
                                    and not line.startswith('Memory dump:') 
                                    and not line.startswith('====')
                                    and line.strip() != ''])
                
                if output_lines > 5:
                    status = 'Works'
                else:
                    status = 'Partial'
                    
                # Check for common errors
                if 'Error:' in content or 'Exception:' in content:
                    status = 'Partial'
            elif 'STATUS: FAILED' in content:
                status = 'Fails'
            elif 'STATUS: TIMED OUT' in content:
                status = 'Fails'
            else:
                status = 'Unknown'
            
            # Extract any specific limitations from the content
            limitations = "No specific limitations noted"
            if 'Error:' in content:
                error_line = re.search(r'Error:.*', content)
                if error_line:
                    limitations = error_line.group(0)
            elif 'Exception:' in content:
                exception_lines = re.search(r'Exception:.*?(?:\n.*?){0,5}', content, re.DOTALL)
                if exception_lines:
                    limitations = exception_lines.group(0).replace('\n', ' ')
            
            results[plugin_name] = {
                'status': status,
                'limitations': limitations if len(limitations) < 100 else limitations[:100] + "..."
            }
    
    return results

def create_compatibility_table(results):
    """Create a compatibility table from the results"""
    data = []
    
    for plugin, info in sorted(results.items()):
        notes = ""
        if info['status'] == 'Works':
            notes = "Successfully produces usable output"
        elif info['status'] == 'Partial':
            notes = "Limited functionality or output"
        elif info['status'] == 'Fails':
            notes = "Plugin fails to execute properly"
        
        if info['limitations'] != "No specific limitations noted":
            notes += f" - {info['limitations']}"
            
        data.append({
            'Plugin': plugin,
            'Status': info['status'],
            'Notes/Limitations': notes
        })
    
    return pd.DataFrame(data)

def generate_visualization(results, output_file):
    """Generate a visualization of plugin compatibility"""
    # Convert results to a format suitable for visualization
    plugins = []
    statuses = []
    
    for plugin, info in sorted(results.items()):
        plugins.append(plugin)
        statuses.append(info['status'])
    
    # Create a numeric representation of statuses for coloring
    status_to_num = {'Works': 2, 'Partial': 1, 'Fails': 0, 'Unknown': -1}
    status_nums = [status_to_num[s] for s in statuses]
    
    # Set up the plot
    plt.figure(figsize=(12, 8))
    cmap = ListedColormap(['#ff9999', '#ffcc99', '#99cc99', '#cccccc'])
    
    y_pos = np.arange(len(plugins))
    bars = plt.barh(y_pos, [1] * len(plugins), color=[cmap(x/2) for x in status_nums])
    
    # Add status text to bars
    for i, status in enumerate(statuses):
        plt.text(0.5, i, status, ha='center', va='center', color='black')
    
    # Set up labels and title
    plt.yticks(y_pos, plugins)
    plt.xlabel('Compatibility Status')
    plt.title('Volatility3 Linux Plugin Compatibility with Android Memory Dumps')
    
    # Add a legend
    legend_elements = [
        plt.Rectangle((0, 0), 1, 1, color=cmap(0), label='Fails'),
        plt.Rectangle((0, 0), 1, 1, color=cmap(0.5), label='Partial'),
        plt.Rectangle((0, 0), 1, 1, color=cmap(1), label='Works')
    ]
    plt.legend(handles=legend_elements, loc='upper right')
    
    # Save the plot
    plt.tight_layout()
    plt.savefig(output_file)
    print(f"Visualization saved to {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Analyze Volatility plugin test results')
    parser.add_argument('results_dir', help='Directory containing test results')
    parser.add_argument('-o', '--output', default='plugin_compatibility.png', 
                        help='Output file for visualization (default: plugin_compatibility.png)')
    parser.add_argument('-c', '--csv', action='store_true', 
                        help='Output results as CSV file')
    args = parser.parse_args()
    
    # Check if results directory exists
    if not os.path.isdir(args.results_dir):
        print(f"Error: Results directory {args.results_dir} does not exist")
        return 1
    
    # Parse results
    results = parse_results_directory(args.results_dir)
    
    if not results:
        print("No results found in the specified directory")
        return 1
    
    # Create compatibility table
    df = create_compatibility_table(results)
    
    # Display table
    print("\nPlugin Compatibility Results:\n")
    print(df.to_string(index=False))
    
    # Save as CSV if requested
    if args.csv:
        csv_file = os.path.join(args.results_dir, 'compatibility_results.csv')
        df.to_csv(csv_file, index=False)
        print(f"\nResults saved to {csv_file}")
    
    # Generate visualization
    generate_visualization(results, args.output)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())