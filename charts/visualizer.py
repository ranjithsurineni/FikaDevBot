import matplotlib.pyplot as plt

def generate_churn_chart(churn_data, path="churn.png"):
    """
    Generates an enhanced code churn chart with additions and deletions,
    gridlines, axis labels, legend, title, and spike annotations.

    Args:
        churn_data (list of dict): A list of dictionaries, each containing
                                   'sha', 'additions', and 'deletions' for a commit.
        path (str): The file path to save the generated chart.

    Returns:
        str: The path to the saved chart image, or None if no data is provided.
    """
    if not churn_data:
        print("No churn data available to generate chart.")
        return None

    # Prepare data for plotting
    shas = [item["sha"][:7] for item in churn_data] # Shorten SHA for readability
    additions = [item["additions"] for item in churn_data]
    deletions = [item["deletions"] for item in churn_data]
    
    plt.figure(figsize=(14, 7)) # Set a larger figure size for better clarity

    # Plot additions as positive bars
    plt.bar(shas, additions, color='green', label='Additions', zorder=2) # zorder to bring bars to front of grid
    # Plot deletions as negative bars to show them going downwards from the zero line
    plt.bar(shas, [-d for d in deletions], color='red', label='Deletions', zorder=2) 

    # Add a horizontal line at y=0 for clear demarcation
    plt.axhline(0, color='grey', linewidth=0.8, zorder=1)

    # Add gridlines for better readability
    plt.grid(axis='y', linestyle='--', alpha=0.7, zorder=0) # Grid behind bars
    plt.grid(axis='x', linestyle=':', alpha=0.5, zorder=0)

    # Set axis labels and title with appropriate font sizes
    plt.xlabel("Commit (Short SHA)", fontsize=12)
    plt.ylabel("Lines Changed (Additions +, Deletions -)", fontsize=12)
    plt.title("Code Churn per Commit: Additions and Deletions", fontsize=14)
    
    # Rotate x-axis labels for better readability if SHAs are long
    plt.xticks(rotation=45, ha='right', fontsize=9)
    plt.yticks(fontsize=9)

    # Add a legend to distinguish additions and deletions
    plt.legend(fontsize=10)

    # Annotate significant commits or spikes
    # A "spike" is defined as a commit with a total (additions + deletions) greater than a threshold.
    spike_threshold = 500 # This threshold aligns with DiffAnalyst's definition of a spike

    for i, (sha, add, dele) in enumerate(zip(shas, additions, deletions)):
        total_churn_for_this_commit = add + dele # This represents sum of absolute lines changed
        
        if total_churn_for_this_commit > spike_threshold:
            # Determine y-position for annotation. Place it above additions or below deletions,
            # depending on which absolute value is larger for clarity.
            if add >= dele: # If additions are greater or equal to deletions (magnitude)
                y_pos = add + 50 # Place annotation above the additions bar
                va_align = 'bottom'
            else: # If deletions are greater (magnitude)
                y_pos = -dele - 50 # Place annotation below the deletions bar
                va_align = 'top'

            plt.annotate(
                f'Total Churn: {total_churn_for_this_commit}', # Display total lines changed
                xy=(sha, add if add >= dele else -dele), # Point to the end of the dominant bar
                xytext=(sha, y_pos), # Position the text
                textcoords='data',
                arrowprops=dict(facecolor='black', shrink=0.05, width=0.5, headwidth=5),
                ha='center', va=va_align,
                bbox=dict(boxstyle="round,pad=0.3", fc="yellow", ec="black", lw=1, alpha=0.7),
                fontsize=8
            )

    plt.tight_layout() # Adjust layout to prevent labels from overlapping
    
    plt.savefig(path) # Save the figure to the specified path
    plt.close() # Close the figure to free up memory and prevent display issues

    return path
