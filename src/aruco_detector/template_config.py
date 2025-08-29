"""
ArUco Marker Template Configuration
Generated for multiple krathong templates.
"""

# Template marker sets for krathong variants
TEMPLATE_MARKER_SETS = {
    "krathong1": {
        "name": "Traditional Krathong (Original)",
        "description": "Classic traditional design",
        "markers": [0, 1, 2, 3],
        "mask_file": "mask1_final.png",  # Existing mask
    },
    "krathong2": {
        "name": "Modern Krathong",
        "description": "Contemporary modern design",
        "markers": [4, 5, 6, 7],
        "mask_file": "mask2_final.png",  # Created mask
    },
    "krathong3": {
        "name": "Lotus Krathong",
        "description": "Lotus flower inspired design",
        "markers": [8, 9, 10, 11],
        "mask_file": "mask3_final.png",  # Created mask
    },
    "krathong4": {
        "name": "Royal Krathong",
        "description": "Elegant royal design",
        "markers": [12, 13, 14, 15],
        "mask_file": "mask4_final.png",  # Created mask
    },
    "krathong5": {
        "name": "Children Krathong",
        "description": "Kid-friendly simple design",
        "markers": [16, 17, 18, 19],
        "mask_file": "krathong5_mask.png",  # To be created later
    },
}

# Quick lookup: marker ID -> template
MARKER_TO_TEMPLATE = {}
for template_id, config in TEMPLATE_MARKER_SETS.items():
    for marker_id in config["markers"]:
        MARKER_TO_TEMPLATE[marker_id] = template_id


# Template detection function
def detect_template_from_markers(detected_marker_ids):
    """
    Detect which template is being used based on detected marker IDs.

    Args:
        detected_marker_ids: List of detected ArUco marker IDs

    Returns:
        Template ID string or None if no match found
    """
    detected_set = set(detected_marker_ids)

    for template_id, config in TEMPLATE_MARKER_SETS.items():
        template_markers = set(config["markers"])

        # Check if all template markers are detected
        if template_markers.issubset(detected_set):
            return template_id

    return None


def detect_template_partial(detected_marker_ids, min_markers=3):
    """
    Detect which template is being used based on partial marker detection.
    Useful for display purposes when not all markers are visible.

    Args:
        detected_marker_ids: List of detected ArUco marker IDs
        min_markers: Minimum number of markers required for partial detection

    Returns:
        Template ID string or None if no match found
    """
    detected_set = set(detected_marker_ids)

    best_match = None
    best_score = 0

    for template_id, config in TEMPLATE_MARKER_SETS.items():
        template_markers = set(config["markers"])

        # Calculate overlap
        overlap = len(template_markers.intersection(detected_set))

        # Only consider if we have at least min_markers
        if overlap >= min_markers:
            # Calculate score based on percentage of markers detected
            score = overlap / len(template_markers)
            if score > best_score:
                best_score = score
                best_match = template_id

    return best_match


# Get template configuration
def get_template_config(template_id):
    """Get configuration for a specific template."""
    return TEMPLATE_MARKER_SETS.get(template_id)


# List all available templates
def list_templates():
    """Get list of all available template IDs."""
    return list(TEMPLATE_MARKER_SETS.keys())
